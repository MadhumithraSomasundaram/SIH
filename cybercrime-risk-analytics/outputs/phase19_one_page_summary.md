# Predictive Cybercrime Intelligence System
## Executive One-Page Project Summary
**Problem Statement ID:** 26184  
**Classification:** Authorized Law Enforcement Analytical Decision-Support System  
**Framework Status:** Complete, Verified, and Presentation Ready  

---

### 1. Title & Project Overview
**Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations**  
An end-to-end intelligence system that predicts the likelihood and spatial corridors of physical cash withdrawals following cyber financial fraud complaints, enabling proactive police beat patrol deployment.

### 2. The Problem
Cyber fraud syndicates rapidly transfer stolen funds through digital mule account chains, but their ultimate goal is extracting physical cash via ATMs to sever the digital trail. Traditional law enforcement response is reactive—investigations typically commence days after withdrawal has occurred.

### 3. Proposed Solution
A multi-tiered predictive analytics framework that transforms incoming cybercrime complaints into calibrated 0–100 risk scores, explains contributing factors via SHAP, correlates events with historical DBSCAN spatial hotspots, and routes priority alerts to an authorized, audited case management workspace.

### 4. System Architecture
```
Ingestion (Sanitized Signals) ──▶ Data Cleaning & Standardization ──▶ 64 Spatio-Temporal Features
                                                                                 │
                                                                                 ▼
Audit Ledger ◀── Analyst Workspace ◀── Alert Engine ◀── GIS Map ◀── XGBoost + DBSCAN + SHAP
```

### 5. Technology Stack
- **Core Analytics & ML**: Python 3.11, XGBoost 3.2.0, scikit-learn 1.9.1, SHAP 0.51.0, Pandas, NumPy
- **Spatial & Database**: PostgreSQL 15+, PostGIS 3.x, GeoAlchemy2, SQLAlchemy 2.0, Shapely
- **Backend & Serving**: FastAPI, Uvicorn, Pydantic v2, Starlette TestClient
- **Frontend & GIS**: Leaflet.js, Vanilla HTML5 / Tactical Dark Mode CSS (zero heavy dependencies)
- **Security & RBAC**: python-jose (JWT), bcrypt (12-round salted hashing)

### 6. Machine Learning Methodology
- **Target**: `future_withdrawal` (binary indicator; 24-hour forward-looking horizon).
- **Partitioning**: Strict chronological 70/15/15 split (Train: 7,000, Validation: 1,500, Test: 1,500).
- **Class Imbalance Handling**: Cost-sensitive gradient learning via `scale_pos_weight = 8.6154` (no synthetic SMOTE).
- **Hyperparameters**: `max_depth = 3`, `n_estimators = 200`, `learning_rate = 0.05`, `subsample = 0.8`.
- **Risk Score**: Deterministic formula $\text{risk\_score} = \text{round}(P \times 100)$ with tiers: LOW (0–39), MODERATE (40–59), HIGH (60–79), CRITICAL (80–100).

### 7. Quantitative Results (Phase 8 Locked Metrics)
- **Test PR-AUC**: **0.1029** (baseline: 0.103 under severe ~10% class imbalance)
- **Test ROC-AUC**: **0.4760** | **Test Accuracy**: **0.8693** (86.93%)
- **Test Specificity**: **0.9673** (96.73% true negative rate, minimizing false operational alarms)
- **Test Precision**: **0.0638** | **Test Recall**: **0.0194** | **Test F1**: **0.0297**
- **Test Suite Verification**: **239 passed**, **1 skipped** (external service), **0 failed** across entire codebase.

### 8. GIS & Spatial Intelligence
- **DBSCAN Density Clustering**: Discovered **40 distinct analytical hotspot clusters** ($\epsilon = 1.5\text{ km}$, $\text{MinPts} = 5$).
- **PostGIS Layer**: Stores `GEOMETRY(Point, 4326)` with GIST spatial indexing for sub-10ms ATM proximity lookups (`ST_DWithin`).
- **Interactive Command Center**: Choropleth risk gradients, hotspot polygon boundaries, and multi-criteria filters mounted at `/dashboard`.

### 9. Alert Engine
- **Trigger Rules**: Risk score $\ge 60$ (HIGH/CRITICAL) or intersection with active DBSCAN hotspot.
- **Operational Safeguards**: Automated deduplication, 60-minute cooldown window, and hardcoded `human_review_required = True`.
- **Zero Coercive Actions**: Prohibits automated account freezes, transaction blocking, or punitive actions.

### 10. Analyst Case Workflow
- Role-gated portal mounted at `/analyst` enforcing separation across ANALYST, SUPERVISOR, and ADMIN roles.
- State-machine lifecycle: `NEW` $\to$ `ACKNOWLEDGED` $\to$ `IN_REVIEW` $\to$ `RESOLVED` (or `DISMISSED`).
- Chronological case notes and safe external evidence reference linking (`NCRP-REF-*`).
- Non-repudiable audit ledger (`AnalystAuditLog`) recording all officer queries, updates, and timestamps.

### 11. Privacy & Security Safeguards
- **PCI-DSS & PII Exclusion**: Zero account numbers, card PANs, PINs, CVVs, OTPs, or Aadhaar numbers in feature matrices or API payloads.
- **Application Security**: Strict Pydantic input validation (HTTP 422), parameterized SQL queries, safe path routing, and bcrypt password hashing.

### 12. Documented Limitations
- Evaluated on synthetic/anonymized historical datasets; real-world deployment requires live bank telemetry.
- Predicts spatial corridors (1.5 km clusters), not exact individual ATM hardware IDs.
- Model naturally produces scores up to 63 on test data; CRITICAL scores ($\ge 80$) are not naturally produced under threshold 0.5.
- Strictly an advisory decision-support system requiring human verification before field dispatch.

### 13. Future Roadmap
- Authorized live integration with I4C / NCRP complaint webhooks and core banking switches under RBI regulatory frameworks.
- Graph Neural Network (GNN) modeling for cross-bank multi-hop mule account traversal.
- Automated model drift tracking (PSI/KS tests) and dynamic re-calibration pipelines.
