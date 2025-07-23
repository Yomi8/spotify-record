import mysql.connector.pooling

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

# Translate auth0_id to internal user_id
def get_user_id_from_auth0(auth0_id):
    conn = db_pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM core_users WHERE auth0_id = %s", (auth0_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None