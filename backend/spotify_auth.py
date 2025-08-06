import os
from dotenv import load_dotenv
import spotipy
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import time
from db import run_query
import logging

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

if not client_id or not client_secret:
    raise Exception("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set")

logger = logging.getLogger(__name__)

# Used for app-level Spotify metadata lookups (e.g., song info)
app_auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp_app = Spotify(auth_manager=app_auth_manager)


def safe_spotify_call(func, *args, max_retries=5, delay=1, **kwargs):
    logger.info("safe_spotify_call called")
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            logger.info(f"Spotify API call succeeded on attempt {attempt+1}")
            return result
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get("Retry-After", delay))
                logger.warning(f"Rate limited. Retrying in {retry_after} seconds...")
                time.sleep(retry_after)
            else:
                logger.error(f"Spotify API error: {e}")
                raise
        except (requests.exceptions.RequestException, Exception) as e:
            logger.warning(f"Error calling Spotify API (attempt {attempt+1}): {e}")
            time.sleep(delay * (2 ** attempt))
    raise Exception("Max retries exceeded for Spotify API call")

def save_spotify_tokens(user_id, access_token, refresh_token, expires_at):
    query = """
        INSERT INTO spotify_tokens (user_id, access_token, refresh_token, expires_at)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            access_token = VALUES(access_token),
            refresh_token = VALUES(refresh_token),
            expires_at = VALUES(expires_at)
    """
    run_query(query, (user_id, access_token, refresh_token, expires_at), commit=True)

def get_spotify_tokens(user_id):
    query = "SELECT access_token, refresh_token, expires_at FROM spotify_tokens WHERE user_id = %s"
    return run_query(query, (user_id,), fetchone=True, dict_cursor=True)

def refresh_spotify_token(refresh_token):
    response = requests.post("https://accounts.spotify.com/api/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    })

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to refresh Spotify token")

def get_user_spotify(auth0_id: str) -> Spotify:
    user = run_query("SELECT id FROM core_users WHERE auth0_id = %s", (auth0_id,), fetchone=True, dict_cursor=True)
    if not user:
        raise Exception("User not found")
    user_id = user["id"]

    tokens = get_spotify_tokens(user_id)
    if not tokens:
        raise Exception("Spotify tokens not found")

    # Refresh token if expired
    if tokens["expires_at"] < int(time.time()):
        new_token = refresh_spotify_token(tokens["refresh_token"])
        save_spotify_tokens(
            user_id,
            new_token["access_token"],
            new_token.get("refresh_token", tokens["refresh_token"]),
            new_token["expires_at"]
        )
        access_token = new_token["access_token"]
    else:
        access_token = tokens["access_token"]

    return Spotify(auth=access_token)

# Optional helper to get a Spotify client for a specific access token
def get_user_spotify_client(access_token: str) -> Spotify:
    return Spotify(auth=access_token)