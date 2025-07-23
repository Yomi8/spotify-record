import os
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

import time
from db import run_query

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

if not client_id or not client_secret:
    raise Exception("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set")

# Used for app-level Spotify metadata lookups (e.g., song info)
app_auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp_app = Spotify(auth_manager=app_auth_manager)

# Used for user-specific actions (e.g., recent plays)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="user-read-recently-played",
    show_dialog=True,
    cache_handler=MemoryCacheHandler()
)

def get_user_spotify(auth0_id: str) -> Spotify:
    user = run_query("SELECT id FROM core_users WHERE auth0_id = %s", (auth0_id,), one=True)
    if not user:
        raise Exception("User not found")
    user_id = user["id"]

    tokens = run_query(
        "SELECT access_token, refresh_token, expires_at FROM spotify_tokens WHERE user_id = %s",
        (user_id,), one=True
    )
    if not tokens:
        raise Exception("Spotify tokens not found")

    sp_oauth.token_info = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "expires_at": tokens["expires_at"],
        "scope": "user-read-recently-played",
        "token_type": "Bearer"
    }

    if tokens["expires_at"] < int(time.time()):
        new_token = sp_oauth.refresh_access_token(tokens["refresh_token"])

        run_query("""
            UPDATE spotify_tokens
            SET access_token = %s,
                refresh_token = %s,
                expires_at = %s
            WHERE user_id = %s
        """, (
            new_token["access_token"],
            new_token.get("refresh_token", tokens["refresh_token"]),
            new_token["expires_at"],
            user_id
        ), commit=True)

        sp_oauth.token_info = new_token

    return Spotify(auth=sp_oauth.get_access_token(as_dict=False))

# Optional helper to get a Spotify client for a specific access token
def get_user_spotify_client(access_token: str) -> Spotify:
    return Spotify(auth=access_token)