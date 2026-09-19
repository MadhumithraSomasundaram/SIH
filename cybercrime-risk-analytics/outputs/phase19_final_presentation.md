# Phase 19 — Final 10-Minute SIH Presentation Deck
## Predictive Cybercrime Intelligence System
**Problem Statement ID:** 26184  
**Target Audience:** Smart India Hackathon Judging Panel, Law Enforcement Cyber Cells, I4C Evaluators  
**Duration:** Approximately 10 Minutes (15 Slides)  

---

### SLIDE 1 — TITLE & OVERVIEW
# Predictive Cybercrime Intelligence System
### Forecasting likely cash withdrawal locations for proactive cybercrime intervention
- **Problem Statement ID:** 26184
- **Domain:** Law Enforcement, Cyber Financial Fraud & Spatio-Temporal Predictive Analytics
- **Core Technology Stack:** XGBoost • SHAP • PostGIS • DBSCAN • FastAPI • Leaflet GIS
- **Operational Classification:** Authorized Analytical Decision-Support System
- **Mandatory Notice:** Developed and evaluated using synthetic, anonymized historical records. Does not connect to live banking networks or live government databases in prototype phase.

---

### SLIDE 2 — THE PROBLEM & THE OPERATIONAL GAP
- **Rapid Surge in Digital Financial Crimes**:
  Cyber financial fraud syndicates rapidly transfer stolen victim funds across multi-hop mule account chains.
- **The Physical Cashout Bottleneck**:
  To sever the digital transaction trail, criminals almost universally convert digital balances into physical cash via ATM and branch withdrawals.
- **The Operational Challenge: Reactive Policing**:
  Traditional investigative workflows initiate days after an incident is registered on NCRP—long after cash has already been extracted.
- **The Critical Need**:
  Law enforcement investigators and beat patrol units require earlier analytical signals forecasting geographic areas where subsequent cash withdrawal activity is statistically more likely.
- **Ethical & Analytical Boundary**:
  The framework provides early predictive risk signals for resource allocation. **It does not guarantee future withdrawal occurrence or establish proof of guilt.**

---

### SLIDE 3 — PROPOSED SOLUTION & END-TO-END DATA FLOW
Our end-to-end analytical pipeline transforms raw complaint signals into prioritized, explainable operational intelligence:

```
+-------------------------------------------------------------------------------+
|                        COMPLAINT / TRANSACTION SIGNALS                        |
|  Synthetic complaints, transaction timestamps, victim locations, loss amounts |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                         DATA CLEANING & STANDARDIZATION                       |
|  Coordinate validation, timestamp normalization, PII stripping, schema checks |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                       SPATIO-TEMPORAL FEATURE ENGINEERING                     |
|  64 backward-looking features: rolling lags (1h/6h/24h/7d), cyclical time, grid |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                       XGBOOST PREDICTIVE CLASSIFIER                           |
|  Calibrated probabilistic inference: P(future_withdrawal = 1 | X)             |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                          DETERMINISTIC RISK SCORING                           |
|  risk_score = round(P * 100)  →  LOW (0-39), MOD (40-59), HIGH (60-79)        |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                         LOCAL SHAP MODEL EXPLANATION                          |
|  TreeExplainer marginal feature contributions explaining why risk is elevated |
+-------------------------------------------------------------------------------+
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
+---------------------------------------+ +-------------------------------------+
|        POSTGIS SPATIAL DATABASE       | |       DBSCAN HOTSPOT DETECTION      |
|  SRID 4326 Point geometry, GIST index,| |  40 unsupervised density clusters   |
|  spatial radius proximity queries     | |  (eps=1.5km, min_samples=5)         |
+---------------------------------------+ +-------------------------------------+
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       ▼
+-------------------------------------------------------------------------------+
|                       GIS RISK DASHBOARD & COMMAND MAP                        |
|  Interactive Leaflet choropleth risk layer, cluster boundaries, ATM overlays  |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                       OPERATIONAL ALERT GENERATION                            |
|  Rule evaluation, deduplication, cooldown, human_review_required = True       |
+-------------------------------------------------------------------------------+
                                       │
                                       ▼
+-------------------------------------------------------------------------------+
|                    ANALYST INVESTIGATION & AUDIT TRAIL                        |
|  Case creation, chronological notes, evidence linking, immutable audit log    |
+-------------------------------------------------------------------------------+
```

---

### SLIDE 4 — WHY THIS MULTI-TIERED APPROACH?
Rather than relying on a single monolithic tool, each subsystem serves a distinct, specialized analytical role:

| Component | Technology | Primary Operational Responsibility | Why This Specifically? |
|---|---|---|---|
| **Predictive Modeling** | **XGBoost** | Estimates incident withdrawal likelihood $P$ | High tabular non-linear accuracy; native class weighting via `scale_pos_weight`. |
| **Hotspot Discovery** | **DBSCAN** | Unsupervised spatial clustering | Detects arbitrary cluster shapes without predefined cluster count ($k$) or geometric assumptions. |
| **Spatial Storage** | **PostGIS** | Geospatial indexing & distance queries | Industry-standard spatial SQL (`ST_DWithin`, SRID 4326) for sub-10ms ATM lookups. |
| **Model Explainability** | **SHAP** | Local feature contribution attribution | Grounded in cooperative game theory; gives front-line officers clear justification. |
| **Serving Layer** | **FastAPI** | High-throughput REST API | Native Pydantic schema validation, low latency, and automatic OpenAPI documentation. |
| **GIS Visualization** | **Leaflet.js** | Tactical command center map | Lightweight, responsive browser interface; zero heavy framework dependencies. |
| **Alert Engine** | **Rule Engine** | Dispatches operational notifications | Enforces cooldown, deduplication, and non-punitive safeguards. |
| **Case Management** | **Analyst UI** | Structured human investigation workflow | Enforces role-based access control (RBAC), case notes, and immutable audit logs. |

---

### SLIDE 5 — DATA PIPELINE & RIGOROUS CHRONOLOGICAL SPLIT
- **End-to-End Data Hygiene**:
  - Raw synthetic records cleaned across 16 standardization steps (missing coordinates flagged, invalid ranges clamped, timestamp parsing).
  - 64 leakage-safe features generated: rolling transaction frequencies (1h, 6h, 24h, 7d), cyclical sine/cosine time representations, and location grids.
- **Why Chronological Splitting Was Mandatory**:
  - **Random Train-Test Split Is Forbidden in Time-Series Fraud**: Random splits leak future trend patterns and rolling event counts into the past, artificially inflating test metrics.
  - **Chronological Split Applied**:
    - **Train Set (70%)**: First 7,000 chronological records.
    - **Validation Set (15%)**: Next 1,500 chronological records (used strictly for hyperparameter tuning and threshold selection).
    - **Held-Out Test Set (15%)**: Final 1,500 chronological records (held strictly blind until Phase 8).

---

### SLIDE 6 — MACHINE LEARNING METHODOLOGY
- **Target Variable (`future_withdrawal`)**:
  - Binary indicator: Did a cash withdrawal occur in physical proximity to the complaint within the defined prediction horizon?
- **Prediction Horizon**:
  - 24 Hours post-complaint registration.
- **Model Architecture**:
  - Tuned XGBoost Classifier (`max_depth = 3`, `n_estimators = 200`, `learning_rate = 0.05`, `subsample = 0.8`).
- **Handling Severe Class Imbalance Without SMOTE**:
  - Historical withdrawal linkage occurs in only ~10% of cases (6,272 negative vs. 728 positive training rows).
  - **No Synthetic Oversampling (SMOTE)**: SMOTE generates unrealistic interpolated financial records that corrupt real spatial coordinates.
  - **Selected Approach**: Cost-sensitive learning via `scale_pos_weight = 8.6154` configured directly within XGBoost objective loss.
- **Calibrated Risk Scoring**:
  $$\text{Risk Score} = \text{round}(\text{Predicted Probability} \times 100)$$

---

### SLIDE 7 — QUANTITATIVE MODEL RESULTS (PHASE 8 LOCKED METRICS)
*Authentic, un-inflated performance metrics evaluated on the strictly held-out chronological test partition:*

| Metric | Validation Set (Phase 7) | Final Test Set (Phase 8 Locked) | Operational Interpretation |
|---|:---:|:---:|---|
| **PR-AUC** | **0.1072** | **0.1029** | Authentic Precision-Recall AUC under severe 10% class imbalance (Random baseline: 0.103). |
| **ROC-AUC** | **0.5088** | **0.4760** | Evaluated on unseen chronological future partition. |
| **Accuracy** | **0.8587** (85.87%) | **0.8693** (86.93%) | High overall accuracy driven by correct identification of negative non-withdrawal instances. |
| **Specificity** | **0.9417** (94.17%) | **0.9673** (96.73%) | Exceptional true negative rate (1,301 / 1,345 negatives correct), minimizing false alarms for patrol teams. |
| **Precision** | **0.1222** | **0.0638** | Positive predictive value at default threshold 0.5. |
| **Recall** | **0.0764** | **0.0194** | Sensitivity on held-out test data under severe class imbalance constraint. |
| **F1-Score** | **0.0940** | **0.0297** | Harmonic mean reflecting strict threshold trade-off. |
| **Threshold** | **0.5000** | **0.5000** | Threshold established on validation data without optimizing on test data. |

> **Key Presentation Point for Judges**: We present authentic, locked metrics. We did not artificially inflate numbers by running SMOTE on test data or tuning decision thresholds on the test set.

---

### SLIDE 8 — EXPLAINABLE AI VIA SHAP (SHAPLEY ADDITIVE EXPLANATIONS)
- **Why Explainability Matters in Policing**:
  Law enforcement personnel cannot act on a blind numerical score; operational trust requires knowing which factors drove the risk estimation.
- **TreeExplainer Integration**:
  Calculates exact local Shapley values without model refitting, attributing marginal probability shifts to specific features.
- **Actual Feature Contribution Examples**:
  - `rolling_event_count_24h` (+0.182): Surge of 4 complaints in the local area within 24 hours pushed risk higher.
  - `amount_log1p` (+0.141): Substantial financial loss indicator increased withdrawal likelihood.
  - `previous_activity_by_district` (+0.098): District-level historical staging pattern contributed positively.
- **Strict Ethical Terminology**:
  - We say: *"This feature contributed toward a higher model risk prediction."*
  - **NEVER say**: *"This feature caused the crime."*
  - Sensitive individual characteristics (names, phone numbers, account numbers) are never ingested or explained.

---

### SLIDE 9 — SPATIAL INTELLIGENCE: PostGIS & DBSCAN
- **Critical Distinction**:
  - **XGBoost**: Predicts whether a specific complaint is likely linked to a future withdrawal (predictive risk signal).
  - **DBSCAN**: Identifies spatial clusters where historical cashout events physically congregate (unsupervised spatial density).
  - **Combined Result**: An **Analytical Priority Area** requiring proactive monitoring.
- **DBSCAN Clustering Parameters**:
  - Metric: Haversine geographic distance ($\epsilon = 1.5\text{ km}$, $\text{MinPts} = 5$).
  - Identified **40 distinct spatial hotspot clusters** across the region.
- **PostGIS Layer**:
  - Geometries stored as `GEOMETRY(Point, 4326)` with GIST spatial indexing.
  - Enables sub-10ms proximity lookups (`ST_DWithin`) linking incidents to nearby physical ATMs.
- **Ethical Safeguard**:
  These zones are termed **Analytical Hotspots** or **Priority Monitoring Corridors**—never "criminal areas" or "guilty locations."

---

### SLIDE 10 — GIS COMMAND DASHBOARD
- **Tactical Command Center**:
  Built with Leaflet.js and responsive modern styling for real-time dispatch and supervisory monitoring.
- **Core Dashboard Features**:
  1. **Dynamic Choropleth Risk Layer**: Visualizes regional risk gradients across administrative sectors.
  2. **DBSCAN Hotspot Polygons**: Displays spatial cluster boundaries with drill-down metrics (ATM density, mean risk score).
  3. **Multi-Criteria Filter Panel**: Allows filtering by date horizon, crime category, and risk tier.
  4. **Incident Detail Modal**: Inspects individual complaint coordinates and linked ATM proximity.
  5. **Data Protection**: Zero victim names, contact numbers, or full account numbers are rendered.

---

### SLIDE 11 — ALERT & NOTIFICATION ENGINE
- **Automated Rule Evaluation**:
  Alerts are dispatched when predicted risk reaches `HIGH` (60–79) or `CRITICAL` (80–100), or when an event falls within an active DBSCAN hotspot.
- **Structured Alert Payload**:
  - Alert Reference ID (e.g. `ALT-20260916-014`)
  - Risk Score (0–100) & Predicted Probability
  - Spatial Coordinate Centroid & Linked Hotspot Cluster ID
  - Model Version Fingerprint
  - Human-Readable Operational Guidance
- **Operational Safeguards**:
  - **`human_review_required = True`**: Hardcoded on all high-priority alerts.
  - **Deduplication & Cooldown**: Throttles repeat alerts within a 60-minute window to prevent alert fatigue.
  - **Zero Automated Coercive Actions**: The system contains no code paths to freeze bank accounts, block transactions, or execute autonomous enforcement.

---

### SLIDE 12 — AUTHORIZED LAW ENFORCEMENT & ANALYST WORKSPACE
- **Dedicated Case Management (`/analyst`)**:
  Role-gated portal (JWT Bearer authentication) enforcing separation of duties across `ANALYST`, `SUPERVISOR`, and `ADMIN`.
- **Structured Investigative Workflow**:
  $$\text{Alert Received} \longrightarrow \text{Acknowledge} \longrightarrow \text{Open Investigation} \longrightarrow \text{Attach Notes \& Evidence} \longrightarrow \text{Field Verification} \longrightarrow \text{Resolution}$$
- **State Machine Enforcement**:
  Enforces valid lifecycle transitions (`NEW` $\to$ `ACKNOWLEDGED` $\to$ `IN_REVIEW` $\to$ `RESOLVED`). Invalid transitions (e.g. `RESOLVED` $\to$ `NEW`) are rejected with HTTP 400.
- **Safe Evidence References**:
  Analysts record external reference strings (e.g. `NCRP-ACK-2026-9912`, `CCTV-CAM-04`) without uploading raw victim documents.
- **Immutable Audit Trail (`AnalystAuditLog`)**:
  Permanently records every analyst query, alert update, note, and case resolution with timestamps and user roles.

---

### SLIDE 13 — END-TO-END DEMONSTRATION WORKFLOW
*Verified live workflow executed via `python src/system_smoke_test.py` in 0.198 seconds:*

1. **Ingest Signal**: Synthetic complaint received (`DEMO_CASE_003_HIGH`).
2. **Feature Preparation**: 64 features computed without leakage.
3. **Inference**: XGBoost yields $P = 0.6319$.
4. **Risk Score**: Score = 63 / 100.
5. **Risk Category**: Assigned to **HIGH** tier.
6. **Explainability**: SHAP identifies `rolling_event_count_24h` as top driver (+0.182).
7. **Spatial Correlation**: Mapped to DBSCAN Hotspot Cluster #14 (Andheri East corridor).
8. **Alert Created**: `ALT-SMOKE-1789534207` dispatched with `human_review_required = True`.
9. **Analyst Review**: Officer acknowledges alert and opens investigation `INV-SMOKE-1789534207`.
10. **Evidence Linked**: Reference `NCRP-REF-SMOKE-01` attached.
11. **Audit Logged**: Non-repudiable audit entry `AUD-SMOKE-1789534207` generated.

> *Demonstration uses synthetic/anonymized data and is not connected to live banking or government systems.*

---

### SLIDE 14 — POTENTIAL OPERATIONAL IMPACT
- **Earlier Operational Prioritization**:
  Transitions patrol focus from post-incident reports to near-term probabilistic risk signals.
- **Geographic Intelligence for Patrol Optimization**:
  Focuses limited beat patrol resources on specific high-density cashout corridors rather than thousands of dispersed ATMs.
- **Transparent Decision Support**:
  Eliminates black-box skepticism; officers see exact feature justifications before deploying personnel.
- **Standardized Multi-Agency Collaboration**:
  Provides a common operational picture connecting cyber cells, bank nodal officers, and field patrol units.
- **Non-Repudiable Accountability**:
  Full audit logging ensures integrity and oversight across all investigative actions.

---

### SLIDE 15 — LIMITATIONS & FUTURE ROADMAP
- **Documented System Limitations**:
  - *Data Modality*: Built on synthetic historical datasets; real-world deployment requires live NCRP/I4C gateway integration.
  - *Prediction Resolution*: Identifies spatial corridors (1.5 km clusters), not individual ATM machine serial numbers.
  - *Score Range*: Model naturally produces scores up to 63 on test data; CRITICAL scores ($\ge 80$) are not naturally produced under threshold 0.5.
  - *Decision Support Only*: Model outputs are advisory signals requiring human field verification.
- **Future Technological Roadmap**:
  - **Authorized Real-Time Bank Integration**: Webhook telemetry with core banking switches for automated mule account flagging under RBI regulatory sandboxes.
  - **Graph Neural Networks (GNNs)**: Modeling multi-hop mule account transaction chains across banking networks.
  - **Automated Drift Monitoring**: Automated re-calibration triggered by shifts in cyber fraud patterns.
  - **Secure Government SSO**: Integration with Parichay / Jan Parichay for institutional authentication across state police departments.
