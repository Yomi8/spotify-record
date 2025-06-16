from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
import mysql.connector
import json
import os
from datetime import datetime
import requests
import sys

print("Python executing Flask app:", sys.executable)

SPOTIFY_TOKEN = "972e38506b164833aea4abe281f96585"

app = Flask(__name__)

CORS(app, origins=["https://yomi16.nz", "http://127.0.0.1:3000"], supports_credentials=True)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# JWT Setup
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

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="recordserver",
    password="$3000JHCpaperPC",
    database="spotifydb",
    pool_name="spotify_pool",
    pool_size=5
)

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "OK", "message": "Test successful"}), 200

@app.route('/api/status', methods=['GET'])
def db_status():
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT 1")
        return jsonify({"status": "OK", "message": "Database connected"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route('/api/users')
def get_users():
    with db.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM core_users")
        users = cursor.fetchall()
    return jsonify(users)

@app.route('/api/users/sync', methods=['POST'])
def sync_user():
    data = request.get_json()
    required_fields = ['auth0_id', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "ERROR", "message": "Missing required fields"}), 400

    try:
        with db.cursor() as cursor:
            query = """
                INSERT INTO core_users (auth0_id, email, username, show_explicit, dark_mode)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    email = VALUES(email),
                    username = VALUES(username),
                    show_explicit = VALUES(show_explicit),
                    dark_mode = VALUES(dark_mode)
            """
            cursor.execute(query, (
                data['auth0_id'],
                data['email'],
                data.get('username'),
                int(data.get('show_explicit', 1)),
                int(data.get('dark_mode', 0))
            ))
            db.commit()
        return jsonify({"status": "OK", "message": "User synced successfully"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

def get_spotify_metadata(uri):
    track_uri = uri.split(":")[-1]
    r = requests.get(f"https://api.spotify.com/v1/tracks/{track_uri}", headers={
        "Authorization": f"Bearer {SPOTIFY_TOKEN}"
    })
    if r.status_code == 200:
        d = r.json()
        album = d["album"]
        return {
            "track_name": d["name"],
            "artist_name": d["artists"][0]["name"],
            "artist_id": d["artists"][0]["id"],

            "album_name": album["name"],
            "album_id": album["id"],
            "album_type": album.get("album_type"),
            "album_uri": album.get("uri"),
            "release_date": album.get("release_date"),
            "release_date_precision": album.get("release_date_precision"),

            "duration_ms": d["duration_ms"],
            "is_explicit": d["explicit"],

            "image_url": album["images"][0]["url"] if album["images"] else None,
            "preview_url": d.get("preview_url"),
            "popularity": d.get("popularity"),
            "is_local": d.get("is_local", False)
        }
    return None

@app.route('/api/upload-spotify-json', methods=['POST'])
@jwt_required()
def upload_spotify_json():
    auth0_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Invalid file"}), 400

    try:
        data = json.loads(file.read())

        if not isinstance(data, list):
            return jsonify({"error": "Expected a list of streaming records"}), 400

        # Get user with auth_id
        with db.cursor() as cursor:
            cursor.execute("SELECT user_id FROM core_users WHERE auth0_id = %s", (auth0_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "User not found"}), 404
            user_id = user[0]

        inserted = 0
        for stream in data:
            ts = stream.get("ts")
            uri = stream.get("spotify_track_uri")
            if not ts or not uri:
                continue

            with db.cursor() as cursor:
                cursor.execute("SELECT usage_id FROM usage_logs WHERE user_id = %s AND ts = %s", (user_id, ts))
                if cursor.fetchone():
                    continue  # Duplicate

                cursor.execute("SELECT song_id FROM core_songs WHERE spotify_uri = %s", (uri,))
                song = cursor.fetchone()
                if not song:
                    metadata = get_spotify_metadata(uri)
                    if not metadata:
                        continue

                    cursor.execute("""
                        INSERT INTO core_songs (spotify_uri, track_name, artist_name, album_name, duration_ms, image_url)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        uri,
                        metadata["track_name"],
                        metadata["artist_name"],
                        metadata["album_name"],
                        metadata["duration_ms"],
                        metadata["image_url"]
                    ))
                    song_id = cursor.lastrowid
                else:
                    song_id = song[0]

                cursor.execute("""
                    INSERT INTO core_songs (
                        spotify_uri, track_name,
                        artist_name, artist_id,
                        album_name, album_id, album_type, album_uri,
                        release_date, release_date_precision,
                        duration_ms, is_explicit,
                        image_url, preview_url, popularity, is_local
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    uri, metadata["track_name"],
                    metadata["artist_name"], metadata["artist_id"],
                    metadata["album_name"], metadata["album_id"], metadata["album_type"], metadata["album_uri"],
                    metadata["release_date"], metadata["release_date_precision"],
                    metadata["duration_ms"], metadata["is_explicit"],
                    metadata["image_url"], metadata["preview_url"], metadata["popularity"], metadata["is_local"]
                ))

                inserted += 1

        db.commit()
        return jsonify({"status": "success", "inserted": inserted}), 200

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
