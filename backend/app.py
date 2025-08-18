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
import logging

# Spotipy imports
from spotipy import Spotify
from spotify_auth import save_spotify_tokens, get_spotify_tokens, get_user_spotify_client, client_id, client_secret, redirect_uri
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler

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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),        # Writes to file
        logging.StreamHandler()                # Also prints to console
    ]
)

# RQ config
app.config['RQ_REDIS_URL'] = 'redis://localhost:6379/0'
app.config['RQ_DEFAULT_TIMEOUT'] = 1800
redis_conn = Redis.from_url(app.config['RQ_REDIS_URL'])
rq = RQ(app)

class NoCacheHandler(CacheHandler):
    def get_cached_token(self):
        return None
    
    def save_token_to_cache(self, token_info):
        pass

def get_local_spotify_oauth(scope=SPOTIFY_SCOPES):
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        show_dialog=True,
        cache_handler=NoCacheHandler()  # Use the custom handler instead of None
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
        logging.warning("JWT verification failed: %s", e)
        return {"msg": "Invalid token"}, 401

    session["auth0_id"] = auth0_id
    sp_oauth_local = get_local_spotify_oauth()
    auth_url = sp_oauth_local.get_authorize_url()
    logging.info("Redirecting user to Spotify auth URL: %s", auth_url)
    return redirect(auth_url)

@app.route("/api/spotify/callback")
def spotify_callback():
    code = request.args.get("code")
    logging.info("Spotify callback received with code: %s", code)
    logging.debug("Session contents: %s", dict(session))

    sp_oauth_local = get_local_spotify_oauth("user-read-recently-played")

    try:
        token_info = sp_oauth_local.get_access_token(code)
        logging.debug("Spotify token info: %s", json.dumps(token_info, indent=2))
    except Exception as e:
        logging.error("Spotify token exchange error: %s", e)
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

    if not refresh_token:
        existing_tokens = get_spotify_tokens(user_id)
        logging.debug("Existing tokens for user_id %s: %s", user_id, existing_tokens)
        if existing_tokens:
            refresh_token = existing_tokens["refresh_token"]
            logging.info("Reusing existing refresh token")

    if not (access_token and refresh_token and expires_at):
        return jsonify({"error": "Incomplete token information"}), 500

    try:
        logging.info("Saving Spotify tokens for user_id=%s", user_id)
        save_spotify_tokens(user_id, access_token, refresh_token, expires_at)

        sp = Spotify(auth=access_token)
        profile = sp.current_user()
        email = profile.get("email", "N/A")
        logging.info("Fetched Spotify profile: %s (%s)", email, profile.get("id"))
        return redirect("/")
    except Exception as e:
        logging.error("Failed to save Spotify tokens or fetch profile: %s", e)
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
        logging.error("Error fetching recently played: %s", e)
        return jsonify({"error": "Failed to fetch data", "details": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def db_status():
    try:
        run_query("SELECT 1")
        return jsonify({"status": "OK", "message": "Database connected"}), 200
    except Exception as e:
        logging.error("Database connection check failed: %s", e)
        return jsonify({"status": "ERROR", "message": str(e)}), 500

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
        logging.error("Error fetching job status: %s", e)
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
    song_image_url = None
    if snapshot.get("most_played_song_id"):
        song_row = run_query(
            """
            SELECT s.track_name, a.artist_name, s.image_url
            FROM core_songs s
            JOIN core_artists a ON s.artist_id = a.artist_id
            WHERE s.song_id = %s
            """,
            (snapshot["most_played_song_id"],),
            fetchone=True,
            dict_cursor=True
        )
        if song_row:
            song_name = song_row["track_name"]
            song_artist_name = song_row["artist_name"]
            song_image_url = song_row["image_url"]

    snapshot["most_played_song"] = song_name
    snapshot["most_played_song_artist"] = song_artist_name
    snapshot["most_played_song_image_url"] = song_image_url

    # Most played artist
    artist_name = None
    artist_image_url = None
    if snapshot.get("most_played_artist_id"):
        artist_row = run_query(
            """
            SELECT artist_name, JSON_UNQUOTE(JSON_EXTRACT(artist_images, '$[0].url')) AS image_url
            FROM core_artists
            WHERE artist_id = %s
            """,
            (snapshot["most_played_artist_id"],),
            fetchone=True,
            dict_cursor=True
        )
        if artist_row:
            artist_name = artist_row["artist_name"]
            artist_image_url = artist_row["image_url"]

    snapshot["most_played_artist"] = artist_name
    snapshot["most_played_artist_image_url"] = artist_image_url

    # Binge song
    binge_song_name = None
    binge_artist_name = None
    binge_image_url = None
    if snapshot.get("longest_binge_song_id"):
        binge_row = run_query(
            """
            SELECT s.track_name, a.artist_name, s.image_url
            FROM core_songs s
            JOIN core_artists a ON s.artist_id = a.artist_id
            WHERE s.song_id = %s
            """,
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

    # 1. Check for existing snapshot
    snapshot = fetch_snapshot()
    
    # 2. If we have a snapshot, check if it's fresh enough
    if snapshot:
        # Ensure snapshot_time is parsed as UTC
        snapshot_time = pendulum.instance(snapshot["snapshot_time"], tz="UTC")
        now = pendulum.now("UTC")

        age_minutes = now.diff(snapshot_time).in_minutes()
        print(f"Snapshot time (UTC): {snapshot_time}", flush=True)
        print(f"Current time (UTC): {now}", flush=True)
        print(f"Age in minutes: {age_minutes}", flush=True)
        
        if age_minutes < 10:  # Snapshot is fresh (less than 10 minutes old)
            redis_conn.delete(redis_key)  # Clear any running job marker
            snapshot = enrich_snapshot(snapshot)
            return jsonify({"snapshot": snapshot}), 200

    # 3. Check if a job is already running
    if redis_conn.exists(redis_key):
        return jsonify({"message": "Snapshot generation in progress"}), 202

    # 4. No fresh snapshot and no running job, start a new one
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

    # Search songs
    songs = run_query("""
        SELECT
            s.song_id,
            s.track_name,
            a.artist_name,
            s.image_url
        FROM core_songs s
        JOIN core_artists a ON s.artist_id = a.artist_id
        WHERE s.track_name LIKE %s OR a.artist_name LIKE %s
        LIMIT 30
    """, (f"%{query}%", f"%{query}%"), dict_cursor=True)

    # Search artists with safe JSON extraction
    artists = run_query("""
        SELECT
            artist_id,
            artist_name,
            CASE
                WHEN JSON_VALID(artist_images)
                THEN JSON_UNQUOTE(JSON_EXTRACT(artist_images, '$[0].url'))
                ELSE NULL
            END AS image_url
        FROM core_artists
        WHERE artist_name LIKE %s
        LIMIT 30
    """, (f"%{query}%",), dict_cursor=True)

    return jsonify({
        "songs": songs,
        "artists": artists
    }), 200


@app.route('/api/song/<song_id>', methods=['GET'])
def get_song_details(song_id):
    # Get song info with extended details
    song = run_query("""
        SELECT 
            s.song_id,
            s.spotify_uri,
            s.track_name,
            a.artist_name,
            a.artist_id,
            s.album_name,
            s.album_id,
            s.album_type,
            s.album_uri,
            s.release_date,
            s.release_date_precision,
            s.duration_ms,
            s.is_explicit,
            s.image_url,
            s.preview_url,
            s.popularity,
            s.is_local,
            s.created_at
        FROM core_songs s
        JOIN core_artists a ON s.artist_id = a.artist_id
        WHERE s.song_id = %s
    """, (song_id,), fetchone=True, dict_cursor=True)

    if not song:
        return jsonify({"error": "Song not found"}), 404

    # Calculate stats from usage_logs using ts
    stats = run_query("""
        SELECT
            MIN(ts) AS first_played,
            MAX(ts) AS last_played,
            COUNT(*) AS play_count,
            COUNT(DISTINCT DATE(ts)) as days_played
        FROM usage_logs
        WHERE song_id = %s
    """, (song_id,), fetchone=True, dict_cursor=True)

    # Calculate longest binge
    binge_stats = run_query("""
        SELECT COUNT(*) as binge_count
        FROM (
            SELECT COUNT(*) as consecutive_plays
            FROM (
                SELECT ts,
                    LAG(ts) OVER (ORDER BY ts) as prev_ts
                FROM usage_logs
                WHERE song_id = %s
                ORDER BY ts
            ) t
            WHERE TIMESTAMPDIFF(MINUTE, prev_ts, ts) <= 30
            GROUP BY DATE_FORMAT(ts, '%%Y-%%m-%%d %%H:%%i')
        ) b
        ORDER BY binge_count DESC
        LIMIT 1
    """, (song_id,), fetchone=True, dict_cursor=True)

    song.update(stats or {})
    song["longest_binge"] = binge_stats["binge_count"] if binge_stats else 0

    return jsonify(song), 200

@app.route('/api/artist/<int:artist_id>', methods=['GET'])
def get_artist_details(artist_id):
    artist = run_query("""
        SELECT
            artist_id,
            artist_name AS name,
            artist_uri AS spotify_uri,
            artist_followers,
            artist_popularity,
            JSON_UNQUOTE(JSON_EXTRACT(artist_images, '$[0].url')) AS image_url,
            artist_genres,
            (
                SELECT COUNT(*) FROM usage_logs ul
                JOIN core_songs cs ON ul.song_id = cs.song_id
                WHERE cs.artist_id = a.artist_id
            ) AS total_streams
        FROM core_artists a
        WHERE artist_id = %s
    """, (artist_id,), dict_cursor=True)

    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    artist_data = artist[0]
    try:
        genres = json.loads(artist_data.get("artist_genres") or "[]")
        if not genres:
            genres = ["Unknown"]
    except Exception:
        genres = ["Unknown"]
    artist_data["genres"] = genres

    return jsonify(artist_data), 200

@app.route('/api/lists/songs', methods=['GET'])
@jwt_required()
def get_top_songs():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    # Parse query parameters
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "Invalid limit"}), 400

    # Build WHERE clause
    filters = ["ul.user_id = %s"]
    params = [user_id]

    if start:
        filters.append("ul.ts >= %s")
        params.append(start)
    if end:
        filters.append("ul.ts <= %s")
        params.append(end)

    where_clause = " AND ".join(filters)

    query = f"""
        SELECT
            s.song_id,
            s.track_name,
            a.artist_name,
            s.artist_id,
            s.image_url,
            COUNT(ul.usage_id) AS play_count
        FROM usage_logs ul
        JOIN core_songs s ON ul.song_id = s.song_id
        JOIN core_artists a ON s.artist_id = a.artist_id
        WHERE {where_clause}
        GROUP BY s.song_id, s.track_name, a.artist_name, s.image_url
        ORDER BY play_count DESC
        LIMIT {limit}
    """

    songs = run_query(query, tuple(params), dict_cursor=True)
    return jsonify({"songs": songs}), 200

@app.route('/api/lists/artists', methods=['GET'])
@jwt_required()
def get_top_artists():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    # Parse query parameters
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "Invalid limit"}), 400

    # Build WHERE clause
    filters = ["ul.user_id = %s"]
    params = [user_id]

    if start:
        filters.append("ul.ts >= %s")
        params.append(start)
    if end:
        filters.append("ul.ts <= %s")
        params.append(end)

    where_clause = " AND ".join(filters)

    query = f"""
        SELECT
            a.artist_id,
            a.artist_name,
            MAX(s.image_url) AS image_url,
            COUNT(ul.usage_id) AS play_count
        FROM usage_logs ul
        JOIN core_songs s ON ul.song_id = s.song_id
        JOIN core_artists a ON s.artist_id = a.artist_id
        WHERE {where_clause}
        GROUP BY a.artist_id, a.artist_name
        ORDER BY play_count DESC
        LIMIT {limit}
    """

    artists = run_query(query, tuple(params), dict_cursor=True)
    return jsonify({"artists": artists}), 200

@app.route('/api/artist/<int:artist_id>/songs', methods=['GET'])
@jwt_required()
def get_top_songs_by_artist(artist_id):
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    try:
        limit = int(request.args.get("limit", 100))
    except ValueError:
        return jsonify({"error": "Invalid limit"}), 400

    query = """
        SELECT
            s.song_id,
            s.track_name,
            s.image_url,
            COUNT(ul.usage_id) AS play_count,
            MIN(ul.ts) AS first_played,
            MAX(ul.ts) AS last_played
        FROM usage_logs ul
        JOIN core_songs s ON ul.song_id = s.song_id
        WHERE ul.user_id = %s AND s.artist_id = %s
        GROUP BY s.song_id, s.track_name, s.image_url
        ORDER BY play_count DESC
        LIMIT %s
    """

    songs = run_query(query, (user_id, artist_id, limit), dict_cursor=True)

    for song in songs:
        if song['first_played']:
            song['first_played'] = pendulum.instance(song['first_played']).to_iso8601_string()
        if song['last_played']:
            song['last_played'] = pendulum.instance(song['last_played']).to_iso8601_string()

    return jsonify({"songs": songs}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)