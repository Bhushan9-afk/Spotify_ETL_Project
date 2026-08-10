import os

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
TOKEN_URL = "https://accounts.spotify.com/api/token"
BASE_URL = "https://api.spotify.com/v1"
LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY", "")
LASTFM_BASE_URL = "http://ws.audioscrobbler.com/2.0/"
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "172.24.96.1")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "spotify_etl")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")

ARTISTS = [
    "Travis Scott",
    "Drake",
    "Kendrick Lamar",
    "Taylor Swift",
    "The Weeknd",
    "Bad Bunny",
    "Ariana Grande",
    "Post Malone",
    "J. Cole",
    "Billie Eilish"
]