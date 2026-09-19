# Smart India Hackathon 2026 — Master Presentation Deck Specification

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Audience:** Smart India Hackathon Grand Finale Technical Jury & Police Observers  
**Target Duration:** 8 to 10 Minutes (12 Slides)  
**Tone:** Technically Rigorous, Empirically Grounded, Operationally Realistic

---

### SLIDE 1: Title & Project Identification
- **Slide Title:** Cybercrime Predictive Analytics Framework (PS ID: 26184)
- **Subtitle:** *Forecasting Physical Cashout Corridors to Enable Timely Law Enforcement Interdiction*
- **Main Bullet Points:**
  - Problem Statement ID: 26184
  - Theme: Smart Automation & Law Enforcement Intelligence
  - Submitter: Team Antigravity (SIH 2026)
  - Core Focus: Bridging the 4-Hour Cashout Window via Predictive ML and Geospatial Clustering
- **Suggested Visual:** Framework composite banner showing the Command Center GIS map and real-time alert feed.
- **Speaker Notes:** *"Respected jury members, today we present an end-to-end predictive analytics framework designed for Problem Statement 26184. Our mission is simple: interdict cyber financial fraud before stolen citizen money disappears into untraceable cash at physical ATMs."*
- **Evidence Required:** Project repository checkpoint and active OpenAPI interface.
- **Claims to Avoid:** Do not claim deployment across all police stations in India.

---

### SLIDE 2: Problem Background — The "Cashout Window"
- **Slide Title:** Problem Background: The Critical Cashout Gap
- **Main Bullet Points:**
  - Citizen reporting delay: 1 to 4 hours post-incident.
  - Money mule extraction velocity: ATM cashouts occur within 60 to 180 minutes.
  - Traditional response is purely post-mortem: bank transaction records arrive days after cash is gone.
  - Physical ATM withdrawal is the syndicate's single physical point of vulnerability.
- **Suggested Visual:** Timeline diagram comparing citizen delay, bank reporting lag, and mule withdrawal velocity.
- **Speaker Notes:** *"Digital ledger hops happen in milliseconds, but physical cash withdrawal requires a physical runner at a physical ATM. Our entire framework targets this critical physical cashout bottleneck."*
- **Evidence Required:** NCRP crime report statistics and banking flow research.
- **Claims to Avoid:** Do not claim that cybercrime can be completely eliminated overnight.

---

### SLIDE 3: Existing Operational Challenges
- **Slide Title:** Operational Bottlenecks in Current Cyber Triage
- **Main Bullet Points:**
  - Overwhelming volume: Thousands of incoming cyber complaints daily.
  - High noise-to-signal ratio: Inability to instantly flag imminent high-loss extractions.
  - Inter-agency friction: Police analysts and bank fraud desks operate in isolated silos.
  - Black-box opacity: Officers refuse to dispatch patrol units without explainable justifications.
- **Suggested Visual:** Split diagram: Traditional siloed investigative lag vs. Proactive unified triage.
- **Speaker Notes:** *"Police triage officers are inundated. Without automated risk scoring, spatial clustering, and inter-agency coordination, patrol teams cannot arrive before mules complete their withdrawals."*
- **Evidence Required:** Phase 1 and Phase 12 investigative audit reports.
- **Claims to Avoid:** Do not criticize police personnel; focus on technological limitations of legacy workflows.

---

### SLIDE 4: Proposed Solution Overview
- **Slide Title:** Proposed Solution: Unified Predictive Intelligence Platform
- **Main Bullet Points:**
  - Real-Time Intake: Raw complaint feature derivation in 14.2 milliseconds.
  - Machine Learning Engine: Calibrated XGBoost classifier forecasting 24-hour cashout propensity.
  - Transparent AI: Local SHAP attribution detailing exact risk factors per complaint.
  - Geospatial Corridors: DBSCAN clustering mapping candidate ATM clusters within 5km radii.
  - Inter-Agency Portals: Dedicated, role-separated workspaces for Police Analysts and Bank Officers.
- **Suggested Visual:** High-level solution workflow icon diagram from complaint to field dispatch.
- **Speaker Notes:** *"We do not build another static dashboard. We built an active intelligence engine that derives 64 features in 14ms, computes risk probability, matches nearest ATM hotspots, and triggers coordinated banking and field responses."*
- **Evidence Required:** End-to-end integration test results (`outputs/phase13_e2e_workflow_results.json`).
- **Claims to Avoid:** Do not claim the system automatically arrests suspects.

---

### SLIDE 5: System Architecture & Dual-Mode Persistence
- **Slide Title:** Modular 3-Tier Architecture & Dual Persistence
- **Main Bullet Points:**
  - Presentation Tier: Vanilla HTML5/CSS3/JS with Leaflet 1.9.4 maps (zero-build, instant load).
  - Controller Tier: Asynchronous FastAPI gateway with strict Pydantic v2 schemas.
  - Dual Persistence Architecture:
    - `CSV_FALLBACK_DEV` (Active): Resilient offline mode with atomic threadlocks and zero dependencies.
    - `POSTGRESQL_POSTGIS` (Enterprise Target): Packaged DDL with GiST spatial indexing.
  - Automatic fault detection: Server dynamically routes traffic without fatal crashes.
- **Suggested Visual:** Mermaid 3-tier architecture diagram (`FINAL_SYSTEM_ARCHITECTURE.md`).
- **Speaker Notes:** *"Notice our architecture's built-in resilience: if PostgreSQL is disconnected, the system auto-detects the state and routes all operations to CSV fallback mode. Zero downtime, 100% operational continuity."*
- **Evidence Required:** `database/connection.py` health check output (`storage_mode: CSV_FALLBACK_DEV`).
- **Claims to Avoid:** Do not claim PostgreSQL is running when operating in CSV fallback.

---

### SLIDE 6: Data Engineering & Chronological Split
- **Slide Title:** Data Processing & Leakage-Free Temporal Splitting
- **Main Bullet Points:**
  - 10,000 synthetic complaints, 80,000 cashouts, 3,000 physical ATMs across India.
  - 64 derived features: cyclic time, transaction velocity ratios, spatial coordinates, amount categories.
  - Chronological Partitioning: Train (7,000, Jan-Jun), Val (1,500, Jun-Jul), Test (1,500, Jul-Aug 2026).
  - Strict leakage prevention: Preprocessors fitted strictly on training data; zero future look-ahead bias.
- **Suggested Visual:** Chronological timeline bar diagram showing temporal split boundaries.
- **Speaker Notes:** *"We adhere to the highest machine learning standards. Random cross-validation in temporal cyber fraud produces severe data leakage. We enforce strict chronological splits, freezing our preprocessors to mirror real-world deployment."*
- **Evidence Required:** `models/phase7_xgboost_metadata.json` and `src/temporal_split.py`.
- **Claims to Avoid:** Do not use real personal citizen data.

---

### SLIDE 7: ML Modeling & Explainable AI (SHAP)
- **Slide Title:** Predictive ML Pipeline & Local SHAP Attribution
- **Main Bullet Points:**
  - Pipeline: Scikit-learn `Pipeline` (`ColumnTransformer` + `XGBClassifier`).
  - Imbalance Mitigation: Calibrated thresholding and positive scale weights ($8.62$).
  - Verified Performance: PR-AUC 0.2248 (**2.17x above random**), Precision 29.14%, Recall 32.90%.
  - Local Explainability: Instant SHAP waterfall plots explaining the top positive and negative drivers.
- **Suggested Visual:** SHAP feature importance plot and sample local waterfall chart.
- **Speaker Notes:** *"Fraud data is heavily imbalanced (~10% positives). A naive model predicting zero gets 90% accuracy. We report honest PR-AUC of 0.2248 and 29% precision, backed by local SHAP explanations so officers know why an alert triggered."*
- **Evidence Required:** `FINAL_ML_MODEL_DOCUMENTATION.md` and `outputs/evaluation_metrics_v2.csv`.
- **Claims to Avoid:** Do not claim 99% accuracy; explain why precision/recall matter in fraud triage.

---

### SLIDE 8: Geospatial Clustering & ATM Proximity
- **Slide Title:** Geospatial DBSCAN Clustering & ATM Matching
- **Main Bullet Points:**
  - Spatial Density Algorithm: DBSCAN with $\varepsilon=500\text{ meters}$ and $\text{MinPts}=3$.
  - 40 Recurrent Hotspot Clusters: Discovered across historical withdrawal loci.
  - Vectorized Proximity Engine: Computes spherical Haversine distances to 3,000 ATMs in **2.4ms**.
  - Dynamic 5km Buffer Corridors: Identifies specific candidate ATM machines within the extraction zone.
- **Suggested Visual:** Leaflet map screenshot showing Chennai ATM clusters, heatmap overlay, and 5km circle.
- **Speaker Notes:** *"The model predicts cashout likelihood; our GIS engine answers 'where'. DBSCAN clusters past extraction corridors, while vectorized Haversine queries match nearby physical ATMs in under 3 milliseconds."*
- **Evidence Required:** `outputs/phase14_hotspots_geojson.geojson` and `GET /gis/predicted-locations`.
- **Claims to Avoid:** Do not claim to predict the exact GPS coordinate down to 1 millimeter.

---

### SLIDE 9: Portals, Alerts & Investigation Workflow
- **Slide Title:** Integrated Portals & Active Case Lifecycle
- **Main Bullet Points:**
  - Command Center (`/dashboard/`): High-level KPI metrics, heatmaps, and spatial corridor lines.
  - Analyst Workspace (`/analyst/`): Triage alert feed with 60-minute cooldown protection.
  - Active Case Management: Single-click promotion to investigation, chronological officer notes, evidence logging.
  - Banking Liaison Desk (`/bank/`): Institutional mule account hold orders and inter-agency collaboration.
- **Suggested Visual:** Screenshot grid showing Command Center, Alert Queue, and Case Management Drawer.
- **Speaker Notes:** *"We provide tailored interfaces: field commanders view regional heatmaps; detectives triage alerts and manage formal evidence; and banking officers issue immediate account freezes."*
- **Evidence Required:** Live frontend mounts at `/dashboard/`, `/analyst/`, and `/bank/`.
- **Claims to Avoid:** Do not show fake static mockups; show the real running web portals.

---

### SLIDE 10: Security, RBAC & Immutable Audit Trail
- **Slide Title:** Security, Privacy & Non-Repudiation Audit
- **Main Bullet Points:**
  - Zero Trust Access: Signed HS256 JWT tokens with 120-minute expiry; client tokens in `sessionStorage`.
  - Strict 4-Role RBAC: Complete isolation between `ANALYST`, `SUPERVISOR`, `ADMIN`, and `BANK_ANALYST`.
  - Inter-Agency Partitioning: Bank analysts strictly forbidden from police case files and evidence.
  - Immutable Audit Logging: Append-only log recording actor, timestamp, action, and SHA-256 hash.
- **Suggested Visual:** RBAC permission matrix and audit log entry format with SHA-256 hash.
- **Speaker Notes:** *"Security is foundational. Our banking liaison desk is cryptographically restricted from viewing police evidence, and every action—from login to outcome recording—is anchored in an immutable audit trail."*
- **Evidence Required:** `FINAL_SECURITY_AND_PRIVACY_DOCUMENTATION.md` and `outputs/phase17_analyst_audit_log.csv`.
- **Claims to Avoid:** Do not display raw passwords or API keys.

---

### SLIDE 11: Testing Verification & Honest Limitations
- **Slide Title:** Verification Scorecard & Known Limitations
- **Main Bullet Points:**
  - Test Suite Matrix: 68 / 68 automated assertions passed (**100% pass rate**).
  - Fast Inference: End-to-end dynamic complaint intake and prediction in **14.2 milliseconds**.
  - Honest Limitations:
    - Tabular propensity model; spatial localization uses empirical 5km corridors.
    - Currently running in local `CSV_FALLBACK_DEV` mode; PostgreSQL setup scripts packaged.
    - Demonstrations use synthetic data to protect citizen privacy.
- **Suggested Visual:** Phase 13 Test Scorecard graphic showing 100% pass rate across 8 suites.
- **Speaker Notes:** *"We believe in engineering honesty. We ran 68 automated tests across 8 suites with a 100% pass rate. We openly document our operational boundaries: our model predicts cashout likelihood, leaving spatial interdiction to our GIS engine."*
- **Evidence Required:** `PHASE_13_FINAL_TEST_SUMMARY.md`.
- **Claims to Avoid:** Do not claim 100% production readiness without noting PostgreSQL setup requirement.

---

### SLIDE 12: Future Roadmap & Hackathon Conclusion
- **Slide Title:** Future Roadmap & Conclusion
- **Main Bullet Points:**
  - Production Pilot: Integration with State Police CCTNS networks and NPCI freeze APIs.
  - Advanced GIS: Road-network routing (`pgRouting`) to predict vehicle transit times to ATMs.
  - Online Learning: Automated quarterly retraining via logged case outcome feedback.
  - Conclusion: A functional, mathematically sound framework transforming reactive triage into proactive interdiction.
- **Suggested Visual:** Future system roadmap timeline from hackathon prototype to national deployment.
- **Speaker Notes:** *"By uniting predictive machine learning, explainable AI, geospatial ATM intelligence, and banking interdiction, our framework bridges the cashout gap. We thank the jury and welcome your questions."*
- **Evidence Required:** `README.md` and repository checkpoint.
- **Claims to Avoid:** Do not claim that commercial contracts have already been signed.
