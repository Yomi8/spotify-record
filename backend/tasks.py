import json
import pendulum
import mysql.connector.pooling
import redis
import os
from dotenv import load_dotenv
import logging
import sys
import traceback

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # output to stdout
        logging.FileHandler("spotify_tasks.log"),  # optional log file
    ]
)

logger = logging.getLogger(__name__)

# Import Spotify auth functions after logger setup
from spotify_auth import sp_app, safe_spotify_call, get_spotify_tokens, get_user_spotify_client, refresh_spotify_token

load_dotenv()

# Spotify API credentials
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
def run_query(query, params=None, commit=False, fetchone=False, dict_cursor=False, many=False, return_lastrowid=False):
    conn = db_pool.get_connection()
    try:
        with conn.cursor(dictionary=dict_cursor) as cursor:
            if many:
                cursor.executemany(query, params)
            else:
                cursor.execute(query, params or ())
            result = None
            if return_lastrowid and commit:
                conn.commit()
                result = cursor.lastrowid
            else:
                if fetchone:
                    result = cursor.fetchone()
                elif cursor.with_rows:
                    result = cursor.fetchall()
            if commit and not return_lastrowid:
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

def get_or_create_artist(spotify_artist_id, spotify):
    # Check if artist already exists
    existing_artist = run_query(
        "SELECT artist_id FROM core_artists WHERE spotify_artist_id = %s",
        (spotify_artist_id,),
        fetchone=True,
        dict_cursor=True
    )
    if existing_artist:
        return existing_artist['artist_id']
    
    # Fetch from Spotify
    artist = safe_spotify_call(lambda: spotify.artist(spotify_artist_id))
    if not artist:
        return None

    run_query("""
        INSERT INTO core_artists (
            spotify_artist_id,
            artist_name,
            artist_uri,
            artist_href,
            artist_external_urls,
            artist_followers,
            artist_genres,
            artist_images,
            artist_popularity
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        artist['id'],
        artist['name'],
        artist.get('uri'),
        artist.get('href'),
        json.dumps(artist.get('external_urls', {})),
        artist.get('followers', {}).get('total'),
        json.dumps(artist.get('genres', [])),
        json.dumps(artist.get('images', [])),
        artist.get('popularity')
    ), commit=True)
    
    new_artist = run_query(
        "SELECT artist_id FROM core_artists WHERE spotify_artist_id = %s",
        (spotify_artist_id,),
        fetchone=True,
        dict_cursor=True
    )
    return new_artist['artist_id'] if new_artist else None

def get_or_create_song(spotify_uri, spotify):
    # Check if song already exists
    existing_song = run_query(
        "SELECT song_id FROM core_songs WHERE spotify_uri = %s",
        (spotify_uri,),
        fetchone=True
    )
    if existing_song:
        return existing_song['song_id']

    # Fetch from Spotify
    track = safe_spotify_call(lambda: spotify.track(spotify_uri))
    if not track:
        return None

    artist_id = None
    if track['artists']:
        artist_id = get_or_create_artist(track['artists'][0]['id'], spotify)

    album = track.get('album', {})
    run_query("""
        INSERT INTO core_songs (
            spotify_uri,
            track_name,
            artist_id,
            album_name,
            album_id,
            album_type,
            album_uri,
            release_date,
            release_date_precision,
            duration_ms,
            is_explicit,
            image_url,
            preview_url,
            popularity,
            is_local
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        track['uri'],
        track['name'],
        artist_id,
        album.get('name'),
        album.get('id'),
        album.get('album_type'),
        album.get('uri'),
        album.get('release_date'),
        album.get('release_date_precision'),
        track.get('duration_ms'),
        int(track.get('explicit', False)),
        album.get('images', [{}])[0].get('url'),
        track.get('preview_url'),
        track.get('popularity'),
        int(track.get('is_local', False))
    ))

    new_song = run_query(
        "SELECT song_id FROM core_songs WHERE spotify_uri = %s",
        (spotify_uri,),
        fetchone=True
    )
    return new_song['song_id'] if new_song else None

def process_spotify_json_file(filepath, user_id):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            streams = json.load(f)

        insert_usage_logs = []

        for entry in streams:
            ts = entry["ts"]
            track_uri = entry.get("spotify_track_uri")

            logger.info(f"Checking for existing usage_log entry at {ts} for user {user_id}...")
            exists = run_query(
                "SELECT 1 FROM usage_logs WHERE user_id = %s AND ts = %s LIMIT 1",
                (user_id, ts),
                fetchone=True
            )
            if exists:
                logger.info(f"Usage log for {ts} already exists. Skipping.")
                continue

            song_id = None
            if track_uri:
                logger.info(f"Processing track URI: {track_uri}")
                # Use the robust get_or_create_song function
                song_id = get_or_create_song(track_uri, sp_app)
                if not song_id:
                    logger.warning(f"Failed to get or create song for URI {track_uri}. Skipping usage log entry.")
                    continue
            else:
                logger.warning(f"No spotify_track_uri found for entry at {ts}. Skipping usage log entry.")
                continue

            # Build usage log entry
            ts_dt = pendulum.parse(ts)
            insert_usage_logs.append((user_id, song_id, ts_dt.to_datetime_string()))

        if insert_usage_logs:
            logger.info(f"Inserting {len(insert_usage_logs)} usage logs...")
            run_query(
                """
                INSERT INTO usage_logs (user_id, song_id, ts)
                VALUES (%s, %s, %s)
                """,
                insert_usage_logs,
                many=True,
                commit=True
            )
            logger.info("Usage logs inserted successfully.")
        else:
            logger.info("No new usage logs to insert from file.")

        os.remove(filepath)
        logger.info(f"File {filepath} removed after successful processing.")

    except Exception as e:
        logger.error(f"Error occurred during processing of {filepath}: {e}")
        traceback.print_exc()
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