# Project Structure & Implementation Analysis
**Cybercrime Predictive Analytics Framework**  
**Problem Statement ID:** 26184  
**Audit Date:** September 19, 2026  
**Auditor:** Senior Software Architect, ML Engineer, Cybersecurity Analyst & GIS Specialist  

---

## 1. Executive Structural Overview

The repository is structured as a Python-based machine learning and spatial analytical intelligence system designed to support Law Enforcement Agencies (LEAs) and financial institutions in prioritizing likely cybercrime cashout locations.

The architecture comprises:
- An offline, reproducible data cleaning and machine learning training pipeline (`src/`, `notebooks/`, `data/`).
- Trained model pipelines and preprocessors stored as serialized joblib artifacts (`models/`).
- An asynchronous FastAPI backend serving prediction, explainability, GIS, alert, and analyst workflows (`api/`).
- A multi-tier storage abstraction supporting PostgreSQL/PostGIS with an automatic local CSV/disk-persistent fallback (`database/`).
- Three specialized frontend interfaces (`dashboard/`, `analyst/`, `bank/`) built with vanilla HTML5, CSS3, and modern ES6 JavaScript.
- A 18-module automated test suite consisting of 342 tests (`tests/`).

```
d:/SIH/SIH_2026/cybercrime_prediction/
│
├── data/
│   ├── raw/                           # Immutable raw CSV datasets (Complaints, Withdrawals, Txns, ATMs, Areas, Accounts)
│   └── processed/                     # Cleaned, standardized, feature-engineered, and chronologically split CSVs
│
├── models/                            # Serialized scikit-learn/XGBoost pipelines and metadata JSONs
│   ├── xgboost_cybercrime_model.pkl   # Primary calibrated inference pipeline (ColumnTransformer + XGBClassifier)
│   ├── baseline_dummy.pkl             # Zero-rule prior baseline
│   ├── baseline_logistic_regression.pkl # Linear baseline pipeline
│   ├── baseline_random_forest.pkl     # Non-linear baseline pipeline
│   └── phase7_xgboost_metadata.json   # 24 training metadata parameters & 64 certified features
│
├── src/                               # Offline batch pipeline scripts (Phases 1–11, 14)
│   ├── data_cleaning.py               # 16-step cleaning & PII masking
│   ├── feature_engineering.py         # 64-feature spatio-temporal generation
│   ├── create_target.py               # 24h qualifying cashout target labeling
│   ├── temporal_split.py              # Chronological train/validation/test split
│   ├── train_baselines.py             # Baseline model training
│   ├── train_xgboost.py               # Primary XGBoost model training & hyperparameter tuning
│   ├── evaluate_final_model.py        # Out-of-sample Phase 8 test evaluation
│   ├── evaluate_temporal_forecasting.py # Deep learning LSTM/GRU feasibility evaluation
│   ├── explain_with_shap.py           # Global & local SHAP TreeExplainer calculation
│   ├── hotspot_detection.py           # DBSCAN unsupervised geospatial clustering
│   ├── mule_pattern_detection.py      # Rule-based heuristic transaction fan-in indicator
│   ├── alert_engine.py                # Predictive alert generation, scoring, and deduplication
│   └── predict.py                     # Production inference engine & schema validator
│
├── api/                               # FastAPI serving layer (Endpoints, Auth, Middleware)
│   ├── main.py                        # Application lifecycle, `/predict`, `/explain`, `/health`
│   ├── auth.py                        # API key guard (`X-API-Key`) & JWT verification
│   ├── gis_routes.py                  # GIS GeoJSON endpoints (`/gis/summary`, `/gis/hotspots`, `/gis/predicted-locations`)
│   ├── alert_routes.py                # Alert lifecycle, dispatch log, and transition APIs
│   ├── analyst_routes.py              # RBAC-gated investigation docketing, brief export, and outcome tracking
│   ├── bank_routes.py                 # Institutional banking portal endpoints & ATM proximity queries
│   ├── dependencies.py                # Singleton app state & model loading lifecycle
│   ├── error_handlers.py              # Sanitized exception handlers (PII leak prevention)
│   └── schemas.py                     # Pydantic v2 schemas for API contracts
│
├── database/                          # Persistence layer & Multi-storage abstraction
│   ├── connection.py                  # SQLAlchemy engine, session management, and health diagnostics
│   ├── models.py                      # SQLAlchemy ORM models (CybercrimeEvent, Hotspot, Alert, etc.)
│   ├── crud.py                        # Database operations and CSV fallback loaders
│   ├── investigation_models.py        # Investigation docketing, notes, evidence, audit, and outcome models
│   ├── investigation_schemas.py       # Investigation Pydantic schemas & state transition matrices
│   ├── investigation_crud.py          # Thread-safe persistent CSV fallback & DB operations for analyst interface
│   ├── spatial_queries.py             # PostGIS ST_DWithin and ST_Centroid queries
│   └── init_db.py                     # Database table creation script
│
├── dashboard/                         # Frontend 1: GIS Heatmap & Analytical Hotspot Dashboard
│   ├── index.html                     # Responsive dark-theme tactical operations center
│   ├── css/                           # Custom dark cyber-security design system
│   └── js/                            # Leaflet map controller, filter engine, alert drawer, KPI charts
│
├── analyst/                           # Frontend 2: Authorized LEA Analyst Portal
│   ├── index.html                     # Tactical docket management & case queues
│   ├── investigation.html             # Case dossier: SHAP attribution, ATM proximity, evidence, outcome loop
│   ├── alerts.html                    # Real-time triage queue with status transition actions
│   ├── audit.html                     # Immutable audit trail inspection (Supervisor/Admin only)
│   ├── css/                           # Clean LEA terminal theme
│   └── js/                            # JWT session manager, brief generator, outcome feedback modal
│
├── bank/                              # Frontend 3: Secure Institutional Banking Interface
│   ├── index.html                     # Bank-scoped physical ATM proximity alert view
│   ├── css/                           # Banking compliance theme
│   └── js/                            # Institution-specific ATM proximity filter
│
├── notifications/                     # Alert dispatch notification channels
│   ├── dispatcher.py                  # Multi-channel notification router & retry engine
│   ├── email.py                       # Simulated SMTP alert sender
│   ├── sms.py                         # Simulated cellular SMS dispatcher
│   ├── webhook.py                     # Simulated secure webhook dispatcher
│   └── notification_log.py            # Persistent CSV dispatch logging (`outputs/notification_log.csv`)
│
├── tests/                             # Automated test suite (342 test cases across 18 modules)
├── sql/                               # PostGIS table definitions, extensions, and spatial index scripts
├── config/                            # Alert thresholds and system configuration (`alert_config.json`)
├── outputs/                           # Comprehensive audit reports, metrics, evaluation curves, figures, and CSV logs
└── notebooks/                         # 6 sequential exploratory and developmental Jupyter notebooks
```

---

## 2. Component-by-Component Implementation Analysis

### 2.1 Backend Architecture
- **Framework:** FastAPI (`0.115+`) with Uvicorn server and Pydantic v2 schemas.
- **Startup Lifecycle:** `api/main.py:lifespan` dynamically loads `models/xgboost_cybercrime_model.pkl`, metadata JSON, and certified feature columns into singleton `AppState` (`api/dependencies.py`). If model artifacts are missing, graceful 503 error responses are returned.
- **CORS & Error Shielding:** localhost-scoped CORS policy (`localhost`, `127.0.0.1`). Stack traces and internal paths are masked via `api/error_handlers.py`.
- **Finding:** Fully implemented and operational.

### 2.2 Frontend Interfaces
1. **GIS Heatmap Dashboard (`/dashboard`):**
   - Implemented in vanilla HTML/JS with Leaflet (`1.9.4`) and Leaflet.heat (`0.2.0`).
   - Renders 40 DBSCAN spatial clusters (`/gis/hotspots`), 2,000 recent complaints (`/gis/events`), and district-aggregated risk heatmaps (`/gis/risk-heatmap`).
   - Feature Gap: Does **not** query `GET /gis/predicted-locations`.
2. **Authorized Analyst Workspace (`/analyst`):**
   - Implemented across 4 views (`index.html`, `investigation.html`, `alerts.html`, `audit.html`).
   - Enforces Bearer JWT authentication, allows case docketing, evidence logging, note creation, intelligence brief generation, and ground truth outcome capture.
3. **Institutional Banking Portal (`/bank`):**
   - Role-scoped portal for `BANK_ANALYST` users filtering alerts within proximity (1.0 to 10.0 km) of 3,000 physical ATMs.

### 2.3 Machine Learning Pipeline
- **Classifier:** XGBoost (`XGBClassifier`) wrapped in a scikit-learn `Pipeline` with `ColumnTransformer` (median imputation for 52 numerical features, One-Hot Encoding for 12 categorical features).
- **Target Variable:** Binary classification: `future_withdrawal \in {0, 1}` indicating whether a complaint leads to a qualifying cashout event within 24 hours at an ATM within 10 km or in the same district.
- **Critical Architectural Reality:** The ML model is a **binary propensity classifier**, **not** a coordinate regression or spatial grid forecasting model. Location forecasting is handled by joining high-risk complaints to unsupervised DBSCAN clusters (`src/hotspot_detection.py`) and nearest ATMs via Haversine distance.
- **Empirical Performance on Holdout Test Set (`outputs/phase8_final_test_metrics.csv`):**
  - Accuracy: `0.8693` (driven by 89.6% class imbalance)
  - Precision: `0.0638` (6.38%)
  - Recall: `0.0194` (1.94%)
  - F1-Score: `0.0297`
  - ROC-AUC: `0.4760` (below 0.50 random chance)
  - PR-AUC: `0.1029` (baseline prevalence: `0.1033`)

### 2.4 Database & Persistence Layer
- **PostgreSQL / PostGIS Readiness:** SQLAlchemy models (`database/models.py`, `database/investigation_models.py`) define full relational schemas with PostGIS geometry columns and GIST spatial indexes.
- **Host Operational Status:** PostgreSQL is currently **offline / disconnected** on the host environment (`localhost:5432` unreachable).
- **Fallback Mechanism:** The system executes in `CSV_FALLBACK_DEV` mode:
  - GIS data is read from `outputs/phase14_*.csv` and `outputs/phase9_*.csv`.
  - Alerts are persisted to `outputs/phase16_demo_alerts.csv`.
  - Analyst audit trail is persisted to `outputs/phase17_analyst_audit_log.csv`.
  - Outcome feedback is persisted to `outputs/phase21_outcome_feedback.csv`.

### 2.5 Explainability Subsystem (SHAP)
- **Engine:** `shap.TreeExplainer` on the frozen XGBoost classifier.
- **API Endpoint:** `POST /explain` dynamically calculates real, record-specific Shapley values for the provided input features in ~77ms without background sampling approximations.
- **Analyst Integration:** In `api/analyst_routes.py`, `_build_investigation_explanation()` attempts to resolve the feature record from `outputs/feature_engineered_cybercrime_data.csv` or demo cases and executes `explain_prediction()`, falling back to global SHAP ranking if unresolved.

### 2.6 Alert Generation & Notification Dispatch
- **Engine:** `src/alert_engine.py` evaluates complaint risk scores against configurable thresholds (`alert_config.json`).
- **Tiers:** `CRITICAL` (score ≥ 80), `HIGH` (60–79), `MODERATE` (40–59), `LOW` (0–39).
- **Deduplication:** Enforces a 60-minute spatial-temporal cooldown per area/hotspot to prevent alert flooding.
- **Dispatch:** Simulated multi-channel dispatcher (`notifications/dispatcher.py`) logs dispatches to `outputs/notification_log.csv`.

---

## 3. Actually Implemented vs. Planned Feature Matrix

| Subsystem | Feature | Implementation Status | Evidence / File Path | Limitations / Deviations |
|---|---|:---:|---|---|
| **Data Cleaning** | 16-step cleaning & PII masking | ✅ IMPLEMENTED | `src/data_cleaning.py` | Standalone batch script; not executed dynamically on raw API complaint submission. |
| **Transaction Flow** | Intermediate fund flow modeling | ⚠️ PARTIAL | `src/mule_pattern_detection.py` | Lightweight fan-in heuristic; not a Graph Neural Network (GNN); features not joined into ML model. |
| **Feature Engineering** | 64 Spatio-temporal features | ✅ IMPLEMENTED | `src/feature_engineering.py` | Derived entirely from `Fraud_Cases.csv`. Account profiles (`Accounts.csv`) and transaction hops (`Transactions.csv`) are unused. |
| **ML Inference** | XGBoost cashout prediction | ✅ IMPLEMENTED | `src/predict.py`, `models/xgboost_cybercrime_model.pkl` | Binary classifier for cashout propensity; does not directly predict $(x,y)$ coordinates. |
| **Location Forecast** | Direct coordinate ML prediction | ❌ NOT IMPLEMENTED | — | Model does not output coordinates; spatial localization is decoupled via DBSCAN centroids and ATM radius matching. |
| **Time-Window** | Dynamic time-to-event forecast | ⚠️ PARTIAL | `src/evaluate_temporal_forecasting.py` | Fixed 24-hour target window ($T_0 \le T_w \le T_0+24\text{h}$); not a continuous survival or hazard model. |
| **Risk Scoring** | Calibrated risk score (0–100) | ✅ IMPLEMENTED | `src/predict.py:probability_to_risk_score` | Deterministic linear mapping from calibrated probability. |
| **GIS Map** | Heatmap & Hotspot Leaflet map | ✅ IMPLEMENTED | `dashboard/js/map.js`, `api/gis_routes.py` | Displays DBSCAN clusters and event heatmaps. Does **not** render `GET /gis/predicted-locations`. |
| **ATM Proximity** | Spatial join to 3,000 physical ATMs | ✅ IMPLEMENTED | `api/gis_routes.py`, `api/bank_routes.py` | Vectorized Haversine distance matrix against `ATMs_Locations.csv`. |
| **SHAP Attribution** | Local TreeExplainer attribution | ✅ IMPLEMENTED | `src/predict.py:explain_prediction`, `POST /explain` | Exact additive local attribution computed in polynomial time. |
| **Alert Engine** | Threshold evaluation & dedup | ✅ IMPLEMENTED | `src/alert_engine.py`, `api/alert_routes.py` | Enforces 60-min cooldown and severity categorization. |
| **Analyst Portal** | Docketing, Briefs & Evidence | ✅ IMPLEMENTED | `api/analyst_routes.py`, `analyst/investigation.html` | Exportable dossier synthesizing SHAP, ATM proximity, and timeline. |
| **Outcome Feedback** | Ground truth outcome recording | ✅ IMPLEMENTED | `database/investigation_crud.py:record_outcome_feedback` | Captures prevented loss and precision calibration; persisted to CSV. |
| **PostgreSQL / PostGIS** | Spatial database persistence | ⚠️ PARTIAL | `database/models.py`, `database/connection.py` | Schema and queries fully implemented, but PostgreSQL service is offline; operates in fallback mode. |
| **Automated Tests** | 342 test regression suite | ✅ IMPLEMENTED | `tests/` (341 passed, 1 skipped) | Comprehensive unit and integration test coverage. |
