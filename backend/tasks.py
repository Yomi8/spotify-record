import json
import pendulum
from spotify_auth import sp_app, get_spotify_tokens, get_user_spotify_client, refresh_spotify_token
import mysql.connector.pooling
import redis
import os
import time
from dotenv import load_dotenv
import logging
import sys

# Configure global logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # output to stdout
        logging.FileHandler("spotify_tasks.log"),  # optional log file
    ]
)

logger = logging.getLogger(__name__)


load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_TOKEN_INFO = {"access_token": None, "expires_at": 0}
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

redis_conn = redis.Redis.from_url("redis://localhost:6379/0")

# Setup MySQL connection pool (reuse same config)
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="spotify_pool",
    pool_size=5,
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

def get_artist_metadata(artist_id):
    try:
        logger.info("Fetching artist metadata for artist ID: %s", artist_id)
        artist = sp_app.artist(artist_id)
        return {
            "artist_id": artist["id"],
            "artist_name": artist["name"],
            "artist_uri": artist["uri"],
            "artist_href": artist.get("href"),
            "artist_external_urls": artist.get("external_urls"),
            "artist_followers": artist.get("followers", {}).get("total"),
            "artist_genres": artist.get("genres", []),
            "artist_images": artist.get("images"),
            "artist_popularity": artist.get("popularity"),
        }
    except Exception as e:
        logger.error(f"Error fetching artist metadata for ID {artist_id}: {e}")
        return None

def get_or_create_artist(cursor, artist_uri):
    # Check if artist exists by artist_uri
    cursor.execute("SELECT artist_id FROM core_artists WHERE artist_uri = %s", (artist_uri,))
    row = cursor.fetchone()
    if row:
        return row[0]
    # Fetch from Spotify and insert
    spotify_artist_id = artist_uri.split(":")[-1]
    artist_data = get_artist_metadata(spotify_artist_id)
    if not artist_data:
        return None
    cursor.execute("""
        INSERT INTO core_artists (
            artist_uri, artist_name, artist_href, artist_external_urls,
            artist_followers, artist_genres, artist_images, artist_popularity
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        artist_data["artist_uri"],
        artist_data["artist_name"],
        artist_data["artist_href"],
        json.dumps(artist_data["artist_external_urls"]),
        artist_data["artist_followers"],
        json.dumps(artist_data["artist_genres"]),
        json.dumps(artist_data["artist_images"]),
        artist_data["artist_popularity"],
    ))
    return cursor.lastrowid

def get_track_metadata(uri):
    track_id = uri.split(":")[-1]
    try:
        logger.info("Fetching metadata for track ID: %s", track_id)
        track = sp_app.track(track_id)
        album = track["album"]
        artist = track["artists"][0]
        return {
            "track_name": track["name"],
            "artist_name": artist["name"],
            "artist_uri": artist["uri"],
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
        logger.error(f"Error fetching track metadata for URI {uri}: {e}")
        return None

def process_spotify_json_file(file_path, user_id):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Invalid JSON structure: expected a list")

        inserted = 0
        conn = db_pool.get_connection()
        cursor = conn.cursor()

        total = len(data)
        for index, entry in enumerate(data):
            logger.info(f"Processing entry {index + 1} of {total}, inserted so far: {inserted}")

            ts_str = entry.get("ts")
            track_uri = entry.get("spotify_track_uri")
            if not ts_str or not track_uri:
                continue

            try:
                ts = pendulum.parse(ts_str).to_datetime_string()
            except Exception:
                continue

            cursor.execute(
                "SELECT 1 FROM usage_logs WHERE user_id = %s AND ts = %s",
                (user_id, ts)
            )
            if cursor.fetchone():
                continue

            cursor.execute("SELECT song_id FROM core_songs WHERE spotify_uri = %s", (track_uri,))
            song_row = cursor.fetchone()

            if song_row:
                song_id = song_row[0]
            else:
                metadata = get_track_metadata(track_uri)
                if not metadata:
                    continue

                # Get or create artist and get artist_id (int)
                artist_id = get_or_create_artist(cursor, metadata["artist_uri"])
                if not artist_id:
                    continue

                cursor.execute("""
                    INSERT INTO core_songs (
                        spotify_uri, track_name, artist_id,
                        album_name, album_id, album_type, album_uri,
                        release_date, release_date_precision,
                        duration_ms, is_explicit,
                        image_url, preview_url, popularity, is_local
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    track_uri,
                    metadata["track_name"],
                    artist_id,
                    metadata["album_name"],
                    metadata["album_id"],
                    metadata["album_type"],
                    metadata["album_uri"],
                    metadata["release_date"],
                    metadata["release_date_precision"],
                    metadata["duration_ms"],
                    int(metadata["is_explicit"]),
                    metadata["image_url"],
                    metadata["preview_url"],
                    metadata["popularity"],
                    int(metadata["is_local"]),
                ))
                song_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO usage_logs (
                    user_id, song_id, ts, ms_played, platform, conn_country, ip_addr,
                    spotify_track_uri, episode_name, episode_show_name, reason_start,
                    reason_end, shuffle, skipped, offline, offline_timestamp, incognito_mode
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                song_id,
                ts,
                entry.get("ms_played"),
                entry.get("platform"),
                entry.get("conn_country"),
                entry.get("ip_addr"),
                track_uri,
                entry.get("episode_name"),
                entry.get("episode_show_name"),
                entry.get("reason_start"),
                entry.get("reason_end"),
                entry.get("shuffle"),
                entry.get("skipped"),
                entry.get("offline"),
                entry.get("offline_timestamp"),
                entry.get("incognito_mode"),
            ))

            inserted += 1

        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "COMPLETE", "inserted": inserted, "total": total}

    except Exception as e:
        logger.error(f"[{index}] Error processing entry: {e}", exc_info=True)
        raise

def get_range_bounds(now, range_type):
    if range_type == 'day':
        return now.subtract(days=1), now
    elif range_type == 'week':
        return now.subtract(weeks=1), now
    elif range_type == 'month':
        return now.subtract(months=1), now
    elif range_type == 'year':
        return now.subtract(years=1), now
    else:
        raise ValueError(f"Unknown range type: {range_type}")

def get_user_lifetime_range(cursor, user_id):
    cursor.execute("SELECT MIN(ts) AS start, MAX(ts) AS end FROM usage_logs WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    return row['start'], row['end']

def calculate_longest_binge(rows):
    if not rows: return None, 0, None, None

    max_song = rows[0]['song_id']
    max_count = 1
    max_start = rows[0]['ts']
    max_end = rows[0]['ts']

    current_song = rows[0]['song_id']
    current_start = rows[0]['ts']
    count = 1

    for i in range(1, len(rows)):
        if rows[i]['song_id'] == current_song:
            count += 1
        else:
            if count > max_count:
                max_song, max_count = current_song, count
                max_start, max_end = current_start, rows[i - 1]['ts']
            current_song = rows[i]['song_id']
            current_start = rows[i]['ts']
            count = 1

    if count > max_count:
        max_song, max_count = current_song, count
        max_start, max_end = current_start, rows[-1]['ts']

    return max_song, max_count, max_start, max_end

def get_snapshot_data(cursor, user_id, start, end):
    cursor.execute("""
        SELECT COUNT(*) AS total FROM usage_logs
        WHERE user_id = %s AND ts BETWEEN %s AND %s
    """, (user_id, start, end))
    total = cursor.fetchone()['total']

    cursor.execute("""
        SELECT song_id, SUM(ms_played) AS total_played
        FROM usage_logs
        WHERE user_id = %s AND ts BETWEEN %s AND %s
        GROUP BY song_id ORDER BY total_played DESC LIMIT 1
    """, (user_id, start, end))
    row = cursor.fetchone()
    top_song = row['song_id'] if row else None

    # UPDATED: Join core_artists to get artist_name
    cursor.execute("""
        SELECT ca.artist_name, SUM(ul.ms_played) AS total_artist_played
        FROM usage_logs ul
        JOIN core_songs cs ON ul.song_id = cs.song_id
        JOIN core_artists ca ON cs.artist_id = ca.artist_id
        WHERE ul.user_id = %s AND ul.ts BETWEEN %s AND %s
        GROUP BY ca.artist_id, ca.artist_name
        ORDER BY total_artist_played DESC LIMIT 1
    """, (user_id, start, end))
    row = cursor.fetchone()
    top_artist = row['artist_name'] if row else None

    cursor.execute("""
        SELECT song_id, ts FROM usage_logs
        WHERE user_id = %s AND ts BETWEEN %s AND %s
        ORDER BY ts ASC
    """, (user_id, start, end))
    binge_rows = cursor.fetchall()
    binge_song, binge_count, binge_start, binge_end = calculate_longest_binge(binge_rows)

    return {
        "total_songs": total,
        "top_song": top_song,
        "top_artist": top_artist,
        "binge_song": binge_song,
        "binge_count": binge_count,
        "binge_start": binge_start,
        "binge_end": binge_end,
    }

# 1. Automated Period Snapshot (day/week/month/year/lifetime)
def generate_snapshot_for_period(user_id, period):
    logger.info(f"Starting snapshot generation for user {user_id} period {period}")
    redis_key = f"snapshot_job:{user_id}:{period}"

    now = pendulum.now("UTC")  # <-- Always use UTC

    try:
        with db_pool.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                if period == "lifetime":
                    start, end = get_user_lifetime_range(cursor, user_id)
                    if not start or not end:
                        logger.warning(f"No usage logs for user {user_id}, skipping lifetime snapshot")
                        return
                else:
                    start, end = get_range_bounds(now, period)

                # Force to pendulum instances and convert to UTC
                start = pendulum.instance(start).in_timezone("UTC")
                end = pendulum.instance(end).in_timezone("UTC")

                stats = get_snapshot_data(cursor, user_id, start, end)

                # Safely convert optional fields if they exist, and force to UTC
                binge_start_ts = pendulum.instance(stats["binge_start"]).in_timezone("UTC").to_datetime_string() if stats.get("binge_start") else None
                binge_end_ts = pendulum.instance(stats["binge_end"]).in_timezone("UTC").to_datetime_string() if stats.get("binge_end") else None

                snapshot_data = {
                    "user_id": user_id,
                    "range_type": period,
                    "snapshot_time": now.to_datetime_string(),  # UTC
                    "total_songs_played": stats["total_songs"],
                    "most_played_song_id": stats.get("top_song"),
                    "most_played_artist_name": stats.get("top_artist"),
                    "longest_binge_song_id": stats.get("binge_song"),
                    "binge_count": stats.get("binge_count"),
                    "binge_start_ts": binge_start_ts,
                    "binge_end_ts": binge_end_ts,
                    "range_start": start.to_datetime_string(),  # UTC
                    "range_end": end.to_datetime_string(),      # UTC
                }

                query = """
                    INSERT INTO user_snapshots (
                        user_id, total_songs_played, most_played_song_id, 
                        most_played_artist_name, longest_binge_song_id, binge_count,
                        snapshot_time, binge_start_ts, binge_end_ts,
                        range_start, range_end, range_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                run_query(
                    query,
                    (
                        snapshot_data["user_id"],
                        snapshot_data["total_songs_played"],
                        snapshot_data["most_played_song_id"],
                        snapshot_data["most_played_artist_name"],
                        snapshot_data["longest_binge_song_id"],
                        snapshot_data["binge_count"],
                        snapshot_data["snapshot_time"],
                        snapshot_data["binge_start_ts"],
                        snapshot_data["binge_end_ts"],
                        snapshot_data["range_start"],
                        snapshot_data["range_end"],
                        snapshot_data["range_type"],
                    ),
                    commit=True,
                )

                logger.info(f"Snapshot generated for user {user_id} ({period}) at {snapshot_data['snapshot_time']}")

    except Exception as e:
        logger.error(f"Error generating snapshot for user {user_id} ({period}): {e}")
        raise

    finally:
        redis_conn.delete(redis_key)
        logger.info(f"Snapshot generation complete for user {user_id} period {period}")
 
# 2. Custom Range Snapshot (API input or manual)
def generate_snapshot_for_range(user_id, start, end):
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)

    snapshot = get_snapshot_data(cursor, user_id, start, end)

    cursor.execute("""
        INSERT INTO user_snapshots (
            user_id, total_songs_played, most_played_song_id,
            most_played_artist_name, longest_binge_song_id, binge_count,
            binge_start_ts, binge_end_ts, range_start, range_end, range_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, snapshot["total_songs"], snapshot["top_song"],
        snapshot["top_artist"], snapshot["binge_song"], snapshot["binge_count"],
        snapshot["binge_start"], snapshot["binge_end"], start, end, 'custom'
    ))

    conn.commit()
    cursor.close()
    conn.close()
    return {"user_id": user_id, "range_type": "custom", "range_start": start, "range_end": end}

def fetch_recently_played_and_store(user_id):
    logger.info(f"Fetching recent plays for user {user_id}")
    try:
        tokens = get_spotify_tokens(user_id)
        if not tokens:
            logger.warning(f"No Spotify tokens found for user {user_id}")
            return {"status": "SKIPPED", "reason": "No tokens"}

        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        expires_at = tokens["expires_at"]

        # Check if token is expired
        if pendulum.now().int_timestamp >= expires_at:
            logger.info(f"Access token expired for user {user_id}, refreshing...")
            new_data = refresh_spotify_token(refresh_token)
            if not new_data:
                return {"status": "ERROR", "reason": "Failed to refresh token"}
            access_token = new_data["access_token"]
            expires_in = new_data.get("expires_in", 3600)
            expires_at = pendulum.now().int_timestamp + expires_in

            # Save new token to DB
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE spotify_tokens SET access_token = %s, expires_at = %s WHERE user_id = %s",
                (access_token, expires_at, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()

        sp = get_user_spotify_client(access_token)

        # Try getting recently played tracks
        try:
            recent_data = sp.current_user_recently_played(limit=50)
        except Exception as e:
            if "401" in str(e):  # Token may have just expired
                logger.warning(f"401 error fetching recent tracks. Trying token refresh for user {user_id}...")
                new_data = refresh_spotify_token(refresh_token)
                if not new_data:
                    return {"status": "ERROR", "reason": "Failed to refresh token on retry"}
                access_token = new_data["access_token"]
                expires_at = pendulum.now().int_timestamp + new_data.get("expires_in", 3600)

                # Save new token to DB
                conn = db_pool.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE core_users SET access_token = %s, expires_at = %s WHERE user_id = %s",
                    (access_token, expires_at, user_id)
                )
                conn.commit()
                cursor.close()
                conn.close()

                # Retry with new client
                sp = get_user_spotify_client(access_token)
                recent_data = sp.current_user_recently_played(limit=50)
            else:
                raise

        if not recent_data or "items" not in recent_data:
            return {"status": "SKIPPED", "reason": "No recent plays"}

        inserted = 0
        skipped = 0
        conn = db_pool.get_connection()
        cursor = conn.cursor()

        for item in recent_data["items"]:
            ts = pendulum.parse(item["played_at"]).to_datetime_string()
            track = item["track"]
            track_uri = track["uri"]

            cursor.execute(
                "SELECT 1 FROM usage_logs WHERE user_id = %s AND ts = %s",
                (user_id, ts)
            )
            if cursor.fetchone():
                skipped += 1
                continue

            cursor.execute(
                "SELECT song_id, duration_ms FROM core_songs WHERE spotify_uri = %s", (track_uri,)
            )
            song_row = cursor.fetchone()
            if song_row:
                song_id = song_row[0]
                duration_ms = song_row[1]
            else:
                metadata = get_track_metadata(track_uri)
                if not metadata:
                    continue

                # Get or create artist and get artist_id (int)
                artist_id = get_or_create_artist(cursor, metadata["artist_uri"])
                if not artist_id:
                    continue

                cursor.execute("""
                    INSERT INTO core_songs (
                        spotify_uri, track_name, artist_id,
                        album_name, album_id, album_type, album_uri,
                        release_date, release_date_precision,
                        duration_ms, is_explicit,
                        image_url, preview_url, popularity, is_local
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    track_uri,
                    metadata["track_name"],
                    artist_id,
                    metadata["album_name"],
                    metadata["album_id"],
                    metadata["album_type"],
                    metadata["album_uri"],
                    metadata["release_date"],
                    metadata["release_date_precision"],
                    metadata["duration_ms"],
                    int(metadata["is_explicit"]),
                    metadata["image_url"],
                    metadata["preview_url"],
                    metadata["popularity"],
                    int(metadata["is_local"]),
                ))
                song_id = cursor.lastrowid
                duration_ms = metadata["duration_ms"]

            cursor.execute("""
                INSERT INTO usage_logs (
                    user_id, song_id, ts, ms_played, platform, conn_country,
                    spotify_track_uri, reason_start, reason_end, shuffle, skipped
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                song_id,
                ts,
                item.get("ms_played", duration_ms),
                "spotify",
                None,
                track_uri,
                "recent_play",
                "track_done",
                False,
                False,
            ))

            inserted += 1

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status": "COMPLETE",
            "inserted": inserted,
            "skipped": skipped,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Error in fetch_recently_played_and_store: {e}")
        raise