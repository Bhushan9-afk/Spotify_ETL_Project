# Entity Relationship Diagram

## Tables

### dim_artist
| Column | Type | Key |
|---|---|---|
| artist_id | VARCHAR(50) | PK |
| artist_name | VARCHAR(255) | |
| genres | TEXT[] | |

### dim_album
| Column | Type | Key |
|---|---|---|
| album_id | VARCHAR(50) | PK |
| album_name | VARCHAR(255) | |
| album_type | VARCHAR(20) | |
| release_date | DATE | |
| artist_id | VARCHAR(50) | FK → dim_artist |

### dim_track
| Column | Type | Key |
|---|---|---|
| track_id | VARCHAR(50) | PK |
| track_name | VARCHAR(255) | |
| duration_ms | INTEGER | |
| is_explicit | BOOLEAN | |

### fact_tracks
| Column | Type | Key |
|---|---|---|
| track_id | VARCHAR(50) | FK → dim_track |
| artist_id | VARCHAR(50) | FK → dim_artist |
| album_id | VARCHAR(50) | FK → dim_album |
| duration_ms | INTEGER | |
| lastfm_listeners | INTEGER | |
| lastfm_playcount | BIGINT | |
| load_date | DATE | |

## Relationships
- dim_artist 1:* dim_album
- dim_album 1:* fact_tracks
- dim_artist 1:* fact_tracks
- dim_track 1:1 fact_tracks
