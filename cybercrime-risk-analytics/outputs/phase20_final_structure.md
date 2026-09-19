# Phase 20: Comprehensive System Directory Architecture
## Complete Inventory of the Cybercrime Predictive Analytics Framework
### Problem Statement ID: 26184 — SIH Final Verification

This document provides an exhaustive structural map of the complete repository, detailing directory roles, primary components, architectural boundaries, and phase lineages from Phase 1 through Phase 20.

---

### High-Level Architecture Overview

```
cybercrime_prediction/
├── analyst/                  # Phase 17: Authorized Analyst Interface & Investigation Modules
├── api/                      # Phase 12 & 16: FastAPI Application, Routers & Schemas
├── config/                   # Configuration Settings, Logging & Environment Variables
├── dashboard/                # Phase 15: GIS Dashboard Static Assets (HTML, CSS, JS)
├── data/                     # Phase 1-5: Processed, Synthetic & Demo Data Partitions
├── database/                 # Phase 13 & 17: SQLAlchemy ORM Models, Sessions & Migrations
├── models/                   # Phase 7 & 8: Frozen XGBoost Classifier & Model Metadata
├── notebooks/                # Exploratory Data Analysis & Analytical Prototyping
├── notifications/            # Phase 16: Alert Dispatcher & Multi-Channel Notification Engine
├── outputs/                  # Verification Reports, Visualizations, Metrics & Defense Dossiers
├── scripts/                  # Utility Scripts, Batch Launchers & Demonstration Tools
├── sql/                      # Phase 13: PostgreSQL / PostGIS DDL Schemas & Spatial Queries
├── src/                      # Core Data Pipelines, Feature Engineering, Training & Spatial Clustering
├── tests/                    # Comprehensive Pytest Validation Suite (Unit, Integration, Auth)
├── README.md                 # Primary Project Documentation & SIH Presentation Guide
└── requirements.txt          # Python Dependencies & Pinned Production Versions
```

---

### Exhaustive Directory Breakdown

#### 1. `analyst/` (Phase 17 — Authorized Analyst Interface)
- **Role:** Implements the stateful case management and analyst workflow modules for credentialed cyber cell investigators.
- **Key Modules:**
  - `investigation_service.py`: Business logic for case assignment, transition validation (`NEW` $\to$ `UNDER_INVESTIGATION` $\to$ `ACTION_TAKEN` / `DISMISSED`), note addition, and SHA-256 evidence attachment.
  - `case_management.py`: Case search, filtering by risk tier, pagination, and multi-parameter query processing.
  - `dossier_generator.py`: Generates court-admissible PDF/JSON intelligence briefings with embedded SHAP explanations and Section 65B/63 cryptographic verification headers.

#### 2. `api/` (Phase 12, 16 & 17 — REST Application Core)
- **Role:** High-performance asynchronous REST API powered by FastAPI and Uvicorn.
- **Key Modules:**
  - `main.py` / `app.py`: FastAPI application entry point, CORS middleware, exception handlers, and router registration.
  - `auth.py`: Role-Based Access Control (RBAC) supporting Analyst, Supervisor, and Auditor roles with JWT token validation.
  - `routers/`:
    - `prediction_router.py`: Handles `/api/v1/predict` and `/api/v1/explain` endpoints.
    - `alert_router.py`: Handles `/api/v1/alerts`, filtering, and priority queues.
    - `analyst_router.py`: Handles `/api/v1/investigations/*` case transitions and note logging.
    - `gis_router.py`: Exposes DBSCAN hotspot polygons and GeoJSON spatial feeds.
  - `schemas.py`: Pydantic v2 data models for input validation, risk scoring responses, and audit entries.

#### 3. `config/` (System Configuration)
- **Role:** Centralized configuration management, environment variables, and logging configurations.
- **Key Modules:**
  - `settings.py`: Pydantic BaseSettings loading `.env` variables with safe local defaults.
  - `logging_config.py`: Structured JSON logging configuration for audit trails and security monitoring.

#### 4. `dashboard/` (Phase 15 — Interactive GIS Dashboard)
- **Role:** Lightweight, high-performance browser interface for spatial situational awareness.
- **Key Files:**
  - `index.html`: Dashboard layout containing Leaflet map canvas, alert queue panel, SHAP breakdown modal, and case notes drawer.
  - `css/dashboard.css`: Dark-mode tactical UI styling with WCAG AA compliant contrast ratios and responsive flexbox grids.
  - `js/dashboard.js`: Client-side state management, Leaflet layer controllers, WebSocket/polling alert updates, and offline fallback handlers.

#### 5. `data/` (Data Pipelines & Demo Partitions)
- **Role:** Stores structured datasets, processed features, and pre-packaged demonstration payloads.
- **Subdirectories:**
  - `demo/`: Contains `demo_prediction_input.csv` (pre-validated cases spanning all risk tiers for zero-risk hackathon demonstration).
  - `processed/`: Train, validation, and test feature matrices used during Phases 1–8.
  - `synthetic/`: Synthetic transaction feeds preserving real-world statistical correlations without exposing victim PII.

#### 6. `database/` (Phase 13 & 17 — Persistence Layer)
- **Role:** SQLAlchemy ORM models, database engines, and session lifecycle managers.
- **Key Modules:**
  - `connection.py`: Resilient database session provider with connection pooling and graceful offline detection.
  - `investigation_models.py`: Database models for `InvestigationCase`, `InvestigationNote`, `EvidenceAttachment`, and `AuditLog`.
  - `investigation_schemas.py`: Pydantic schemas validating database transactions and API representations.

#### 7. `models/` (Phase 7 & 8 — Machine Learning Artifacts)
- **Role:** Immutable storage for pre-trained, locked ML models and metadata.
- **Key Files:**
  - `xgboost_cybercrime_model.pkl`: Serialized production XGBoost model ($n=100$, depth 4).
  - `phase7_xgboost_metadata.json`: Complete hyperparameters, feature names, training timestamps, and input schema definitions.

#### 8. `notifications/` (Phase 16 — Alerting Engine)
- **Role:** Multi-channel alerting service delivering prioritized intelligence to duty analysts.
- **Key Modules:**
  - `alert_engine.py`: Evaluates incoming risk scores against tier thresholds, deduplicates alerts, and calculates escalation intervals.
  - `dispatcher.py`: Dispatches alerts via in-app UI banners, email hooks, and police dispatch webhooks.

#### 9. `outputs/` (Validation Reports, Visualizations & Defense Dossiers)
- **Role:** Comprehensive record of all Phase 1–20 analytical deliverables, charts, metrics, and documentation.
- **Key Files:**
  - `phase20_project_defense.md`: 18 structured technical and operational defense sections.
  - `phase20_hard_questions.md`: 40 deep-dive technical questions and answers.
  - `phase20_operational_questions.md`: 18 law enforcement operational answers.
  - `phase20_what_if_questions.md`: 16 failure mode and edge-case handling analyses.
  - `phase20_why_not_defense.md`: Comprehensive justification for rejecting alternative architectures.
  - `phase20_technical_60_seconds.md`: Crisp 60-second technical flow summary.
  - `phase20_architecture_2_minutes.md`: Plain-language 2-minute system overview.
  - `phase20_model_explanation.md`: Mathematical breakdown of XGBoost and SHAP.
  - `phase20_demo_failure_recovery.md`: 14 live demo failure modes and recovery procedures.
  - `phase15_hotspots.geojson`: Spatial vector file containing pre-rendered DBSCAN clusters.
  - `phase18_system_health_report.md` & `FINAL_PROJECT_STATUS.md`: Phase 18 master audit sign-offs.

#### 10. `scripts/` (Demonstration & Operational Tooling)
- **Role:** 1-click execution scripts, automated test runners, and report generators.
- **Key Files:**
  - `run_demo.bat`: Windows batch script that performs pre-flight verification, executes smoke test, and launches API + browser dashboard.
  - `run_tests.bat`: Automated test runner executing system smoke tests and pytest suites.
  - `load_database.py`: Database initialization and seed script for PostGIS environments.

#### 11. `sql/` (Phase 13 — Database DDL & PostGIS Queries)
- **Role:** Relational database schemas and spatial indexing scripts.
- **Key Files:**
  - `schema.sql`: DDL statements defining PostgreSQL tables, foreign key constraints, and PostGIS geometry columns (`GEOMETRY(Point, 4326)`).
  - `spatial_queries.sql`: Pre-compiled PostGIS spatial queries utilizing `ST_ClusterDBSCAN` and `ST_DistanceSphere`.

#### 12. `src/` (Core Data & ML Pipelines)
- **Role:** Ground-truth implementations of data preprocessing, feature engineering, model inference, and spatial analysis.
- **Key Modules:**
  - `predict.py` / `predict_pipeline.py`: Production inference wrapper applying Platt calibration, risk tiering, and SHAP explainability.
  - `features.py`: Feature engineering pipeline computing transaction velocity, amount ratios, and temporal deltas.
  - `clustering.py`: DBSCAN spatial clustering engine with Haversine distance metric ($\varepsilon=500\text{m}, \text{MinPts}=3$).
  - `system_smoke_test.py`: Lightweight, standalone 10-step end-to-end verification script.

#### 13. `tests/` (Quality Assurance & Test Suite)
- **Role:** Comprehensive automated test suite validating system correctness.
- **Key Test Files:**
  - `test_api.py`: Tests REST endpoints, input validation, and HTTP response codes.
  - `test_authorization.py`: Validates RBAC permissions, token expiration, and role restrictions.
  - `test_alert_engine.py`: Verifies alert thresholding, tier assignment, and deduplication logic.
  - `test_analyst_api.py`: Validates case state transitions, note logging, and audit append integrity.
  - `test_gis_dashboard.py`: Verifies GeoJSON serialization and spatial cluster endpoint fidelity.
  - `test_end_to_end.py`: Comprehensive full-pipeline integration test.

---

### Integrity Affirmation
Every directory and file in this repository strictly adheres to the non-punitive, decision-support mandate of Problem Statement ID 26184. No models were retrained, no Phase 8 metrics were modified, and all components operate harmoniously under production conditions.
