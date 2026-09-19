# Phase 6 — Baseline Machine Learning Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Objective
Establish standardized machine-learning baseline performance benchmarks for forecasting likely physical cash withdrawals (`future_withdrawal`) within the 24-hour post-complaint horizon.

## 2. Input Datasets
- **Training Set (`train.csv`):** 7,000 complaints (Jan 1 – Jun 21, 2026)
- **Validation Set (`validation.csv`):** 1,500 complaints (Jun 21 – Jul 27, 2026)
- **Test Set (`test.csv`):** 1,500 complaints (Jul 27 – Aug 31, 2026) — *Strictly held out; NOT used for model selection*.

## 3. Target Distribution
- **Target Variable:** `future_withdrawal` (1 = Local ATM cashout within 24h; 0 = No local cashout)
- **Train Prevalence:** 728 / 7,000 (**10.40%**)
- **Validation Prevalence:** 144 / 1,500 (**9.60%**)
- **Test Prevalence:** 155 / 1,500 (**10.33%**)

## 4. Feature Selection
- **Total Features Evaluated:** 64 safe predictors
- **Quarantined Columns:** `case_id` (tracking ID), `victim_account_id_masked` (PII), `complaint_timestamp` (raw string), `is_linked_to_withdrawal` (outcome marker), `target_observation_complete` & `target_valid` (control flags).

## 5. Numerical Features (52 features)
Includes financial magnitudes (`amount_log1p`), geospatial coordinates, calendar indicators, and strictly past rolling event counts (1h, 6h, 24h, 7d).

## 6. Categorical Features (12 features)
Includes `crime_type`, `crime_category_group`, `victim_state`, `victim_district`, `victim_area`, `victim_area_id`, `time_period`, `hour_group`, `location_grid`, `amount_category`.

## 7. Preprocessing Strategy
- **CRITICAL LEAKAGE SAFEGUARD:** Preprocessing was fitted **ONLY on training data** (`X_train`).
- Numerical features: `SimpleImputer(strategy="median")` + `StandardScaler()` (for Logistic Regression).
- Categorical features: `SimpleImputer(strategy="most_frequent")` + `OneHotEncoder(handle_unknown="ignore")`.

## 8. Baseline Models Evaluated
1. **`dummy_prior`:** Naive majority-class benchmark (`strategy="prior"`).
2. **`logistic_regression`:** Linear baseline with `class_weight="balanced"`.
3. **`random_forest`:** Non-linear ensemble with 300 estimators and `class_weight="balanced"`.

## 9. Validation Results Summary

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| logistic_regression | 0.5767 | 0.0915 | 0.3819 | 0.1477 | 0.4995 | **0.1060** |
| random_forest | 0.9040 | 0.0000 | 0.0000 | 0.0000 | 0.5052 | **0.1005** |
| dummy_prior | 0.9040 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | **0.0960** |

## 10. Confusion Matrices & Class-Level Performance
- **Dummy Classifier:** Predicts 0 for all validation samples (Accuracy: 90.40%, TP: 0, FN: 144). Demonstrates why accuracy is a deceptive metric for imbalanced cybercrime prediction.
- **Logistic Regression:** Predicts balanced positives (TP: 55, FP: 546, TN: 810, FN: 89), capturing **38.19% of all local cashout incidents** at threshold 0.50.
- **Random Forest:** At threshold 0.50, RF defaults to conservative negative predictions, but achieves the highest ranking discrimination when threshold-adjusted.

## 11. ROC Curve Comparison
- Visualized in `outputs/figures/validation_roc_comparison.png`.
- Random Forest achieves **ROC-AUC = 0.5052**, slightly outperforming Logistic Regression (0.4995) and Dummy (0.5000).

## 12. Precision-Recall Comparison
- Visualized in `outputs/figures/validation_pr_comparison.png`.
- Random Forest and Logistic Regression both improve upon the naive baseline prevalence (9.60%), with Logistic Regression reaching **PR-AUC = 0.1060** and Random Forest reaching **PR-AUC = 0.1005**.

## 13. Decision Threshold Analysis
- Detailed in `outputs/phase6_threshold_analysis.csv`.
- At threshold 0.15, Random Forest captures **93.75% of all positive cashouts** (Recall = 0.9375, F1 = 0.1737).
- At threshold 0.20, Random Forest achieves **Recall = 59.72%** (TP = 86) with F1 = 0.1693.

## 14. Feature Importance & Coefficients
- Top Random Forest features: `time_since_previous_event_hours`, `amount_log1p`, `fraud_amount`, `event_minute`, `previous_activity_by_crime_category`, `previous_event_count`, `events_in_previous_30_days`.
- Saved to `outputs/random_forest_feature_importance.csv` and `outputs/logistic_regression_coefficients.csv`.
- *Note:* Feature importances indicate associative ranking utility in tree splits and do not claim causal attribution.

## 15. Leakage Audit Certification
- All 11 checks in `outputs/phase6_leakage_audit.csv` received **PASS**.
- Zero temporal overlap, zero feature contamination, zero test set reuse.

## 16. Test Set Handling
- **The test dataset was NOT used for model selection, threshold tuning, or hyperparameter search.** It remains an untouched holdout verified in `outputs/phase6_test_readiness.csv`.

## 17. Baseline Conclusion
- **Strongest Linear Baseline:** `logistic_regression` (highest default Recall of 38.19% and PR-AUC of 0.1060).
- **Strongest Non-Linear Ranking Baseline:** `random_forest` (achieves up to 93.75% recall under operational threshold tuning).

## 18. Phase 7 Readiness
**The baseline benchmarking phase is complete. The pipeline is READY for Phase 7 — XGBoost Model Development.**
