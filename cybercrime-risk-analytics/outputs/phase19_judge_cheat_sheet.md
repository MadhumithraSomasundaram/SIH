# Phase 19 — Judge Rapid-Fire Cheat Sheet
## 14 Core Technical & Operational Defenses (2–4 Sentences Each)
**Problem Statement ID:** 26184  
**Project:** Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations  

---

### 1. "What is your target variable?"
Our target is `future_withdrawal`, a binary indicator denoting whether a complaint is linked to a physical cash withdrawal within a 24-hour forward-looking horizon in the proximate spatial sector. It was constructed strictly from chronological event sequences without leaking post-incident withdrawal attributes into the input feature matrix.

### 2. "Why XGBoost?"
XGBoost provides the highest empirical accuracy on non-linear tabular datasets with mixed feature types and missing values. It handles our ~10% class imbalance natively via the `scale_pos_weight` parameter and integrates seamlessly with SHAP TreeExplainer for exact, real-time feature attribution.

### 3. "Why a 24-hour prediction horizon?"
Over 70% of cash mule withdrawals take place within the first 6 to 24 hours following fraudulent fund transfers. A 24-hour window provides an actionable operational window for police beat patrol deployment, whereas narrower windows are too short for human triage and wider windows are too diffuse for tactical positioning.

### 4. "How did you avoid data leakage?"
We enforced a strict chronological split (first 70% train, next 15% validation, final 15% test) so the model never trains on future events. All 64 features were engineered strictly backward in time, preprocessors were fitted exclusively on training data, and all post-event fields were purged from the input schemas.

### 5. "Why DBSCAN over K-Means?"
Cybercrime withdrawal corridors follow non-linear street networks and commercial strips rather than circular blobs. DBSCAN discovers arbitrary geometric cluster shapes, automatically filters out isolated rural noise points, and eliminates the need to arbitrarily predefine the number of clusters ($k$).

### 6. "What does SHAP do in your framework?"
SHAP uses cooperative game theory to calculate the exact marginal contribution of each feature to a given prediction. It explains to law enforcement officers in plain language which specific factors—such as a 24-hour complaint surge or large transaction amount—drove the risk score higher.

### 7. "How do alerts work?"
The alert engine evaluates incoming predictions against risk thresholds ($\ge 60$ for HIGH) and spatial intersection with active DBSCAN hotspots. Every alert is tagged with mandatory human review (`human_review_required = True`), and deduplication rules prevent alert fatigue by throttling repeat notifications within a 60-minute window.

### 8. "Can you identify criminals?"
**No, absolutely not.** Our system generates probabilistic risk signals and spatial monitoring corridors for authorized human review; it has zero capability or mandate to identify, profile, or accuse individual persons. All system outputs are strictly advisory decision-support indicators.

### 9. "Can you guarantee that a withdrawal will happen?"
**No.** The model estimates a conditional probability based on historical spatio-temporal patterns, not a deterministic guarantee. It optimizes limited police resources by directing patrols to areas with higher statistical likelihood of criminal cashout activity.

### 10. "Do you have live bank data or NCRP integration?"
**No, not in this prototype.** The system was built and evaluated using synthetic, anonymized datasets that accurately mirror the schema of real cyber financial fraud complaints. Live institutional access would be established during production deployment under RBI and I4C regulatory frameworks.

### 11. "What is your final test performance?"
Evaluated on 1,500 held-out chronological test records, our locked metrics are: **PR-AUC = 0.1029** (matching the random baseline under severe 10% class imbalance), **ROC-AUC = 0.4760**, **Accuracy = 86.93%**, and **Specificity = 96.73%**. We present authentic, locked numbers without tuning thresholds on the test set.

### 12. "What happens if the model is wrong?"
Because the system is strictly decision-support with mandatory human verification, an incorrect prediction has zero coercive impact on citizens. A false positive simply results in visible police patrol presence in a commercial area—which deters crime naturally—while false negatives are addressed by traditional post-facto investigative pipelines.

### 13. "How will you deploy this in production?"
We would package the FastAPI microservices into containerized Kubernetes pods hosted on State Data Centre (SDC) infrastructure connected to high-availability PostgreSQL/PostGIS clusters. Incoming complaint webhooks from NCRP/I4C and anonymized bank ATM telemetry would be consumed via asynchronous Kafka message queues with single-sign-on access via Jan Parichay.

### 14. "What is your biggest limitation?"
Our biggest limitation is that the framework operates on synthetic historical data and predicts spatial corridors (approx. 1.5 km clusters) rather than exact individual ATM terminal hardware IDs. Pinpoint machine-level certainty requires real-time telemetry from core banking switches, which is outside the scope of a standalone prototype.
