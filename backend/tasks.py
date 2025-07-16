import json
import pendulum
from celery_app import celery
from spotify_client import sp
import mysql.connector.pooling
import requests
import os
from dotenv import load_dotenv
from celery.exceptions import Ignore

load_dotenv()

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

def get_spotify_metadata(uri):
    track_id = uri.split(":")[-1]
    try:
        track = sp.track(track_id)
        album = track["album"]
        return {
            "track_name": track["name"],
            "artist_name": track["artists"][0]["name"],
            "artist_id": track["artists"][0]["id"],
            "album_name": album["name"],
            "album_id": album["id"],
            "album_type": album.get("album_type"),
            "album_uri": album.get("uri"),
            "release_date": album.get("release_date"),
            "release_date_precision": album.get("release_date_precision"),
            "duration_ms": track["duration_ms"],
            "is_explicit": track["explicit"],
            "image_url": album["images"][0]["url"] if album["images"] else None,
            "preview_url": track.get("preview_url"),
            "popularity": track.get("popularity"),
            "is_local": track.get("is_local", False)
        }
    except Exception as e:
        print(f"Error fetching track metadata: {e}")
        return None



@celery.task(bind=True)
def process_spotify_json_file(self, filepath, auth0_id):
    inserted = 0
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            self.update_state(
                state='FAILURE',
                meta={
                    'exc_type': 'InvalidFormatError',
                    'exc_message': 'Uploaded file is not a JSON list',
                    'exc_module': 'process_spotify_json_file'
                }
            )
            raise Ignore()

        conn = db_pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM core_users WHERE auth0_id = %s", (auth0_id,))
        user = cursor.fetchone()
        if not user:
            self.update_state(
                state='FAILURE',
                meta={
                    'exc_type': 'UserNotFoundError',
                    'exc_message': 'User not found',
                    'exc_module': 'process_spotify_json_file'
                }
            )
            raise Ignore()
        user_id = user[0]

        total = len(data)

        for index, stream in enumerate(data):
            ts = stream.get("ts")
            uri = stream.get("spotify_track_uri")
            if not ts or not uri:
                continue

            # Skip duplicate streams
            cursor.execute("SELECT usage_id FROM usage_logs WHERE user_id = %s AND ts = %s", (user_id, ts))
            if cursor.fetchone():
                continue

            # Check if song already exists
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

            # Insert usage record
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

            if index % 10 == 0:
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "inserted": inserted,
                        "processed": index,
                        "total": total,
                        "progress_pct": int(index / total * 100)
                    }
                )

        conn.commit()
        cursor.close()
        conn.close()

        return {'status': 'success', 'inserted': inserted, 'total': total}

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'exc_type': type(e).__name__,
                'exc_message': str(e),
                'exc_module': e.__class__.__module__
            }
        )
        raise Ignore()

@celery.task(bind=True)
def update_user_snapshots(self, user_id=None):
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)

    if user_id is not None:
        users = [{'user_id': user_id}]
    else:
        cursor.execute("SELECT user_id FROM core_users")
        users = cursor.fetchall()

    periods = ['day', 'week', 'month', 'year']

    def get_range_bounds(period):
        now = pendulum.now("UTC")
        if period == 'day':
            return now.start_of('day'), now.end_of('day')
        elif period == 'week':
            return now.start_of('week'), now.end_of('week')
        elif period == 'month':
            return now.start_of('month'), now.end_of('month')
        elif period == 'year':
            return now.start_of('year'), now.end_of('year')
        else:
            raise ValueError("Unsupported period")

    def calculate_longest_binge(rows):
        if not rows:
            return None, 0, None, None

        max_song = None
        max_count = 0
        max_start_ts = None
        max_end_ts = None

        current_song = rows[0]['song_id']
        current_start_ts = rows[0]['ts']
        current_count = 1

        for i in range(1, len(rows)):
            song_id = rows[i]['song_id']
            ts = rows[i]['ts']

            if song_id == current_song:
                current_count += 1
            else:
                if current_count > max_count:
                    max_song = current_song
                    max_count = current_count
                    max_start_ts = current_start_ts
                    max_end_ts = rows[i - 1]['ts']

                current_song = song_id
                current_start_ts = ts
                current_count = 1

        if current_count > max_count:
            max_song = current_song
            max_count = current_count
            max_start_ts = current_start_ts
            max_end_ts = rows[-1]['ts']

        return max_song, max_count, max_start_ts, max_end_ts

    for user in users:
        uid = user['user_id']

        for period in periods:
            range_start, range_end = get_range_bounds(period)

            cursor.execute("""
                SELECT COUNT(*) AS total FROM usage_logs
                WHERE user_id = %s AND ts BETWEEN %s AND %s
            """, (uid, range_start, range_end))
            total_songs = cursor.fetchone()['total']

            cursor.execute("""
                SELECT song_id, SUM(ms_played) AS total_played
                FROM usage_logs
                WHERE user_id = %s AND ts BETWEEN %s AND %s
                GROUP BY song_id
                ORDER BY total_played DESC
                LIMIT 1
            """, (uid, range_start, range_end))
            song_row = cursor.fetchone()
            most_played_song_id = song_row['song_id'] if song_row else None

            cursor.execute("""
                SELECT cs.artist_name, SUM(ul.ms_played) AS total_artist_played
                FROM usage_logs ul
                JOIN core_songs cs ON ul.song_id = cs.song_id
                WHERE ul.user_id = %s AND ul.ts BETWEEN %s AND %s
                GROUP BY cs.artist_name
                ORDER BY total_artist_played DESC
                LIMIT 1
            """, (uid, range_start, range_end))
            artist_row = cursor.fetchone()
            most_played_artist = artist_row['artist_name'] if artist_row else None

            cursor.execute("""
                SELECT song_id, ts FROM usage_logs
                WHERE user_id = %s AND ts BETWEEN %s AND %s
                ORDER BY ts ASC
            """, (uid, range_start, range_end))
            binge_rows = cursor.fetchall()
            binge_song_id, binge_count, binge_start_ts, binge_end_ts = calculate_longest_binge(binge_rows)

            cursor.execute("""
                INSERT INTO user_snapshots (
                    user_id,
                    total_songs_played,
                    most_played_song_id,
                    most_played_artist_name,
                    longest_binge_song_id,
                    binge_count,
                    binge_start_ts,
                    binge_end_ts,
                    range_start,
                    range_end,
                    range_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                uid,
                total_songs,
                most_played_song_id,
                most_played_artist,
                binge_song_id,
                binge_count,
                binge_start_ts,
                binge_end_ts,
                range_start,
                range_end,
                period
            ))

            conn.commit()

    cursor.close()
    conn.close()
