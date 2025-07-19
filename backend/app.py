# Flask package imports
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_rq2 import RQ

# Worker imports
from redis import Redis
from rq import Queue
from rq.job import Job
from tasks import process_spotify_json_file, generate_snapshot_for_period, generate_snapshot_for_range

# Database and utility imports
import mysql.connector.pooling
import pendulum

import sys
import os
import json
import uuid

print("Python executing Flask app:", sys.executable)

SPOTIFY_TOKEN = "972e38506b164833aea4abe281f96585"

app = Flask(__name__)
CORS(app, origins=["https://yomi16.nz", "http://127.0.0.1:3000"], supports_credentials=True)


# Upload config
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# JWT config
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_ALGORITHM"] = "RS256"
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
jwt = JWTManager(app)

# RQ config
app.config['RQ_REDIS_URL'] = 'redis://localhost:6379/0'
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
def run_query(query, params=None, commit=False, fetchone=False):
    conn = db_pool.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            result = cursor.fetchone() if fetchone else cursor.fetchall() if cursor.with_rows else None
        if commit:
            conn.commit()
        return result
    finally:
        conn.close()

# Translate auth0_id to internal user_id
def get_user_id_from_auth0(auth0_id):
    """
    Lookup internal user_id from auth0_id. Returns user_id (int) or None.
    """
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

    job = rq.get_queue().enqueue(process_spotify_json_file, filepath, user_id)

    return jsonify({"status": "queued", "job_id": job.id}), 202

# Generate pre-defined snapshots
@app.route("/api/snapshots/generate", methods=["POST"])
@jwt_required()
def generate_snapshots():
    auth0_id = get_jwt_identity()
    user_id = get_user_id_from_auth0(auth0_id)

    if not user_id:
        return jsonify({"error": "User not found"}), 404

    period = request.json.get("period", "day")
    if period not in {"day", "week", "month", "year", "lifetime"}:
        return jsonify({"error": "Invalid period type"}), 400

    job = rq.get_queue(generate_snapshot_for_period, user_id, period)
    return jsonify({"status": "started", "job_id": job.id}), 202

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

    job = rq.get_queue(generate_snapshot_for_range, user_id, start_dt, end_dt)
    return jsonify({"status": "started", "job_id": job.id}), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
