# Phase 10 — Explainable AI (SHAP) Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Objective
Provide model transparency and interpretable attribution for the primary XGBoost classification model using **SHAP (SHapley Additive exPlanations)**. This phase answers:
> *"Why did the model assign this specific future cash withdrawal risk?"*

**Core Explainability Principles:**
- Explains model predictions through cooperative game theory (Shapley values).
- Distinguishes **associative predictive attribution** from real-world **causality**.
- Guarantees full mathematical consistency between base value, feature contributions, and model log-odds.
- Strict isolation of sensitive financial credentials and PII.

---

## 2. Model & Input Feature Architecture
- **Model Pipeline:** `sklearn.pipeline.Pipeline` with `ColumnTransformer` + `XGBClassifier` (200 estimators, max_depth=3, learning_rate=0.05).
- **Raw Predictor Features:** 64 leakage-safe predictors.
- **Transformed Feature Space:** 556 features (numerical predictors + one-hot encoded categories).
- **Explanation Cohort:** Full chronological validation dataset (`validation.csv`, 1,500 complaints) for global attributions; stratified test complaints for local demonstration.

---

## 3. Top 10 Features by Global SHAP Importance

| rank | feature | mean_abs_shap_value | mean_shap_value | interpretation |
| --- | --- | --- | --- | --- |
| 1 | previous_activity_by_crime_category | 0.17433300614356995 | -0.16882599890232086 | Historical baseline frequency of cyber incidents in matching category or jurisdiction |
| 2 | previous_activity_by_location | 0.09627000242471695 | -0.033562999218702316 | Historical baseline frequency of cyber incidents in matching category or jurisdiction |
| 3 | previous_activity_by_district | 0.08567699790000916 | -0.08266299962997437 | Historical baseline frequency of cyber incidents in matching category or jurisdiction |
| 4 | events_in_previous_7_days | 0.08301500231027603 | -0.0672840029001236 | Recent activity velocity (events logged in short rolling temporal windows) |
| 5 | rolling_crime_event_count_7d | 0.055709000676870346 | 0.000311999989207834 | Recent activity velocity (events logged in short rolling temporal windows) |
| 6 | events_in_previous_1_day | 0.05394100025296211 | -0.016752999275922775 | Recent activity velocity (events logged in short rolling temporal windows) |
| 7 | events_in_previous_30_days | 0.046959999948740005 | -0.03690100088715553 | Recent activity velocity (events logged in short rolling temporal windows) |
| 8 | event_day | 0.04597099870443344 | -0.018583999946713448 | Temporal dispatch context and diurnal cybercrime activity timing |
| 9 | fraud_amount | 0.04035999998450279 | -0.015014000236988068 | Financial scale and magnitude of complaint fraud loss |
| 10 | rolling_event_count_1h | 0.03852999955415726 | -0.004554999992251396 | Recent activity velocity (events logged in short rolling temporal windows) |

---

## 4. Global Model Behavior & Attribution Direction
- **Primary Attribution Drivers:**
  - `previous_activity_by_crime_category`: Serves as the primary anchor for category-level cashout frequency. High historical category volumes adjust the baseline prediction upward.
  - `previous_activity_by_location` & `previous_activity_by_district`: Provide geographic crime clustering context.
  - `events_in_previous_7_days` & `events_in_previous_1_day`: Reflect recent burst velocity in complaints.
  - `fraud_amount` & `amount_log1p`: Financial loss magnitude modulates cashout probability.
- **Attribution Direction:**
  - **Positive SHAP Contribution ($+ \phi_i$):** Pushes model log-odds output toward `future_withdrawal = 1` (higher risk score).
  - **Negative SHAP Contribution ($-\phi_i$):** Pushes model log-odds output toward `future_withdrawal = 0` (lower risk score).

---

## 5. Visualizations
- **Global Summary Bar Chart:** `outputs/figures/phase10_shap_summary_bar.png`
- **Global Beeswarm Plot:** `outputs/figures/phase10_shap_beeswarm.png`
- **Local Waterfall Plots:**
  - LOW Risk Example: `outputs/figures/shap_local_low_risk.png`
  - MODERATE Risk Example: `outputs/figures/shap_local_moderate_risk.png`
  - HIGH Risk Example: `outputs/figures/shap_local_high_risk.png`

---

## 6. XGBoost Gain vs. SHAP Importance Comparison

| feature | xgboost_importance | shap_importance | shap_rank | xgboost_rank |
| --- | --- | --- | --- | --- |
| previous_activity_by_crime_category | 29.794696807861328 | 0.17433300614356995 | 1 | 31 |
| previous_activity_by_location | 24.23025131225586 | 0.09627000242471695 | 2 | 89 |
| previous_activity_by_district | 28.3738956451416 | 0.08567699790000916 | 3 | 42 |
| events_in_previous_7_days | 25.7675895690918 | 0.08301500231027603 | 4 | 66 |
| rolling_crime_event_count_7d | 29.101957321166992 | 0.055709000676870346 | 5 | 35 |
| events_in_previous_1_day | 22.22031593322754 | 0.05394100025296211 | 6 | 123 |
| events_in_previous_30_days | 25.89548110961914 | 0.046959999948740005 | 7 | 64 |
| event_day | 31.832733154296875 | 0.04597099870443344 | 8 | 17 |
| fraud_amount | 26.954111099243164 | 0.04035999998450279 | 9 | 49 |
| rolling_event_count_1h | 28.83592987060547 | 0.03852999955415726 | 10 | 38 |

**Key Analytical Takeaway:**
- **XGBoost Gain:** Highlights sparse features that create high purity gains on localized splits (e.g., specific one-hot time slices or location grids).
- **SHAP Mean |Value|:** Highlights features that systematically shift predictions across the entire complaint distribution (continuous rolling counters and historical category activity).

---

## 7. Mathematical Consistency Verification
$$\text{Base Value (Log-Odds)} + \sum_{i=1}^{556} \text{SHAP}_i = \text{Model Output Margin}$$
$$\text{Predicted Probability} = \frac{1}{1 + e^{-\text{Margin}}}$$

- **Max difference between margin and base + sum(SHAP):** $< 1.2 \times 10^{-6}$ (**PASS**).
- **Max difference between sigmoid margin and predicted probability:** $< 1.0 \times 10^{-7}$ (**PASS**).
- Verifies exact mathematical faithfulness of the TreeExplainer implementation.

---

## 8. Leakage & Sensitive Data Audits
- **Leakage Audit:** **PASS** (`outputs/phase10_leakage_audit.csv`) — Zero target-derived features or future attributes in explanation matrices.
- **Sensitive Data Audit:** **PASS** (`outputs/phase10_sensitive_data_audit.csv`) — Zero raw bank account numbers, card credentials, PINs, OTPs, or PII exposed.

---

## 9. Important Limitations
1. **Model Explanation $\ne$ Causality:** SHAP explains the *model's internal decision logic*, not the real-world criminal behavior causing ATM cashouts.
2. **Correlation Sharing:** Correlated features (such as multiple rolling window counters) share Shapley values across splits.
3. **Decision Support Context:** SHAP outputs serve to guide human-in-the-loop law enforcement analysts during triage; they do not constitute autonomous proof of criminal activity.

---

## 10. Conclusion & Phase 11 Readiness
Phase 10 successfully incorporates Explainable AI via SHAP, delivering both global feature transparency and individualized human-readable local justifications.

**Phase 10 is COMPLETE. Ready for Phase 11 — Spatial Hotspot & Geographic Cluster Analysis.**
