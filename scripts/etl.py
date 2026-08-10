from etl_config import (
    CLIENT_ID, CLIENT_SECRET, TOKEN_URL, BASE_URL,
    LASTFM_API_KEY, LASTFM_BASE_URL, ARTISTS,
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
    POSTGRES_USER, POSTGRES_PASSWORD
)
import requests
import json
import time
import os
import pandas as pd
from sqlalchemy import create_engine, text


def get_access_token():
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    auth = (CLIENT_ID, CLIENT_SECRET)
    for attempt in range(5):
        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data, auth=auth, timeout=10)
            if response.status_code == 200:
                return response.json()["access_token"]
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 30))
                print(f"  Rate limited on token. Waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"  Token attempt {attempt + 1}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  Token attempt {attempt + 1} failed: {e}")
        time.sleep(3)
    raise Exception("Token request failed after retries")


def search_artist(artist_name, token):
    url = f"{BASE_URL}/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": artist_name, "type": "artist", "limit": 1}
    for attempt in range(5):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 30))
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            if response.status_code == 502:
                time.sleep(2)
                continue
            response.raise_for_status()
            data = response.json()
            if data["artists"]["total"] == 0:
                return None
            return data["artists"]["items"][0]
        except requests.exceptions.RequestException as e:
            print(f"    Spotify retry {attempt + 1} for {artist_name}: {e}")
            time.sleep(3)
    return None


def fetch_albums(artist_id, token):
    url = f"{BASE_URL}/artists/{artist_id}/albums"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": 5, "include_groups": "album,single", "market": "US"}
    for attempt in range(5):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 30))
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            if response.status_code == 502:
                time.sleep(2)
                continue
            response.raise_for_status()
            return response.json()["items"]
        except requests.exceptions.RequestException as e:
            print(f"    Spotify retry {attempt + 1}: {e}")
            time.sleep(3)
    return []


def fetch_album_tracks(album_id, token):
    url = f"{BASE_URL}/albums/{album_id}/tracks"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": 50, "market": "US"}
    for attempt in range(5):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 30))
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            if response.status_code == 502:
                time.sleep(2)
                continue
            response.raise_for_status()
            return response.json()["items"]
        except requests.exceptions.RequestException as e:
            print(f"    Spotify retry {attempt + 1}: {e}")
            time.sleep(3)
    return []


def fetch_lastfm_track_info(track_name, artist_name, token):
    params = {
        "method": "track.getInfo",
        "api_key": token,
        "artist": artist_name,
        "track": track_name,
        "format": "json"
    }
    for attempt in range(3):
        try:
            response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "track" in data:
                    return {
                        "lastfm_listeners": data["track"].get("listeners", 0),
                        "lastfm_playcount": data["track"].get("playcount", 0),
                        "lastfm_top_tags": str([t["name"] for t in data["track"].get("toptags", {}).get("tag", [])[:5]])
                    }
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"    Last.fm retry {attempt + 1} for {track_name}")
            time.sleep(2)
        except Exception as e:
            print(f"    Last.fm error for {track_name}: {e}")
            break
    return {"lastfm_listeners": 0, "lastfm_playcount": 0, "lastfm_top_tags": "[]"}


def extract_artist_data(artist_name, token):
    artist = search_artist(artist_name, token)
    if artist is None:
        print(f"Artist not found: {artist_name}")
        return None

    artist_id = artist["id"]
    print(f"Found artist: {artist['name']}")

    albums = fetch_albums(artist_id, token)
    print(f"  Albums found: {len(albums)}")

    tracks = []
    for album in albums:
        album_tracks = fetch_album_tracks(album["id"], token)
        for track in album_tracks:
            lastfm_info = fetch_lastfm_track_info(track["name"], artist["name"], LASTFM_API_KEY)
            tracks.append({
                "track_id": track["id"],
                "track_name": track["name"],
                "artist_name": artist["name"],
                "artist_id": artist_id,
                "album_name": album["name"],
                "album_type": album["album_type"],
                "release_date": album["release_date"],
                "duration_ms": track["duration_ms"],
                "explicit": track.get("explicit", False),
                "lastfm_listeners": lastfm_info["lastfm_listeners"],
                "lastfm_playcount": lastfm_info["lastfm_playcount"],
                "lastfm_top_tags": lastfm_info["lastfm_top_tags"]
            })
        time.sleep(1)

    print(f"  Tracks collected: {len(tracks)}")
    return {
        "artist_name": artist["name"],
        "artist_id": artist_id,
        "genres": artist.get("genres", []),
        "tracks": tracks
    }


def extract_all_artists():
    token = get_access_token()
    all_tracks = []
    all_artists = []

    for artist_name in ARTISTS:
        print(f"\n--- Processing: {artist_name} ---")
        result = extract_artist_data(artist_name, token)
        if result:
            all_artists.append({
                "artist_id": result["artist_id"],
                "artist_name": result["artist_name"],
                "genres": str(result["genres"])
            })
            all_tracks.extend(result["tracks"])
        time.sleep(2)

    return {
        "artists": all_artists,
        "tracks": all_tracks
    }


def save_data(result):
    folder = "data"
    os.makedirs(folder, exist_ok=True)

    with open(f"{folder}/spotify_raw.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    df = pd.DataFrame(result["tracks"])
    df.to_csv(f"{folder}/tracks.csv", index=False)

    print(f"\nFiles Saved Successfully")
    print(f"Total tracks: {len(df)}")
    if not df.empty:
        print(df.head())


def load_to_postgres(result):
    if not result["tracks"]:
        print("No tracks to load. Skipping database load.")
        return

    engine = create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS fact_tracks CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_track CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_album CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_artist CASCADE"))

    engine.dispose()

    engine = create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    artist_df = pd.DataFrame(result["artists"])
    artist_df.to_sql("dim_artist", engine, if_exists="append", index=False)

    albums = {}
    for track in result["tracks"]:
        album_key = f"{track['artist_id']}_{track['album_name']}"
        if album_key not in albums:
            albums[album_key] = {
                "album_id": f"ALB_{abs(hash(album_key)) % 10**10}",
                "album_name": track["album_name"],
                "album_type": track["album_type"],
                "release_date": track["release_date"],
                "artist_id": track["artist_id"]
            }

    album_df = pd.DataFrame(list(albums.values()))
    album_df.to_sql("dim_album", engine, if_exists="append", index=False)

    tracks_df = pd.DataFrame(result["tracks"])
    tracks_df = tracks_df.rename(columns={"explicit": "is_explicit"})
    tracks_df = tracks_df.drop_duplicates(subset=["track_id"])

    tracks_df[["track_id", "track_name", "duration_ms", "is_explicit"]].to_sql(
        "dim_track", engine, if_exists="append", index=False
    )

    fact_df = pd.DataFrame(result["tracks"])
    fact_df = fact_df.drop_duplicates(subset=["track_id"])
    fact_df["album_id"] = fact_df.apply(
        lambda r: f"ALB_{abs(hash(str(r['artist_id']) + '_' + str(r['album_name']))) % 10**10}",
        axis=1
    )
    fact_df = fact_df[["track_id", "artist_id", "album_id", "duration_ms", "lastfm_listeners", "lastfm_playcount"]]
    fact_df["load_date"] = pd.Timestamp.now().date()

    fact_df.to_sql("fact_tracks", engine, if_exists="append", index=False)

    print(f"Loaded {len(tracks_df)} tracks into star schema")


if __name__ == "__main__":
    result = extract_all_artists()
    save_data(result)
    load_to_postgres(result)