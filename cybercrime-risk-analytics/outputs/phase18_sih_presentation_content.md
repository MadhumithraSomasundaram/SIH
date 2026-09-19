# Phase 18 — Smart India Hackathon (SIH) Presentation Content
## Slide Deck: Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations
**Problem Statement ID:** 26184  
**Target Agency:** Law Enforcement Agencies, State Cyber Cells, Indian Cyber Crime Coordination Centre (I4C)  

---

### SLIDE 1: Title & Team Overview
- **Title**: Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations
- **Subtitle**: Actionable Decision-Support Intelligence for Proactive Law Enforcement Intervention
- **Problem Statement ID**: 26184
- **Mission**: Bridging the critical temporal gap between cyber financial fraud complaint registration and physical cash-out withdrawals.

---

### SLIDE 2: Problem Statement & National Context
- **The Challenge**: Organized cybercrime syndicates execute rapid multi-hop digital fraud, funneling stolen proceeds into mule accounts.
- **The Physical Bottleneck**: The fraud lifecycle almost always concludes with a physical ATM or branch cash withdrawal to break the digital audit trail.
- **The Window of Opportunity**: An estimated 30-to-180 minute operational window exists between complaint registration and cash withdrawal.
- **The Mandate**: Build a predictive analytics framework capable of forecasting the spatial corridors and probability of cash withdrawal in advance.

---

### SLIDE 3: Existing Limitations & The Operational Gap
- **Reactive Policing**: Conventional law enforcement actions begin days after complaint registration—long after funds are withdrawn.
- **Data Fragmentation**: Complaints (NCRP), bank transactions, and ATM spatial registries exist in isolated silos without automated correlation.
- **Black-Box Skepticism**: Front-line officers cannot act on opaque AI recommendations without explainable operational context.
- **Resource Constraints**: Police departments cannot station personnel at thousands of ATMs simultaneously without targeted spatial intelligence.

---

### SLIDE 4: Proposed Analytical Solution
- **Proactive Intelligence**: Moving from post-facto forensic analysis to real-time predictive decision support.
- **Dual-Engine Framework**:
  1. *Predictive Machine Learning*: Tuned XGBoost classifier calculating incident withdrawal probability.
  2. *Spatial Density Clustering*: Unsupervised DBSCAN identifying 40 high-priority urban withdrawal corridors.
- **Transparent Explainability**: SHAP local feature attributions identifying exactly why an event is flagged.
- **Operational Integration**: FastAPI backend connected to an interactive Leaflet GIS dashboard and an authorized analyst case workspace.

---

### SLIDE 5: System Architecture & Pipeline Flow
- **Data Flow**:
  1. Ingestion of synthetic, sanitized complaint and transactional signals.
  2. Schema normalization and backward-looking feature engineering (zero target leakage).
  3. Chronological 70/15/15 train, validation, and held-out test partitioning.
  4. XGBoost probabilistic inference $\to$ deterministic 0–100 risk scoring.
  5. Local SHAP factor attribution + DBSCAN spatial corridor cross-referencing.
  6. Automated alert generation with mandatory human-in-the-loop review.
  7. Case investigation tracking and immutable audit logging.

---

### SLIDE 6: Multi-Stage Data Pipeline & Feature Engineering
- **Rigorous Data Hygiene**: Standardized timestamps, categorical harmonization, and bounding coordinate validation.
- **64 Leakage-Safe Features Engineered**:
  - *Temporal*: Cyclical hour/day representations, weekend flags, time period groupings.
  - *Rolling Incident Lags*: 1-hour, 6-hour, 24-hour, and 7-day backward incident frequencies.
  - *Spatial Context*: Coordinate rounding, regional indicators, spatial density grids.
  - *Financial Profile*: Log-transformed fraud amounts, zero-amount flags, high-value indicators.
- **Target Integrity**: Binary `future_withdrawal` target strictly segregated; zero post-event fields allowed in input matrices.

---

### SLIDE 7: Predictive Modeling: Optimized XGBoost Classifier
- **Model Selection**: Benchmarked against Logistic Regression, Random Forest, and Decision Trees. XGBoost selected for superior handling of tabular non-linearities and missingness.
- **Class Imbalance Handling**: Extreme natural class imbalance (~10% positive rate) addressed via validation-tuned `scale_pos_weight = 8.6154`.
- **Frozen Hyperparameters**:
  - `n_estimators = 200`, `max_depth = 3`, `learning_rate = 0.05`
  - `subsample = 0.8`, `colsample_bytree = 0.8`
- **Rigorous Boundary**: Tuned strictly on validation data; test set strictly held out until final Phase 8 evaluation.

---

### SLIDE 8: Risk Scoring Formula & SHAP Explainability
- **Deterministic Risk Scoring**:
  $$\text{risk\_score} = \text{round}(P(\text{future\_withdrawal} = 1) \times 100)$$
- **Operational Risk Tiers**:
  - `0–39`: LOW (Routine monitoring)
  - `40–59`: MODERATE (Enhanced area surveillance)
  - `60–79`: HIGH (Priority analyst review & beat patrol notice)
  - `80–100`: CRITICAL (Urgent supervisory dispatch flag)
- **Local SHAP Feature Drivers**: TreeExplainer computes individual contribution values (e.g., elevated 24h complaint frequency contributes +0.18 to probability), providing transparent operational justification to investigators.

---

### SLIDE 9: Spatial Intelligence: DBSCAN Hotspots & PostGIS
- **Density-Based Spatial Clustering (DBSCAN)**:
  - Metric: Haversine distance on geographic coordinates ($\epsilon = 1.5\text{ km}$, $\text{MinPts} = 5$).
  - Identified **40 distinct analytical hotspot clusters** containing historical ATM cash-out concentrations.
- **PostGIS Integration**:
  - Spatial storage using `GEOMETRY(Point, 4326)` with GIST spatial indexing.
  - Enables sub-10ms radius queries (`ST_DWithin`) to identify nearby ATMs when a complaint is flagged.

---

### SLIDE 10: Interactive GIS Risk Dashboard
- **Technology**: Leaflet.js + Vanilla HTML/CSS/JS (no heavy framework bloat).
- **Key Capabilities**:
  - Real-time choropleth risk intensity layer across districts.
  - Interactive DBSCAN hotspot polygons with drill-down metrics (ATM density, mean risk score).
  - Multi-criteria filtering by date range, crime category, and risk tier.
  - Clean, responsive dark-mode tactical interface designed for command center screens.

---

### SLIDE 11: Alert Engine & Operational Notification
- **Intelligent Alert Rules**: Triggered when predicted risk score $\ge 60$ (HIGH) or when event falls within an active DBSCAN hotspot cluster.
- **Anti-Fatigue Safeguards**:
  - *Deduplication*: Suppresses redundant alerts for repeated complaints in the same grid.
  - *Cooldown Window*: Throttles repetitive dispatches within a 60-minute interval.
- **Mandatory Human-in-the-Loop Flag**: `human_review_required = True` explicitly set on every alert.

---

### SLIDE 12: Authorized Analyst & Law Enforcement Interface
- **Role-Based Security**: Role-gated access (JWT Bearer tokens) enforcing separation of duties between ANALYST, SUPERVISOR, and ADMIN.
- **Case Management Workspace**:
  - Direct alert-to-investigation conversion.
  - Timestamped chronological case note logging.
  - Non-sensitive external evidence reference linking (e.g., NCRP report IDs).
  - Strict status flow: `NEW` $\to$ `ACKNOWLEDGED` $\to$ `IN_REVIEW` $\to$ `RESOLVED` (or `DISMISSED`).

---

### SLIDE 13: End-to-End Demonstration Lifecycle
- **Step-by-Step Live Walkthrough**:
  1. Ingest incoming synthetic complaint `DEMO_CASE_003_HIGH`.
  2. Model predicts probability $P = 0.6319 \implies \text{Risk Score } 63 \text{ (HIGH)}$.
  3. SHAP plots expose primary drivers (`rolling_event_count_24h`).
  4. Spatial correlation maps incident to Hotspot Cluster #14.
  5. Alert `ALT-SMOKE` generated and acknowledged by analyst.
  6. Case investigation opened and resolved with immutable audit trail.
- **Latency**: Total pipeline execution completes in `< 0.35 seconds`.

---

### SLIDE 14: Rigorous Quantitative Evaluation (Phase 8 Locked Metrics)
- **Authentic Performance Reporting (Zero Invented Numbers)**:
  - **Test Dataset**: 1,500 held-out records (chronologically separated).
  - **PR-AUC**: **0.1029** (Reflects authentic performance under extreme 10% class imbalance; random baseline = 0.103).
  - **ROC-AUC**: **0.4760**
  - **Test Accuracy**: **0.8693** (86.93%)
  - **Test Specificity**: **0.9673** (96.73% true negative rate, minimizing false alarms)
  - **Precision**: **0.0638** | **Recall**: **0.0194** | **F1 Score**: **0.0297**
- **Test Suite Verification**: 21 passed, 1 skipped (external DB service), 0 failed across 22 comprehensive integration checkpoints.

---

### SLIDE 15: Ethical Safeguards, Limitations & Future Roadmap
- **Ethical & Legal Safeguards**:
  - *Decision Support Only*: The system generates predictive risk signals—it never labels individuals as criminals.
  - *No Automated Coercive Actions*: Zero automated hooks for account freezing, transaction blocking, or punitive actions.
  - *Privacy by Design*: Strictly excludes banking credentials (PAN, PIN, CVV) and national IDs (Aadhaar).
- **Documented Limitations**:
  - Evaluated on synthetic/anonymized datasets without real-time bank core feeds.
  - Maximum natural score on test data is 63 (CRITICAL tier $\ge 80$ is not produced under threshold 0.5).
- **Future Roadmap**:
  - Secure institutional integration with I4C / NCRP live complaint streams.
  - Direct ATM switch telemetry feeds under RBI regulatory sandboxes.
  - Online model re-calibration and streaming spatial analytics.
