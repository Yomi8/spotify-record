from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_cors import CORS
import mysql.connector
import json
import os
from datetime import datetime
import json, requests

import sys
print("Python executing Flask app:", sys.executable)


SPOTIFY_TOKEN = "972e38506b164833aea4abe281f96585"

app = Flask(__name__)

CORS(app, origins=["https://yomi16.nz", "http://127.0.0.1:3000"], supports_credentials=True)

app.config['UPLOAD_FOLDER'] = 'uploads'  # create this folder
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_ALGORITHM"] = "RS256"
app.config["JWT_PUBLIC_KEY"] = """
-----BEGIN CERTIFICATE-----
MIIDHTCCAgWgAwIBAgIJYhpuuDywxD5cMA0GCSqGSIb3DQEBCwUAMCwxKjAoBgNV
BAMTIWRldi1pZDVmbTJicWQxNmkxbnJ2LmF1LmF1dGgwLmNvbTAeFw0yNTA1Mjcy
MTM1MTBaFw0zOTAyMDMyMTM1MTBaMCwxKjAoBgNVBAMTIWRldi1pZDVmbTJicWQx
NmkxbnJ2LmF1LmF1dGgwLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
ggEBAMktdbK5XQMHp9OImMbZ8n3lv0sL1842NZ1b2vNb8JNcmR1BQQKTZa5T7kkt
itUi5zv7gCrJ5XU39uyb74L/E4ekHQTM9H2KgoxHYRK854AnWDusbJjU4ogdmlyS
I5IxL1YPj9qygId2rFICOujLj+Y5CN0VDtthcUlkBnHkHMI+WUcOyelSDPXZ+V+I
ncnONnR6c3z+YxOBzyosrn+EvbnKYoJxrEUzlYUsA2fqtDphJgw/B2pb9EVnhDAD
xwTC8Yi7i05ulN4DfSBGzKOp1POTrfNG2cQ2DlM+pu4lhkKpK5xBDMsvoXwQJqFJ
JvMEmJZof4PBI5tl1aN+fIpntL8CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAd
BgNVHQ4EFgQUW2gTzwznATWc9YQtWMFAltpMrxUwDgYDVR0PAQH/BAQDAgKEMA0G
CSqGSIb3DQEBCwUAA4IBAQCYEWzX/I84pidjcI9WsOw9tFpDPdDE9JB3uRCAOMtx
HZNwCM2ObSh7jyVpG6n/81fUx0I8A3whfLiaYUIe8+YzEz+FfidmH1hxn+6tE9FP
dRMRRk8XLgH2BOmSixZlS6vg5HhtnyMxw7HsRpY1r+YYFyibUwgltJA4HCiXoQZ4
02P2xn/jNgVLk75FLSXI6mI35CPU19IpxAQXVYgF9+goDh2bp7us40A/Kk6mfQbx
V1WJHFPMfBzobLvLQDH9JJ8XU2Z+t6qonzYn/VlB6i5gwLjOZGxRZiqyBwpv6FeV
aXiDs+VEZT2i6/V47jtSW8gzBTV+IIVJSQLYfV6qi10H
-----END CERTIFICATE-----
"""

jwt = JWTManager(app)

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="recordserver",
    password="$3000JHCpaperPC",
    database="spotifydb"
)

cursor = db.cursor()

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"status": "OK", "message": "Test successful"}), 200

@app.route('/api/status', methods=['GET'])
def db_status():
    try:
        cursor.execute("SELECT 1")
        return jsonify({"status": "OK", "message": "Database connected"}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route('/api/users')
def get_users():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM core_users")
    users = cursor.fetchall()
    cursor.close()
    return jsonify(users)

@app.route('/api/users/sync', methods=['POST'])
def sync_user():
    data = request.get_json()

    required_fields = ['auth0_id', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "ERROR", "message": "Missing required fields"}), 400

    auth0_id = data['auth0_id']
    email = data['email']
    username = data.get('username', None)
    show_explicit = int(data.get('show_explicit', 1))
    dark_mode = int(data.get('dark_mode', 0))

    try:
        cursor = db.cursor()
        # Insert or update user
        query = """
        INSERT INTO core_users (auth0_id, email, username, show_explicit, dark_mode)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            email = VALUES(email),
            username = VALUES(username),
            show_explicit = VALUES(show_explicit),
            dark_mode = VALUES(dark_mode)
        """
        cursor.execute(query, (auth0_id, email, username, show_explicit, dark_mode))
        db.commit()
        cursor.close()
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
        return {
            "track_name": d["name"],
            "artist_name": d["artists"][0]["name"],
            "album_name": d["album"]["name"],
            "duration_ms": d["duration_ms"],
            "image_url": d["album"]["images"][0]["url"] if d["album"]["images"] else None
        }
    return None


@app.route('/api/upload-spotify-json', methods=['POST'])
@jwt_required()
def upload_spotify_json():
    try:
        token = request.headers.get("Authorization", "").split(" ")[1]
        import jwt
        print("Token header:", jwt.get_unverified_header(token))
    except Exception as e:
        print("JWT header parse failed:", e)

    auth0_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Invalid file"}), 400

    try:
        content = file.read(20 * 1024 * 1024)
        data = json.loads(content)

        if not isinstance(data, list):
            return jsonify({"error": "Expected a list of streaming records"}), 400

        cursor = db.cursor()

        # Get user_id from auth0_id
        cursor.execute("SELECT id FROM core_users WHERE auth0_id = %s", (auth0_id,))
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

            # Check if stream already exists for user
            cursor.execute("SELECT id FROM usage_logs WHERE user_id = %s AND ts = %s", (user_id, ts))
            if cursor.fetchone():
                continue  # skip duplicates by timestamp

            # Get or insert song
            cursor.execute("SELECT id FROM core_songs WHERE spotify_uri = %s", (uri,))
            song = cursor.fetchone()
            if not song:
                metadata = get_spotify_metadata(uri)
                if not metadata:
                    continue  # skip if Spotify API fails

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

            # Insert stream
            cursor.execute("""
                INSERT INTO usage_logs (
                    user_id, song_id, ts, ms_played, platform, conn_country, ip_addr,
                    spotify_track_uri, episode_name, episode_show_name, reason_start,
                    reason_end, shuffle, skipped, offline, offline_timestamp, incognito_mode
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, song_id, datetime.fromisoformat(ts.replace("Z", "+00:00")),
                stream.get("ms_played"), stream.get("platform"), stream.get("conn_country"),
                stream.get("ip_addr"), uri, stream.get("episode_name"),
                stream.get("episode_show_name"), stream.get("reason_start"),
                stream.get("reason_end"), stream.get("shuffle"), stream.get("skipped"),
                stream.get("offline"), stream.get("offline_timestamp"), stream.get("incognito_mode")
            ))
            inserted += 1

        db.commit()
        cursor.close()
        return jsonify({"status": "success", "inserted": inserted}), 200

    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
