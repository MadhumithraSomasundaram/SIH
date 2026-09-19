# Phase 13 Initial Project Inspection & Pre-Flight Audit

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** September 19, 2026  
**Auditor:** Senior Software Integration Engineer & SIH Project Auditor  
**Operating Storage Mode:** `CSV_FALLBACK_DEV` (PostgreSQL offline)  
**Git Checkpoint:** Initialized on branch `master` (Commit: `Checkpoint before Phase 13 integration testing`)

---

## 1. Executive Summary
This document records the pre-flight structural inspection and environment audit of the Cybercrime Predictive Analytics Framework prior to conducting Phase 13 end-to-end integration and demonstration testing. The framework is an operational intelligence decision-support platform designed to forecast probable physical cash withdrawal corridors from incoming cybercrime complaints within a 24-hour observation window.

The baseline audit confirms that all core modules—FastAPI application, XGBoost inference pipeline, SHAP explainability service, DBSCAN spatial clustering, alert management engine, LEA investigation workspace, and banking interface—are present and synthetically operational in `CSV_FALLBACK_DEV` mode.

---

## 2. Complete Project Inventory & Architecture

```
d:/SIH/SIH_2026/cybercrime_prediction/
├── api/                           # REST API layer (FastAPI)
│   ├── main.py                    # Core application entry point, lifecycle & prediction endpoints
│   ├── auth.py                    # Lightweight API key & JWT authentication guard
│   ├── dependencies.py            # Singleton AppState (model & preprocessor cache)
│   ├── schemas.py                 # Pydantic request/response data contracts
│   ├── error_handlers.py          # Uniform error handlers masking stack traces
│   ├── alert_routes.py            # Alert lifecycle management (/alerts)
│   ├── analyst_routes.py          # LEA analyst interface, auth, investigations (/analyst)
│   ├── bank_routes.py             # Read-only banking portal (/bank)
│   ├── complaint_routes.py        # Dynamic complaint ingestion & feature generation (/complaints)
│   └── gis_routes.py              # Spatial endpoints, corridors, hotspots (/gis)
├── src/                           # Business logic, inference & feature services
│   ├── predict.py                 # Model loading, single/batch prediction, risk scoring
│   ├── explain_with_shap.py       # SHAP TreeExplainer local attribution
│   ├── hotspot_detection.py       # DBSCAN spatial clustering & centroid extraction
│   ├── spatial_cashout_service.py # Spatial corridor prediction & ATM association
│   ├── complaint_feature_service.py # Dynamic 64-feature extraction from raw complaint
│   ├── alert_engine.py            # Risk rule evaluation, cooldown & deduplication
│   └── system_smoke_test.py       # 10-step pre-flight verification script
├── database/                      # Data persistence layer
│   ├── connection.py              # SQLAlchemy engine, session maker & health probe
│   ├── models.py                  # Core database tables (PostGIS geometry enabled)
│   ├── schemas.py                 # Pydantic ORM schemas
│   ├── crud.py                    # Database operations with CSV fallback
│   ├── investigation_models.py    # Tables: analyst_users, investigations, notes, evidence, audit
│   └── investigation_crud.py      # Investigation CRUD with persistent CSV mirror
├── dashboard/                     # Web dashboard frontend (HTML/CSS/JS)
│   ├── index.html                 # Leaflet GIS dashboard
│   └── js/                        # Leaflet map layers, filters, alerts, charts, auth interceptor
├── analyst/                       # LEA Analyst portal
│   ├── index.html                 # Analyst login & KPI overview
│   ├── alerts.html                # Alert triage queue
│   ├── investigation.html         # Investigation detail, notes, evidence, SHAP brief
│   ├── audit.html                 # Immutable audit trail table
│   └── js/                        # SessionStorage auth, HTTP client, DOM renderers
├── bank/                          # Financial institution portal
│   ├── index.html                 # Bank ATM network view
│   └── js/bank.js                 # ATM-scoped proximity alerts (read-only)
├── data/                          # Datasets & backups
│   ├── raw/                       # Original synthetic datasets (Fraud_Cases, ATMs, etc.)
│   ├── processed/                 # Cleaned datasets, train/val/test splits
│   ├── demo/                      # Demonstration test input records
│   └── backup_csv/                # Atomic SHA-256 verified backup directory
├── models/                        # Serialized ML artifacts
│   ├── xgboost_cybercrime_model.pkl # Trained sklearn Pipeline (preprocessor + XGBClassifier)
│   └── phase7_xgboost_metadata.json # Feature schema, hyperparameters, training timestamp
├── outputs/                       # Generated audit reports, evaluation metrics, logs
├── scripts/                       # Operational batch scripts
│   ├── run_demo.bat               # 1-click demonstration launcher
│   ├── run_tests.bat              # Test suite executor
│   ├── backup_csv_data.py         # CSV atomic backup & hash manifest tool
│   └── reconcile_and_audit_migration.py # Synthetic data reconciliation engine
└── tests/                         # Comprehensive pytest test suite (30 test modules)
```

---

## 3. Existing Modules & Functionality Status

| Module | Purpose | Status | Storage / Fallback Behavior |
| :--- | :--- | :---: | :--- |
| **Model Inference Engine** | XGBoost classification on 64 predictor features | **OPERATIONAL** | In-memory singleton via `AppState`; loads at startup. |
| **Explainable AI (SHAP)** | Local TreeExplainer attribution per record | **OPERATIONAL** | Computed on-the-fly; falls back to precomputed global ranking if tree explainer fails. |
| **Spatial Corridors (GIS)** | Predicted cashout corridors and 5 km ATM proximity | **OPERATIONAL** | In-memory KD-Tree / Haversine filtering using `phase14_withdrawal_hotspots.csv`. |
| **Dynamic Complaint API** | Converts raw complaint payload to 64 model features | **OPERATIONAL** | Stores submitted complaints in local registry and fallback CSV. |
| **Alert Management** | Evaluates HIGH/CRITICAL thresholds, cooldown & deduplication | **OPERATIONAL** | `database.crud._LOCAL_ALERTS_CACHE` backed by `outputs/phase16_demo_alerts.csv`. |
| **LEA Investigation Portal** | Case lifecycle, timestamped notes, evidence metadata, timeline | **OPERATIONAL** | Dual-write: SQLAlchemy ORM if DB available; persistent CSV `outputs/phase17_analyst_audit_log.csv`. |
| **Bank Portal** | Read-only scoped ATM proximity alerts | **OPERATIONAL** | Read-only Haversine distance matrix between bank ATMs and hotspot centroids. |
| **Audit Logging** | Immutable tracking of logins, alerts, predictions, case updates | **OPERATIONAL** | Appended to `outputs/phase17_analyst_audit_log.csv` with file locking. |

---

## 4. Current Storage Mode
- **Active Mode:** `CSV_FALLBACK_DEV`
- **Host Audit:** Port 5432 is closed; local PostgreSQL service is offline.
- **Reporting Integrity:** `GET /database/health` properly reports status `disconnected` (HTTP 503) and surfaces `storage_mode: "CSV_FALLBACK_DEV"` without crashing or halting other endpoints.
- **Data Integrity:** All 9 core synthetic CSV datasets are verified with SHA-256 hashes in `outputs/phase11_csv_backup_manifest.json`.

---

## 5. Existing Test Commands
The repository includes automated validation runners:
```powershell
# 1. 10-Step Pre-Flight System Smoke Test (Execution time: ~1.9s):
python src/system_smoke_test.py

# 2. Pytest Unit, Integration, Auth, GIS, and Database Fallback Suites:
pytest tests/ -v -m "not live_db"

# 3. Dedicated Phase Test Suites:
pytest tests/test_authorization.py -v
pytest tests/test_bank_interface.py -v
pytest tests/test_audit_persistence.py -v
pytest tests/test_complaints_api.py -v
pytest tests/test_phase10_model_evaluation.py -v
pytest tests/test_phase11_database_integration.py -v
```

---

## 6. Required Environment Variables

| Variable | Default (Fallback) | Description | Production Requirement |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | None (`sqlite:///...` or fallback) | PostgreSQL connection string | Must point to PostgreSQL with PostGIS extension. |
| `ANALYST_JWT_SECRET` | `prototype-dev-secret-NOT-for-production-...` | Signing secret for HS256 JWT tokens | Must be overridden with cryptographically secure 64+ character key. |
| `DASHBOARD_API_KEY` | `sih26184-dashboard-prototype-key-2026` | Static prototype header guard for public dashboard | Custom high-entropy key or mutual TLS in production. |
| `ANALYST_TOKEN_EXPIRE_MINUTES` | `480` (8 hours) | Token validity window | Standard operational shift duration (8 hours). |
| `DISABLE_API_KEY_AUTH` | `false` | Development bypass flag | Must strictly remain `false` in staging/production. |
| `ENABLE_PREDICTION_STORAGE`| `true` | Persist inference results to database | Supported in PostgreSQL and fallback modes. |

---

## 7. Known Issues & Deployment Risks

1. **Host PostgreSQL Offline:** Because PostgreSQL is not running as a local host service, all operations currently execute in `CSV_FALLBACK_DEV`. While 100% of endpoints function cleanly, scale testing beyond synthetic sizes requires spinning up a PostGIS container.
2. **Temporal Drift from Cumulative Features:** Audited in Phase 10, the legacy XGBoost model incorporates unbounded cumulative counters (`previous_event_count`, `location_total_previous_events`) that degrade holdout test recall (1.94%). This is a documented analytical finding that must be clearly communicated to judges.
3. **Prototype Authentication Scope:** User accounts (`demo_analyst`, `demo_supervisor`, `demo_admin`, `demo_bank`) are prototype credentials intended for hackathon demonstration. Production deployment requires integration with official government single sign-on (SSO) and CCTNS identity providers.
4. **Non-Causal Analytical Signal:** The framework estimates spatial cashout corridors based on empirical withdrawal patterns and nearby ATMs. It does not predict individual criminal identities or guarantee exact future cashouts.
