CREATE TABLE IF NOT EXISTS artists (
    artist_id VARCHAR(50) PRIMARY KEY,
    artist_name VARCHAR(255) NOT NULL,
    genres TEXT[],
    popularity INTEGER,
    followers INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS albums (
    album_id VARCHAR(50) PRIMARY KEY,
    album_name VARCHAR(255) NOT NULL,
    album_type VARCHAR(20),
    release_date DATE,
    artist_id VARCHAR(50) REFERENCES artists(artist_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tracks (
    track_id VARCHAR(50) PRIMARY KEY,
    track_name VARCHAR(255) NOT NULL,
    duration_ms INTEGER,
    popularity INTEGER,
    explicit BOOLEAN,
    album_id VARCHAR(50) REFERENCES albums(album_id),
    artist_id VARCHAR(50) REFERENCES artists(artist_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);