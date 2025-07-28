# Flask package imports
from flask import Flask, request, jsonify, redirect, session
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_cors import CORS
from flask_rq2 import RQ

# Worker imports
from redis import Redis
from rq.job import Job
from tasks import process_spotify_json_file, generate_snapshot_for_period, generate_snapshot_for_range, fetch_recently_played_and_store

# Database imports
from db import run_query, get_user_id_from_auth0

# Utility imports
import sys
import os
import json
import uuid
import pendulum
import requests
from base64 import b64encode
import urllib.parse

# Spotipy imports
from spotipy import Spotify
from spotify_auth import save_spotify_tokens, get_spotify_tokens, get_user_spotify_client, client_id, client_secret, redirect_uri
from spotipy.oauth2 import SpotifyOAuth

SPOTIFY_SCOPES = "user-read-recently-played user-read-email"

app = Flask(__name__)
CORS(app, origins=["https://yomi16.nz", "http://127.0.0.1:3000"], supports_credentials=True)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "73268weyuhyg423uqw9dihefgry5423^&T&&*@(#&EGTY")

# Upload config
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# JWT config
app.config["JWT_TOKEN_LOCATION"] = ["headers", "query_string"]
app.config["JWT_ALGORITHM"] = "RS256"
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["JWT_QUERY_STRING_NAME"] = "access_token"
app.config["JWT_PUBLIC_KEY"] = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyS11srldAwen04iYxtny
feW/SwvXzjY1nVva81vwk1yZHUFBApNlrlPuSS2K1SLnO/uAKsnldTf27Jvvgv8T
h6QdBMz0fYqCjEdhErzngCdYO6xsmNTiiB2aXJIjkjEvVg+P2rKAh3asUgI66MuP
5jkI3RUO22FxSWQGceQcwj5ZRw7J6VIM9dn5X4idyc42dHpzfP5jE4HPKiyuf4S9
ucpignGsRTOVhSwDZ+q0OmEmDD8Halv0RWeEMAPHBMLxiLuLTm6U3gN9IEbMo6nU
85Ot80bZxDYOUz6m7iWGQqkrnEEMyy+hfBAmoUkm8wSYlmh/g8Ejm2XVo358ime0
vwIDAQAB
-----END PUBLIC KEY-----
"""

# Session config
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_DOMAIN"] = "yomi16.nz"

jwt = JWTManager(app)

# RQ config
app.config['RQ_REDIS_URL'] = 'redis://localhost:6379/0'
redis_conn = Redis.from_url(app.config['RQ_REDIS_URL'])
rq = RQ(app)

def get_local_spotify_oauth(scope=SPOTIFY_SCOPES):
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        show_dialog=True,
        cache_handler=None
    )

@app.route("/api/spotify/login")
def spotify_login():
    token = request.args.get("access_token")
    if not token:
        return {"msg": "Missing token"}, 401

    try:
        verify_jwt_in_request()
        auth0_id = get_jwt_identity()
    except Exception as e:
        return {"msg": "Invalid token"}, 401

    session["auth0_id"] = auth0_id

    # Create a new SpotifyOAuth instance for this request
    sp_oauth_local = get_local_spotify_oauth()
    auth_url = sp_oauth_local.get_authorize_url()
    print(f"Auth URL: {auth_url}", flush=True)
    return redirect(auth_url)

@app.route("/api/spotify/callback")
def spotify_callback():
    code = request.args.get("code")
    print(f"Spotify callback code: {code}", flush=True)
    print(f"Session contents: {dict(session)}", flush=True)

    sp_oauth_local = get_local_spotify_oauth("user-read-recently-played")

    try:
        token_info = sp_oauth_local.get_access_token(code)
        print(f"[DEBUG] token_info: {json.dumps(token_info, indent=2)}", flush=True)
    except Exception as e:
        print(f"Spotify token exchange error: {e}", flush=True)
        if "invalid_grant" in str(e):
            auth0_id = session.get("auth0_id")
            if auth0_id:
                user_id = get_user_id_from_auth0(auth0_id)
                if user_id:
                    run_query("DELETE FROM spotify_tokens WHERE user_id = %s", (user_id,), commit=True)
        return jsonify({"error": f"Failed to get access token: {str(e)}"}), 500

    auth0_id = session.get("auth0_id")
    print(f"auth0_id from session: {auth0_id}", flush=True)
    if not auth0_id:
        return jsonify({"error": "Missing user session"}), 400

    user_id = get_user_id_from_auth0(auth0_id)
    print(f"user_id from db: {user_id}", flush=True)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")
    expires_at = token_info.get("expires_at")
    
    if not refresh_token:
        existing_tokens = get_spotify_tokens(user_id)
        print(f"[DEBUG] Existing tokens for user_id={user_id}: {existing_tokens}", flush=True)
        if existing_tokens:
            refresh_token = existing_tokens["refresh_token"]
            print("Reusing existing refresh token", flush=True)

    if not (access_token and refresh_token and expires_at):
        return jsonify({"error": "Incomplete token information"}), 500

    try:
        print(f"[DEBUG] Saving tokens for user_id={user_id}")
        print(f"[DEBUG] access_token={access_token[:10]}..., refresh_token={refresh_token[:10]}..., expires_at={expires_at}", flush=True)
        save_spotify_tokens(user_id, access_token, refresh_token, expires_at)
        
        # New code to fetch and print Spotify profile information
        sp = Spotify(auth=access_token)
        profile = sp.current_user()
        print(f"[DEBUG] Spotify profile for user_id={user_id}: {profile['email']} ({profile['id']})", flush=True)
        
        return redirect("/")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/spotify/recent", methods=["GET"])
@jwt_required()
def get_recently_played():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)

    if not user_id:
        return jsonify({"error": "User not found"}), 404

    token_row = get_spotify_tokens(user_id)
    if not token_row:
        return jsonify({"error": "Spotify not connected"}), 400

    sp_user = get_user_spotify_client(token_row["access_token"])

    try:
        recent = sp_user.current_user_recently_played(limit=50)
        return jsonify(recent), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch data", "details": str(e)}), 500

# Check if database is connected
@app.route('/api/status', methods=['GET'])
def db_status():
    try:
        run_query("SELECT 1")
        return jsonify({"status": "OK", "message": "Database connected"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# Get status of a job by ID
@app.route("/api/job-status/<job_id>")
def job_status(job_id):
    try:
        conn = Redis.from_url(app.config['RQ_REDIS_URL'])
        job = Job.fetch(job_id, connection=conn)
        status = job.get_status()

        return jsonify({
            "job_id": job.id,
            "status": status,
            "result": job.result,
            "error": job.exc_info if job.is_failed else None,
        }), 200

    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 200

# Sync user data from Auth0
@app.route('/api/users/sync', methods=['POST'])
def sync_user():
    data = request.get_json()
    required_fields = ['auth0_id', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "ERROR", "message": "Missing required fields"}), 400

    try:
        run_query("""
            INSERT INTO core_users (auth0_id, email, username, show_explicit, dark_mode)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                email = VALUES(email),
                username = VALUES(username),
                show_explicit = VALUES(show_explicit),
                dark_mode = VALUES(dark_mode)
        """, (
            data['auth0_id'], data['email'], data.get('username'),
            int(data.get('show_explicit', 1)), int(data.get('dark_mode', 0))
        ), commit=True)
        return jsonify({"status": "OK", "message": "User synced successfully"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# Upload Spotify Extended Listining JSON file
@app.route('/api/upload-spotify-json', methods=['POST'])
@jwt_required()
def upload_spotify_json():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id) 

    if not user_id:
        return jsonify({"error": "User not found"}), 404


    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Invalid file"}), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    unique_filename = f"{uuid.uuid4()}.json"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)

    queue = rq.get_queue()
    job = queue.enqueue(process_spotify_json_file, filepath, user_id)

    return jsonify({"status": "queued", "job_id": job.id}), 202

# Call spotify to fetch recently played tracks
@app.route("/api/spotify/fetch-recent", methods=["POST"])
@jwt_required()
def trigger_fetch_recent():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    queue = rq.get_queue("recent_queue")  # Matches worker queue name
    job = queue.enqueue(fetch_recently_played_and_store, user_id)

    return jsonify({
        "status": "queued",
        "job_id": job.id
    }), 202

def enrich_snapshot(snapshot):
    # Most played song
    song_name = None
    artist_name = None
    image_url = None
    if snapshot.get("most_played_song_id"):
        song_row = run_query(
            "SELECT track_name, artist_name, image_url FROM core_songs WHERE song_id = %s",
            (snapshot["most_played_song_id"],),
            fetchone=True,
            dict_cursor=True
        )
        if song_row:
            song_name = song_row["track_name"]
            artist_name = song_row["artist_name"]
            image_url = song_row["image_url"]

    snapshot["most_played_song"] = song_name
    snapshot["most_played_artist"] = artist_name
    snapshot["most_played_song_image_url"] = image_url

    # Binge song
    binge_song_name = None
    binge_artist_name = None
    binge_image_url = None
    if snapshot.get("longest_binge_song_id"):
        binge_row = run_query(
            "SELECT track_name, artist_name, image_url FROM core_songs WHERE song_id = %s",
            (snapshot["longest_binge_song_id"],),
            fetchone=True,
            dict_cursor=True
        )
        if binge_row:
            binge_song_name = binge_row["track_name"]
            binge_artist_name = binge_row["artist_name"]
            binge_image_url = binge_row["image_url"]

    snapshot["longest_binge_song"] = binge_song_name
    snapshot["longest_binge_artist"] = binge_artist_name
    snapshot["longest_binge_song_image_url"] = binge_image_url

    snapshot["total_plays"] = snapshot.get("total_songs_played")

    return snapshot

# Generate pre-defined snapshots
@app.route("/api/snapshots/generate", methods=["POST"])
@jwt_required()
def generate_snapshots():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)

    if not user_id:
        return jsonify({"error": "User not found"}), 404

    periods = request.json.get("periods")  # expecting a list, e.g. ["day", "year"]
    if not periods:
        return jsonify({"error": "Missing 'periods' in request body"}), 400

    valid_periods = {"day", "week", "month", "year", "lifetime"}

    # Validate input periods
    invalid_periods = [p for p in periods if p not in valid_periods]
    if invalid_periods:
        return jsonify({"error": f"Invalid period types: {invalid_periods}"}), 400

    queue = rq.get_queue()
    jobs = []
    for period in periods:
        job = queue.enqueue(generate_snapshot_for_period, user_id, period)
        jobs.append({"period": period, "job_id": job.id})

    return jsonify({"status": "started", "jobs": jobs}), 202

# Generate custom snapshot for a specific date range
@app.route("/api/snapshots/generate/custom", methods=["POST"])
@jwt_required()
def generate_custom_snapshot():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)

    if not user_id:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    start = data.get("start")
    end = data.get("end")

    if not start or not end:
        return jsonify({"error": "Missing 'start' or 'end' timestamp"}), 400

    try:
        start_dt = pendulum.parse(start)
        end_dt = pendulum.parse(end)
    except Exception as e:
        return jsonify({"error": f"Invalid datetime format: {str(e)}"}), 400

    queue = rq.get_queue()
    job = queue.enqueue(generate_snapshot_for_range, user_id, start_dt, end_dt)
    return jsonify({"status": "started", "job_id": job.id}), 202

@app.route('/api/snapshots/<period>/latest', methods=['GET'])
@jwt_required()
def get_latest_snapshot(period):
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)

    print("Getting latest snapshot for user:", user_id, "period:", period, flush=True)

    redis_key = f"snapshot_job:{user_id}:{period}"
    now = pendulum.now("UTC")

    def fetch_snapshot():
        try:
            snapshot = run_query(
                """
                SELECT *
                FROM user_snapshots
                WHERE user_id = %s AND range_type = %s
                ORDER BY snapshot_time DESC
                LIMIT 1
                """,
                (user_id, period),
                fetchone=True,
                dict_cursor=True,
            )
            return snapshot
        except Exception as e:
            print(f"Error fetching snapshot: {e}", flush=True)
            return None

    # 1. Check for a fresh snapshot first
    snapshot = fetch_snapshot()
    print(f"DEBUG: Initial snapshot fetch result: {snapshot}", flush=True)  # Add flush=True
    if snapshot:
        snapshot_time = pendulum.parse(str(snapshot["snapshot_time"]))
        print(f"DEBUG: snapshot_time={snapshot_time}, now={now}", flush=True)
        age_minutes = now.diff(snapshot_time).in_minutes()
        print(f"DEBUG: age_minutes={age_minutes}", flush=True)
        if age_minutes < 10:
            redis_conn.delete(redis_key)
            snapshot = enrich_snapshot(snapshot)
            return jsonify({"snapshot": snapshot}), 200

    # 2. If no fresh snapshot, check if job is running
    if redis_conn.exists(redis_key):
        snapshot = fetch_snapshot()
        print(f"DEBUG: Redis exists, snapshot fetch result: {snapshot}", flush=True)  # Add flush=True
        if snapshot:
            snapshot_time = pendulum.parse(str(snapshot["snapshot_time"]))
            print(f"DEBUG: snapshot_time={snapshot_time}, now={now}", flush=True)
            age_minutes = now.diff(snapshot_time).in_minutes()
            print(f"DEBUG: age_minutes={age_minutes}", flush=True)
            if age_minutes < 10:
                redis_conn.delete(redis_key)
                snapshot = enrich_snapshot(snapshot)
                return jsonify({"snapshot": snapshot}), 200
        return jsonify({"message": "Snapshot generation in progress"}), 202

    # 3. No job running, start job
    redis_conn.set(redis_key, "1", ex=600)  # expire in 10 mins
    queue = rq.get_queue()
    job = queue.enqueue(generate_snapshot_for_period, user_id, period)

    return jsonify({
        "message": "Generating new snapshot",
        "job_id": job.id
    }), 202

@app.route('/api/search', methods=['GET'])
def search_songs_artists():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Missing search query"}), 400

    # Search both songs and artists (case-insensitive, partial match)
    results = run_query("""
        SELECT song_id, track_name, artist_name, image_url
        FROM core_songs
        WHERE track_name LIKE %s OR artist_name LIKE %s
        LIMIT 30
    """, (f"%{query}%", f"%{query}%"), dict_cursor=True)

    return jsonify({"results": results}), 200

@app.route('/api/song/<song_id>', methods=['GET'])
def get_song_details(song_id):
    # Get song info
    song = run_query("""
        SELECT song_id, track_name, artist_name, image_url
        FROM core_songs
        WHERE song_id = %s
    """, (song_id,), fetchone=True, dict_cursor=True)

    if not song:
        return jsonify({"error": "Song not found"}), 404

    # Calculate stats from usage_logs using ts
    stats = run_query("""
        SELECT
            MIN(ts) AS first_played,
            MAX(ts) AS last_played,
            COUNT(*) AS play_count
        FROM usage_logs
        WHERE song_id = %s
    """, (song_id,), fetchone=True, dict_cursor=True)

    # Optionally, implement longest binge logic here if you define it
    song.update(stats or {})
    song["longest_binge"] = None  # Placeholder for now

    return jsonify(song), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
