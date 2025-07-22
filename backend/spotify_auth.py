import os
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

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

# Optional helper to get a Spotify client for a specific access token
def get_user_spotify_client(access_token: str) -> Spotify:
    return Spotify(auth=access_token)