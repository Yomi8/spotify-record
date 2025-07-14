from flask import Flask, request, jsonify, Blueprint
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
from celery.result import AsyncResult
from celery_app import celery
from tasks import process_spotify_json_file, update_user_snapshots
import mysql.connector.pooling
from datetime import datetime
import requests
import sys
import os
import json
import uuid

snapshots_bp = Blueprint("snapshots", __name__)

print("Python executing Flask app:", sys.executable)

SPOTIFY_TOKEN = "972e38506b164833aea4abe281f96585"

app = Flask(__name__)
CORS(app, origins=["https://yomi16.nz", "http://127.0.0.1:3000"], supports_credentials=True)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

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

db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="spotify_pool",
    pool_size=10,
    host="127.0.0.1",
    user="recordserver",
    password="$3000JHCpaperPC",
    database="spotifydb"
)

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

@app.route('/api/status', methods=['GET'])
def db_status():
    try:
        run_query("SELECT 1")
        return jsonify({"status": "OK", "message": "Database connected"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    result = AsyncResult(task_id, app=celery)
    response = {
        "task_id": task_id,
        "status": result.status
    }

    # If task is in progress or failed, get metadata (e.g., progress, errors)
    if result.state == "PROGRESS" or result.state == "FAILURE":
        response["progress"] = result.info  # This includes what you passed to update_state

    # If task finished
    elif result.ready():
        response["result"] = result.result

    return jsonify(response)

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

@app.route('/api/upload-spotify-json', methods=['POST'])
@jwt_required()
def upload_spotify_json():
    auth0_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Invalid file"}), 400

    # Save uploaded file to temp folder
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{uuid.uuid4()}.json"
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)

    # Launch celery task
    task = process_spotify_json_file.delay(filepath, auth0_id)

    return jsonify({"status": "processing", "task_id": task.id}), 202

@snapshots_bp.route("/api/snapshots/generate", methods=["POST"])
@jwt_required()
def generate_snapshots():
    user_id = get_jwt_identity()  # assuming this returns user_id

    # Trigger the task for only the requesting user
    task = update_user_snapshots.apply_async(args=[user_id])

    return jsonify({"status": "started", "task_id": task.id}), 202

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
