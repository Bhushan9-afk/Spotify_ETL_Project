import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from etl import (
    get_access_token,
    search_artist,
    fetch_albums,
    fetch_album_tracks,
    fetch_lastfm_track_info,
    extract_artist_data,
    extract_all_artists,
    save_data,
    load_to_postgres
)
from etl_config import ARTISTS


class TestAccessToken:
    @patch('etl.requests.post')
    def test_get_access_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token_123"}
        mock_post.return_value = mock_response

        token = get_access_token()
        assert token == "test_token_123"

    @patch('etl.requests.post')
    def test_get_access_token_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_client"}
        mock_post.return_value = mock_response

        with pytest.raises(Exception):
            get_access_token()


class TestSearchArtist:
    @patch('etl.requests.get')
    def test_search_artist_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "artists": {
                "total": 1,
                "items": [{"id": "test_id", "name": "Drake"}]
            }
        }
        mock_get.return_value = mock_response

        result = search_artist("Drake", "fake_token")
        assert result["name"] == "Drake"
        assert result["id"] == "test_id"

    @patch('etl.requests.get')
    def test_search_artist_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "artists": {"total": 0, "items": []}
        }
        mock_get.return_value = mock_response

        result = search_artist("UnknownArtist", "fake_token")
        assert result is None


class TestDataValidation:
    def test_artists_list_not_empty(self):
        assert len(ARTISTS) > 0
        assert len(ARTISTS) == 10

    def test_artists_list_has_no_duplicates(self):
        assert len(ARTISTS) == len(set(ARTISTS))

    def test_artists_list_has_no_empty_strings(self):
        assert all(isinstance(a, str) and a.strip() for a in ARTISTS)


class TestSaveData:
    def test_save_data_creates_files(self, tmp_path):
        result = {
            "artists": [{"artist_id": "1", "artist_name": "Test", "genres": "[]"}],
            "tracks": [
                {
                    "track_id": "t1",
                    "track_name": "Song 1",
                    "artist_name": "Test",
                    "artist_id": "1",
                    "album_name": "Album 1",
                    "album_type": "album",
                    "release_date": "2023-01-01",
                    "duration_ms": 200000,
                    "explicit": False,
                    "lastfm_listeners": 1000,
                    "lastfm_playcount": 5000,
                    "lastfm_top_tags": "[]"
                }
            ]
        }
        os.chdir(tmp_path)
        save_data(result)

        assert os.path.exists("data/spotify_raw.json")
        assert os.path.exists("data/tracks.csv")

        df = pd.read_csv("data/tracks.csv")
        assert len(df) == 1
        assert df.iloc[0]["track_name"] == "Song 1"


class TestEmptyData:
    def test_load_to_postgres_empty_data(self, capsys):
        result = {"artists": [], "tracks": []}
        load_to_postgres(result)
        captured = capsys.readouterr()
        assert "No tracks to load" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
