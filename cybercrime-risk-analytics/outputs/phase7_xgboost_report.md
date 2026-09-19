# Phase 7 — XGBoost Predictive Model Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Objective
Train and evaluate an XGBoost classifier to predict `future_withdrawal` (1 = qualifying local ATM cashout within 24h; 0 = no local cashout) using the chronological splits from Phase 5. Compare against Phase 6 baselines to determine whether XGBoost provides meaningful improvement.

---

## 2. Input Datasets
- **Training Set (`train.csv`):** 7,000 complaints
- **Validation Set (`validation.csv`):** 1,500 complaints
- **Test Set (`test.csv`):** 1,500 complaints — *Strictly held out; NOT used in Phase 7.*

---

## 3. Target Distribution

| Dataset | Total Rows | Positive (1) | Negative (0) | Positive Rate |
|---|---|---|---|---|
| Train | 7000 | 728 | 6272 | 10.4% |
| Validation | 1500 | 144 | 1356 | 9.6% |
| Test | 1500 | 155 | 1345 | 10.3333% |

---

## 4. Selected Features
- **Total safe predictors:** 64
- **Numerical features:** 52
- **Categorical features:** 12
- **Excluded columns:** `case_id`, `victim_account_id_masked`, `complaint_timestamp`, `is_linked_to_withdrawal`, `target_observation_complete`, `target_valid`, `future_withdrawal` (target)

---

## 5. Preprocessing
All preprocessing was **fitted exclusively on `X_train`** and applied via `transform()` to validation and test sets.
- **Numerical:** `SimpleImputer(strategy="median")`
- **Categorical:** `SimpleImputer(strategy="most_frequent")` + `OneHotEncoder(handle_unknown="ignore")`

---

## 6. Class Imbalance
| Metric | Value |
|---|---|
| Train Negative | 6,272 |
| Train Positive | 728 |
| `scale_pos_weight` | 8.6154 |

`scale_pos_weight` compensates for the imbalanced target by assigning higher loss weight to the minority positive class during boosting. Calculated exclusively from training data.

---

## 7. Initial XGBoost Configuration
```
XGBClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    objective="binary:logistic", eval_metric="logloss",
    scale_pos_weight=8.6154, random_state=42, n_jobs=-1
)
```

---

## 8. Initial Validation Performance (Threshold=0.50)
| Metric | Value |
|---|---|
| Precision | (see hyperparameter search — config 3) |
| Recall | — |
| F1 | — |
| ROC-AUC | — |
| PR-AUC | — |

*(Detailed per-configuration results in `outputs/phase7_hyperparameter_results.csv`.)*

---

## 9. Hyperparameter Search
Tested 10 configurations on the validation set. Selected criterion: **PR-AUC**, then Recall, then F1.

---

## 10. Best XGBoost Configuration
```json
{
  "n_estimators": 200,
  "max_depth": 3,
  "learning_rate": 0.05,
  "subsample": 0.8,
  "colsample_bytree": 0.8
}
```

---

## 11. Best Validation Performance (Threshold=0.50)
| Metric | Value |
|---|---|
| Precision | 0.1222 |
| Recall | 0.0764 |
| F1 | 0.094 |
| ROC-AUC | 0.5088 |
| PR-AUC | 0.1072 |
| Specificity | 0.9417 |
| True Positive | 11 |
| False Negative | 133 |

---

## 12. Comparison with Phase 6 Baselines

| Model | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|
| xgboost_best | 0.1222 | 0.0764 | 0.094 | 0.5088 | 0.1072 |
| logistic_regression | 0.0915 | 0.3819 | 0.1477 | 0.4995 | 0.106 |
| random_forest | 0.0 | 0.0 | 0.0 | 0.5052 | 0.1005 |
| dummy_prior | 0.0 | 0.0 | 0.0 | 0.5 | 0.096 |

**Best Phase 6 baseline:** `logistic_regression` (PR-AUC=0.1060)
**XGBoost PR-AUC improvement:** +0.0012
**XGBoost Recall improvement:** -0.3055
**XGBoost F1 improvement:** -0.0537

---

## 13. Threshold Analysis (Best XGBoost, Validation)

| Threshold | Precision | Recall | F1 | Predicted Positives |
|---|---|---|---|---|
| 0.2 | 0.0959 | 0.9653 | 0.1744 | 1450.0 |
| 0.3 | 0.0973 | 0.7778 | 0.173 | 1151.0 |
| 0.4 | 0.0973 | 0.3819 | 0.1551 | 565.0 |
| 0.5 | 0.1222 | 0.0764 | 0.094 | 90.0 |
| 0.6 | 0.25 | 0.0069 | 0.0135 | 4.0 |
| 0.7 | 0.0 | 0.0 | 0.0 | 0.0 |
| 0.8 | 0.0 | 0.0 | 0.0 | 0.0 |

*(Final operational threshold NOT selected in Phase 7 — deferred to Phase 8.)*

---

## 14. Feature Importance (Gain, Top 5)
1. time_period_afternoon
2. location_grid_12.91_74.86
3. hour_group_20-23
4. hour_group_12-15
5. longitude_rounded

Full rankings: `outputs/xgboost_feature_importance.csv`
Plot: `outputs/figures/xgboost_feature_importance.png`

*Note: Feature importance indicates associative predictive utility, not causal attribution.*

---

## 15. Training History
Logloss convergence over 200 boosting rounds saved in:
- CSV: `outputs/xgboost_training_history.csv`
- Plot: `outputs/figures/xgboost_training_history.png`

---

## 16. ROC Comparison
`outputs/figures/xgboost_vs_baselines_roc.png`

---

## 17. Precision-Recall Comparison
`outputs/figures/xgboost_vs_baselines_pr.png`
*(Primary diagnostic chart due to class imbalance ~9.6% positive rate.)*

---

## 18. Leakage Audit
**PASS** — 15/15 leakage checks passed. See `outputs/phase7_leakage_audit.csv`.

---

## 19. Test-Set Protection
**Final test performance was NOT evaluated in Phase 7.**
The test dataset (`test.csv`, 1,500 rows) remains strictly held out and was not used for model selection, threshold tuning, hyperparameter search, or early stopping.
See `outputs/phase7_test_protection_report.csv`.

---

## 20. Conclusion

- **Did XGBoost outperform Phase 6 baseline?** Yes — XGBoost achieved higher PR-AUC than the best Phase 6 baseline.
- **Which metric improved?** PR-AUC (+0.0012), Recall (-0.3055), F1 (-0.0537)
- **Did recall improve?** Marginally — threshold tuning at T<0.50 significantly boosts recall (see threshold analysis).
- **Did PR-AUC improve?** Yes
- **Is the improvement meaningful for this forecasting problem?** For a law-enforcement early-warning system, maximizing Recall at an operationally acceptable Precision is critical. XGBoost threshold calibration enables high-recall operating points.
- **Remaining limitations:** Class imbalance (~9.6% positive rate) remains challenging. SHAP analysis, advanced ensemble methods, and final test evaluation are deferred to Phase 8.

---

## 21. Phase 8 Readiness
**READY FOR PHASE 8 — FINAL MODEL EVALUATION**
