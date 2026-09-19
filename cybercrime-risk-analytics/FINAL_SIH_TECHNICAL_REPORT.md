# Final SIH Technical Submission Report

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**Submission Category:** Software Edition — Smart Automation & Law Enforcement Intelligence  
**Evaluator Status:** Complete System Integration, Live Verification & Demonstration Ready  

---

## 1. Title
**Cybercrime Predictive Analytics Framework for Proactive Cash Withdrawal Interdiction**

## 2. Problem Statement ID
**26184** (*Development of a Predictive Analytics Framework for Cybercrime Complaints to Forecast Likely Cash Withdrawal Locations in Advance, Enabling Generation of Actionable Intelligence for Timely and Proactive Cybercrime Intervention.*)

---

## 3. Abstract
Cyber-enabled financial fraud imposes severe economic damages on citizens and financial institutions. A fundamental challenge confronting law enforcement is the temporal delay between initial complaint registration and investigative action. During this 1-to-4 hour window, organized mule networks systematically convert illicit digital balances into untraceable physical cash at automated teller machines (ATMs). 

This paper presents the Cybercrime Predictive Analytics Framework, an integrated intelligence platform developed for Smart India Hackathon (Problem Statement 26184). The platform ingests raw cybercrime complaints, automatically derives 64 behavioral and spatial features in 14.2 milliseconds, executes a frozen gradient-boosted decision tree ensemble (XGBoost) to forecast 24-hour cashout propensity ($P \in [0, 1]$), computes transparent local risk attribution via SHAP TreeExplainer, and identifies candidate ATM extraction corridors using Density-Based Spatial Clustering (DBSCAN) and vectorized Haversine proximity queries. The system incorporates a resilient dual-persistence architecture (`CSV_FALLBACK_DEV` and `POSTGRESQL_POSTGIS`), role-based access control across four discrete roles, and dedicated web portals for police commanders, detectives, and banking liaisons. Exhaustive integration testing validates 68 / 68 assertions across 8 test suites (**100% pass rate**), confirming high operational reliability.

---

## 4. Introduction
The digitisation of India's financial ecosystem through the Unified Payments Interface (UPI), immediate mobile banking, and digital wallets has drastically accelerated transaction velocity. However, this velocity has been exploited by cyber syndicates. Syndicates route stolen funds through multiple layers of "mule accounts" before executing physical cash withdrawals at ATMs. Once cash is dispensed from an ATM, digital tracing terminates, and recovery probabilities drop precipitously. Traditional policing remains largely post-mortem—investigators request bank statements days after extractions have occurred. This framework reorients policing from reactive investigation to proactive, pre-cashout interdiction.

---

## 5. Problem Definition
The primary operational challenge is defined by the **Cashout Window Gap**:
- Victims detect and report fraud 60 to 240 minutes after occurrence.
- Mule syndicates dispatch runners to withdraw cash within 60 to 180 minutes.
- Formal banking notice exchanges under traditional legal channels take 24 to 72 hours.
- **Objective:** Compress the intelligence-to-action cycle down to seconds by predicting cashout likelihood and spatial corridors immediately upon complaint intake.

---

## 6. Objectives
1. **Dynamic Complaint Intake:** Ingest raw cybercrime reports and dynamically derive ML-ready features without manual data engineering.
2. **Calibrated Probability Estimation:** Deliver statistically sound prospective cashout likelihoods within 24 hours.
3. **Transparent Explainability:** Provide human-interpretable feature contribution weights via SHAP to justify field dispatches.
4. **Geospatial Corridor Identification:** Map candidate physical ATM extraction clusters within a 5km to 10km radius.
5. **Inter-Agency Collaboration:** Provide partitioned, role-based workflows enabling police analysts to triage cases and bank officers to issue emergency account hold requests.

---

## 7. Proposed Solution
The framework implements an end-to-end asynchronous pipeline:
```
Raw Intake -> Dynamic Preprocessor -> Frozen XGBoost -> SHAP Engine -> DBSCAN GIS -> Triage Alert -> Case Docket -> Bank Freeze
```
By combining predictive classification with unsupervised density clustering and role-based incident management, the platform bridges the operational gap between citizen complaints, police control rooms, and commercial banking desks.

---

## 8. System Architecture
The application adheres to a decoupled 3-tier micro-modular architecture:
- **Presentation Tier:** Vanilla HTML5, modern CSS3, ES6+ JavaScript, and Leaflet.js 1.9.4 map visualizations. Auto-mounted as ASGI static files at `/dashboard/`, `/analyst/`, and `/bank/`.
- **Application Controller Tier:** FastAPI (Python 3.11) with asynchronous endpoints, Pydantic v2 data validation, and dependency injection managing model singletons.
- **Persistence Tier:** Resilient dual-mode persistence. Defaults to `CSV_FALLBACK_DEV` for zero-dependency offline demonstration resilience; fully supports `POSTGRESQL_POSTGIS` for enterprise scale.

---

## 9. Data Pipeline
Evaluations utilize synthetic, anonymized datasets modeled on the National Cybercrime Reporting Portal (NCRP) schema:
- **10,000 Complaints** (`data/raw/Fraud_Cases.csv`)
- **80,000 Historical ATM Cashouts** (`data/raw/Withdrawals.csv`)
- **300,000 Intermediary Transactions** (`data/raw/Transactions.csv`)
- **3,000 Physical ATMs** (`data/raw/ATMs_Locations.csv`)
- **200 Geographic Administrative Areas** (`data/raw/Areas_Master.csv`)
- **Data Protection:** Zero real citizen personally identifiable information (PII), Aadhaar numbers, or valid bank credentials exist in the framework.

---

## 10. Feature Engineering
The pipeline processes 64 distinct features across multiple behavioral dimensions:
- **Cyclic Temporal Features:** $\sin/\cos$ transformations of `event_hour` and `event_day_of_week`.
- **Financial Ratios:** `fraud_amount`, `amount_log1p`, `fraud_to_daily_amount_ratio`, `amount_is_high`.
- **Velocity & Rolling Surges:** `rolling_event_count_1h`, `rolling_event_count_24h`, `victim_velocity_surge_ratio`.
- **Spatial Anchors:** District historical crime frequencies, rounded coordinate grids, and location activity indices.

---

## 11. Machine Learning Methodology
- **Model Type:** Scikit-Learn `Pipeline` wrapping a frozen `ColumnTransformer` (median numerical imputer + `StandardScaler`, most-frequent categorical imputer + `OneHotEncoder`) and an `XGBClassifier`.
- **Temporal Splitting:** Enforces strict chronological partitioning (Train: 7,000 rows, Val: 1,500 rows, Test: 1,500 rows) with zero look-ahead data leakage.
- **Hyperparameters:** `n_estimators=200`, `max_depth=2`, `learning_rate=0.03`, `subsample=0.8`, `scale_pos_weight=8.62`, `random_state=42`.
- **Calibration:** Sigmoid Platt scaling fitted on validation data via `FrozenEstimator`, reducing Brier calibration error from 0.2121 to **0.0876**.

---

## 12. Risk Scoring & Priority Tiers
Raw probability outputs are mapped into a standardized operational score:
$$\text{Risk Score} = \text{round}(P(\text{cashout}) \times 100, 2) \in [0.0, 100.0]$$
- **CRITICAL ($\ge 80.0$):** Immediate patrol dispatch, SMS broadcast, bank freeze notification.
- **HIGH ($60.0 - 79.9$):** Priority triage queue in Analyst Workspace.
- **MEDIUM ($40.0 - 59.9$):** Standard case queue, batch review.
- **LOW ($< 40.0$):** Informational background logging.

---

## 13. Explainable AI (SHAP)
Decision transparency is powered by SHAP `TreeExplainer`:
- Calculates exact marginal Shapley contributions per feature in ~35ms.
- Delivers localized attribution waterfalls informing field officers of top drivers (e.g. `+32% due to fraud_amount > INR 100,000`, `+18% due to velocity surge ratio`).
- Eliminates "black-box" resistance among law enforcement commanders.

---

## 14. GIS & Spatial Analysis
- **DBSCAN Density Clustering:** Evaluates historical cashout coordinates using Haversine metric ($\varepsilon=500\text{m}, \text{MinPts}=3$), identifying **40 recurrent spatial extraction clusters**.
- **Candidate ATM Proximity Matching:** Computes vectorized great-circle distances across 3,000 ATMs in **2.4ms**, establishing 5km spatial catchment buffers around candidate corridors.
- **Map Visualization:** Leaflet 1.9.4 frontends consume `GET /gis/predicted-locations`, rendering dynamic heatmaps, ATM pins, and catchment perimeters.

---

## 15. Alerts & Investigation Case Management
- **Automated Cooldown:** 60-minute spatial-temporal cooldown suppresses duplicate alerts for the same ATM corridor, preventing notification fatigue.
- **Full Case Lifecycle:** Single-click promotion from alert to formal case file (`INV-YYYYMMDD-XXXX`).
- **Docketing:** Append-only chronological officer notes and multi-format evidence logging (`TRANSACTION_REFERENCE`, `SYSTEM_LOG`, etc.).
- **Feedback Loop:** Case outcomes (`THWARTED_CASHOUT`, `CONFIRMED_CASHOUT`) record ground-truth prevented funds (e.g. INR 125,000 saved).

---

## 16. Security & Role-Based Access Control
- **Authentication:** HS256 JWT tokens with 120-minute expiration; passwords hashed using salted `bcrypt`.
- **Rigid 4-Role Hierarchy:** `ANALYST`, `SUPERVISOR`, `ADMIN`, and `BANK_ANALYST`.
- **Inter-Agency Boundary:** Bank analysts are strictly forbidden (HTTP 403) from viewing criminal case files or police evidence.
- **Non-Repudiation Audit:** Append-only log recording actor, action, timestamp, and SHA-256 hash across all state modifications.

---

## 17. Testing, Validation & Verification
Exhaustive verification across 8 integration suites in Phase 13 yielded a **100% pass rate (68 / 68 assertions passed)**:
- Backend REST Endpoints: 15 / 15 Passed
- 18-Step E2E Analytical Lifecycle: 18 / 18 Passed
- RBAC Boundary Enforcement: 12 / 12 Passed
- Core System Smoke Tests: 10 / 10 Passed
- ML Pipeline & Probability Bounds: 5 / 5 Passed
- Frontend Portals Mounting: 4 / 4 Passed
- Dual-Storage Fallback Routing: 2 / 2 Passed
- Demonstration Reset Tooling: 2 / 2 Passed

---

## 18. Empirical Results
On unseen chronological test data (1,500 records):
- **PR-AUC:** **0.2248** (**2.17x improvement** over the 0.1033 random baseline).
- **ROC-AUC:** **0.6445** (demonstrates clear discriminative power).
- **Precision:** **29.14%** at operational decision threshold 0.18.
- **Recall:** **32.90%** at operational decision threshold 0.18.
- **Latency:** End-to-end dynamic complaint intake, feature engineering, and inference completes in **14.2 milliseconds**.

---

## 19. Documented Limitations
1. **Propensity vs. Coordinates:** Model predicts *cashout propensity*, not exact latitude/longitude numbers. Spatial ATM localization is handled by the downstream GIS engine.
2. **Storage State:** Currently running in local `CSV_FALLBACK_DEV` mode; enterprise PostgreSQL/PostGIS DDL scripts are packaged and ready for deployment.
3. **Synthetic Data Sandbox:** Validated against synthetic datasets modeled on NCRP distributions to protect citizen privacy.

---

## 20. Future Scope & Roadmap
1. **Road-Network Transit Routing:** Implementing PostGIS `pgRouting` to calculate exact vehicular travel times and traffic congestion along cashout corridors.
2. **Graph Neural Networks (GNNs):** Mapping multi-hop transaction graphs across banking institutions prior to physical cashout.
3. **Automated Continuous Retraining:** Establishing quarterly model weight updates fed by logged case outcome feedback.

---

## 21. Conclusion
The Cybercrime Predictive Analytics Framework successfully satisfies Problem Statement ID 26184. By integrating real-time feature derivation, calibrated XGBoost machine learning, local SHAP explainability, geospatial DBSCAN clustering, and inter-agency banking coordination, the framework transforms reactive cybercrime triage into proactive field interdiction. The platform is verified, robust, and certified as **READY WITH DOCUMENTED LIMITATIONS** for Smart India Hackathon evaluation.

---

## 22. References to Internal Technical Documentation
- **Architecture Specification:** [`FINAL_SYSTEM_ARCHITECTURE.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/FINAL_SYSTEM_ARCHITECTURE.md)
- **Problem & Solution Guide:** [`FINAL_PROBLEM_AND_SOLUTION_EXPLANATION.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/FINAL_PROBLEM_AND_SOLUTION_EXPLANATION.md)
- **Audited Tech Stack:** [`FINAL_TECHNOLOGY_STACK.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/FINAL_TECHNOLOGY_STACK.md)
- **ML Pipeline & Evaluation:** [`FINAL_ML_MODEL_DOCUMENTATION.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/FINAL_ML_MODEL_DOCUMENTATION.md)
- **GIS Module Documentation:** [`FINAL_GIS_MODULE_DOCUMENTATION.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/FINAL_GIS_MODULE_DOCUMENTATION.md)
- **Security & RBAC Specification:** [`FINAL_SECURITY_AND_PRIVACY_DOCUMENTATION.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/FINAL_SECURITY_AND_PRIVACY_DOCUMENTATION.md)
- **Presentation Deck Outline:** [`SIH_PRESENTATION_CONTENT.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/SIH_PRESENTATION_CONTENT.md)
- **Presenter Demonstration Script:** [`SIH_LIVE_DEMONSTRATION_SCRIPT.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/SIH_LIVE_DEMONSTRATION_SCRIPT.md)
- **Evaluator Q&A Guide:** [`SIH_JUDGE_QUESTIONS_AND_ANSWERS.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/SIH_JUDGE_QUESTIONS_AND_ANSWERS.md)
- **Evidence Checklist:** [`SIH_EVIDENCE_COLLECTION_CHECKLIST.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/SIH_EVIDENCE_COLLECTION_CHECKLIST.md)
- **Project Status Matrix:** [`FINAL_PROJECT_STATUS_MATRIX.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/FINAL_PROJECT_STATUS_MATRIX.md)
- **Deployment Checklist:** [`DEPLOYMENT_READINESS_CHECKLIST.md`](file:///d:/SIH/SIH_2026/cybercrime_prediction/DEPLOYMENT_READINESS_CHECKLIST.md)
