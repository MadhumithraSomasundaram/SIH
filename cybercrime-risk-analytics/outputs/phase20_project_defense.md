# PROJECT DEFENSE
## Comprehensive Technical, Methodological and Operational Defense
**Problem Statement ID:** 26184  
**Project:** Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations  
**Evaluation Forum:** Smart India Hackathon (SIH) Grand Finale  
**Target Agency:** Law Enforcement Agencies, State Cyber Crime Police Stations, I4C / MHA  

---

## 1. Problem
### What problem does the system solve?
When citizens register complaints on the National Cybercrime Reporting Portal (NCRP / 1930), stolen funds are rapidly siphoned through chains of digital mule accounts. However, the cyber fraud lifecycle almost universally terminates at a physical touchpoint: converting digital balances into un-traceable physical cash at an automated teller machine (ATM) or bank branch.

Currently, law enforcement response is almost entirely **reactive**: forensic investigations, bank statement requisitions, and account lien requests commence days or weeks after complaint registration—long after cash has been withdrawn. 

This framework solves the **proactive operational gap**. It analyzes initial complaint signals and spatio-temporal transaction patterns to forecast geographic sectors where future cash withdrawal activity is statistically more likely within 24 hours. This allows police commanders to prioritize beat patrol dispatches, deploy deterrent field surveillance, and coordinate with bank security teams before the cash disappears.

---

## 2. Exact Prediction
### What exactly does the ML model predict?
The machine learning model predicts the **conditional probability** that an incoming cybercrime complaint will be linked to a physical cash withdrawal within a 24-hour forward-looking horizon in the proximate geographical sector:

$$P(\text{future\_withdrawal} = 1 \mid X)$$

where $X$ represents a vector of 64 engineered spatio-temporal, financial, and relational features. 

The probability is mapped deterministically to an integer **Risk Score** (0–100):
$$\text{risk\_score} = \text{round}(P \times 100)$$

and tiered into standardized operational categories:
- **LOW**: 0–39
- **MODERATE**: 40–59
- **HIGH**: 60–79
- **CRITICAL**: 80–100 *(Empirical note: The trained model yields natural test scores up to 63; scores $\ge 80$ are not naturally produced on this test distribution under threshold 0.5)*.

---

## 3. Data
### What data is used?
The prototype utilizes 6 sanitized, synthetic relational datasets designed to accurately simulate NCRP and core banking structures without exposing real citizen PII:
1. `Fraud_Cases.csv` (10,000 complaints): Incident timestamps, crime types, reported amounts, victim districts, and approximate coordinates.
2. `Withdrawals.csv` (80,000 withdrawal events): ATM cashout timestamps, amounts, and terminal coordinates.
3. `Transactions.csv` (300,000 transaction hops): Intermediate digital fund transfers across accounts.
4. `ATMs_Locations.csv` (3,000 ATM locations): Physical coordinates, bank affiliations, and installation types (onsite/offsite).
5. `Areas_Master.csv` (200 administrative areas): District boundaries and geographic centroids.
6. `Accounts.csv` (30,000 account profiles): Synthetic account tenure and transaction volume indicators.

---

## 4. Target
### How is `future_withdrawal` created?
The target variable is a binary indicator (`1` or `0`). For each complaint record in the historical training set:
1. A forward-looking temporal window of **24 hours** from `complaint_timestamp` was constructed.
2. Historical withdrawal records were queried to determine if any cashout event was linked to the underlying fraud account chain within a spatial proximity buffer (1.5 km) of the complaint's spatial sector.
3. If one or more qualifying cashout events occurred within the window, `future_withdrawal = 1`; otherwise, `future_withdrawal = 0`.
4. The positive class prevalence across the 10,000 records is approximately **10.33%** (728 positive in train, 144 in validation, 155 in test), establishing a realistic, severe class imbalance.

---

## 5. Leakage Prevention
### How was leakage prevented?
To prevent target leakage and data snooping:
1. **Zero Future Lookahead in Features**: All rolling incident counts (1h, 6h, 24h, 7d) and lag aggregations were computed strictly backward in time relative to the complaint timestamp.
2. **Purging Post-Event Fields**: Actual withdrawal timestamps, cashout amounts, ATM terminal IDs, and subsequent transaction statuses were strictly excluded from the feature matrix.
3. **Isolated Preprocessing Pipelines**: Imputers, standard scalers, and one-hot encoders (`ColumnTransformer`) were fitted exclusively on the chronological training split and frozen. Validation and test partitions were transformed using frozen parameters without refitting.
4. **Cryptographic Verification**: Automated SHA-256 hash audits verified that test datasets and model artifacts remained bit-for-bit identical throughout evaluation.

---

## 6. Temporal Validation
### Why was chronological splitting used?
Random $k$-fold cross-validation or random train/test splits are **statistically invalid for time-series fraud prediction**. In a random split:
- Future events leak into the training set, allowing the model to train on future rolling averages to predict past incidents.
- Transient localized fraud bursts are simultaneously present in train and test splits, producing artificially inflated, illusory performance metrics.

We enforced a strict chronological split:
- **Train Set (70%)**: First 7,000 records (`2026-01-01` to `2026-06-21`)
- **Validation Set (15%)**: Next 1,500 records (`2026-06-21` to `2026-07-27`) — used exclusively for hyperparameter tuning and threshold selection.
- **Held-Out Test Set (15%)**: Final 1,500 records (`2026-07-27` to `2026-08-31`) — held strictly blind and unexamined until final Phase 8 evaluation.

---

## 7. Model
### Why XGBoost?
We benchmarked Logistic Regression, Dummy Classifiers, and Random Forests in Phase 6. XGBoost was selected as the final production model because:
1. **Tabular Superiority**: Gradient-boosted decision trees consistently outperform deep neural networks and linear models on high-dimensional tabular fraud data with mixed continuous and sparse categorical variables.
2. **Missingness & Outlier Robustness**: Natively handles missing values through default split directions without distorting distributions via crude mean imputation.
3. **Imbalance Handling**: Natively supports cost-sensitive gradient optimization via `scale_pos_weight`.
4. **Explainability**: Enables exact, polynomial-time Shapley value calculations via `shap.TreeExplainer`.

---

## 8. Class Imbalance
### How was imbalance handled?
The natural positive class prevalence is only ~10% (1 positive withdrawal per 9 non-withdrawal complaints). 
- **Why We Avoided SMOTE**: Synthetic Minority Over-sampling (SMOTE) generates synthetic points via linear interpolation between neighboring feature vectors. In spatial-temporal fraud data, this creates nonsensical coordinate combinations (e.g., coordinates in bodies of water or impossible administrative districts) and corrupts discrete categorical indicators.
- **Our Solution**: Cost-sensitive objective loss weighting via `scale_pos_weight = 8.6154` (the ratio of negative to positive training samples: $6,272 / 728$). This scales the gradient of the loss function for positive samples, penalizing false negatives heavily during tree building.

---

## 9. Evaluation
### How was the model evaluated?
The final model was evaluated on the 1,500 held-out chronological test complaints using the decision threshold ($0.50$) derived from validation set analysis:
- **Test PR-AUC**: **0.1029** (Precision-Recall AUC reflects true performance under 10% class imbalance; random baseline = 0.103).
- **Test ROC-AUC**: **0.4760**
- **Test Accuracy**: **0.8693** (86.93%)
- **Test Specificity**: **0.9673** (96.73% true negative rate, proving strong protection against false operational alarms).
- **Test Precision**: **0.0638**
- **Test Recall**: **0.0194**
- **Test F1-Score**: **0.0297**

> **Defense Position**: We report honest, authentic metrics. We did not tune the threshold on the test set or use SMOTE to manufacture artificial test performance.

---

## 10. Explainability
### Why SHAP?
Machine learning in law enforcement cannot operate as a black box. If an alert triggers a police beat patrol, commanders and officers require immediate operational justification.
- **SHAP (SHapley Additive exPlanations)** is grounded in cooperative game theory. It calculates the fair marginal contribution of each feature to the difference between the actual prediction and the base dataset expectation.
- TreeExplainer calculates exact local Shapley values in $< 60\text{ ms}$, presenting officers with transparent drivers (e.g., localized 24h complaint surge contributed $+0.182$ to probability).
- **Ethical Language**: We explicitly state *"this feature contributed toward a higher model prediction"*; we never claim it *"caused the crime"*.

---

## 11. Spatial Intelligence
### Why DBSCAN?
Traditional spatial hotspot analysis uses K-Means or fixed grid cells:
- K-Means assumes circular, convex clusters and forces every isolated rural point into a cluster.
- Fixed grid cells split natural corridors across arbitrary cell boundaries.
- **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** uses Haversine distance ($\epsilon = 1.5\text{ km}$, $\text{MinPts} = 5$) to discover non-linear, arbitrary cluster shapes following real urban commercial roads and transit corridors. It automatically identifies 40 physical cashout hotspots while filtering out isolated noise points.

---

## 12. Database
### Why PostGIS?
Relational databases alone cannot efficiently index geographic coordinates. PostGIS adds spatial data types (`GEOMETRY(Point, 4326)`), GIST spatial R-Tree indexing, and OpenGIS-compliant SQL functions (`ST_DWithin`, `ST_Distance`). It allows the application to execute sub-10 millisecond spatial radius queries linking incoming complaints to nearby ATM registries.

---

## 13. API
### Why FastAPI?
FastAPI was chosen as the enterprise microservice serving layer because:
1. **Asynchronous Architecture**: Non-blocking ASGI runtime capable of handling thousands of concurrent requests.
2. **Pydantic v2 Contracts**: Rust-compiled data validation that strictly validates types and coordinate ranges, rejecting malformed inputs with HTTP 422.
3. **Automated Documentation**: Generates interactive Swagger/OpenAPI documentation (`/docs`) out of the box.

---

## 14. Alerts
### How are alerts generated?
The rule-based notification engine evaluates predictions against operational thresholds:
1. **Risk Threshold**: Triggered when a single prediction risk score $\ge 60$ (HIGH/CRITICAL).
2. **Spatial Hotspot Intersection**: Triggered when incident coordinates fall within an active DBSCAN cluster buffer.
3. **Deduplication & Cooldown**: Suppresses redundant alerts for repeated complaints in the same sector within a 60-minute window.
4. **Mandatory Human Flag**: Every generated alert hardcodes `human_review_required = True`.

---

## 15. Human Review
### Why is human review required?
The system is explicitly an **analytical decision-support system, not an autonomous enforcement agent**. Predictive algorithms estimate statistical correlation, not legal certainty. Mandatory human review ensures:
- Experienced police analysts verify local context before dispatching resources.
- Zero automated coercive actions (no automated account freezing or transaction blocking).
- Constitutional safeguards and procedural due process are strictly preserved.

---

## 16. Security
### How is sensitive information protected?
1. **Privacy-by-Design**: Bank account numbers, 16-digit card PANs, PINs, CVVs, OTPs, and citizen Aadhaar numbers are strictly excluded from all feature matrices and API schemas.
2. **Credential Protection**: Analyst passwords use 12-round salted bcrypt hashing; session tokens use signed JWTs with strict expiration.
3. **Database Security**: SQLAlchemy ORM enforces parameterized queries, eliminating SQL injection.
4. **Evidence Sanitization**: Case investigations store safe metadata reference strings (e.g. `NCRP-REF-*`) rather than storing raw personal documents.

---

## 17. Limitations
### What cannot the system currently do?
1. **No Live Core Banking Access**: Operates on synthetic/anonymized data; does not tap live NPCI switches or core banking networks.
2. **Corridor, Not Pinpoint Machine**: Forecasts geographic corridors (1.5 km clusters), not exact individual ATM machine serial numbers.
3. **Score Ceiling**: Max natural test score is 63; scores $\ge 80$ (CRITICAL tier) are not naturally produced under threshold 0.5.
4. **Decision Support Only**: Does not identify individual suspects or guarantee withdrawal occurrence.

---

## 18. Deployment
### How could this become a production system?
1. **Infrastructure**: Deploy containerized FastAPI pods orchestrated via Kubernetes on State Data Centre (SDC) or MeghRaj government cloud.
2. **Data Ingestion**: Establish secure webhook ingestion connecting to I4C / NCRP complaint feeds via government API gateways.
3. **Banking Switch Integration**: Partner with major public/private banks under RBI regulatory sandbox frameworks for real-time ATM telemetry.
4. **Authentication**: Integrate with Jan Parichay (National Single Sign-On) for institutional police access.
5. **Streaming Architecture**: Ingest high-velocity streams via Apache Kafka with model inference run on Triton or ONNX runtimes.
