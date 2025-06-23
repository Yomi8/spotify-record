import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise Exception("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set")

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = Spotify(auth_manager=auth_manager)
