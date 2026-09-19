# Comprehensive Audited Technology Stack Specification

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**Auditor:** Senior Software Integration Engineer  
**Inspection Scope:** Direct verification of `requirements.txt`, imports in `api/`, `src/`, `database/`, and frontend bundles in `dashboard/`, `analyst/`, and `bank/`.

---

## 1. Technology Stack Architecture Overview

The framework employs a robust, modern, open-source technology stack optimized for rapid asynchronous execution, explainable machine learning, and resilient fallback persistence:

```
[Presentation Tier]   : Vanilla HTML5 / Modern CSS3 / JavaScript ES6+ / Leaflet.js 1.9.4
[Application Gateway] : Python 3.11 / FastAPI 0.110+ / Pydantic v2 / Uvicorn (ASGI)
[ML & Analytics]      : XGBoost 3.2.0 / Scikit-Learn 1.9.1 / SHAP 0.44+ / NumPy / Pandas
[Persistence Layer]   : Resilient Dual-Mode (CSV_FALLBACK_DEV / PostgreSQL 15+ & PostGIS 3.3+)
[Security & Audit]    : Python-JOSE (JWT HS256) / bcrypt / Thread-Safe Append Logs
```

---

## 2. Exhaustive Technology Audit Matrix

| Category | Technology | Purpose & Rationale | Implementing Modules | Integration Status | Known Limitations |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Frontend** | **HTML5 & Vanilla CSS3** | High-performance, zero-build UI rendering with responsive grid/flexbox layouts. Avoids frontend framework churn. | `dashboard/index.html`, `analyst/*.html`, `bank/index.html` | **FULLY INTEGRATED** | Requires manual DOM updates in JavaScript rather than reactive virtual DOM. |
| **Frontend** | **JavaScript ES6+** | Native asynchronous API client (`fetch`), dynamic modal handling, JWT token management. | `dashboard/js/*.js`, `analyst/js/*.js`, `bank/js/*.js` | **FULLY INTEGRATED** | Relies on browser `sessionStorage`; multi-tab sync requires separate events. |
| **Frontend** | **Leaflet.js 1.9.4** | Lightweight interactive GIS map engine rendering GeoJSON layers, markers, and circular buffers. | `dashboard/js/map.js` | **FULLY INTEGRATED** | Requires active Internet connectivity to fetch base map tiles (CartoDB/OSM). |
| **Backend** | **Python 3.11** | Core programming language offering optimal speed, type hinting, and scientific library support. | Entire codebase (`api/`, `src/`, `database/`) | **FULLY INTEGRATED** | Global Interpreter Lock (GIL) managed via asynchronous I/O and process workers. |
| **Backend** | **FastAPI** | High-throughput asynchronous ASGI web framework with automatic OpenAPI/Swagger generation. | `api/main.py`, `api/*_routes.py` | **FULLY INTEGRATED** | Requires lifespan context management for proper startup model loading. |
| **Backend** | **Pydantic v2** | Strict runtime data validation, schema enforcement, and JSON serialization. | `api/schemas.py`, `database/schemas.py` | **FULLY INTEGRATED** | Strict type parsing will reject malformed input payloads with HTTP 422. |
| **Backend** | **Uvicorn** | Lightning-fast ASGI web server implementation based on `uvloop` and `httptools`. | Server launch (`uvicorn api.main:app`) | **FULLY INTEGRATED** | Single-worker default; production requires multi-worker process manager. |
| **Machine Learning** | **XGBoost 3.2.0** | Gradient boosted decision tree ensemble with high predictive accuracy on tabular fraud datasets. | `models/xgboost_cybercrime_model.pkl`, `api/dependencies.py` | **FULLY INTEGRATED** | Predicts cashout probability, not exact physical latitude/longitude coordinates. |
| **Machine Learning** | **Scikit-Learn 1.9.1**| End-to-end `Pipeline` and `ColumnTransformer` providing frozen, leakage-free preprocessing. | `src/train_baselines.py`, `api/dependencies.py` | **FULLY INTEGRATED** | Pipeline parameters are frozen at runtime; cannot dynamically adapt to new categories without retraining. |
| **Machine Learning** | **SHAP 0.44+** | Local feature attribution via `TreeExplainer`, generating transparent risk factor breakdowns. | `api/analyst_routes.py`, `outputs/phase10_*` | **FULLY INTEGRATED** | Calculating exact Shapley values on large batches can incur CPU latency; optimized via background pre-caching. |
| **Analytics** | **DBSCAN Clustering**| Density-Based Spatial Clustering of Applications with Noise discovering geographic hotspots. | `src/hotspot_detection.py`, `api/gis_routes.py` | **FULLY INTEGRATED** | Fixed parameters ($\varepsilon=500\text{m}, \text{MinPts}=3$) do not dynamically adjust to sparse rural jurisdictions. |
| **Analytics** | **Haversine Distance**| Vectorized spherical distance calculation querying candidate ATMs against complaint centroids. | `database/spatial_queries.py`, `api/gis_routes.py` | **FULLY INTEGRATED** | Assumes spherical Earth model (accurate to within 0.5%, sufficient for 5km-10km buffers). |
| **Analytics** | **NumPy & Pandas** | High-performance vectorized numerical operations and tabular data transformation. | Data preprocessing, feature extraction, CSV parsing | **FULLY INTEGRATED** | High-concurrency pandas read/write on single CSV files requires atomic filelocks. |
| **Database** | **`CSV_FALLBACK_DEV`**| Zero-dependency filesystem storage using atomic threadlocks and NaN-safe JSON serialization. | `database/crud.py`, `database/investigation_crud.py` | **FULLY INTEGRATED (ACTIVE)** | Not suitable for enterprise multi-million record concurrency; designed for hackathon and demo environments. |
| **Database** | **PostgreSQL 15+** | Relational database persistence with ACID compliance, connection pooling, and relational integrity. | `database/connection.py`, `database/models.py` | **CONFIGURED / DEPLOY READY** | Requires active PostgreSQL daemon running on target host (currently offline in dev). |
| **Database** | **PostGIS 3.3+** | Geospatial database extension enabling GiST spatial indexes and SQL spatial functions (`ST_DWithin`). | `database/spatial_queries.py`, `sql/init_postgis.sql` | **CONFIGURED / DEPLOY READY** | Requires PostgreSQL service with PostGIS extension binaries installed. |
| **Database** | **SQLAlchemy 2.0** | Modern Python SQL toolkit and Object-Relational Mapper (ORM) managing sessions and pooling. | `database/connection.py` | **FULLY INTEGRATED** | Manages connection pool pre-pinging (`pool_pre_ping=True`) for fault recovery. |
| **Security** | **Python-JOSE (JWT)** | Cryptographic JSON Web Token issuance and verification using symmetric HS256 signatures. | `api/auth_routes.py`, `api/dependencies.py` | **FULLY INTEGRATED** | Stateless tokens require centralized blacklisting if immediate mid-session revocation is needed. |
| **Security** | **Bcrypt** | Direct cryptographic one-way password hashing with per-user salt generation. | `database/investigation_crud.py` | **FULLY INTEGRATED** | Deliberately computationally intensive to defend against brute-force dictionary attacks. |
| **Security** | **Audit Trail Engine**| Append-only tamper-evident event log recording user identity, action, and SHA-256 hash. | `database/investigation_crud.py`, `outputs/phase17_*` | **FULLY INTEGRATED** | Relies on filesystem append protections; enterprise production benefits from write-once storage (WORM). |

---

## 3. Technology Stack Governance

- **Zero Bloat:** All unneeded dependencies (e.g. heavyweight JavaScript frameworks or proprietary cloud SDKs) have been excluded.
- **Portability:** The entire application runs natively on both Windows and Linux environments without container dependencies.
- **Open Standards:** Built exclusively upon open-source, non-proprietary software packages.
