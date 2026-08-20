# Spotify ETL Pipeline

An end-to-end Data Engineering pipeline that extracts music data from Spotify and Last.fm APIs, transforms it with Python and Pandas, loads it into a PostgreSQL star schema, orchestrates the workflow with Apache Airflow, and visualizes it in Power BI.

---

## Architecture

```
┌──────────────────┐
│   Spotify API    │
│   Last.fm API    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Python ETL      │
│  (Pandas)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  PostgreSQL      │
│  (Star Schema)   │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Airflow │ │Power BI│
│(DAG)   │ │(Dashboard)
└────────┘ └────────┘
```

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | ETL scripting |
| Pandas | Data transformation |
| PostgreSQL 18 | Data warehouse |
| Apache Airflow | Pipeline orchestration |
| Power BI | Data visualization |
| Docker | Containerization |
| GitHub | Version control |

---

## Data Model (Star Schema)

```
┌──────────────┐     ┌──────────────┐
│  dim_artist  │     │  dim_album   │
│──────────────│     │──────────────│
│ artist_id PK │◄────│ artist_id FK │
│ artist_name  │     │ album_id PK  │
│ genres       │     │ album_name   │
└──────────────┘     │ album_type   │
                     │ release_date │
                     └──────┬───────┘
                            │
┌──────────────┐            │
│  dim_track   │            │
│──────────────│            │
│ track_id PK  │◄───────────┘
│ track_name   │
│ duration_ms  │
│ is_explicit  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  fact_tracks     │
│──────────────────│
│ track_id FK      │
│ artist_id FK     │
│ album_id FK      │
│ duration_ms      │
│ lastfm_listeners │
│ lastfm_playcount │
│ load_date        │
└──────────────────┘
```

---

### Dimension Tables

**dim_artist**  
Stores artist-level descriptive attributes including artist ID, name, and genres.

**dim_album**  
Stores album-level attributes such as album name, album type (album/single), and release date, with a foreign key to the artist.

**dim_track**  
Stores track-level descriptive attributes including track ID, name, duration in milliseconds, and explicit flag.

### Fact Table

**fact_tracks**  
Stores measurable track-level metrics and foreign keys connecting the dimensions. Contains duration in milliseconds, Last.fm listener counts, Last.fm play counts, and load date.

**Fact table grain:** One record per track extracted during an ETL load.

---

## 🔌 API Integration

### Spotify API — Primary Metadata Source
Spotify is the primary source for music metadata including:
- Artist information (name, genres, follower counts)
- Album information (name, type, release date, album art)
- Track information (name, duration, explicit flag, release date)

### Last.fm — Supplementary Engagement Metrics
Last.fm is used as a supplementary source for engagement metrics that the Spotify API does not provide via the Client Credentials flow, including:
- **Listener counts** — unique listeners per track
- **Play counts** — total play counts per track
- **Top tags** — genre/style tags where available

**Why Last.fm was added:**  
During development, Spotify's Client Credentials flow did not provide streaming/play-count metrics required for the intended engagement analysis. Instead of treating this as a limitation, the project incorporated Last.fm as a supplementary data source. This demonstrates multi-source API integration and adaptation to API limitations. Last.fm does not replace Spotify; it supplements Spotify's metadata with engagement metrics that Spotify's Client Credentials flow does not expose.

---

## Star Schema

### Dimension Tables

**dim_artist**  
Stores artist-level descriptive attributes.  
Columns: `artist_id` (PK), `artist_name`, `genres`

**dim_album**  
Stores album-level attributes such as album name, album type (album/single), and release date.  
Foreign key: `artist_id` → `dim_artist.artist_id`

**dim_track**  
Stores track-level descriptive attributes including track ID, name, duration in milliseconds, and explicit flag.

### Fact Table

**fact_tracks**  
Stores measurable track-level metrics and foreign keys connecting the dimensions.  
**Fact table grain:** One record per track extracted during an ETL load.

Columns: `track_id` (FK), `artist_id` (FK), `album_id` (FK), `duration_ms`, `lastfm_listeners`, `lastfm_playcount`, `load_date`

### Relationships
```
dim_artist 1:* dim_album
dim_album 1:* fact_tracks
dim_artist 1:* fact_tracks
dim_track 1:1 fact_tracks
```

The star schema allows analytical queries across:
- Artists (genres, popularity)
- Albums (type, release timeline)
- Tracks (duration, explicit content)
- Last.fm engagement metrics (listeners, play counts, tags)

---

## 🐳 Docker

Docker provides a reproducible local environment for the pipeline. Docker Compose manages two services:

| Service | Purpose |
|---------|---------|
| **postgres** | PostgreSQL 16 database (port 5432) with persisted volume |
| **etl** | Python ETL service that runs the extraction pipeline |

Containers communicate through the Docker Compose network. The ETL container connects to PostgreSQL using the Compose service name `postgres` as the hostname (e.g., `postgres:5432`) rather than `localhost`. Credentials and configuration are supplied via a `.env` file loaded by both services.

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env_file: .env
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
  etl:
    build:
      context: .
      dockerfile: docker/Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
    env_file: .env
```

> **Note on Docker Hub reliability:** Registry pulls can be blocked by network-level TLS resets (observed as CloudFront EOF errors). As a fallback, the project runs successfully against a local PostgreSQL instance without Docker.

---

## 🔄 Apache Airflow

Apache Airflow orchestrates the ETL pipeline on a daily schedule. The DAG (`spotify_etl`) defines the following task flow:

```
Airflow DAG (schedule: @daily)
    ↓
Authenticate with Spotify & Last.fm APIs
    ↓
Extract artist data (10 artists, 5 albums each)
    ↓
Extract Last.fm track engagement data
    ↓
Transform & clean with Pandas
    ↓
Load into PostgreSQL star schema
    ↓
Pipeline completion
```

The DAG includes retry logic with exponential backoff for API rate limits (429) and transient server errors (502). The scheduler runs the DAG daily to keep the warehouse current.

---

## 📊 Power BI Dashboard

The Power BI dashboard provides an analytical layer over the PostgreSQL warehouse. It connects via DirectQuery to the `spotify_etl` database on `localhost:5432`.

### Dashboard Pages

| Page | Focus |
|-------|-------|
| **Page 1 — Executive Overview** | KPI cards (total tracks, total plays, total listeners, total artists), top artists by play count, album type distribution |
| **Page 2 — Detailed Analysis** | Top tracks table, releases over time (line chart), listeners by artist (column chart), artist slicer |

### Visualizations & Filters

| Visualization | Purpose |
|---|---|
| **KPI Cards** | Total tracks (839), total play count, total listeners, total artists |
| **Bar Chart — Top Artists** | Rank artists by total play count |
| **Donut Chart — Tracks per Artist** | Proportion of tracks contributed by each artist |
| **Clustered Column Chart — Listeners by Artist** | Compare total listeners across artists |
| **Line Chart — Releases Over Time** | Track release volume by album release date |
| **Table — Top Tracks** | Track name, artist, album, play count, listeners, explicit flag |
| **Slicer — Artist Filter** | Dropdown to filter all visuals by selected artist |

### Filtered View — Travis Scott Example
The dashboard supports artist-level filtering. When **Travis Scott** is selected:
- The overall dataset contains **839 tracks** across 10 artists
- Selecting **Travis Scott** filters the dashboard to approximately **73 tracks** (the filtered subset for that artist)
- All visuals (charts, tables, KPIs) update to reflect only Travis Scott's tracks

This filtering enables users to move from portfolio-level analysis to individual-artist deep dives.

---

## 🧪 Testing

The project includes a pytest test suite in `tests/test_etl.py` with 9 passing tests:

| Test Class | Coverage |
|---|---|
| `TestAccessToken` | Token retrieval success & failure handling |
| `TestSearchArtist` | Artist search found / not found |
| `TestDataValidation` | Artists list validation (count, duplicates, empties) |
| `TestSaveData` | CSV/JSON output file creation |
| `TestEmptyData` | Empty data handling in PostgreSQL load |

Run tests:
```bash
cd D:\Spotify_ETL_Project
python -m pytest tests/test_etl.py -v
```

**Current result:** 9 passed, 0 failed.

---

## 📈 Key Business Insights

The pipeline and dashboard enable the following analytical insights:

### Artist Performance
The dashboard ranks artists by total play count and listener count. High-engagement artists (e.g., The Weeknd, Taylor Swift) can be identified for partnership or marketing focus.

### Track Performance
Individual track engagement is measurable via Last.fm play counts and listener counts. High-engagement tracks (e.g., Billie Eilish — "Oxytocin" with ~9.9M plays) can be identified for playlist placement or marketing.

### Album Performance
Album-level aggregation (via `dim_album`) allows comparison of album performance by play count and listener reach. Full albums vs. singles can be compared via `album_type`.

### Artist Filtering
The dashboard's artist slicer enables drilling from portfolio-level (839 tracks, 10 artists) to individual-artist analysis. Example: selecting **Travis Scott** filters the dataset from 839 tracks to approximately **73 tracks**, enabling deep-dive analysis on that artist's catalog.

### Explicit Content
The `is_explicit` flag in `dim_track` allows filtering or analyzing explicit vs. non-explicit content distribution across artists and albums.

### Engagement Analysis
Last.fm listener counts and play counts provide a proxy for track popularity and audience engagement, enabling cross-artist, cross-album, and cross-track comparison of music engagement.

---

### 📌 Business Recommendations

1. **Prioritize high-engagement artists** — Use play count and listener metrics to identify artists with strongest audience engagement for partnership or playlist placement.

2. **Leverage artist-level filtering** — Use the artist slicer to conduct deep-dive analyses on individual artist catalogs for targeted marketing campaigns.

3. **Track album-level performance** — Compare album vs. single performance via `album_type` to inform release strategy.

4. **Leverage engagement metrics for content planning** — Use play count and listener trends to identify high-performing content themes for future curation.

5. **Monitor explicit content distribution** — Track explicit content ratios across artists to align with platform guidelines or audience targeting.

---

## Lessons Learned

1. **API Rate Limiting**: Spotify enforces strict rate limits. Implemented retry logic with exponential backoff and `Retry-After` header handling for 429 responses.
2. **Star Schema Design**: Separating fact and dimension tables improves query performance and maintainability in Power BI.
3. **WSL2 Networking**: WSL2 has a separate network namespace from Windows. Used host IP (`172.24.96.1`) for cross-environment PostgreSQL connectivity from WSL2.
4. **Docker Hub Reliability**: Registry pulls can be blocked by network-level TLS resets (CloudFront EOF errors). Documented as a known limitation; local PostgreSQL serves as fallback.
5. **Multi-source API Integration**: Spotify's Client Credentials flow lacks streaming metrics. Integrated Last.fm as a supplementary source for engagement data.
6. **Docker Networking**: Containers communicate via Compose service names (`postgres`); `localhost` does not resolve across containers.
6. **WSL2 Networking**: WSL2 uses a virtual network; Windows host IP (`ip route show | grep default`) must be used for cross-environment connectivity.

---

## Future Improvements

- [ ] Add more data sources (Genius for lyrics, YouTube for video metrics)
- [ ] Implement incremental loading (only new/changed data)
- [ ] Add data quality checks (Great Expectations)
- [ ] Deploy to cloud (AWS RDS + EC2 or Azure PostgreSQL)
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Implement real-time streaming (Kafka + Spark)

---

## Security

All sensitive credentials are managed via environment variables. **Never commit secrets.**

### Setup Instructions

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Add your credentials to `.env`:
   ```env
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   LASTFM_API_KEY=your_lastfm_api_key
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=spotify_etl
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_postgres_password
   ```
3. **Never commit `.env`** — it is listed in `.gitignore`.

**Never commit:**
- Spotify Client Secret
- Last.fm API Key
- Database passwords
- Access tokens

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 18
- Docker Desktop
- Power BI Desktop

### 1. Clone the Repository
```bash
git clone https://github.com/Bhushan9-afk/Spotify_ETL_Project.git
cd Spotify_ETL_Project
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL
```sql
CREATE DATABASE spotify_etl;
```

### 4. Configure Environment Variables
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Add your credentials:
```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
LASTFM_API_KEY=your_lastfm_key
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=spotify_etl
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
```

### 5. Run the ETL Pipeline
```bash
python scripts/etl.py
```

### 6. Start Airflow
```bash
airflow standalone
```

### 7. Open Power BI
Connect to `localhost:5432` → `spotify_etl` database.

---

## Folder Structure

```
Spotify_ETL_Project/
├── data/               # Raw and processed data
├── sql/                # SQL scripts
├── scripts/            # Python ETL scripts
├── airflow/            # Airflow DAGs
├── dashboard/          # Power BI files
├── screenshots/        # Dashboard screenshots
├── docs/               # Documentation
├── docker/             # Docker configuration
├── tests/              # Unit tests
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Key Metrics

| Metric | Value |
|---|---|
| Artists | 10 |
| Albums | 50 |
| Tracks | 839 |
| Data Sources | Spotify API + Last.fm API |

---

## Lessons Learned

1. **API Rate Limiting**: Spotify enforces strict rate limits. Implemented retry logic with exponential backoff and `Retry-After` header handling for 429 responses.
2. **Star Schema Design**: Separating fact and dimension tables improves query performance and maintainability in Power BI.
3. **WSL2 Networking**: WSL2 has a separate network namespace from Windows. Used host IP (`172.24.96.1`) for cross-environment PostgreSQL connectivity from WSL2.
4. **Docker Hub Reliability**: Registry pulls can be blocked by network-level TLS resets (CloudFront EOF errors). Documented as a known limitation; local PostgreSQL serves as fallback.
4. **Multi-source API Integration**: Spotify's Client Credentials flow lacks streaming metrics. Integrated Last.fm as a supplementary source for engagement data.
5. **Docker Networking**: Containers communicate via Compose service names (`postgres`); `localhost` does not resolve across containers.
6. **WSL2 Networking**: WSL2 uses a virtual network; Windows host IP (`ip route show | grep default`) must be used for cross-environment connectivity.
5. **Docker Hub Reliability**: Registry pulls can be blocked by network-level TLS resets. Documented as a known limitation; local PostgreSQL serves as fallback.

---

## Future Improvements

- [ ] Add more data sources (Genius for lyrics, YouTube for video metrics)
- [ ] Implement incremental loading (only new/changed data)
- [ ] Add data quality checks (Great Expectations)
- [ ] Deploy to cloud (AWS RDS + EC2 or Azure PostgreSQL)
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Implement real-time streaming (Kafka + Spark)

---

## Author

**Bhushan** — Data Engineer

[GitHub](https://github.com/Bhushan9-afk) | [LinkedIn](https://www.linkedin.com/in/bhushan-sarwade/)

---

## License

MIT License