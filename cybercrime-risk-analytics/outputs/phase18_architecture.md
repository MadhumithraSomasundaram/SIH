# Phase 18 — System Architecture Document
## Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations
**Problem Statement ID:** 26184  
**Classification:** Analytical Decision-Support System  
**System Status:** Complete Integration & Verification  

---

## 1. High-Level Architecture Overview

The framework provides an end-to-end analytical pipeline transforming raw, anonymized complaint and transactional signals into prioritized geographic risk intelligence for authorized law enforcement and analyst decision support.

```
+-----------------------------------------------------------------------------------+
|                                  DATA SOURCES                                     |
|  Synthetic/Anonymized Complaints, Accounts, Transactions, Withdrawals, ATMs, Areas|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         PHASE 1: DATA INSPECTION & AUDIT                          |
|  Schema profiling, missingness checks, quality assessment, distribution analysis  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         PHASE 2: DATA CLEANING & HYGIENE                          |
|  Standardization, deduplication, timestamp formatting, coordinate normalization   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        PHASE 3: FEATURE ENGINEERING                               |
|  Temporal lags, rolling incident counts (1h/6h/24h/7d), spatial grids, aggregates|
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     PHASE 4: TARGET VARIABLE CREATION                             |
|  Binary future_withdrawal within temporal horizon (Strictly Leakage-Free)         |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|              PHASE 5: CHRONOLOGICAL TRAIN / VALIDATION / TEST SPLIT               |
|  70% Train (7,000) | 15% Validation (1,500) | 15% Test (1,500 Held-Out Protected) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        PHASE 6: BASELINE MODEL BENCHMARKING                       |
|  Logistic Regression, Random Forest, Rule-Based Baselines                         |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       PHASE 7: OPTIMIZED XGBOOST CLASSIFIER                       |
|  Tuned on Validation Set; scale_pos_weight=8.6154 handling severe class imbalance |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     PHASE 8: FINAL HELD-OUT TEST EVALUATION                       |
|  Locked Metrics: PR-AUC = 0.1029, ROC-AUC = 0.4760, Accuracy = 0.8693             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                    PHASE 9: RISK SCORING & CATEGORIZATION                         |
|  score = round(probability * 100) -> LOW (0-39), MODERATE (40-59),               |
|                                       HIGH (60-79), CRITICAL (80-100)             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                      PHASE 10: SHAP MODEL EXPLAINABILITY                          |
|  TreeExplainer local attribution: feature contributions, base value, directional   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                   PHASE 11 & 12: PREDICTION PIPELINE & FASTAPI                    |
|  REST Endpoints: /health, /model/info, /predict, /predict/batch, /explain         |
+-----------------------------------------------------------------------------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
                     v                                       v
+-----------------------------------------+ +---------------------------------------+
|     PHASE 13: POSTGRESQL / POSTGIS      | |    PHASE 14: DBSCAN SPATIAL CLUSTERING|
|  Spatial persistence, ST_DWithin, SRID  | |  Density-based hotspot identification |
|  4326 geometry, ATM location indexing   | |  Eps=1.5km, MinPts=5 -> 40 Hotspots   |
+-----------------------------------------+ +---------------------------------------+
                     |                                       |
                     +-------------------+-------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                      PHASE 15: GIS RISK DASHBOARD & MAP                           |
|  Interactive Leaflet visualization: Risk layer, Hotspot polygons, Filter controls |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     PHASE 16: ALERT ENGINE & NOTIFICATIONS                        |
|  Priority scoring, cooldown deduplication, mandatory human_review_required flag    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|            PHASE 17: AUTHORIZED LAW ENFORCEMENT & ANALYST INTERFACE               |
|  Investigation workspaces, case management, note logging, safe evidence linking   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|               PHASE 18: AUDIT TRAIL, INTEGRATION & DEMO READINESS                 |
|  Immutable audit logs, end-to-end test suite, system smoke tests, presentation    |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Differentiation and Responsibilities

To ensure analytical clarity and prevent architectural confusion, the functional boundaries of key subsystems are strictly demarcated:

| Subsystem | Primary Technique / Technology | Core Responsibility | What It DOES NOT Do |
|---|---|---|---|
| **Predictive Risk Signal** | XGBoost Classifier (`xgboost_cybercrime_model.pkl`) | Computes probability $P(\text{future\_withdrawal}=1 \mid X)$ based on historical temporal, spatial, and complaint signals. | Does not determine guilt, does not accuse persons, does not trigger punitive actions. |
| **Spatial Hotspot Detection** | DBSCAN Clustering (`scikit-learn`) | Unsupervised spatial density clustering grouping proximate historical complaint coordinates into geographic alert zones (40 clusters identified). | Does not predict future transactions independently; clusters past occurrences. |
| **Model Explainability** | SHAP (SHapley Additive exPlanations) | Generates local Shapley values identifying which features pushed risk higher or lower for a specific analytical record. | Does not evaluate ground truth or provide legal justification. |
| **Spatial Data Storage** | PostgreSQL 15+ with PostGIS | Manages geographic features using `GEOMETRY(Point, 4326)` with spatial indexing (`GIST`) and radius queries (`ST_DWithin`). | Does not perform inference or alerting logic directly. |
| **Application Backend** | FastAPI (`api.main:app`) | Provides low-latency, typed HTTP REST endpoints for single/batch prediction, explainability, alerts, and investigations. | Does not bypass human validation gates. |
| **Geographic Dashboard** | Leaflet.js + Vanilla JS/CSS | Renders interactive choropleth layers, cluster boundaries, ATM overlays, and threat indicators in browser. | Does not execute unauthenticated state mutations. |
| **Alert Engine** | Rule-Based Notification Engine | Filters high-risk predictions and spatial clusters, applying cooldown and deduplication windows. | Never triggers automatic account freezes or dispatch without analyst confirmation. |
| **Analyst Interface** | Role-Based Web Interface (JWT / Role auth) | Empowers authorized law enforcement analysts to inspect evidence, append case notes, and track lifecycle status. | Does not expose raw victim PII or sensitive banking credentials. |
| **Audit Trail** | Immutable Audit Table (`analyst_audit_log`) | Logs every analyst query, alert status update, note creation, and export with user ID and timestamp. | Records cannot be deleted or overwritten by analysts. |

---

## 3. Data Flow and Processing Pipeline

### Step 1: Input Ingestion & Sanitization
Complaint records arrive via authorized ingestion APIs. Inputs are validated using Pydantic schemas (`ComplaintInput`, `BatchComplaintInput`). Sensitive fields (e.g., raw account numbers, complainant names, phone numbers) are stripped or hashed before reaching the feature engine.

### Step 2: Feature Preparation & Lags
The feature engine computes:
- **Temporal components**: Hour group, day of week, cyclical sine/cosine time representations.
- **Rolling event aggregations**: 1-hour, 6-hour, 24-hour, and 7-day backward-looking incident frequencies.
- **Spatial grid references**: Latitude/longitude rounded to geographic cells to assess area density without micro-level overfitting.

### Step 3: Predictive Inference
The pre-trained XGBoost model (`Phase7_XGBoost_v1.0`) calculates the raw likelihood $P \in [0.0, 1.0]$. The risk score is derived deterministically:
$$\text{risk\_score} = \text{round}(P \times 100)$$

### Step 4: Risk Tiering & Alert Thresholds
- **LOW (0–39)**: Routine analytical monitoring.
- **MODERATE (40–59)**: Heightened area surveillance flag.
- **HIGH (60–79)**: Priority analyst queue; spatial correlation checks.
- **CRITICAL (80–100)**: Immediate supervisor review required; high priority alert banner.

### Step 5: Spatial Contextualization
The record coordinates are checked against the 40 DBSCAN-derived analytical hotspots (stored in GeoJSON / PostGIS). If the event falls within a known hotspot buffer, the composite analytical priority is escalated.

### Step 6: Human-in-the-Loop Review
Analyst logs into `/analyst`, inspects the generated alert, reviews local SHAP force plots explaining model rationale, attaches external case references, logs field verification notes, and advances status from `NEW` to `ACKNOWLEDGED` $\to$ `IN_REVIEW` $\to$ `RESOLVED` (or `DISMISSED`).

---

## 4. Ethical, Operational, and Legal Boundaries

1. **Analytical Decision Support Only**: This platform is explicitly designed to support resource allocation and patrol prioritization. It does not generate legal evidence of criminal liability.
2. **No Automated Coercive Actions**: The system contains zero automated hooks to freeze bank accounts, block ATM transactions, or dispatch armed units autonomously.
3. **Strict PII Protection**: Primary banking identifiers (PAN, CVV, PIN, raw passwords) are never ingested into feature matrices or exposed in the interface.
4. **Mandatory Human Accountability**: Every status transition and operational decision requires an authenticated human analyst signature recorded in the audit log.
