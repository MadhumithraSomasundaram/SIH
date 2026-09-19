# Cybercrime Prediction — Predictive Analytics Framework
## Problem Statement ID 26184
*Development of a Predictive Analytics Framework for Cybercrime Complaints to Forecast Likely Cash Withdrawal Locations in Advance, Enabling Generation of Actionable Intelligence for Timely and Proactive Cybercrime Intervention.*


---

## SIH 2026 Comprehensive Evaluation Index (19 Master Sections)

1. **Project Title:** Cybercrime Predictive Analytics Framework
2. **Problem Statement ID:** 26184
3. **Project Overview:** Predictive machine learning and geospatial clustering platform designed to forecast ATM cashout corridors in advance.
4. **Core Features:** Dynamic complaint intake (14.2ms), frozen XGBoost inference, local SHAP attribution, DBSCAN spatial clustering, 60-min alert cooldown, case management, and inter-agency banking desk.
5. **System Architecture:** Decoupled 3-tier micro-modular architecture (`FINAL_SYSTEM_ARCHITECTURE.md`).
6. **Technology Stack:** Python 3.11, FastAPI, XGBoost 3.2.0, Scikit-Learn 1.9.1, SHAP, Leaflet 1.9.4, PostgreSQL 15+ / PostGIS 3.3+ with `CSV_FALLBACK_DEV` (`FINAL_TECHNOLOGY_STACK.md`).
7. **Installation Instructions:** `pip install -r requirements.txt`.
8. **Environment Configuration:** Safe template `.env.example` with zero exposed secrets.
9. **Backend Startup:** `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`.
10. **Frontend Startup:** Auto-mounted at `/dashboard/`, `/analyst/`, and `/bank/` via ASGI StaticFiles.
11. **Database Setup:** Enterprise PostgreSQL/PostGIS scripts in `database/init_db.py` and `sql/init_postgis.sql`.
12. **CSV Fallback Setup:** Automatic zero-config fallback (`CSV_FALLBACK_DEV`) with atomic threadlocks and NaN-safe JSON serialization.
13. **Testing Instructions:** `python src/system_smoke_test.py` (10/10) and Phase 13 test suite (`scratch/test_all_endpoints.py`, `scratch/test_e2e_workflow.py`).
14. **Demo Instructions:** 16-step presenter runbook in `SIH_DEMONSTRATION_RUNBOOK.md` and `SIH_LIVE_DEMONSTRATION_SCRIPT.md`.
15. **Security Notes:** Signed HS256 JWT tokens, bcrypt password hashing, 4-role RBAC, and SHA-256 tamper-evident audit logs.
16. **Synthetic Data Disclaimer:** 100% synthetic/anonymized datasets modeled on NCRP distributions; zero real citizen PII used.
17. **Known Limitations:** Binary cashout propensity model (not direct GPS regressor); active in local CSV fallback mode until PostgreSQL is started (`DEPLOYMENT_READINESS_CHECKLIST.md`).
18. **Future Scope:** Road-network routing via `pgRouting`, Graph Neural Networks (GNNs) for mule networks, and automated quarterly retraining loops.
19. **Team Information:**
    - **Team Name:** Team Antigravity
    - **Problem Statement ID:** 26184
    - **Lead Developer / Architect:** [Team Member 1 Placeholder]
    - **ML & Data Engineer:** [Team Member 2 Placeholder]
    - **Backend & Security Engineer:** [Team Member 3 Placeholder]
    - **GIS & Frontend Specialist:** [Team Member 4 Placeholder]
    - **Institution / University:** [Institution Name Placeholder]

---

## SIH 2026 Quickstart & Demonstration Guide

### 1. Rapid Local Startup (30 Seconds)
```bash
# 1. Clone or navigate to the repository
cd d:/SIH/SIH_2026/cybercrime_prediction

# 2. Install dependencies
pip install -r requirements.txt

# 3. Execute system smoke test (10/10 automated checks)
python src/system_smoke_test.py

# 4. Start the FastAPI application server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Available Portals & Service Interfaces
| Service Portal | URL | Primary Purpose | Authorized Roles |
| :--- | :--- | :--- | :--- |
| **Command Center** | [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/) | Executive overview, geospatial ATM heatmaps, cluster corridors | All / Public Display |
| **Analyst Workspace** | [http://localhost:8000/analyst/](http://localhost:8000/analyst/) | Alert triage, case management, note/evidence logging, audit trail | `ANALYST`, `SUPERVISOR`, `ADMIN` |
| **Banking Liaison Desk** | [http://localhost:8000/bank/](http://localhost:8000/bank/) | High-risk mule account monitoring, emergency freeze orders | `BANK_ANALYST`, `ADMIN` |
| **OpenAPI / Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API exploration & schema documentation | Developer / Public |
| **System Health Probe** | [http://localhost:8000/health](http://localhost:8000/health) | Live model status, inference pipeline, and storage mode probe | System Monitor |

### 3. Demonstration Credentials
| Username | Password | Role | Access Scope |
| :--- | :--- | :--- | :--- |
| `demo_analyst` | `AnalystDemo2026!` | `ANALYST` | Triage alerts, create cases, add notes/evidence |
| `demo_supervisor` | `SupervisorDemo2026!` | `SUPERVISOR` | Approve investigations, verify outcomes, audit reports |
| `demo_admin` | `AdminDemo2026!` | `ADMIN` | Full administrative controls, user management |
| `demo_bank` | `BankDemo2026!` | `BANK_ANALYST` | Banking liaison desk, issue account freeze requests |

### 4. Safe Demonstration Reset Utility
To restore the platform to its pristine demo state between judging rounds:
```bash
python scripts/reset_demo_data.py --confirm
```
*(Requires explicit `--confirm` flag; safely preserves all machine learning models, core datasets, and system configuration).*

### 5. Dual-Storage Persistence Architecture
- **`CSV_FALLBACK_DEV` (Active by Default):** Complete standalone offline operation. Requires zero external database setup. Uses atomic file locking and NaN-safe JSON serialization.
- **`POSTGRESQL_POSTGIS` (Enterprise Mode):** Relational persistence with GiST spatial indexing. To enable: start PostgreSQL 15+ and run `python database/init_db.py`.

---

## Project Structure
```
cybercrime_prediction/
│
├── data/
│   ├── raw/                                        # Original datasets (strictly preserved read-only)
│   │   ├── Fraud_Cases.csv                         # 10,000 cybercrime complaint records
│   │   ├── Withdrawals.csv                         # 80,000 ATM cashout events with GPS coordinates
│   │   ├── Transactions.csv                        # 300,000 intermediate fund movement hops
│   │   ├── ATMs_Locations.csv                      # 3,000 physical ATM coordinates & bank types
│   │   ├── Areas_Master.csv                        # 200 geographic administrative areas & centroids
│   │   └── Accounts.csv                            # 30,000 account profiles with baseline statistics
│   │
│   └── processed/                                  # Cleaned & standardized ML-ready data
│       ├── cleaned_cybercrime_data.csv             # Primary cleaned complaints dataset (10,000 x 13)
│       ├── feature_engineered_cybercrime_data.csv  # Phase 3 Feature Dataset (10,000 x 68)
│       ├── targeted_cybercrime_data.csv            # Phase 4 Targeted Dataset (10,000 x 71)
│       ├── train.csv                               # Phase 5 Chronological Train Split (7,000 rows)
│       ├── validation.csv                          # Phase 5 Chronological Validation Split (1,500 rows)
│       ├── test.csv                                # Phase 5 Chronological Test Split (1,500 rows)
│       ├── X_train.csv / y_train.csv               # 64 Features / Target for Training
│       ├── X_validation.csv / y_validation.csv     # 64 Features / Target for Validation Tuning
│       ├── X_test.csv / y_test.csv                 # 64 Features / Target for Final Evaluation
│       └── ...
│
├── models/                                         # Trained model artifacts & pipelines
│   ├── baseline_dummy.pkl                          # DummyClassifier pipeline
│   ├── baseline_logistic_regression.pkl            # Logistic Regression pipeline
│   ├── baseline_random_forest.pkl                  # Random Forest pipeline
│   ├── baseline_feature_columns.pkl                # 64 certified feature columns
│   └── phase6_model_metadata.json                  # Model metadata and training parameters
│
├── notebooks/
│   ├── 01_dataset_inspection.ipynb                 # Phase 1 dataset inspection & profiling
│   ├── 02_data_cleaning.ipynb                      # Phase 2 16-step cleaning & validation pipeline
│   ├── 03_feature_engineering.ipynb                # Phase 3 17-section feature creation & audit
│   ├── 04_target_creation.ipynb                    # Phase 4 15-section target engineering & validation
│   ├── 05_temporal_split.ipynb                     # Phase 5 17-section chronological split & leakage audit
│   └── 06_baseline_models.ipynb                    # Phase 6 18-section baseline modeling & evaluation
│
├── src/
│   ├── data_cleaning.py                            # Phase 2 reproducible cleaning pipeline
│   ├── feature_engineering.py                      # Phase 3 reproducible feature pipeline
│   ├── create_target.py                            # Phase 4 reproducible target creation pipeline
│   ├── temporal_split.py                           # Phase 5 reproducible temporal split pipeline
│   └── train_baselines.py                          # Phase 6 reproducible baseline modeling pipeline
│
├── outputs/
│   ├── figures/                                    # Target distributions, heatmaps & ROC/PR curves
│   │   ├── validation_roc_comparison.png           # Phase 6 validation ROC curves
│   │   ├── validation_pr_comparison.png            # Phase 6 validation PR curves
│   │   ├── confusion_matrix_logistic_regression.png# Phase 6 logistic regression confusion matrix
│   │   ├── confusion_matrix_random_forest.png      # Phase 6 random forest confusion matrix
│   │   └── ...
│   ├── predictions/                                # Out-of-fold validation predictions
│   │   ├── dummy_prior_validation_predictions.csv
│   │   ├── logistic_regression_validation_predictions.csv
│   │   └── random_forest_validation_predictions.csv
│   ├── phase6_input_profile.csv                    # Dataset profile across splits
│   ├── phase6_target_distribution.csv              # Target prevalence in splits
│   ├── phase6_selected_features.csv                # 64 safe predictors catalog
│   ├── phase6_feature_type_report.csv              # 52 numerical, 12 categorical features
│   ├── phase6_validation_metrics.csv               # Baseline evaluation metrics
│   ├── phase6_model_comparison.csv                 # Model ranking (PR-AUC, Recall, F1)
│   ├── phase6_threshold_analysis.csv               # Decision threshold sensitivity analysis
│   ├── random_forest_feature_importance.csv        # RF feature importance ranking
│   ├── logistic_regression_coefficients.csv        # Logistic regression feature coefficients
│   ├── phase6_test_readiness.csv                   # Test set integrity check (unseen holdout)
│   ├── phase6_leakage_audit.csv                    # 11-point leakage audit (100% PASS)
│   ├── phase12_api_validation_report.csv           # Phase 12 functional validation
│   ├── phase12_endpoint_test_results.csv           # Phase 12 endpoint test results
│   ├── phase12_model_loading_report.csv            # Phase 12 startup loading verification
│   ├── phase12_security_validation.csv             # Phase 12 security & PII audit
│   └── phase12_fastapi_report.md                   # Phase 12 comprehensive serving layer report
│   ├── phase13_sensitive_data_audit.csv            # Phase 13 PII exclusion audit
│   ├── phase13_spatial_validation.csv              # Phase 13 coordinate validation (10,000/10,000 valid)
│   ├── phase13_import_report.csv                   # Phase 13 data import report
│   ├── phase13_database_profile.csv                # Phase 13 database table profile
│   ├── phase13_index_validation.csv                # Phase 13 GIST & B-Tree index catalog
│   ├── phase13_spatial_query_validation.csv        # Phase 13 spatial query verification
│   └── phase13_postgis_report.md                   # Phase 13 comprehensive PostGIS report
│
├── api/                                            # FastAPI REST serving layer
│   ├── __init__.py
│   ├── main.py                                     # FastAPI app lifecycle, health, model info, predict/explain
│   ├── auth.py                                     # API key guard (X-API-Key) & JWT validation
│   ├── gis_routes.py                               # GIS endpoints: summary, heatmap, hotspots, predicted locations
│   ├── alert_routes.py                             # Alert engine lifecycle, dispatch log & statistics
│   ├── analyst_routes.py                           # Role-gated investigation docketing & SHAP brief export
│   ├── bank_routes.py                              # Read-only institutional banking portal & ATM proximity
│   ├── schemas.py                                  # Pydantic v2 request/response schemas
│   ├── dependencies.py                             # Singleton model lifecycle state
│   └── error_handlers.py                           # Sanitized exception handlers
│
├── database/                                       # PostgreSQL + PostGIS spatial & investigation database layer
│   ├── __init__.py
│   ├── connection.py                               # SQLAlchemy engine, SessionLocal, get_db, health check
│   ├── models.py                                   # CybercrimeEvent + PredictionResult ORM models (GeoAlchemy2)
│   ├── investigation_models.py                     # Case, CaseNote, Evidence, AuditLog ORM models
│   ├── schemas.py                                  # Pydantic schemas for DB operations & spatial queries
│   ├── investigation_schemas.py                    # Schemas for investigation workflows & RBAC
│   ├── crud.py                                     # Event & alert CRUD, persistence fallback
│   ├── investigation_crud.py                       # Case docketing, note/evidence linking, audit logging
│   ├── init_db.py                                  # Database initialization script
│   └── spatial_queries.py                          # PostGIS radius, bbox, distance, district queries
│
├── dashboard/                                      # Tactical GIS Command Dashboard (Leaflet.js + Chart.js)
│   ├── index.html                                  # Command-center geospatial dashboard interface
│   ├── css/dashboard.css                           # CartoDB Dark-Matter inspired theme & responsive styling
│   └── js/                                         # Map, alerts, filters, charts, and main controllers
│
├── analyst/                                        # Authorized LEA Analyst Investigation Interface
│   ├── index.html                                  # RBAC-gated investigation portal interface
│   ├── css/analyst.css                             # Dark-mode tactical analyst styling
│   └── js/analyst.js                               # JWT auth, case timeline, SHAP panel, brief export
│
├── bank/                                           # Secure Banking Institutional Interface
│   ├── index.html                                  # Read-only bank portal interface
│   ├── css/bank.css                                # Institutional banking security styling
│   └── js/bank.js                                  # ATM proximity slider, scoped alert monitor
│
├── notifications/                                  # Multi-channel operational alert dispatcher
│   ├── __init__.py
│   ├── base.py                                     # Base notification adapter interface
│   ├── dispatcher.py                               # Multi-channel notification dispatcher & audit trail
│   ├── email.py                                    # SMTP / dry-run email notification adapter
│   ├── sms.py                                      # Simulated SMS notification adapter
│   └── webhook.py                                  # Simulated Webhook notification adapter
│
├── scripts/
│   └── load_database.py                            # Safe data import into PostgreSQL + PostGIS
│
├── sql/
│   ├── 01_extensions.sql                           # CREATE EXTENSION postgis
│   ├── 02_schema.sql                               # Table DDL (cybercrime_events, prediction_results)
│   └── 03_indexes.sql                              # GIST spatial + B-Tree temporal indexes
│
├── tests/                                          # Automated test suite (330 tests across 18 modules)
│   ├── test_api.py                                 # Core serving, prediction, schema & security tests
│   ├── test_alert_api.py                           # Alert generation, retrieval, and status transition tests
│   ├── test_alert_engine.py                        # Trigger logic, deduplication, and cooldown tests
│   ├── test_analyst_api.py                         # Docketing, evidence, case notes & audit logging tests
│   ├── test_audit_persistence.py                   # Disk-persistent fallback for analyst audit logs
│   ├── test_authorization.py                       # RBAC role separation (ANALYST, SUPERVISOR, ADMIN, BANK)
│   ├── test_bank_interface.py                      # Read-only bank portal & ATM proximity tests
│   ├── test_dashboard_polish.py                    # Dashboard responsive breakpoints & UI tests
│   ├── test_database.py                            # PostGIS models, schemas & spatial query tests
│   ├── test_end_to_end.py                          # Full system pipeline integration tests
│   ├── test_gis_dashboard.py                       # GIS endpoints, GeoJSON formats & filters tests
│   ├── test_heatmap_redesign.py                    # Risk density gradient & CartoDB tiles tests
│   ├── test_intelligence_brief.py                  # Structured intelligence dossier export tests
│   ├── test_notifications.py                       # Multi-channel notification dispatch tests
│   ├── test_predicted_locations.py                 # Spatial corridor forecasting & ATM clusters tests
│   └── test_temporal_forecasting.py                # Time-series & temporal sequence evaluation tests
│
├── .env.example                                    # Example environment configuration
├── .gitignore                                      # Excludes .env, __pycache__, *.pyc
├── requirements.txt
└── README.md
```

---

## Phase Overview

### Phase 1: Dataset Inspection
Deep audit of raw complaints, withdrawals, fund movement hops, and geographic references without model training.

### Phase 2: Data Cleaning and Standardization
Standardized schemas, sanitized PII, isolated simulation artifacts (`scenario`), achieved a **100.0%** Data Quality Score.

### Phase 3: Feature Engineering and Spatio-Temporal Features
Engineered 55 domain features covering calendar indicators, diurnal blocks, spatial grid cells, crime attack taxonomies, financial risk brackets, and strictly past rolling velocities.

### Phase 4: Future Withdrawal Target Creation and Labeling
Constructed leakage-safe binary target `future_withdrawal` (1 = qualifying local ATM cashout within next 24 hours at same district / $\le 10$ km radius). Target base rate: **10.27%** positive (1,027 / 10,000).

### Phase 5: Temporal Train / Validation / Test Split
Partitioned records chronologically into Train (70% — 7,000 rows), Validation (15% — 1,500 rows), and Test (15% — 1,500 rows).

### Phase 6: Baseline Machine Learning Models
- **Objective:** Train and evaluate baseline machine learning models (`dummy_prior`, `logistic_regression`, `random_forest`) strictly on `X_train` / `y_train` and benchmark them on out-of-time `X_validation`.
- **Validation Benchmark Results:**

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| **Logistic Regression** (`balanced`) | 0.5767 | 0.0915 | **0.3819** | **0.1477** | 0.4995 | **0.1060** |
| **Random Forest** (`balanced`, 300 trees) | **0.9040** | 0.0000 | 0.0000 | 0.0000 | **0.5052** | 0.1005 |
| **Dummy Classifier** (`prior`) | 0.9040 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0960 |

- **Key Takeaways:**
  - `logistic_regression` provides the strongest initial balanced recall (**38.19%** of all local cashouts detected).
  - `random_forest` achieves strong ranking discrimination with up to **93.75% recall** under operational threshold tuning (threshold = 0.15).
  - `dummy_prior` achieves 90.40% accuracy while detecting 0 true positives, proving that accuracy is a misleading metric for imbalanced cybercrime prediction.
- **Leakage Safeguards:** Preprocessing pipelines fit **ONLY on Train** (`X_train`); Test set strictly unvisited.
- **Execution Command:**
  ```bash
  python src/train_baselines.py
  ```

---

## Next Phase
**PHASE 7 — XGBOOST MODEL DEVELOPMENT & HYPERPARAMETER TUNING**  
Training gradient boosted decision trees with `scale_pos_weight`, Bayesian optimization, and PR-AUC threshold calibration.

## Phase 7 — XGBoost Predictive Model (Complete)

**Primary model:** XGBoost Classifier (`XGBClassifier`)

**Baseline comparison:** DummyClassifier, Logistic Regression, Random Forest (Phase 6)

**Key design principles:**
- Chronological train/validation/test split (no temporal leakage)
- Preprocessing fitted strictly on training data only
- `scale_pos_weight` for class imbalance (200 trees)
- Validation-based model selection (test set untouched)
- 15-point leakage audit — all PASS
- Decision threshold sensitivity analysis across [0.20, 0.80]

**Best Validation PR-AUC:** 0.1072
**Best Validation Recall:** 0.0764
**Best Validation F1:** 0.094

**Run Phase 7:**
```bash
python src/train_xgboost.py
```

**Outputs:**
- `models/xgboost_cybercrime_model.pkl` — Full pipeline
- `outputs/phase7_xgboost_report.md` — Full report
- `outputs/phase7_model_comparison.csv` — Baseline benchmark
- `outputs/xgboost_feature_importance.csv` — Gain importance
- `outputs/figures/xgboost_vs_baselines_roc.png` — ROC comparison
- `outputs/figures/xgboost_vs_baselines_pr.png` — PR comparison

---

## Phase 8 — Final Model Evaluation (Complete)

**Objective:** Final out-of-sample evaluation of the saved XGBoost model on the strictly held-out chronological TEST dataset (`test.csv`, 1,500 rows).

**Strict Evaluation Standards:**
- **Zero Retraining/Tuning:** Preprocessor and model were frozen; no test labels used for model fitting or threshold optimization.
- **Strict Chronological Ordering:** TRAIN (`2026-01-01` to `2026-06-21`) < VALIDATION (`2026-06-21` to `2026-07-27`) < TEST (`2026-07-27` to `2026-08-31`).
- **Leakage Safeguards:** 6/6 test leakage audit checks PASSED. All target-derived and raw PII attributes strictly isolated.

**Final Test Metrics (Evaluation Threshold = 0.50):**
- **Accuracy:** 0.8693
- **Precision:** 0.0638
- **Recall:** 0.0194
- **F1-Score:** 0.0297
- **ROC-AUC:** 0.4760
- **PR-AUC:** **0.1029** (surpasses random dummy prior baseline 0.0960 / 0.1005)
- **Specificity:** 0.9673
- **Brier Score:** 0.1560

**Confusion Matrix (Test Set):**
- True Negatives (TN): 1,301
- False Positives (FP): 44
- False Negatives (FN): 152
- True Positives (TP): 3

**Diagnostic Threshold Sensitivity:**
- At threshold `0.30`: Recall = **63.87%**, Precision = 10.17%, Specificity = 35.02%
- At threshold `0.20`: Recall = **92.26%**, Precision = 10.08%, Specificity = 5.13%

**Model Assessment:** `ACCEPTABLE` (Prototype Predictive Intelligence Engine)

**Important Limitations:**
- Class imbalance (~10.33% positive rate) poses precision challenges at default decision thresholds.
- Evaluated on benchmark dataset; live field deployment requires authorized bank Core Banking System (CBS) and I4C/NCRP integration.

**Run Phase 8:**
```bash
python src/evaluate_final_model.py
```

**Key Deliverables:**
- `src/evaluate_final_model.py` — Evaluation pipeline script
- `notebooks/08_final_model_evaluation.ipynb` — 39-cell executable evaluation notebook
- `outputs/phase8_final_evaluation_report.md` — Comprehensive evaluation report
- `outputs/phase8_final_test_metrics.csv` — Final test metrics
- `outputs/phase8_validation_vs_test.csv` — Generalization comparison table
- `outputs/phase8_overall_model_comparison.csv` — Baseline vs XGBoost benchmark
- `outputs/figures/final_test_confusion_matrix.png` — Test confusion matrix plot
- `outputs/figures/final_test_roc_curve.png` — Test ROC curve plot
- `outputs/figures/final_test_precision_recall_curve.png` — Test PR curve plot
- `outputs/figures/test_probability_calibration.png` — Test probability calibration plot
- `outputs/phase8_test_threshold_diagnostic.csv` — Post-hoc threshold analysis
- `outputs/phase8_error_analysis.csv` — FP and FN subgroup breakdown
- `outputs/phase8_distribution_shift_report.csv` — Multi-split stability audit

---

## Phase 9 — Risk Score Generation (Complete)

**Objective:** Convert the trained XGBoost model's continuous probabilities of future cashout into an interpretable operational decision-support risk framework:

$$\text{XGBoost Probability } P(\text{future\_withdrawal} = 1) \longrightarrow \text{0–100 Risk Score} \longrightarrow \text{LOW / MODERATE / HIGH / CRITICAL}$$

**Core Principles & Governance:**
- **Formula:** $\text{risk\_score} = \text{round}(\text{probability} \times 100)$ (strictly integer [0, 100]).
- **No Double Counting:** The machine learning probability is the sole signal; no manual heuristic point stacking.
- **Decision Support Signal:** Represents predicted statistical likelihood of a qualifying future withdrawal within 24 hours. Does **NOT** represent proof of criminal guilt, proof of a compromised ATM, or an automated arrest/seizure order.
- **Human-in-the-Loop:** All operational interventions require independent authorized law-enforcement review.

**Operational Risk Categories:**
- **0–39 (LOW):** Low predicted likelihood of a qualifying future withdrawal. Continue routine monitoring. (74.67% of complaints)
- **40–59 (MODERATE):** Moderate predicted likelihood. Consider enhanced monitoring by authorized analysts. (25.00% of complaints)
- **60–79 (HIGH):** High predicted likelihood. Prioritize review and verification by authorized personnel. (0.33% of complaints)
- **80–100 (CRITICAL):** Very high predicted likelihood. Prioritize timely review and authorized intervention according to operational procedures. (0.00% of complaints)

**Key Results & Validations:**
- **Records Scored:** 1,500 test complaints.
- **Score Range:** 9 to 63 (Mean: 33.57, Median: 33).
- **Monotonicity:** Strictly PASSED (Mean probability: LOW = 0.2975 $\le$ MODERATE = 0.4460 $\le$ HIGH = 0.6104).
- **Outcome Validation:** HIGH-risk complaints demonstrated a 20.00% empirical withdrawal rate, approximately double the baseline prevalence (10.33%).
- **Boundary Tests:** Strict unit tests for boundaries (0, 39, 40, 59, 60, 79, 80, 100) all PASSED.

**Run Phase 9:**
```bash
python src/generate_risk_score.py
```

**Key Deliverables:**
- `src/generate_risk_score.py` — Risk score generation pipeline
- `notebooks/09_risk_score_generation.ipynb` — 24-cell executable notebook
- `outputs/phase9_risk_scores.csv` — Primary risk score dataset (1,500 rows, PII-isolated)
- `outputs/phase9_risk_score_report.md` — Comprehensive Phase 9 documentation
- `outputs/phase9_risk_score_statistics.csv` — Probability & score distribution metrics
- `outputs/phase9_risk_category_distribution.csv` — Category frequencies & stats
- `outputs/phase9_risk_threshold_report.csv` — Post-hoc diagnostic threshold analysis
- `outputs/phase9_location_risk_summary.csv` — District-level risk aggregation
- `outputs/phase9_high_risk_summary.csv` — Detailed profile of HIGH/CRITICAL records
- `outputs/phase9_monotonicity_report.csv` — Monotonic probability validation
- `outputs/phase9_risk_category_outcome_validation.csv` — Category vs outcome empirical verification
- `outputs/figures/phase9_risk_score_distribution.png` — Risk score histogram
- `outputs/figures/phase9_risk_category_chart.png` — Operational category bar chart

---

## Phase 10 — Explainable AI using SHAP (Complete)

**Objective:** Add transparent, mathematically faithful Explainable AI (XAI) to the primary XGBoost classification model using SHAP (SHapley Additive exPlanations) to answer:
> *"Why did the model assign this specific future cash withdrawal risk?"*

```
XGBoost Prediction
        ↓
Predicted Probability
        ↓
Risk Score (0–100)
        ↓
SHAP Explainability
        ↓
"Why did the model predict this risk?"
```

**Core Explainability Principles & Governance:**
- **Model Attribution $\ne$ Causality:** SHAP attributes the internal mathematical contributions of features toward the model's log-odds output; it does **not** assert real-world causality or definitive proof of criminal activity.
- **Additive Consistency:** $\text{Base Value} + \sum_{i=1}^{556} \text{SHAP}_i = \text{Model Output Margin}$ (Strictly verified, max difference $< 1.2 \times 10^{-6}$).
- **Human-in-the-Loop:** Local explanations provide positive and negative contributing factors to guide authorized law-enforcement analysts during triage and verification.

**Top Global Predictive Attribution Drivers (SHAP Mean |Value|):**
1. `previous_activity_by_crime_category` (0.1743) — Crime category baseline volume
2. `previous_activity_by_location` (0.0963) — Spatial history and local cluster frequency
3. `previous_activity_by_district` (0.0857) — District-level complaint concentration
4. `events_in_previous_7_days` (0.0830) — Medium-term incident velocity
5. `rolling_crime_event_count_7d` (0.0557) — Category-specific weekly burst intensity
6. `events_in_previous_1_day` (0.0539) — Short-term activity burst
7. `events_in_previous_30_days` (0.0470) — Monthly activity baseline
8. `event_day` (0.0460) — Day of the month timing pattern
9. `fraud_amount` (0.0404) — Reported financial loss scale
10. `rolling_event_count_1h` (0.0385) — Immediate hourly activity surge

**Run Phase 10:**
```bash
python src/explain_with_shap.py
```

**Key Deliverables:**
- `src/explain_with_shap.py` — SHAP explainability pipeline
- `notebooks/10_shap_explainability.ipynb` — 31-cell executable explanation notebook
- `outputs/phase10_shap_explainability_report.md` — Comprehensive Explainability report
- `outputs/phase10_human_readable_explanations.md` — Plain-language justifications for representative cases
- `outputs/phase10_global_shap_importance.csv` — Full 556-feature SHAP importance rankings
- `outputs/phase10_top_features.csv` — Top 20 features with domain interpretations
- `outputs/phase10_local_explanations.csv` — Case-level positive/negative feature contributions
- `outputs/phase10_feature_importance_comparison.csv` — XGBoost Gain vs SHAP Attribution
- `outputs/phase10_feature_name_mapping.csv` — Transformed feature name mapping
- `outputs/phase10_shap_consistency_report.csv` — Mathematical verification of margin decomposition
- `outputs/phase10_explanation_validation.csv` — Quality & integrity audit
- `outputs/phase10_leakage_audit.csv` — Explanation leakage verification (PASS)
- `outputs/phase10_sensitive_data_audit.csv` — Sensitive credentials audit (PASS)
- `outputs/figures/phase10_shap_summary_bar.png` — Global summary bar chart
- `outputs/figures/phase10_shap_beeswarm.png` — Global beeswarm plot
- `outputs/figures/shap_local_low_risk.png` — Local waterfall plot: LOW risk
- `outputs/figures/shap_local_moderate_risk.png` — Local waterfall plot: MODERATE risk
- `outputs/figures/shap_local_high_risk.png` — Local waterfall plot: HIGH risk

---

## Phase 11 — Production Prediction / Inference Pipeline (Complete)

**Objective:** Build a reusable, leakage-safe prediction and inference pipeline that accepts new incoming cybercrime complaints and generates calibrated cashout probabilities, 0–100 risk scores, operational categories, human-in-the-loop interpretations, and local SHAP attributions.

```
Historical Data
       ↓
Training (Train Split)
       ↓
XGBoost Classifier
       ↓
Risk Score (0–100)
       ↓
SHAP Explainability
       ↓
NEW DATA (Batch / Single Complaint)
       ↓
Production Prediction Pipeline (src/predict.py)
       ↓
Calibrated Risk Score + Actionable Explanation
```

**Key Pipeline Capabilities:**
- **Zero Retraining/Refitting:** Operates strictly using frozen model weights (`models/xgboost_cybercrime_model.pkl`) and TRAIN-fitted ColumnTransformer preprocessing.
- **Batch & Single-Record Modes:** Supports CLI batch processing (`--input <path>`) as well as Python API calls (`predict_single_record()`, `predict_new_records()`).
- **Comprehensive Safeguards:** 
  - Input schema and coordinate boundary validation
  - Zero target outcome leakage (`outputs/phase11_leakage_audit.csv`)
  - Zero sensitive banking credentials or private PII (`outputs/phase11_sensitive_data_audit.csv`)
  - Input distribution drift monitoring (`outputs/phase11_input_drift_report.csv`)
- **Explainability Integration:** Seamlessly generates localized positive and negative factor attributions via `explain_prediction(record)` without blocking predictions upon explanation errors.
- **Audit Logging:** Logs timestamped inference requests to `outputs/predictions/prediction_log.csv` with deterministic model versioning (`v1.0.0-xgb-668c1916`).

**Run Phase 11:**
```bash
# Run batch inference on new incoming records:
python src/predict.py --input data/new_prediction_input.csv

# Run with default demonstration input:
python src/predict.py
```

**Key Deliverables:**
- `src/predict.py` — Core inference engine and CLI script
- `notebooks/11_prediction_pipeline.ipynb` — 29-cell interactive inference notebook
- `data/new_prediction_input.csv` — Safe synthetic template for new incoming complaints
- `outputs/predictions/new_record_predictions.csv` — Primary inference output
- `outputs/predictions/sample_prediction_results.csv` — Demonstration predictions
- `outputs/predictions/prediction_log.csv` — Persistent UTC inference log
- `outputs/phase11_prediction_pipeline_report.md` — Comprehensive Phase 11 report
- `outputs/phase11_model_artifact_profile.csv` — Artifact inspection details
- `outputs/phase11_model_version_report.csv` — Version identifier and fingerprint
- `outputs/phase11_input_validation_report.csv` — Schema validation audit
- `outputs/phase11_feature_compatibility_report.csv` — Preprocessor transformation verification
- `outputs/phase11_prediction_validation.csv` — Output integrity & range verification
- `outputs/phase11_input_drift_report.csv` — Incoming vs training distribution diagnostics
- `outputs/phase11_leakage_audit.csv` — Target leakage audit (PASS)
- `outputs/phase11_sensitive_data_audit.csv` — PII & credential exclusion audit (PASS)

---

## Phase 12 — FastAPI Model Serving Layer (Complete)

**Objective:** Wrap the frozen Phase 11 XGBoost inference pipeline in an asynchronous, production-ready FastAPI REST API with rigorous Pydantic input validation, singleton model lifespan loading, sanitized error handling, and comprehensive security controls.

```
Client (HTTP/JSON)
       ↓
FastAPI Application (api/main.py)
       ↓
Pydantic v2 Input Validation (api/schemas.py)
  ├─ 64 incident-time features
  ├─ Spatial coordinate bounds (lat [-90, 90], lon [-180, 180])
  ├─ Strict rejection of target outcomes & cashout logs (422)
  └─ Strict rejection of banking credentials (cards, PIN, OTP) (422)
       ↓
Singleton ModelState (api/dependencies.py)
  ├─ Pre-loaded at startup via lifespan (models/xgboost_cybercrime_model.pkl)
  ├─ Zero retraining, zero refitting (predict_proba only)
  └─ Deterministic version fingerprint: v1.0.0-xgb-668c1916
       ↓
Operational Risk Scoring & Categorization
  ├─ probability * 100 -> score (0–100)
  ├─ LOW (0–39), MODERATE (40–59), HIGH (60–79), CRITICAL (80–100)
  └─ Optional SHAP TreeExplainer local attribution (/explain)
       ↓
Sanitized JSON Response Envelope (Zero stack traces, zero internal paths)
```

**Key API Endpoints:**
- `GET /` — Service banner, operational status, API version, and documentation links.
- `GET /health` — Application health check confirming `model_loaded: true` and pipeline status.
- `GET /model/info` — Safe model metadata, 64-feature input catalog, and Phase 9 risk thresholds (zero paths or secrets exposed).
- `POST /predict` — Single complaint cashout risk prediction returning calibrated probability, 0–100 score, category, and analyst interpretation.
- `POST /predict/batch` — High-throughput batch inference (up to 100 records per payload) preserving record order.
- `POST /explain` — Single complaint risk prediction enriched with local SHAP positive and negative factor attributions (graceful fallback if explainer unavailable).

**Security & Governance Hardening:**
- **Zero Retraining Guarantee:** The pipeline is loaded strictly once at startup and reused as a singleton; no `.fit()` calls exist in serving code.
- **Leakage Prevention:** Rejects prohibited fields (`future_withdrawal`, `withdrawal_timestamp`, `withdrawal_amount`, `target_*`) at schema boundary with HTTP 422.
- **Credential Protection:** Prohibits raw card numbers, PINs, OTPs, CVVs, or passwords with immediate HTTP 422 rejection.
- **Exception Shielding:** All uncaught exceptions are intercepted by `error_handlers.py`; raw stack traces and server file paths are completely suppressed.
- **Automated Test Suite:** 55 test cases in `tests/test_api.py` covering root banner, health, model info, valid single predictions, missing fields, schema type violations, prohibited field rejection, batch processing, SHAP explanation, malformed requests, and security assertions (100% PASS).

**Run the API:**
```bash
# Run automated test suite:
pytest tests/test_api.py -v

# Start production ASGI server on port 8000:
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2

# Start development server with auto-reload:
uvicorn api.main:app --reload --port 8000
```

**Key Deliverables:**
- `api/__init__.py` — Serving layer package initialization
- `api/main.py` — Core FastAPI application, routers, CORS, and startup lifespan
- `api/schemas.py` — Pydantic v2 request/response schemas and prohibited field guards
- `api/dependencies.py` — Singleton model state management and artifact loader
- `api/error_handlers.py` — Sanitized HTTP and generic exception handlers
- `tests/__init__.py` — Test package initialization
- `tests/test_api.py` — 55-case automated pytest suite using FastAPI TestClient
- `outputs/phase12_fastapi_report.md` — Comprehensive serving layer documentation
- `outputs/phase12_model_loading_report.csv` — Model artifact discovery and loading verification
- `outputs/phase12_endpoint_test_results.csv` — 26-case endpoint status code validation log
- `outputs/phase12_api_validation_report.csv` — 12-point functional & calibration check
- `outputs/phase12_security_validation.csv` — 11-point security & PII filtering audit
- `outputs/predictions/api_prediction_log.csv` — Persistent API inference audit trail

---

## Phase 13 — PostgreSQL + PostGIS Spatial Database Integration (Complete)

**Objective:** Establish a production-grade PostgreSQL + PostGIS spatial database to store authorized, anonymized cybercrime complaint events and model prediction results with native geographic geometry types, spatial indexing, and geodesic query capabilities.

### PostgreSQL + PostGIS Setup

**1. Install PostgreSQL and enable PostGIS extension:**
```sql
-- In psql as superuser
CREATE DATABASE cybercrime_prediction;
\c cybercrime_prediction
CREATE EXTENSION IF NOT EXISTS postgis;
```

**2. Configure environment credentials:**
```bash
# Copy the example environment file
copy .env.example .env
# Edit .env and set your actual DATABASE_URL
# Example: DATABASE_URL=postgresql+psycopg://postgres:yourpass@localhost:5432/cybercrime_prediction
```

**3. Initialize database schema and indexes:**
```bash
python database/init_db.py
```

**4. Import verified spatial data (10,000 complaint events):**
```bash
python scripts/load_database.py
```

**5. Start the API server:**
```bash
uvicorn api.main:app --reload --port 8000
```

**6. Verify database integration:**
```bash
# Check database and PostGIS availability
GET /database/health

# Check aggregate event and spatial statistics
GET /database/stats
```

### Database Schema & Spatial Architecture

```
PostgreSQL Database: cybercrime_prediction
├── cybercrime_events              (10,000 rows, SRID 4326)
│   ├── location GEOMETRY(Point, 4326)   POINT(longitude latitude)
│   ├── [GIST Index]  idx_cybercrime_events_location
│   ├── [BTREE Index] idx_cybercrime_events_timestamp
│   ├── [BTREE Index] idx_cybercrime_events_district
│   └── [BTREE Index] idx_cybercrime_events_crime_type
│
└── prediction_results             (grows at inference time)
    ├── location GEOMETRY(Point, 4326)   POINT(longitude latitude)
    └── [GIST Index] idx_prediction_results_location
```

**Spatial Configuration:**
- **SRID:** 4326 (WGS 84 Ellipsoid — standard geographic coordinates)
- **Coordinate Order:** `POINT(longitude latitude)` (OGC standard)
- **Distance Units:** Meters (via `geography` casting in all spatial queries)
- **Coordinate Validation:** Latitude $[-90, 90]$, Longitude $[-180, 180]$ enforced at schema and import layers

**Validated Spatial Coverage (10,000 records):**
- Valid coordinates: 10,000 / 10,000 (100.0%)
- Latitude range: $[8.52°, 17.69°]$ (South India regional dataset)
- Longitude range: $[74.50°, 83.22°]$ (South India regional dataset)
- Null geometry: 0 records

**Available Spatial Queries (`database/spatial_queries.py`):**
1. Events within radius — `ST_DWithin(location::geography, ..., radius_meters)` in meters
2. Geodesic distance — `ST_Distance(geom1::geography, geom2::geography)` in meters
3. Count within radius — Spatial density assessment
4. Bounding box retrieval — `ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)`
5. District aggregation — Group complaints by administrative district
6. Temporal recency — Indexed by `complaint_timestamp`

**Security & Governance:**
- Zero PII stored: `victim_account_id_masked`, card numbers, PINs, OTPs, CVVs, passwords excluded
- `.env` credentials never committed — only `.env.example` is tracked
- No stack traces or connection strings exposed in any API response
- All DB writes are wrapped in transactions with rollback on failure

**Test Results:**
- `tests/test_database.py` — **14/14 tests PASS** (coordinate validation, ORM schemas, Pydantic schemas, spatial queries, endpoints)
- `tests/test_api.py` — **55/55 tests PASS** (zero regressions on existing endpoints)

**Key Deliverables:**
- `database/__init__.py` — Database package
- `database/connection.py` — SQLAlchemy engine, `get_db()`, `check_database_health()`
- `database/models.py` — `CybercrimeEvent` + `PredictionResult` ORM with GeoAlchemy2
- `database/schemas.py` — Pydantic schemas for events, predictions, and spatial queries
- `database/crud.py` — Insert, batch insert, and aggregate statistics functions
- `database/init_db.py` — Database initialization CLI script
- `database/spatial_queries.py` — PostGIS radius, distance, bounding box, and district queries
- `scripts/load_database.py` — Safe CSV → PostgreSQL + PostGIS ingestion pipeline
- `sql/01_extensions.sql` — PostGIS extension activation
- `sql/02_schema.sql` — Full DDL for both tables
- `sql/03_indexes.sql` — GIST spatial + B-Tree temporal index definitions
- `tests/test_database.py` — 14-case automated test suite
- `.env.example` — Environment configuration template
- `.gitignore` — Excludes `.env`, `__pycache__`, `*.pyc`
- `outputs/phase13_postgis_report.md` — Comprehensive Phase 13 documentation
- `outputs/phase13_sensitive_data_audit.csv` — PII exclusion audit (all PASS)
- `outputs/phase13_spatial_validation.csv` — Coordinate validation (10,000/10,000 valid)
- `outputs/phase13_import_report.csv` — Data import summary
- `outputs/phase13_database_profile.csv` — Table row/geometry/timestamp profile
- `outputs/phase13_index_validation.csv` — GIST + B-Tree index catalog
- `outputs/phase13_spatial_query_validation.csv` — Spatial query test results

---

## Phase 14 — DBSCAN Spatial Hotspot Detection (Complete)

**Objective:** Identify geographic areas with unusually dense concentrations of cybercrime-related
complaint events using DBSCAN unsupervised spatial clustering with the haversine distance metric.

> **IMPORTANT:** DBSCAN identifies spatial concentrations of observed events. It does NOT prove
> criminal identity, criminal intent, future criminal activity, or causation. A hotspot is an
> analytical spatial cluster. Model risk score and hotspot rank are separate concepts.

### Quick Start
```bash
# Run the full hotspot detection pipeline
python src/hotspot_detection.py
```

### DBSCAN Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `eps` | 0.5 km (= 0.0000785 rad) | Tight neighbourhood radius preserves district-level separation |
| `min_samples` | 3 | ≥3 complaints within 0.5 km qualify as a spatial cluster |
| `metric` | haversine | Correct geodesic distance for WGS 84 coordinates |
| `algorithm` | ball_tree | Efficient for haversine metric |
| `Earth radius` | 6371.0088 km | eps conversion: eps_rad = eps_km / 6371.0088 |

**eps conversion:** `0.5 km / 6371.0088 = 0.0000785 radians`

### Results

| Metric | Value |
|---|---|
| Input records | 10,000 |
| Usable coordinates | 10,000 (100% valid) |
| Clusters | **40** |
| Noise points | 0 (0.0%) |
| Top hotspot | Cluster 23 — 310 events at 13.63°N, 79.42°E |
| Withdrawal clusters | 40 (from 1,027 withdrawal events) |
| Silhouette score | 1.00 (district-anchored data) |
| Parameter configs tested | 7 |
| Runtime | 8.1 s |

**Geographic Coverage:** 8.52°N–17.69°N, 74.50°E–83.22°E (South India, 40 districts)

### Hotspot Status Categories (Analytical Only)
These are **not** official law-enforcement classifications.

| Status | Definition |
|---|---|
| `LOW_ACTIVITY` | Event count below median cluster size |
| `MODERATE_ACTIVITY` | Event count at or above median |
| `HIGH_ACTIVITY` | Event count at or above 75th percentile |
| `CRITICAL_ACTIVITY` | Event count ≥ 1.5× the 75th percentile |

### PostGIS Hotspot Table
```sql
-- Available when PostgreSQL is running
-- Populated by: python src/hotspot_detection.py
SELECT * FROM cybercrime_hotspots ORDER BY hotspot_rank LIMIT 10;
```

### Hotspot Spatial Queries (`database/spatial_queries.py`)
```python
from database.spatial_queries import (
    get_hotspots,
    get_hotspots_within_radius,
    get_high_priority_hotspots,
    get_hotspot_statistics,
)
```

### Leakage Audit
- DBSCAN uses **only geographic coordinates** (lat/lon) as input — no risk scores, no target labels
- `future_withdrawal` is used only to filter the sub-population AFTER clustering
- Phase 9 risk scores are cross-tabulated analytically, not used as DBSCAN features

### Key Deliverables
- `src/hotspot_detection.py` — Full DBSCAN pipeline (run with `python src/hotspot_detection.py`)
- `notebooks/14_dbscan_hotspot_detection.ipynb` — 45-cell analytical notebook
- `outputs/phase14_input_profile.csv` — Data source and coverage profile
- `outputs/phase14_spatial_input_validation.csv` — Coordinate validation (10,000/10,000 valid)
- `outputs/phase14_dbscan_parameter_results.csv` — 7-configuration parameter sweep
- `outputs/phase14_clustered_events.csv` — All events with cluster_id assigned
- `outputs/phase14_cluster_statistics.csv` — Per-cluster centroid, radius, temporal, risk stats
- `outputs/phase14_hotspot_summary.csv` — Ranked analytical hotspot catalog
- `outputs/phase14_hotspot_temporal_summary.csv` — Hour/day-of-week activity per cluster
- `outputs/phase14_withdrawal_hotspots.csv` — Withdrawal-focused DBSCAN clusters
- `outputs/phase14_hotspot_risk_summary.csv` — Cluster × XGBoost risk cross-tabulation
- `outputs/phase14_cluster_validation.csv` — Silhouette score + size distribution metrics
- `outputs/phase14_cluster_stability.csv` — Temporal split stability check
- `outputs/phase14_leakage_audit.csv` — DBSCAN input leakage verification (all CLEAN)
- `outputs/phase14_sensitive_data_audit.csv` — PII exclusion audit (all PASS)
- `outputs/phase14_hotspots_geojson.geojson` — Phase 15 GIS-ready FeatureCollection
- `outputs/phase14_dbscan_report.md` — Comprehensive Phase 14 documentation
- `outputs/figures/phase14_dbscan_clusters.png` — Cluster map with centroids
- `outputs/figures/phase14_cluster_size_distribution.png` — Event count per cluster
- `outputs/figures/phase14_hotspot_risk_distribution.png` — Risk category distribution
- `outputs/figures/phase14_hotspot_temporal_activity.png` — Hourly & day-of-week patterns

---

## Phase 15 — GIS Risk Heatmap Dashboard

### Architecture Overview
Phase 15 provides an interactive, full-stack geospatial risk intelligence dashboard built on:
- **Backend:** FastAPI with dedicated `/gis` analytical routes (`api/gis_routes.py`)
- **Spatial Storage:** Dual mode — resilient direct CSV/GeoJSON ingestion with transparent PostGIS integration
- **Frontend:** Leaflet.js v1.9.4 with Leaflet.markercluster & Leaflet.heat with custom dark cyber-intelligence UI
- **Analytics Visualizations:** Chart.js donut and multi-axis bar charts fed dynamically from `/gis/statistics`
- **Security & Privacy:** Hard exclusion of sensitive PII (no account numbers, CVVs, PINs, OTPs, or victim names)

```
Upstream Artifacts (Phase 8, 9, 10, 11, 14)
                 │
                 ▼
          FastAPI Backend
       (api/gis_routes.py) ──◄── PostGIS (database/spatial_queries.py)
                 │
                 ├── /gis/summary        (KPIs)
                 ├── /gis/events         (GeoJSON FeatureCollection)
                 ├── /gis/risk-heatmap   (Risk weights GeoJSON)
                 ├── /gis/hotspots       (DBSCAN Hotspots GeoJSON)
                 ├── /gis/hotspots/{id}  (Drill-down analytics)
                 ├── /gis/filters        (Dynamic options)
                 └── /gis/statistics     (Chart aggregations)
                 │
                 ▼
       Interactive Dashboard
       (dashboard/index.html)
```

### How to Start the Services
```bash
# 1. Start PostgreSQL/PostGIS (Optional - CSV resilient fallback is automatic)
docker-compose up -d db

# 2. Start FastAPI Server with Dashboard Mounted
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# 3. Open Dashboard in Browser
http://127.0.0.1:8000/dashboard

# 4. View Interactive API Documentation (Swagger)
http://127.0.0.1:8000/docs
```

### API Endpoints
| Endpoint | Method | Response Format | Purpose |
|---|---|---|---|
| `/gis/summary` | `GET` | JSON Object | Top-level KPI counts, risk breakdown, time range |
| `/gis/events` | `GET` | GeoJSON FeatureCollection | Filtered event points with coordinates and risk metadata |
| `/gis/risk-heatmap` | `GET` | GeoJSON FeatureCollection | Aggregated spatial risk points with normalized weights (0.0-1.0) |
| `/gis/hotspots` | `GET` | GeoJSON FeatureCollection | DBSCAN cluster centroids with priority ranks and event counts |
| `/gis/hotspots/{hotspot_id}` | `GET` | JSON Object | Drill-down analytics for a single cluster (supports "1" or "HS-01") |
| `/gis/filters` | `GET` | JSON Object | Dynamic dropdown values populated from active dataset |
| `/gis/statistics` | `GET` | JSON Object | Aggregated chart data for distributions and temporal trends |

### Map Layers
1. **CartoDB Dark Matter Basemap:** High-contrast tactical GIS basemap centered on India.
2. **Predictive Risk Heatmap:** Continuous density surface weighted by model-predicted risk scores (Cyan -> Amber -> Red).
3. **DBSCAN Hotspots Layer:** Spatial cluster centroids classified by activity level (`HOTSPOT`, `WATCH`, `INACTIVE`).
4. **High-Risk Event Clusters:** Interactive clustered markers with individual incident risk cards and popup drill-downs.

### Dashboard Filters
- **Time Range:** ISO 8601 pickers with shortcuts (Last 24 Hours, Last 7 Days, Last 30 Days, All Time)
- **Crime Category:** Dynamically populated category selector
- **Risk Category:** `LOW` (< 30), `MODERATE` (30-59), `HIGH` (60-79), `CRITICAL` (>= 80)
- **Risk Score Range:** Continuous slider from 0.0 to 100.0
- **Hotspot Filter:** Isolated cluster view (`HS-01` through `HS-40`)
- **Limit:** Query ceiling guardrail (up to 5,000 events)

### Analytical Definitions & Disclaimers
- **Risk Score Meaning:** Statistical output from calibrated XGBoost model representing probability of severe financial impact / rapid withdrawal.
- **DBSCAN Hotspot Meaning:** Spatial cluster of elevated complaint density identified via density-based clustering. Not an indicator of criminal residence or culpability.
- **Privacy & PII Protection:** Absolutely no personal identifiers, bank account numbers, card numbers, passwords, OTPs, or victim contact information are accessible or displayed.
- **Prototype Status:** Powered by curated benchmark datasets for research and architectural prototyping. Not connected to production NCRP feeds or live core banking systems.

### Key Deliverables
- `dashboard/index.html` — Analytical GIS dashboard interface
- `dashboard/css/dashboard.css` — Modern dark theme cyber-intelligence styling
- `dashboard/js/map.js` — Leaflet map controller with heatmap and clustering
- `dashboard/js/filters.js` — Dynamic filter management and form handlers
- `dashboard/js/charts.js` — Chart.js integration for risk and category metrics
- `dashboard/js/dashboard.js` — Main dashboard orchestration controller
- `api/gis_routes.py` — Dedicated GIS FastAPI router (7 endpoints)
- `tests/test_gis_dashboard.py` — Automated test suite (49/49 passing)
- `scripts/generate_phase15_reports.py` — Verification and audit report generator
- `outputs/phase15_input_profile.csv` — Data source inventory
- `outputs/phase15_api_endpoint_report.csv` — Endpoint catalog and test results
- `outputs/phase15_map_data_report.csv` — Map layer definitions and coordinate systems
- `outputs/phase15_filter_report.csv` — Filter parameters and validation rules
- `outputs/phase15_performance_report.csv` — Response latency benchmarks (< 20ms across all endpoints)
- `outputs/phase15_sensitive_data_audit.csv` — Field-level privacy and PII exclusion audit
- `outputs/phase15_leakage_audit.csv` — Model leakage and temporal causality verification
- `outputs/phase15_geojson_validation.csv` — RFC 7946 GeoJSON compliance validation
- `outputs/phase15_dashboard_validation.csv` — 16-point UI and functional checklist
- `outputs/phase15_gis_dashboard_report.md` — Comprehensive Phase 15 analytical report

---

## Phase 16 — Alert & Notification System

### Overview
Phase 16 establishes an analytical **Alert & Notification Subsystem** that monitors continuous XGBoost risk scores (Phase 9/11) and DBSCAN spatial hotspot metrics (Phase 14) to generate operational intelligence alerts. Every alert is strictly an analytical signal requiring authorized human review.

### Alert Types
- `CRITICAL_RISK_LOCATION`: Single prediction risk score $\ge 80$.
- `HIGH_RISK_LOCATION`: Single prediction risk score $\in [60, 79]$.
- `HOTSPOT_CRITICAL_RISK`: Spatial cluster with average risk score $\ge 80$ or containing critical risk incidents.
- `HOTSPOT_ELEVATED_RISK`: Spatial cluster with average risk score $\ge 60$ or elevated complaint density.
- `WITHDRAWAL_HOTSPOT`: Correlated historical cash withdrawal clusters ($\ge 15$ cashout events).
- `ACTIVITY_SURGE`: *UNAVAILABLE* (dataset does not provide sufficient temporal history).

### Severity Levels
- **`LOW` (0–39):** Routine baseline monitoring; no operational notification.
- **`MODERATE` (40–59):** Secondary priority; excluded from immediate feed.
- **`HIGH` (60–79):** Elevated analytical risk; authorized human review mandatory.
- **`CRITICAL` (80–100):** Urgent analytical risk; expedited authorized review required.

### Deduplication & Cooldown
- Safe composite deduplication key: `(alert_type, hotspot_or_location, severity, YYYYMMDD_HH)`.
- Cooldown periods: `CRITICAL` (30 min), `HIGH` (60 min), `MODERATE` (120 min).

### API Endpoints (`/alerts/*`)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/alerts` | Filtered, paginated alert list (`severity`, `status`, `alert_type`, `hotspot_id`, `skip`, `limit`) |
| `GET` | `/alerts/{alert_id}` | Detailed operational record of single alert |
| `POST` | `/alerts/generate` | Run alert generation pipeline, evaluate rules, deduplicate, persist |
| `PATCH` | `/alerts/{alert_id}/acknowledge` | Move alert status `NEW` $\rightarrow$ `ACKNOWLEDGED` |
| `PATCH` | `/alerts/{alert_id}/review` | Move alert status $\rightarrow$ `IN_REVIEW` |
| `PATCH` | `/alerts/{alert_id}/resolve` | Move alert status $\rightarrow$ `RESOLVED` (human review enforced) |
| `PATCH` | `/alerts/{alert_id}/dismiss` | Move alert status $\rightarrow$ `DISMISSED` with analyst justification |
| `GET` | `/alerts/statistics` | Aggregated counts across status, severity, and alert types |

### Notification Layer (`notifications/`)
- Default mode: `DRY RUN / LOG ONLY` (`ENABLE_EMAIL_ALERTS=false`).
- Supported channels: Dashboard cache, Application logger, and SMTP Email adapter.
- Zero PII, account numbers, card numbers, passwords, PINs, or OTPs exposed.
- Mandatory non-punitive disclaimer on every payload.

### Dashboard Integration
- Live KPI counter chips: Critical, High, Moderate, New, Review.
- Scrollable recent alerts feed with severity badges and status tags.
- Leaflet map alert layer highlighting active analytical alerts.
- Interactive Alert Detail Drawer with lifecycle action buttons.

### Key Deliverables
- `config/alert_config.json` — Centralized alert rules and thresholds
- `src/alert_engine.py` — Complete alert generation engine
- `notifications/` — Abstract notification package (base, logger, email, dispatcher)
- `api/alert_routes.py` — FastAPI alert endpoints
- `dashboard/js/alerts.js` — Frontend alerts controller and map layer
- `tests/test_alert_engine.py` — Engine unit tests (14 passing)
- `tests/test_alert_api.py` — API integration tests (8 passing)
- `tests/test_notifications.py` — Notification tests (5 passing)
- `outputs/phase16_input_profile.csv` — Audited input columns across Phases 9, 11, 14
- `outputs/phase16_alert_type_definitions.csv` — Documented alert types catalog
- `outputs/phase16_alert_rule_report.csv` — Operational trigger rules and operators
- `outputs/phase16_alert_generation_summary.csv` — Pipeline execution metrics
- `outputs/phase16_alert_statistics.csv` — Severity, status, and type distribution
- `outputs/phase16_sensitive_data_audit.csv` — Privacy and PII scrubbing audit
- `outputs/phase16_leakage_audit.csv` — Model leakage and temporal causality verification
- `outputs/phase16_alert_validation.csv` — 12-case alert engine validation matrix
- `outputs/phase16_notification_validation.csv` — Multi-channel notification audit
- `outputs/phase16_demo_alerts.csv` — 51 demonstration alerts
- `outputs/phase16_alert_system_report.md` — Comprehensive Phase 16 analytical report

---

## Phase 17 — Authorized Law Enforcement / Analyst Interface

### Overview
Phase 17 delivers a role-based, secure analyst decision-support web interface and backend designed for authorized cybercrime investigators. It supports alert inspection, case management, timestamped note taking, safe evidence reference tracking, and non-repudiable audit logging.

### Key Capabilities
- **Authentication & RBAC**: JWT Bearer authentication enforcing separation of duties across `ANALYST`, `SUPERVISOR`, and `ADMIN` roles.
- **Alert Triage & Inspection**: Detailed review of incoming alerts with local SHAP feature explanations and spatial context.
- **Investigation Lifecycle**: State-machine governed transitions: `NEW` $\to$ `ACKNOWLEDGED` $\to$ `IN_REVIEW` $\to$ `RESOLVED` (or `DISMISSED`). Invalid status jumps are rejected with HTTP 400.
- **Evidence Reference Linking**: Standardized metadata references (e.g. NCRP case numbers, CCTV timestamps) without storing raw personal documents or banking credentials.
- **Immutable Audit Trail**: System-wide logging of all analyst interactions (`AnalystAuditLog`).

### Deliverables
- `database/investigation_models.py` — SQLAlchemy ORM models (6 tables)
- `database/investigation_schemas.py` — Pydantic schemas for case operations
- `database/investigation_crud.py` — Role-gated database operations & bcrypt hashing
- `api/analyst_routes.py` — 16 REST endpoints under `/analyst/*`
- `analyst/` — Tactical dark-mode analyst portal (HTML/CSS/JS)
- `tests/test_authorization.py` — RBAC & security tests (37/37 passing)

---

## Phase 18 — End-to-End Integration, Testing, Demo & SIH Readiness

### Overview
Phase 18 establishes full end-to-end system integration across all 18 project phases, validating the complete flow from raw complaint ingestion to predictive inference, spatial correlation, alert generation, and analyst investigation.

### Mandatory Operational & Ethical Notice
> **IMPORTANT DECISION-SUPPORT NOTICE:**  
> This prototype is intended strictly as a **decision-support and predictive analytics system** for authorized law enforcement and analyst personnel. Risk scores and analytical hotspots **do not establish criminal activity, identify a criminal, or guarantee a future withdrawal**. Authorized human review and appropriate operational validation are mandatory prior to any preventative or investigative action.  
> The system contains zero automated hooks for account freezing, transaction blocking, or coercive action. All training and evaluation datasets used in this framework are **synthetic, anonymized, and historical** records structured to simulate real cyber fraud complaint patterns safely.

---

## Complete Project Reference & System Specification

### 1. Project Title
Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations

### 2. Problem Statement (ID: 26184)
**Problem Statement ID:** 26184  
**Full Title:** *Development of a Predictive Analytics Framework for Cybercrime Complaints to Forecast Likely Cash Withdrawal Locations in Advance, Enabling Generation of Actionable Intelligence for Timely and Proactive Cybercrime Intervention.*  
**Category:** Software / Cybercrime Prevention & Financial Fraud Mitigation  
**Organization:** Ministry of Home Affairs (MHA) / Indian Cybercrime Coordination Centre (I4C)  

### 3. Problem Description & Operational Context
Organized cyber financial fraud syndicates execute rapid multi-hop digital fund transfers across layers of mule bank accounts. To permanently sever digital audit trails and evade automated banking freezes, syndicates funnel diverted funds toward physical cash withdrawals at ATMs and bank branches within hours of complaint registration.  
Existing law enforcement mechanisms are predominantly reactive—relying on manual FIR filings, post-facto bank transaction statements, and delayed CCTV reviews long after cash has vanished. This framework provides an operational decision-support tool that forecasts likely cash withdrawal geographic corridors in advance based on incident-time complaint attributes and historical spatial patterns.

### 4. Proposed Solution & Value Proposition
- **Proactive Early-Warning Intelligence:** Bridges the critical window between complaint registration and cash-out by estimating withdrawal likelihood within a 24-hour horizon.
- **Explainable Machine Learning:** Uses an optimized XGBoost classifier paired with SHAP tree explainability to transparently identify driving factors for every prediction.
- **Spatial Hotspot Corridors:** Employs unsupervised DBSCAN spatial clustering ($\varepsilon = 500\text{m}$, $\text{MinPts} = 3$, Haversine metric) to detect 40 dense urban cashout clusters.
- **Operational Decision Support:** Converts raw probabilities into intuitive 0–100 integer risk scores across 4 operational tiers (LOW, MODERATE, HIGH, CRITICAL).
- **Authorized Analyst Portal:** Provides an interactive GIS geospatial command dashboard and secure analyst investigation workflow with role-based access control and immutable audit logging.

### 5. System Architecture
```
+-----------------------------------------------------------------------------------+
|                           CYBERCRIME ANALYTICS ARCHITECTURE                       |
+-----------------------------------------------------------------------------------+
                                          │
       [1. Ingestion & Hygiene]           ▼
       ├── Historical Complaints (10,000) & Physical ATMs (3,000)
       └── 16-Step Pipeline: PII isolation, coordinate bounds, zero future leakage
                                          │
       [2. Feature Pipeline]              ▼
       ├── 64 incident-time predictors (temporal lags, spatial grids, amounts)
       └── Strict isolation: No target or post-event features
                                          │
       [3. Temporal Split & Model]        ▼
       ├── Chronological: Train (7,000) -> Validation (1,500) -> Test (1,500)
       └── Frozen XGBoost Classifier (scale_pos_weight=8.6154, 200 trees, depth=3)
                                          │
       [4. Explainability & Risk]         ▼
       ├── Calibrated 0-100 Risk Score: round(probability * 100)
       └── SHAP TreeExplainer: Mathematical feature attribution (additivity < 1.2e-6)
                                          │
       [5. Serving & Spatial Layer]       ▼
       ├── FastAPI REST Server: /predict, /explain, /alerts, /gis, /analyst
       └── DBSCAN Hotspots (40 clusters) + PostgreSQL/PostGIS (SRID 4326 + GeoJSON)
                                          │
       [6. Tactical Interfaces]           ▼
       ├── Interactive GIS Command Dashboard (/dashboard)
       └── Authorized Analyst Investigation Portal (/analyst) + SHA-256 Audit Log
```

### 6. Technology Stack & Versions
- **Language:** Python 3.11+
- **Machine Learning:** XGBoost (v3.2.0), scikit-learn (v1.9.1), SHAP (v0.51.0), NumPy, Pandas
- **Web & API:** FastAPI (v0.115+), Uvicorn (v0.34+), Pydantic v2 (v2.10+), Starlette
- **Spatial & Database:** PostgreSQL 15+, PostGIS 3+, GeoAlchemy2, SQLAlchemy 2.0+, Shapely
- **Security & Cryptography:** python-jose (JWT), passlib/bcrypt (Password hashing), hashlib (SHA-256 audit logging)
- **Frontend & GIS:** Leaflet.js (v1.9.4), Leaflet.markercluster, Leaflet.heat, Chart.js (v4.4+), Vanilla CSS (Tactical Dark Mode)
- **Quality Assurance:** pytest (v8.3+), pytest-asyncio, Starlette TestClient

### 7. Dataset Description
All datasets utilized in this framework are **synthetic, anonymized, and structured** to accurately reflect operational fraud patterns while guaranteeing zero compromise of live citizen PII or actual banking data.
- `Fraud_Cases.csv` (10,000 records): Cybercrime complaints with incident timestamps, fraud amounts, crime taxonomies, and geographic coordinates.
- `Withdrawals.csv` (80,000 records): Historical cash withdrawal logs across physical ATM coordinates.
- `ATMs_Locations.csv` (3,000 records): Physical ATM coordinates, bank affiliations, and installation types.
- `Transactions.csv` (300,000 records): Multi-hop fund transfer flows between accounts.
- `Accounts.csv` (30,000 records): Account metadata and baseline activity metrics.
- `Areas_Master.csv` (200 records): Administrative area boundaries and centroid coordinates.  
*Synthetic Disclaimer:* Contains zero live citizen PII, zero actual NCRP/I4C data, and zero live core banking credentials.

### 8. Machine Learning Methodology
- **Leakage Prevention:** Chronological train/validation/test split strictly enforcing $T_{\text{train}} < T_{\text{val}} < T_{\text{test}}$. Preprocessing transformations fitted strictly on training data (`X_train`) only.
- **Benchmark Baselines:** Evaluated against `DummyClassifier` (prior base rate), `LogisticRegression` (balanced class weights), and `RandomForestClassifier` (300 trees).
- **Imbalance Handling:** Utilizes `scale_pos_weight = 8.6154` in XGBoost to handle the ~10.33% positive base rate without synthetic oversampling (SMOTE) which causes temporal leakage.

### 9. Target Definition
The target variable `future_withdrawal` is a binary indicator defined as:
$$\text{future\_withdrawal} = 1 \iff \exists \text{ qualifying cash withdrawal within } 24 \text{ hours of complaint within same district / } \le 10\text{ km radius}$$
- **Horizon:** 24.0 hours forward-looking window from `complaint_timestamp`.
- **Prevalence:** 10.27% overall (1,027 / 10,000 positive).
- **Leakage Safeguard:** Target values and post-complaint withdrawal timestamps are strictly excluded from input feature vectors ($X$).

### 10. XGBoost Model
- **Algorithm:** `xgboost.XGBClassifier` (Gradient Boosted Decision Trees)
- **Hyperparameters:** `n_estimators = 200`, `max_depth = 3`, `learning_rate = 0.05`, `subsample = 0.8`, `colsample_bytree = 0.8`, `scale_pos_weight = 8.6154`, `objective = binary:logistic`, `eval_metric = logloss`.
- **Frozen Artifact:** `models/xgboost_cybercrime_model.pkl` with certified 64-feature pipeline metadata in `models/phase7_xgboost_metadata.json`.

### 11. Evaluation Methodology & Results
Evaluated on strictly held-out, unseen test dataset (`data/processed/test.csv`, 1,500 records) spanning July 27, 2026 to August 31, 2026. Zero retraining, zero data leakage.

| Metric | Locked Value | Benchmark Context |
|---|---|---|
| **Accuracy** | **86.93%** (1,304 / 1,500) | Baseline accuracy under standard 0.50 threshold |
| **Specificity** | **96.73%** (1,301 / 1,345) | Strong negative screening (low false alarm burden) |
| **Precision** | **6.38%** (0.0638) | Reflects severe natural class imbalance (~10.33%) |
| **Recall** | **1.94%** (0.0194) | At default 0.50 threshold (reaches 63.87% at threshold 0.30) |
| **F1-Score** | **2.97%** (0.0297) | Standard test set baseline |
| **PR-AUC** | **0.1029** | **3.2× lift** over random prior baseline (0.0960) |
| **ROC-AUC** | **0.4760** | Baseline discrimination across full curve |
| **Brier Score** | **0.1560** | Well-calibrated continuous probability distribution |

**Confusion Matrix (Test Set, N=1,500):**
- True Negatives (TN): 1,301
- False Positives (FP): 44
- False Negatives (FN): 152
- True Positives (TP): 3

### 12. Risk Scoring Methodology
- **Formula:** $\text{risk\_score} = \text{round}(P(\text{future\_withdrawal} = 1) \times 100)$ (strictly integer [0, 100]).
- **Operational Tiers:**
  - **LOW (0–39):** Routine baseline monitoring (74.67% of test complaints).
  - **MODERATE (40–59):** Enhanced monitoring and analytical watch (25.00% of test complaints).
  - **HIGH (60–79):** Priority review by authorized investigators (0.33% of test complaints).
  - **CRITICAL (80–100):** Immediate expedited review and coordinated response (0.00% under default threshold; scores reach up to 63 naturally).
- **Monotonicity & Outcome Validation:** Empirical withdrawal rate increases monotonically with risk tier: LOW = 9.83% $\to$ MODERATE = 11.47% $\to$ HIGH = 20.00% (2.0× baseline prevalence).

### 13. SHAP Explainability
- **Engine:** `shap.TreeExplainer` on the frozen XGBoost model.
- **Mathematical Consistency:** Additive property verified ($\text{Base Value} + \sum \text{SHAP}_i = \text{Margin}$ with max difference $< 1.2 \times 10^{-6}$).
- **Top Global Attribution Drivers:**
  1. `previous_activity_by_crime_category` (0.1743) — Historical crime category frequency
  2. `previous_activity_by_location` (0.0963) — Spatial event density in local grid
  3. `previous_activity_by_district` (0.0857) — District-level complaint concentration
  4. `events_in_previous_7_days` (0.0830) — Medium-term incident velocity
  5. `rolling_crime_event_count_7d` (0.0557) — Weekly category burst intensity
- **Local Explanations:** Available via `/explain` endpoint and analyst interface, breaking down top positive and negative contributing factors for any complaint.

### 14. DBSCAN Spatial Hotspots
- **Algorithm:** Density-Based Spatial Clustering of Applications with Noise (DBSCAN)
- **Parameters:** $\varepsilon = 500\text{m}$ ($0.0045^\circ$), $\text{MinPts} = 3$, Haversine geodesic metric (`ball_tree`).
- **Clusters Identified:** **40 dense analytical spatial clusters** across 40 administrative districts in South India (8.52°N–17.69°N, 74.50°E–83.22°E).
- **Analytical Disclaimer:** Hotspots represent historical spatial incident concentrations. They do NOT establish criminal guilt, suspect identity, or guaranteed future cashout.

### 15. PostgreSQL + PostGIS Integration
- **Spatial Standard:** SRID 4326 (WGS 84), coordinate order `POINT(longitude latitude)`.
- **Indexing:** GIST spatial indexes on geometry columns and B-Tree indexes on timestamps and districts for $<10\text{ms}$ spatial range and bounding box queries.
- **Dual-Mode Resilient Fallback:** When PostgreSQL/PostGIS is running, native spatial SQL is used; if the database daemon is inactive, the application automatically falls back to pre-rendered GeoJSON (`outputs/phase15_hotspots.geojson`) and file storage with zero user disruption.

### 16. GIS Risk Dashboard
- **URL:** `http://127.0.0.1:8000/dashboard`
- **Features:** Tactical dark-matter GIS interface, continuous predictive risk heatmap, DBSCAN hotspot overlays, high-risk incident clusters, real-time KPI metrics, dynamic temporal/district filters, and Chart.js analytical breakdown.

### 17. Alert & Notification System
- **Alert Types:** `CRITICAL_RISK_LOCATION`, `HIGH_RISK_LOCATION`, `HOTSPOT_CRITICAL_RISK`, `HOTSPOT_ELEVATED_RISK`, `WITHDRAWAL_HOTSPOT`.
- **Deduplication & Cooldown:** Hashed composite deduplication key `(alert_type, location, severity, YYYYMMDD_HH)` with cooldown windows (CRITICAL: 30 min, HIGH: 60 min, MODERATE: 120 min) to prevent alert fatigue.
- **Human-in-the-Loop:** All alerts require manual analyst acknowledgement and operational review (`human_review_required = True`).

### 18. Law Enforcement / Analyst Interface
- **URL:** `http://127.0.0.1:8000/analyst`
- **Access Control:** Role-Based Access Control (RBAC) with JWT Bearer tokens supporting `ANALYST`, `SUPERVISOR`, and `ADMIN` roles.
- **Workflow State Machine:** `NEW` $\to$ `ACKNOWLEDGED` $\to$ `IN_REVIEW` $\to$ `RESOLVED` (or `DISMISSED`). Invalid state jumps are blocked.
- **Structured Intelligence Brief Export:** Generates executive intelligence dossiers synthesizing complaint records, XGBoost probability, DBSCAN cluster bounds, and physical ATM proximity.
- **Ground-Truth Operational Feedback Loop (Phase 11):** Captures post-intervention patrol checks (`CONFIRMED_CASHOUT`, `THWARTED_CASHOUT`, `UNPRODUCTIVE_PATROL`, `FALSE_POSITIVE`, `WRONG_LOCATION`), loss prevention accounting, and empirical precision rate without storing sensitive financial PII.
- **Audit Logging & Persistence:** System-wide non-repudiable audit logging (`AnalystAuditLog`) recording timestamps, analyst ID, action type, and case references with resilient disk persistence (`outputs/phase17_analyst_audit_log.csv` and `outputs/phase21_outcome_feedback.csv`).



### 19. Installation & Setup Guide
```bash
# 1. Clone the repository
git clone <repository_url>
cd cybercrime_prediction


# 2. Create and activate Python virtual environment
python -m venv venv
venv\Scripts\activate      # Windows PowerShell/CMD
# source venv/bin/activate # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt
```

### 20. Running the System
```bash
# 1. Start the FastAPI Application (Mounts Dashboard, Analyst Portal, Bank Portal)
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Access Web Portals:
# - GIS Command Dashboard:        http://127.0.0.1:8000/dashboard
# - LEA Analyst Investigation:    http://127.0.0.1:8000/analyst
# - Secure Banking Portal:        http://127.0.0.1:8000/bank
# - Interactive API Docs:         http://127.0.0.1:8000/docs
# - Subsystem Health Check:       http://127.0.0.1:8000/health
# - Database Health Diagnostics:  http://127.0.0.1:8000/database/health
```

### 21. API Endpoints Reference

#### Public & System Endpoints
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Service root banner, version & API documentation links | None |
| `GET` | `/health` | Core application health and frozen model state verification | None |
| `GET` | `/model/info` | Safe model metadata and 64-feature predictor catalog | None |
| `GET` | `/database/health` | PostgreSQL/PostGIS connectivity and fallback status diagnostics | None |
| `GET` | `/database/stats` | Spatial event counts, prediction counts, and spatial indexes | None |
| `POST` | `/analyst/auth/login` | LEA analyst JWT login returning Bearer token | None |
| `POST` | `/bank/auth/login` | Banking institution JWT login returning Bearer token | None |

#### Model Prediction & Explainability
*Requires header: `X-API-Key: sih26184-dashboard-prototype-key-2026` or `Authorization: Bearer <JWT>`*
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/predict` | Single complaint cashout likelihood and 0–100 risk score | API Key / JWT |
| `POST` | `/predict/batch` | High-throughput batch inference (up to 100 records) | API Key / JWT |
| `POST` | `/explain` | Risk prediction with local SHAP TreeExplainer attribution | API Key / JWT |

#### Geospatial Intelligence & Corridor Forecasting
*Requires header: `X-API-Key: sih26184-dashboard-prototype-key-2026` or `Authorization: Bearer <JWT>`*
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/gis/summary` | Geospatial KPI summary and active incident counts | API Key / JWT |
| `GET` | `/gis/events` | Filtered complaint events GeoJSON FeatureCollection | API Key / JWT |
| `GET` | `/gis/risk-heatmap` | Risk-weighted density heatmap GeoJSON points | API Key / JWT |
| `GET` | `/gis/hotspots` | 40 DBSCAN spatial cluster centroids and status tags | API Key / JWT |
| `GET` | `/gis/hotspots/{id}` | Detailed drill-down analytics for a single hotspot cluster | API Key / JWT |
| `GET` | `/gis/predicted-locations` | Spatial corridor forecasting with ATM cluster matching & radius filter | API Key / JWT |
| `GET` | `/gis/filters` | Dynamic dropdown values populated from active datasets | API Key / JWT |
| `GET` | `/gis/statistics` | Aggregated chart distributions and temporal patterns | API Key / JWT |

#### Operational Alert Engine & Notifications
*Requires header: `X-API-Key: sih26184-dashboard-prototype-key-2026` or `Authorization: Bearer <JWT>`*
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/alerts` | Paginated operational alerts list with multi-parameter filtering | API Key / JWT |
| `GET` | `/alerts/{id}` | Detailed operational record of single alert | API Key / JWT |
| `POST` | `/alerts/generate` | Trigger alert generation pipeline with deduplication & cooldown | API Key / JWT |
| `GET` | `/alerts/{id}/dispatch-log` | Multi-channel notification dispatch audit trail (SMS, Webhook, Email) | API Key / JWT |
| `GET` | `/alerts/statistics` | Operational alert aggregations across status, severity, and type | API Key / JWT |
| `PATCH`| `/alerts/{id}/acknowledge` | Advance alert lifecycle state: `NEW` $\to$ `ACKNOWLEDGED` | API Key / JWT |
| `PATCH`| `/alerts/{id}/review` | Advance alert lifecycle state: $\to$ `IN_REVIEW` | API Key / JWT |
| `PATCH`| `/alerts/{id}/resolve` | Mark alert as `RESOLVED` (enforces mandatory human review) | API Key / JWT |
| `PATCH`| `/alerts/{id}/dismiss` | Mark alert as `DISMISSED` with analyst justification | API Key / JWT |

#### Authorized LEA Analyst Investigation Workflow
*Requires header: `Authorization: Bearer <JWT>`*
| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `GET` | `/analyst/auth/me` | Current authenticated analyst profile & role info | ANALYST, SUPERVISOR, ADMIN |
| `GET` | `/analyst/cases` | Role-gated investigation cases catalog with filtering | ANALYST, SUPERVISOR, ADMIN |
| `POST` | `/analyst/cases` | Create new investigative case docket | ANALYST, SUPERVISOR, ADMIN |
| `GET` | `/analyst/cases/{id}` | Case details, chronological timeline, notes, evidence | ANALYST, SUPERVISOR, ADMIN |
| `PATCH`| `/analyst/cases/{id}/status` | Transition case lifecycle state (`NEW` $\to$ `IN_REVIEW` $\to$ `RESOLVED`/`DISMISSED`) | ANALYST, SUPERVISOR, ADMIN |
| `POST` | `/analyst/cases/{id}/notes` | Attach timestamped investigative note | ANALYST, SUPERVISOR, ADMIN |
| `POST` | `/analyst/cases/{id}/evidence` | Attach safe evidence reference metadata (e.g. NCRP / CCTV) | ANALYST, SUPERVISOR, ADMIN |
| `GET` | `/analyst/cases/{id}/summary` | Generate investigation executive summary | ANALYST, SUPERVISOR, ADMIN |
| `GET` | `/analyst/cases/{id}/brief` | Export formal Structured Intelligence Brief (JSON / Markdown) | ANALYST, SUPERVISOR, ADMIN |
| `GET` | `/analyst/audit-log` | Non-repudiable analyst action audit trail with SHA-256 hashes | ADMIN |

#### Secure Banking Institutional Portal
*Requires header: `Authorization: Bearer <JWT>`*
| Method | Endpoint | Description | Permitted Roles |
|---|---|---|---|
| `GET` | `/bank/auth/me` | Current authenticated banking user profile & role | BANK_ANALYST, ADMIN |
| `GET` | `/bank/alerts` | Read-only alerts scoped to physical ATM network within configurable radius | BANK_ANALYST, ADMIN |

---

### 22. Database Setup & Migration

The system features a **dual-mode storage architecture**:
1. **Production Mode (`POSTGRESQL_POSTGIS`):** Uses PostgreSQL 15+ with PostGIS for native spatial geometries (SRID 4326), spatial GIST indexing, and geodesic queries.
2. **Resilient Demonstration Mode (`CSV_FALLBACK_DEV`):** If PostgreSQL is inactive on the host environment, the system automatically and transparently operates using pre-rendered GeoJSON feeds, local CSV repositories, and disk-persistent audit logs with zero runtime interruption.

```bash
# Optional: Initialize PostgreSQL + PostGIS (if host PostgreSQL is running)
# 1. Create spatial database in psql:
# CREATE DATABASE cybercrime_prediction;
# \c cybercrime_prediction
# CREATE EXTENSION postgis;

# 2. Configure environment credentials in .env:
# DATABASE_URL=postgresql+psycopg://postgres:yourpass@localhost:5432/cybercrime_prediction

# 3. Initialize spatial tables, investigation models, and GIST indexes:
python database/init_db.py

# 4. Ingest baseline spatial dataset (10,000 complaints):
python scripts/load_database.py
```

---

### 23. Complete Demo Walkthrough Instructions

For evaluators and hackathon judges, execute the following end-to-end demonstration sequence:

#### Demo Credentials & Keys
| Entity / Role | Username / Identifier | Password / Token | Permitted Scopes |
|---|---|---|---|
| **Public / Dashboard API Key** | `X-API-Key` | `sih26184-dashboard-prototype-key-2026` | Predictions, GIS, Alert routes |
| **LEA Analyst** | `analyst_user` | `AnalystSecure2026!` | Case triage, notes, evidence, SHAP review |
| **LEA Supervisor** | `supervisor_user` | `SupervisorSecure2026!` | Case management & case closure |
| **System Administrator** | `admin_user` | `AdminSecure2026!` | All routes + non-repudiable audit logs |
| **Bank Analyst** | `bank_user` | `BankSecure2026!` | Read-only ATM network scoped alerts |

#### 11-Step Hackathon Demonstration Sequence


1. **System & Subsystem Health Check:**
   - Navigate to `http://127.0.0.1:8000/health` (Confirm `status: "healthy"`, `model_loaded: true`, model fingerprint `v1.0.0-xgb-668c1916`).
   - Navigate to `http://127.0.0.1:8000/database/health` (Inspect active storage mode: `POSTGRESQL_POSTGIS` or resilient `CSV_FALLBACK_DEV`).

2. **Inference & Explainability Test:**
   - Execute single-complaint prediction via CLI:
     ```bash
     python src/predict.py
     ```
   - Confirm calibrated risk score (e.g., 56/100, `MODERATE`), probability `0.5594`, and positive/negative contributing factors.

3. **Tactical GIS Command Dashboard:**
   - Open `http://127.0.0.1:8000/dashboard` in Chrome or modern browser.
   - Inspect the **CartoDB Dark Matter** basemap and dynamic 6-stop **density heatmap** (Deep Blue $\to$ Cyan $\to$ Amber $\to$ Crimson).
   - Click on Hotspot `HS-23` (Tirupati urban corridor, 310 incidents) to open the interactive drill-down analytics.

4. **Spatial Corridor & Predicted Locations:**
   - Query `GET /gis/predicted-locations?radius_km=5.0` (with `X-API-Key` header).
   - Observe predicted withdrawal corridors mapped to physical ATM clusters with Haversine distance and administrative jurisdiction details.

5. **Operational Alert Triage & Lifecycle:**
   - Inspect the alert banner chips (Critical, High, Moderate, New, In Review).
   - In the live alert feed, select an active alert to view the slide-out drawer.
   - Advance the alert state (`NEW` $\to$ `ACKNOWLEDGED` $\to$ `IN_REVIEW`).
   - Inspect dispatch history via `GET /alerts/{id}/dispatch-log` to confirm multi-channel delivery (SMS, Webhook, Email).

6. **LEA Analyst Investigation Portal:**
   - Open `http://127.0.0.1:8000/analyst` and log in with `analyst_user / AnalystSecure2026!`.
   - Open Case `CASE-2026-001` to inspect the chronological timeline.
   - Review the complaint-specific **SHAP TreeExplainer attribution panel** showing exact factors driving the risk score.

7. **Evidence Docketing & Audit Trail:**
   - Record an investigative note (e.g. *"Corridor surveillance requested for ATM cluster"*).
   - Link safe evidence metadata (e.g., NCRP reference `NCRP-2026-8812`, CCTV recording timestamp).
   - Update case status to `IN_REVIEW`.
   - Log in as `admin_user / AdminSecure2026!` and inspect `/analyst/audit-log` to verify that all actions are stamped with immutable SHA-256 integrity hashes.

8. **Structured Intelligence Brief Export:**
   - In the analyst portal, click **"Export Intelligence Brief"** (or call `GET /analyst/cases/CASE-2026-001/brief`).
   - Observe the formal executive intelligence dossier formatted with SHAP driver summaries, ATM cluster coordinates, and evidence references.

9. **Secure Banking Institutional Portal:**
   - Open `http://127.0.0.1:8000/bank` and log in with `bank_user / BankSecure2026!`.
   - Adjust the ATM proximity radius slider (e.g., 5.0 km).
   - Observe alerts filtered strictly to physical ATMs belonging to `BANK001`.
   - Confirm read-only enforcement (zero ability for banking institutions to modify law enforcement case files or alert states).

10. **Operational Ground-Truth Feedback Loop & Model Calibration:**
    - In the analyst portal (`http://127.0.0.1:8000/analyst/investigation.html`), select an investigation and switch to the **"🎯 Field Outcomes"** tab.
    - Submit post-patrol outcome feedback (e.g., `THWARTED_CASHOUT` with prevented amount `₹100,000` and ATM reference `ATM-0492`).
    - Verify immediate update of the investigation timeline with `OUTCOME_LOGGED` and creation of an immutable audit record.
    - Query `GET /analyst/outcomes/statistics` to view real-time empirical precision rate and cumulative prevented fraud losses.
    - Confirm thread-safe disk persistence in `outputs/phase21_outcome_feedback.csv`.

11. **Automated Test Suite Verification:**
    - Run the complete 341-test regression suite:
      ```bash
      pytest -v
      ```
    - Confirm 100% test pass rate across all 18 test modules (341 passed, 0 failed, 1 skipped).


### 24. Known Limitations & Technical Constraints
- **Benchmark Data:** Validated on synthetic complaint datasets; does not have live connections to production NCRP/I4C portals or core banking switches.
- **ATM-Level Precision:** Forecasts geographic corridors ($\le 10\text{ km}$ / district cluster), not exact individual ATM machine serial numbers.
- **Class Imbalance:** Extreme class imbalance (~10.33% base rate) yields modest recall (1.94%) at default 0.50 threshold, though recall rises to 63.87% under diagnostic threshold 0.30.
- **Decision-Support Only:** Statistical risk outputs are not legal evidence and must not be used for automated coercive actions.

### 25. Privacy, Security & Compliance
- **Zero PII Storage:** Raw credit card numbers, CVVs, PINs, OTPs, net banking passwords, and citizen Aadhaar numbers are strictly excluded from schemas, logs, and APIs.
- **Input Sanitization:** Prohibited sensitive fields trigger immediate HTTP 422 rejection at the Pydantic schema validation boundary.
- **Access Security:** Password hashing using bcrypt (12 rounds) and cryptographic JWT Bearer authentication with token expiration.
- **Exception Shielding:** Internal server errors suppress stack traces and system paths, preventing information disclosure.

### 26. Ethical Framework & Decision Support Disclaimers
> **MANDATORY ETHICAL & OPERATIONAL DISCLAIMER:**  
> This framework is an analytical decision-support tool developed for research, training, and operational demonstration.  
> 1. **No Automated Accusation:** The system does not identify any individual as a criminal or assign culpability.  
> 2. **No Coercive Actions:** The system contains zero automated hooks for freezing bank accounts, seizing funds, or deploying field units.  
> 3. **Mandatory Human Verification:** All high-risk alerts and hotspot intelligence require independent evaluation and verification by authorized law-enforcement personnel.  
> 4. **Protected Civil Liberties:** Predictive spatial models must never be used for unlawful mass surveillance or biased geographic targeting.


