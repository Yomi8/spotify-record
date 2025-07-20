import json
import pendulum
from spotify_auth import sp
import mysql.connector.pooling
import redis
import os
from dotenv import load_dotenv

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
        print(f"Error fetching track metadata for URI {uri}: {e}")
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
            # Progress logging (optional)
            print(f"Processing entry {index + 1} of {total}, inserted so far: {inserted}")

            ts_str = entry.get("ts")
            track_uri = entry.get("spotify_track_uri")
            if not ts_str or not track_uri:
                continue

            try:
                ts = pendulum.parse(ts_str).to_datetime_string()
            except Exception:
                continue

            # Check for duplicate usage log
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
                metadata = get_spotify_metadata(track_uri)
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
                    track_uri,
                    metadata["track_name"],
                    metadata["artist_name"],
                    metadata["artist_id"],
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
        # Log error and re-raise for visibility
        print(f"Error in process_spotify_json_file: {e}")
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

    cursor.execute("""
        SELECT cs.artist_name, SUM(ul.ms_played) AS total_artist_played
        FROM usage_logs ul
        JOIN core_songs cs ON ul.song_id = cs.song_id
        WHERE ul.user_id = %s AND ul.ts BETWEEN %s AND %s
        GROUP BY cs.artist_name ORDER BY total_artist_played DESC LIMIT 1
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
    print(f"Starting snapshot generation for user {user_id} period {period}")
    redis_key = f"snapshot_job:{user_id}:{period}"

    now = pendulum.now("UTC")  # <-- Always use UTC

    try:
        with db_pool.get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                if period == "lifetime":
                    start, end = get_user_lifetime_range(cursor, user_id)
                    if not start or not end:
                        print(f"No usage logs for user {user_id}, skipping lifetime snapshot")
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

                print(f"Snapshot generated for user {user_id} ({period}) at {snapshot_data['snapshot_time']}")

    except Exception as e:
        print(f"Error generating snapshot for user {user_id} ({period}): {e}")
        raise

    finally:
        redis_conn.delete(redis_key)
        print(f"Snapshot generation complete for user {user_id} period {period}")
        
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