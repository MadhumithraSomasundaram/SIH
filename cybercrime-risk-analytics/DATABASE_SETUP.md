# PostgreSQL + PostGIS Setup & Storage Architecture
**Cybercrime Predictive Analytics Framework (Smart India Hackathon Problem Statement ID 26184)**

---

## 1. Storage Architecture Overview

The Cybercrime Predictive Analytics Framework employs an enterprise **Dual Storage Strategy** designed for mission-critical reliability:

1. **Primary Storage Mode (`POSTGRESQL_POSTGIS`)**:
   - **Engine**: PostgreSQL 16+ with PostGIS spatial extension.
   - **Purpose**: High-throughput spatial indexing (`GIST` indexes on `location`), spatial radius queries (`ST_DWithin`, `ST_Distance`), bounding-box analytics (`ST_MakeEnvelope`), automated prediction persistence (`prediction_results`), and persistent investigation audit logging (`analyst_audit_log`).
   - **Performance**: Optimized sub-second spatial queries across millions of incident records.

2. **Resilient Development / Demo Fallback Mode (`CSV_FALLBACK_DEV`)**:
   - **Source**: Verified CSV artifacts in `outputs/` (`phase14_clustered_events.csv`, `phase14_hotspot_summary.csv`, etc.).
   - **Purpose**: Ensures that all API endpoints, frontend dashboards, GIS visualization layers, and analytical inference pipelines operate without crashing even when a PostgreSQL instance is not provisioned or running on the developer workstation.
   - **Transparency**: Storage mode is transparently exposed in `GET /database/health` (`storage_mode: "CSV_FALLBACK_DEV"`) and startup logs. The system never fakes database connectivity.

---

## 2. Option A: Quickstart via Docker (Recommended)

The simplest way to run PostgreSQL 16 with PostGIS is using Docker:

### 1. Run PostGIS Container
```bash
docker run -d \
  --name cybercrime_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cybercrime_prediction \
  -p 5432:5432 \
  postgis/postgis:16-3.4
```

### 2. Or using `docker-compose.yml`
Create a `docker-compose.yml` in the project root:
```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:16-3.4
    container_name: cybercrime_postgis
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: cybercrime_prediction
    ports:
      - "5432:5432"
    volumes:
      - postgis_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d cybercrime_prediction"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgis_data:
```
Launch with:
```bash
docker-compose up -d
```

---

## 3. Option B: Native Windows Installation

1. **Download PostgreSQL Installer**:
   - Download the official PostgreSQL 16 installer from [EnterpriseDB](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
   - Run the installer. When prompted, note the superuser password assigned to `postgres`.

2. **Install PostGIS via Stack Builder**:
   - At the end of the installation, check the box to launch **Stack Builder**.
   - Select your PostgreSQL 16 installation.
   - Under **Spatial Extensions**, check **PostGIS 3.4+ Bundle**.
   - Complete the PostGIS installation wizard.

3. **Create Database & Enable Extension**:
   Open Windows Command Prompt or PowerShell and execute:
   ```powershell
   # Connect to psql
   psql -U postgres

   # In psql prompt:
   CREATE DATABASE cybercrime_prediction;
   \c cybercrime_prediction
   CREATE EXTENSION postgis;
   SELECT PostGIS_Version();
   \q
   ```

---

## 4. Environment Configuration

Copy `.env.example` to `.env` in the project root:

```bash
copy .env.example .env
```

Edit `.env` to match your local database credentials. You can either specify a unified `DATABASE_URL` or discrete connection parameters:

```env
# Unified URL (psycopg v3 driver)
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/cybercrime_prediction

# OR Discrete Parameters:
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=cybercrime_prediction

# Connection Settings
DB_CONNECT_TIMEOUT=2
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Feature Flags
ENABLE_PREDICTION_STORAGE=true
```

> **Security Note**: Never commit `.env` containing production passwords to source control. The `.gitignore` file is configured to exclude `.env`.

---

## 5. Schema Initialization

Run the automated database initialization script to create tables, GIST spatial indexes, and B-tree indexes:

```bash
python database/init_db.py
```

This will automatically create:
- `cybercrime_events` (with PostGIS `geometry(Point, 4326)` column and GIST index)
- `prediction_results` (with spatial coordinates, model version, risk scores)
- `hotspots` (Phase 14 spatial cluster polygons/centroids)
- `analyst_audit_log` (audit trail for case review and alert acknowledgment)
- Standard performance indexes on timestamps, crime categories, and districts.

---

## 6. Data Migration / Ingestion

To populate PostgreSQL with historical/anonymized cybercrime data from the processed datasets:

```bash
python scripts/load_database.py --input data/processed/targeted_cybercrime_data.csv
```

Features of the ingestion pipeline:
- **Coordinate Validation**: Validates latitude/longitude bounds before insertion.
- **PII Scrubbing**: Strictly strips sensitive financial data (account numbers, card numbers, OTPs, PINs, passwords).
- **Batch Processing**: Batches records in chunks of 500 for optimal memory and transaction efficiency.
- **Graceful Resilience**: If PostgreSQL is offline, generates validation reports and CSV audit files without crashing.

---

## 7. Verification & Health Monitoring

### Database Health Endpoint
Check connection status and active storage mode:
```bash
curl -X GET http://localhost:8000/database/health
```

**Response (PostgreSQL Active)**:
```json
{
  "status": "connected",
  "database": "connected",
  "storage_mode": "POSTGRESQL_POSTGIS",
  "database_host": "localhost:5432",
  "database_name": "cybercrime_prediction",
  "postgis": true,
  "postgis_version": "3.4.0",
  "error": null,
  "setup_instructions": null
}
```

**Response (PostgreSQL Offline - Fallback Mode)**:
```json
{
  "status": "disconnected",
  "database": "disconnected",
  "storage_mode": "CSV_FALLBACK_DEV",
  "database_host": "localhost:5432",
  "database_name": "cybercrime_prediction",
  "postgis": false,
  "postgis_version": null,
  "error": "Database connection unavailable. System operating in CSV_FALLBACK_DEV mode.",
  "setup_instructions": "To enable primary PostgreSQL+PostGIS storage, start PostgreSQL service and refer to DATABASE_SETUP.md."
}
```

### Database Aggregate Stats Endpoint
```bash
curl -X GET http://localhost:8000/database/stats
```
Returns total event count, spatial coordinates coverage percentage, unique districts, and event time ranges.
