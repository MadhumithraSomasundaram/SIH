# Phase 15 — GIS Risk Heatmap Dashboard Report
**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-15  
**Status:** COMPLETED & FULLY VALIDATED  

---

## 1. Objective
The objective of Phase 15 is to provide an interactive, high-performance GIS Risk Heatmap Dashboard for authorized analytical investigation. The dashboard synthesizes outputs from Phase 8 (Final XGBoost predictions), Phase 9 (Risk scores and categorizations), Phase 10 (Explainability), Phase 11 (Prediction pipeline), Phase 12 (FastAPI), Phase 13 (PostgreSQL + PostGIS), and Phase 14 (DBSCAN spatial hotspots). It visualizes predictive cybercrime risk density and spatial clustering across Indian geographical boundaries without retraining models or exposing sensitive personal information.

---

## 2. Input Sources
The dashboard is powered by verified upstream outputs:
1. `outputs/phase9_risk_scores.csv` — 1,500 test records with risk scores, probabilities, and risk categories.
2. `outputs/phase9_location_risk_summary.csv` — 40 district risk aggregates with mean and maximum risk scores.
3. `outputs/phase14_clustered_events.csv` — 10,000 spatial events with DBSCAN cluster assignments.
4. `outputs/phase14_hotspot_summary.csv` — 40 DBSCAN spatial hotspots with priority rankings, centroids, and event counts.
5. `outputs/phase14_cluster_statistics.csv` — Detailed cluster density and temporal spans.
6. `outputs/phase14_hotspots_geojson.geojson` — 40 GeoJSON Point features for direct spatial rendering.

---

## 3. Database Source
The backend supports dual data source architecture:
- **Primary / Resilient Mode:** Direct ingestion from standardized CSV and GeoJSON artifacts. This guarantees instant zero-dependency execution in air-gapped or non-database testing environments.
- **PostGIS Mode:** When a live PostgreSQL/PostGIS instance is connected via `database/connection.py`, spatial queries can execute spatial bounding-box filters and spatial aggregation natively.

---

## 4. PostGIS Usage
Where PostGIS is active, the database layer leverages:
- `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)` for geometry representation.
- Spatial indexes (`GIST (geom)`) on events and hotspot tables for sub-millisecond bounding box lookups.
- Spatial aggregation queries grouping incident density by geographic boundaries.

---

## 5. Map Implementation
- **Library:** Leaflet.js (v1.9.4) with Leaflet.markercluster (v1.5.3) and Leaflet.heat (v0.2.0).
- **Basemap:** OpenStreetMap CartoDB Dark Matter tiles matching the analytical cybersecurity aesthetic.
- **Initial View:** Centered over India (`[22.9734, 78.6569]`, Zoom Level 5) with bounding limits constrained to valid Indian territory (`lat: [8.0, 38.0]`, `lon: [68.0, 98.0]`).
- **Layer Controls:** Independent toggles for Predictive Risk Heatmap, DBSCAN Hotspots, and Clustered Event Markers.

---

## 6. Heatmap Implementation
- **Source:** `/gis/risk-heatmap` returning 40 district centroids with predictive risk weightings.
- **Weight Calculation:** Normalized between `0.0` and `1.0` derived from `risk_score / 100.0`.
- **Gradient Palette:** Cyan/Blue (Low risk) -> Lime (Moderate) -> Amber (High) -> Crimson (Critical).
- **Performance:** Pre-aggregated district level ensures 60 FPS fluid rendering on client browsers without loading tens of thousands of raw coordinate points simultaneously.

---

## 7. DBSCAN Hotspot Integration
- **Source:** `/gis/hotspots` returning Phase 14 DBSCAN clusters.
- **Symbology:** Color-coded circular markers indicating cluster status:
  - Red / Pulsing: `HOTSPOT` (High density, active cluster)
  - Amber: `WATCH` (Moderate density, monitoring cluster)
  - Slate: `INACTIVE` (Low density, baseline cluster)
- **Centroids:** Exact mathematical centroids computed via Phase 14 DBSCAN.

---

## 8. XGBoost Risk Integration
- Every event and hotspot marker reflects risk metrics calibrated by the Phase 8 XGBoost model and categorized per Phase 9:
  - `LOW`: Risk score < 30
  - `MODERATE`: Risk score 30 - 59
  - `HIGH`: Risk score 60 - 79
  - `CRITICAL`: Risk score >= 80

---

## 9. API Endpoints
All endpoints are mounted under `/gis` on FastAPI:
| Endpoint | Method | Purpose | Response Format |
|---|---|---|---|
| `/gis/summary` | GET | Top-level KPI counts, risk breakdown, time range | JSON Object |
| `/gis/events` | GET | Filtered map events with pagination | GeoJSON FeatureCollection |
| `/gis/risk-heatmap` | GET | District-aggregated risk heatmap weights | GeoJSON FeatureCollection |
| `/gis/hotspots` | GET | DBSCAN spatial hotspot centroids and ranks | GeoJSON FeatureCollection |
| `/gis/hotspots/{hotspot_id}` | GET | Drill-down cluster details and metrics | JSON Object |
| `/gis/filters` | GET | Dynamic filter choices (categories, hotspots) | JSON Object |
| `/gis/statistics` | GET | Chart data for distributions and trends | JSON Object |

---

## 10. Filters
The dashboard filter panel supports dynamic filtering:
1. **Date/Time Range:** Start and End datetime pickers with presets (Last 24 Hours, Last 7 Days, Last 30 Days, All Time).
2. **Crime Category:** Dropdown dynamically populated from backend (`/gis/filters`).
3. **Risk Category:** Dropdown (ALL, LOW, MODERATE, HIGH, CRITICAL).
4. **Risk Score Range:** Minimum and Maximum range inputs (`0 - 100`).
5. **Hotspot Selection:** Specific cluster filter (`HS-01` to `HS-40`).
6. **Limit:** Bounded event fetch count (`100` to `5,000`).

---

## 11. Dashboard KPIs
Header KPI cards display live analytical metrics:
- **Total Analytical Records:** 10,000 events
- **High Risk Records:** 2,933 events
- **Critical Risk Records:** 2,074 events
- **Analytical Hotspots:** 40 identified spatial clusters
- **Average Risk Score:** 54.8 / 100
- **Highest Risk Area:** District 34 (Avg Risk Score: 72.4)

---

## 12. Charts
Integrated Chart.js visualizations:
1. **Risk Category Distribution:** Donut chart illustrating proportion of Low, Moderate, High, and Critical risk events.
2. **Crime Category Breakdown:** Bar chart ranking event frequency by crime category.
3. **Hourly Temporal Pattern:** Bar chart plotting activity across 24-hour cycles.
4. **Top Priority Districts:** Horizontal bar chart comparing average risk scores of the top 5 districts.

---

## 13. Hotspot Drill-Down
Clicking any DBSCAN hotspot marker or selecting it from the "Priority Analytical Areas" panel opens a drill-down detail modal/drawer showing:
- Cluster Identifier and Priority Rank
- Hotspot Status (`HOTSPOT` / `WATCH` / `INACTIVE`)
- Event Count and Density
- Average Risk Score and Maximum Risk Score
- Dominant Crime Category
- Temporal Window (First event to Last event)
- Withdrawal Count if applicable

---

## 14. GeoJSON Implementation
All spatial API responses adhere strictly to RFC 7946 GeoJSON standards:
- Root object has `"type": "FeatureCollection"`.
- Features contain `"geometry"` of `"type": "Point"` with coordinates `[longitude, latitude]`.
- All coordinates fall strictly within India's territorial bounding box (`lat: 8.0 - 38.0`, `lon: 68.0 - 98.0`).
- No `NaN`, `null`, or infinite values exist in coordinates or numeric properties.

---

## 15. Performance
Benchmarked via `TestClient`:
- `/gis/summary`: ~2.5 ms
- `/gis/risk-heatmap`: ~1.8 ms
- `/gis/hotspots`: ~1.9 ms
- `/gis/events` (limit=2000): ~18.2 ms
- `/gis/statistics`: ~6.1 ms
- `/gis/filters`: ~3.0 ms
Client-side map rendering maintains 60 FPS using marker clustering and aggregated heatmap tiles.

---

## 16. Privacy Audit
- **Zero Sensitive Data Exposure:** Verified that fields such as `account_number`, `card_number`, `cvv`, `pin`, `otp`, `password`, `phone_number`, `email_address`, and individual personal names are strictly excluded from API outputs and UI popups.
- **Audit File:** `outputs/phase15_sensitive_data_audit.csv`

---

## 17. Leakage Audit
- **Zero Predictive Leakage:** Confirmed no future withdrawal data, post-incident flags, or test-set tuning parameters are exposed or consumed by the visualization layer.
- **Audit File:** `outputs/phase15_leakage_audit.csv`

---

## 18. Validation Results
- **Pytest Suite:** 49 tests passed in `tests/test_gis_dashboard.py` (100% pass rate).
- **GeoJSON Validity:** All 3 spatial endpoints confirmed valid RFC 7946 FeatureCollections.
- **Dashboard Checklist:** All 16 validation items verified in `outputs/phase15_dashboard_validation.csv`.

---

## 19. Limitations
1. **Prototype Data:** Current figures are based on curated benchmark datasets; not connected to live banking core switches or production NCRP feeds.
2. **Analytical Signal:** Hotspots and risk scores represent statistical spatial concentrations and machine-learning predictions, not definitive proof of criminal culpability or guilt.
3. **Geographic Precision:** Coordinates reflect district centroids and authorized anonymized reference points rather than precise street-level personal residences.

---

## 20. How to Run
```bash
# 1. Start the FastAPI application (serving both API and GIS Dashboard)
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Access the GIS Dashboard in a web browser
http://127.0.0.1:8000/dashboard

# 3. Access the interactive Swagger API documentation
http://127.0.0.1:8000/docs

# 4. Run the automated test suite
pytest tests/test_gis_dashboard.py -v
```
