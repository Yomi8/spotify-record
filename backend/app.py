# Flask package imports
from flask import Flask, request, jsonify, redirect, session
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_cors import CORS
from flask_rq2 import RQ

# Worker imports
from redis import Redis
from rq.job import Job
from tasks import process_spotify_json_file, generate_snapshot_for_period, generate_snapshot_for_range

# Database and utility imports
import mysql.connector.pooling
import pendulum

import sys
import os
import json
import uuid
import requests
from base64 import b64encode
import urllib.parse

from spotipy import Spotify
from spotify_auth import sp_oauth, get_user_spotify_client

print("Python executing Flask app:", sys.executable)

SPOTIFY_SCOPES = "user-read-recently-played"

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

app.config["SESSION_COOKIE_SECURE"] = True  # Only send cookie over HTTPS
app.config["SESSION_COOKIE_SAMESITE"] = "None"  # Allow cross-site cookies
app.config["SESSION_COOKIE_DOMAIN"] = "yomi16.nz"  # Set to your domain

jwt = JWTManager(app)

# RQ config
app.config['RQ_REDIS_URL'] = 'redis://localhost:6379/0'
redis_conn = Redis.from_url(app.config['RQ_REDIS_URL'])
rq = RQ(app)

# MySQL config
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="spotify_pool",
    pool_size=10,
    host="127.0.0.1",
    user="recordserver",
    password="$3000JHCpaperPC",
    database="spotifydb"
)

# Basic query execution
def run_query(query, params=None, commit=False, fetchone=False, dict_cursor=False):
    conn = db_pool.get_connection()
    try:
        with conn.cursor(dictionary=dict_cursor) as cursor:
            cursor.execute(query, params or ())
            result = (
                cursor.fetchone() if fetchone else
                cursor.fetchall() if cursor.with_rows else None
            )
        if commit:
            conn.commit()
        return result
    finally:
        conn.close()

def save_spotify_tokens(user_id, access_token, refresh_token, expires_at):
    query = """
        INSERT INTO spotify_tokens (user_id, access_token, refresh_token, expires_at)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            access_token = VALUES(access_token),
            refresh_token = VALUES(refresh_token),
            expires_at = VALUES(expires_at)
    """
    run_query(query, (user_id, access_token, refresh_token, expires_at), commit=True)

def get_spotify_tokens(user_id):
    query = "SELECT access_token, refresh_token, expires_at FROM spotify_tokens WHERE user_id = %s"
    return run_query(query, (user_id,), fetchone=True, dict_cursor=True)

@app.route("/api/spotify/login")
def spotify_login():
    token = request.args.get("access_token")
    if not token:
        return {"msg": "Missing token"}, 401

    # Manually verify the JWT from the query param
    try:
        verify_jwt_in_request()
        auth0_id = get_jwt_identity()
    except Exception as e:
        return {"msg": "Invalid token"}, 401

    session["auth0_id"] = auth0_id
    print(f"SpotifyOAuth redirect_uri: {sp_oauth.redirect_uri}", flush=True)
    auth_url = sp_oauth.get_authorize_url()
    print(f"Auth URL: {auth_url}", flush=True)
    return redirect(auth_url)

@app.route("/api/spotify/callback")
def spotify_callback():
    code = request.args.get("code")
    print(f"Spotify callback code: {code}", flush=True)

    print(f"Handling callback, redirect_uri is: {sp_oauth.redirect_uri}", flush=True)

    try:
        # This exchanges the code and stores the token in cache
        sp_oauth.get_access_token(code)
        token_info = sp_oauth.get_cached_token()
        print(f"Token info: {json.dumps(token_info, indent=2)}", flush=True)
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
    if not auth0_id:
        return jsonify({"error": "Missing user session"}), 400

    user_id = get_user_id_from_auth0(auth0_id)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")
    expires_at = token_info.get("expires_at")

    # 🛠 Fallback if refresh_token is missing (Spotify may omit it on reauth)
    if not refresh_token:
        existing_tokens = get_spotify_tokens(user_id)
        if existing_tokens:
            refresh_token = existing_tokens["refresh_token"]
            print("Reusing existing refresh token", flush=True)

    if not (access_token and refresh_token and expires_at):
        return jsonify({"error": "Incomplete token information"}), 500

    try:
        save_spotify_tokens(user_id, access_token, refresh_token, expires_at)
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

# Translate auth0_id to internal user_id
def get_user_id_from_auth0(auth0_id):
    conn = db_pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM core_users WHERE auth0_id = %s", (auth0_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
