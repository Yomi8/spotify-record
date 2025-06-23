import json
from datetime import datetime
from celery_app import celery
import mysql.connector.pooling
import requests
import os

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_TOKEN_INFO = {"access_token": None, "expires_at": 0}
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

# Setup MySQL connection pool (reuse same config)
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="spotify_pool",
    pool_size=5,
    host="127.0.0.1",
    user="recordserver",
    password="$3000JHCpaperPC",
    database="spotifydb"
)

def get_spotify_token():
    # Reuse if not expired
    if SPOTIFY_TOKEN_INFO["access_token"] and SPOTIFY_TOKEN_INFO["expires_at"] > time.time():
        return SPOTIFY_TOKEN_INFO["access_token"]

    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}"}
    data = {"grant_type": "client_credentials"}

    r = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    r.raise_for_status()

    token_data = r.json()
    SPOTIFY_TOKEN_INFO["access_token"] = token_data["access_token"]
    SPOTIFY_TOKEN_INFO["expires_at"] = time.time() + token_data["expires_in"]
    return SPOTIFY_TOKEN_INFO["access_token"]


def get_spotify_metadata(uri):
    track_uri = uri.split(":")[-1]
    token = get_spotify_token()

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"https://api.spotify.com/v1/tracks/{track_uri}", headers=headers)

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
    else:
        print("Spotify API error:", r.status_code, r.text)
    return None


@celery.task(bind=True)
def process_spotify_json_file(self, filepath, auth0_id):
    print("Task started for file:", filepath, "by user:", auth0_id)

    inserted = 0
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            return {'status': 'error', 'message': 'JSON is not a list'}

        conn = db_pool.get_connection()
        cursor = conn.cursor()

        # Get user_id by auth0_id
        cursor.execute("SELECT user_id FROM core_users WHERE auth0_id = %s", (auth0_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return {'status': 'error', 'message': 'User not found'}
        user_id = user[0]

        for stream in data:
            ts = stream.get("ts")
            uri = stream.get("spotify_track_uri")
            if not ts or not uri:
                continue

            cursor.execute("SELECT usage_id FROM usage_logs WHERE user_id = %s AND ts = %s", (user_id, ts))
            if cursor.fetchone():
                continue  # Skip duplicates

            cursor.execute("SELECT song_id FROM core_songs WHERE spotify_uri = %s", (uri,))
            song = cursor.fetchone()
            if not song:
                metadata = get_spotify_metadata(uri)
                if not metadata:
                    continue
                cursor.execute("""
                    INSERT INTO core_songs (
                        spotify_uri, track_name, artist_name, artist_id,
                        album_name, album_id, album_type, album_uri,
                        release_date, release_date_precision,
                        duration_ms, is_explicit,
                        image_url, preview_url, popularity, is_local
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    uri, metadata["track_name"], metadata["artist_name"], metadata["artist_id"],
                    metadata["album_name"], metadata["album_id"], metadata["album_type"], metadata["album_uri"],
                    metadata["release_date"], metadata["release_date_precision"],
                    metadata["duration_ms"], metadata["is_explicit"],
                    metadata["image_url"], metadata["preview_url"],
                    metadata["popularity"], metadata["is_local"]
                ))
                song_id = cursor.lastrowid
            else:
                song_id = song[0]

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

        conn.commit()
        cursor.close()
        conn.close()

        return {'status': 'success', 'inserted': inserted}

    except Exception as e:
        return {'status': 'error', 'message': str(e)}
