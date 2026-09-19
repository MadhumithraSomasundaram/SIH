# Phase 13 — PostgreSQL + PostGIS Spatial Database Integration Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Objective

Phase 13 establishes the enterprise spatial database foundation for the Cybercrime Predictive Analytics Framework by integrating **PostgreSQL** with the **PostGIS** spatial extension. The database provides robust, ACID-compliant storage for authorized, anonymized cybercrime complaints and model prediction intelligence using native geographic data types (WGS 84 SRID 4326), spatial indexing (GIST), and geodesic spatial query capabilities.

---

## 2. Architecture & Component Interaction

```
[ Incoming Complaints / Predictions ]
                  │
                  ▼
         [ FastAPI Serving Layer ]
         (api/main.py, api/schemas.py)
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  [ ML Engine ]       [ Database Layer ]
  (Phase 11/12)       (database/connection.py, get_db)
        │                   │
        │             ┌─────┴─────────────────────┐
        │             ▼                           ▼
        │    [ CybercrimeEvent ]        [ PredictionResult ]
        │    (SQLAlchemy + GeoAlchemy2) (SQLAlchemy + GeoAlchemy2)
        │             │                           │
        └─────────────┼───────────────────────────┘
                      ▼
         [ PostgreSQL + PostGIS ]
       ┌─────────────────────────────┐
       │ - SRID 4326 (WGS 84)        │
       │ - POINT(lon lat) Geometries │
       │ - Spatial GIST Indexes      │
       │ - Ellipsoidal Geodesics     │
       └─────────────────────────────┘
```

---

## 3. PostgreSQL Configuration

- **Database Name:** `cybercrime_prediction`
- **Driver:** `psycopg` (v3 modern async/sync binary driver) via SQLAlchemy 2.0
- **Connection URI Format:** `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`
- **Environment Management:** Driven entirely via `.env` and `python-dotenv` (see [`.env.example`](file:///D:/SIH/SIH_2026/cybercrime_prediction/.env.example)). Zero credentials or passwords committed to source control.
- **Connection Pooling:**
  - Pool Size: 5 persistent connections
  - Max Overflow: 10 burst connections
  - Pool Timeout: 30 seconds
  - Pool Recycle: 1800 seconds (30 minutes)
  - Pre-Ping: Enabled (`pool_pre_ping=True`) for automatic dead-connection recovery
  - Connect Timeout: 2 seconds to ensure prompt failure when server is unreachable

---

## 4. PostGIS Configuration

- **Extension:** `postgis` enabled via `CREATE EXTENSION IF NOT EXISTS postgis;` (see [`sql/01_extensions.sql`](file:///D:/SIH/SIH_2026/cybercrime_prediction/sql/01_extensions.sql)).
- **Coordinate Reference System (CRS):** EPSG:4326 (WGS 84 Ellipsoid).
- **Coordinate Order:** Strictly adheres to OGC standards: `POINT(longitude latitude)`:
  - `longitude`: $[-180.0, 180.0]$
  - `latitude`: $[-90.0, 90.0]$
- **Distance Calculation:** Performed using `geography` type casting (`location::geography`) so all distance measurements, buffers, and radius constraints are evaluated in **meters** on the terrestrial spheroid rather than planar degrees.

---

## 5. Database Schema & Tables

Defined in [`sql/02_schema.sql`](file:///D:/SIH/SIH_2026/cybercrime_prediction/sql/02_schema.sql) and mapped via SQLAlchemy in [`database/models.py`](file:///D:/SIH/SIH_2026/cybercrime_prediction/database/models.py):

### Table 1: `cybercrime_events`
Stores authorized, anonymized incident reports with spatial geometries:

| Column | Data Type | Constraints / Properties | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Autoincrementing internal identifier |
| `case_id` | `VARCHAR(64)` | `UNIQUE NOT NULL`, Indexed | Sanitized case reference (e.g., `CMP-2026-000001`) |
| `complaint_timestamp`| `TIMESTAMP` | `NOT NULL`, Indexed | Time incident occurred or reported |
| `crime_type` | `VARCHAR(64)` | `NOT NULL`, Indexed | Standardized crime category (UPI_FRAUD, etc.) |
| `fraud_amount` | `DOUBLE PRECISION`| `NOT NULL` | Financial loss amount in INR |
| `reported_by_authority`| `INTEGER` | `DEFAULT 0` | 1 if reported by authority, 0 if citizen |
| `victim_state` | `VARCHAR(64)` | `NULLABLE` | State boundary name |
| `victim_district`| `VARCHAR(64)` | `NULLABLE`, Indexed | Administrative district |
| `victim_area` | `VARCHAR(128)` | `NULLABLE` | Locality or beat area |
| `victim_area_id` | `VARCHAR(64)` | `NULLABLE` | Area master code reference |
| `latitude` | `DOUBLE PRECISION`| `NULLABLE` | WGS 84 latitude $[-90, 90]$ |
| `longitude` | `DOUBLE PRECISION`| `NULLABLE` | WGS 84 longitude $[-180, 180]$ |
| `location` | `GEOMETRY(Point, 4326)`| `NULLABLE`, GIST Indexed | PostGIS `POINT(longitude latitude)` |
| `is_linked_to_withdrawal`| `INTEGER` | `DEFAULT 0` | Historical cashout flag from source data |
| `future_withdrawal` | `INTEGER` | `NULLABLE` | Binary training target (null for unseen complaints) |
| `created_at` | `TIMESTAMP` | `DEFAULT UTC NOW` | Record creation timestamp |

### Table 2: `prediction_results`
Stores operational inferences generated by Phase 11 / Phase 12 serving layer:

| Column | Data Type | Constraints / Properties | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Autoincrementing prediction id |
| `prediction_reference`| `VARCHAR(64)`| `NOT NULL`, Indexed | Case reference |
| `prediction_timestamp`| `TIMESTAMP`| `NOT NULL`, Indexed | Time of model inference |
| `predicted_probability`| `DOUBLE PRECISION`| `NOT NULL` | Continuous probability $[0.0, 1.0]$ |
| `risk_score` | `INTEGER` | `NOT NULL` | Phase 9 calibrated score $[0, 100]$ |
| `risk_category` | `VARCHAR(32)` | `NOT NULL`, Indexed | Tier (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) |
| `operational_interpretation`| `TEXT` | `NULLABLE` | Plain language analyst guidance |
| `model_version` | `VARCHAR(64)` | `NOT NULL` | Version fingerprint (`v1.0.0-xgb-668c1916`) |
| `latitude` | `DOUBLE PRECISION`| `NULLABLE` | Incident latitude |
| `longitude` | `DOUBLE PRECISION`| `NULLABLE` | Incident longitude |
| `location` | `GEOMETRY(Point, 4326)`| `NULLABLE`, GIST Indexed | Spatial prediction point |
| `victim_district` | `VARCHAR(64)` | `NULLABLE` | Incident district |
| `crime_type` | `VARCHAR(64)` | `NULLABLE` | Crime category |
| `created_at` | `TIMESTAMP` | `DEFAULT UTC NOW` | Record creation timestamp |

---

## 6. Spatial Indexes

Defined in [`sql/03_indexes.sql`](file:///D:/SIH/SIH_2026/cybercrime_prediction/sql/03_indexes.sql):
- **GIST Spatial Indexes:**
  - `idx_cybercrime_events_location`: `USING GIST(location)` on `cybercrime_events`
  - `idx_prediction_results_location`: `USING GIST(location)` on `prediction_results`
- **B-Tree Indexes for Query Optimization:**
  - `idx_cybercrime_events_timestamp` on `complaint_timestamp`
  - `idx_cybercrime_events_crime_type` on `crime_type`
  - `idx_cybercrime_events_district` on `victim_district`
  - `ix_events_district_timestamp` on `(victim_district, complaint_timestamp)`
  - `idx_prediction_results_timestamp` on `prediction_timestamp`
  - `idx_prediction_results_category` on `risk_category`
  - `idx_prediction_results_district_score` on `(victim_district, risk_score)`

---

## 7. Data Validation & Audit Results

Validation conducted across the complete 10,000-record dataset ([`outputs/phase13_spatial_validation.csv`](file:///D:/SIH/SIH_2026/cybercrime_prediction/outputs/phase13_spatial_validation.csv)):
- **Total Records:** 10,000
- **Valid Coordinates:** 10,000 (100.0% valid)
  - Latitude bounds observed: $[8.5241, 17.6868]$ (Well within India / regional bounds $[-90, 90]$)
  - Longitude bounds observed: $[74.4977, 83.2185]$ (Well within regional bounds $[-180, 180]$)
- **Invalid Coordinates:** 0
- **Missing Coordinates:** 0
- **Geometry POINT Created:** 10,000 points in SRID 4326
- **Null Geometry:** 0

### Sensitive Data Audit ([`outputs/phase13_sensitive_data_audit.csv`](file:///D:/SIH/SIH_2026/cybercrime_prediction/outputs/phase13_sensitive_data_audit.csv)):
- Prohibited fields (`card_number`, `pin`, `otp`, `cvv`, `password`, `victim_phone`) are strictly excluded from schemas and ingestion.
- `victim_account_id_masked` is excluded from database storage to eliminate financial account tracing risk in the spatial layer.

---

## 8. Spatial Queries Implementation

Implemented in [`database/spatial_queries.py`](file:///D:/SIH/SIH_2026/cybercrime_prediction/database/spatial_queries.py):
1. **Radius Search:** `find_events_within_radius(db, lat, lon, radius_meters, limit)`
   - Uses `ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography, radius_meters)`
   - Accurately measures distance in meters on the WGS 84 ellipsoid.
2. **Radius Count:** `count_events_within_radius(db, lat, lon, radius_meters)`
   - Fast spatial aggregation for crime density assessment.
3. **Geodesic Distance:** `calculate_distance_meters(db, lat1, lon1, lat2, lon2)`
   - Great-circle / ellipsoidal distance in meters between any two points.
4. **Bounding Box Search:** `find_events_in_bounding_box(db, min_lat, max_lat, min_lon, max_lon, limit)`
   - Uses PostGIS bounding envelope operator `&& ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)`.
5. **District Aggregation:** `group_events_by_district(db)`
   - Groups complaint volume, location completeness, and aggregate fraud loss across districts.
6. **Temporal Recency:** `find_recent_events_by_timestamp(db, since_timestamp, limit)`
   - Fast B-Tree indexed chronological retrieval.

---

## 9. FastAPI Integration & Endpoints

Integrated into [`api/main.py`](file:///D:/SIH/SIH_2026/cybercrime_prediction/api/main.py):
- **`GET /database/health`**:
  - Returns `{"database": "connected", "postgis": true, "postgis_version": "3.x", "error": null}` when healthy.
  - Returns `HTTP 503 Service Unavailable` with clean diagnostic message when database is offline. Never leaks credentials.
- **`GET /database/stats`**:
  - Returns aggregate database counts, spatial coverage percentage, latest/earliest complaint timestamps, and distinct district counts.
  - Returns `HTTP 503` when database is offline.
- **`POST /predict` Integration**:
  - Dependency injection via `get_db()` session manager.
  - Automatically records safe prediction metrics (`predicted_probability`, `risk_score`, `risk_category`, `model_version`, and location point) into `prediction_results`.
  - Fail-safe: if the database is temporarily offline, prediction inference completes seamlessly without error to the API client.

---

## 10. Automated Test Results

Exhaustive test suite verified using `pytest`:

```bash
pytest tests/test_database.py -v
```
**Results: 14/14 tests passing.**
- `TestCoordinateValidation` (4 tests): Valid coordinates pass, latitude bounds enforced, longitude bounds enforced, None coordinates handled safely.
- `TestTableSchemas` (2 tests): `cybercrime_events` and `prediction_results` table registrations verified with all required columns.
- `TestPydanticDatabaseSchemas` (5 tests): Event create schemas, prediction storage schemas, radius query schemas, bounding box validation, and min/max order enforcement verified.
- `TestDatabaseEndpoints` (2 tests): `GET /database/health` and `GET /database/stats` response contracts verified (status 200 or 503 without leaking credentials).
- `TestConnectionHealthFunction` (1 test): `check_database_health()` dictionary structure verified.

Regression Verification:
```bash
pytest tests/test_api.py -v
```
**Results: 55/55 tests passing.** Zero regressions across all Phase 12 endpoints.

---

## 11. Limitations & Future Phase Roadmap

- **No DBSCAN or Clustering:** Phase 13 provides only relational and spatial storage; spatio-temporal hotspot clustering and cashout trajectory analysis are deferred to Phase 14.
- **No Leaflet / GIS UI:** Spatial data is exposed exclusively via REST API JSON; visualization map layers are scheduled for future frontend phases.
- **No Direct Banking Links:** Database operations run on anonymized, authorized cybercrime complaints and do not connect to live core banking or switch systems.

---

## 12. Operational Runbook

### Step 1: Initialize Database & Schema
Ensure PostgreSQL is running and `DATABASE_URL` is set in `.env`:
```bash
# Apply extensions, schema, and indexes
python database/init_db.py
```

### Step 2: Import Verified Spatial Data
```bash
# Ingest 10,000 verified complaint records with spatial points
python scripts/load_database.py
```

### Step 3: Run the API Server
```bash
# Launch FastAPI development server
uvicorn api.main:app --reload --port 8000
```

### Step 4: Verify Endpoints
```bash
# Check database and PostGIS health
curl http://localhost:8000/database/health

# Check database spatial statistics
curl http://localhost:8000/database/stats
```
