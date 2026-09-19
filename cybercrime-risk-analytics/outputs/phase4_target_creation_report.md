# Phase 4 — Future Withdrawal Target Creation and Labeling Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Input Dataset
- `data/processed/feature_engineered_cybercrime_data.csv`

## 2. Input Rows
- **10,000** complaint records

## 3. Output Rows
- **10,000** complaint records (100% preservation)

## 4. Withdrawal Event Definition
- Physical ATM cash withdrawal transactions from `data/processed/cleaned_withdrawals.csv` (80,000 records).
- 28,614 withdrawals are verified ground truth cashouts linked to cybercrime complaints via `case_id`.

## 5. Timestamp Used
- Baseline: `complaint_timestamp` ($T_0$)
- Outcome: `timestamp` in Withdrawals ($T_w$)
- Unified format: ISO-8601 (`YYYY-MM-DD HH:MM:SS`)

## 6. Location Matching Method
- Hybrid administrative and geometric distance matching: Same district (`victim_district == district`) OR Haversine distance $\le 10.0$ km between victim centroid and withdrawal ATM.

## 7. Spatial Threshold
- **10.0 km** (empirically covers local district cashout clusters; eliminates distant interstate mule diversions).

## 8. Prediction Window
- Strictly **next 24 hours** ($T_0 < T_w \le T_0 + 24.0\text{ hours}$). Current event is strictly excluded.

## 9. Number of Positive Targets
- **1,027** records

## 10. Number of Negative Targets
- **8,973** records

## 11. Positive Percentage
- **10.27%**

## 12. Negative Percentage
- **89.73%**

## 13. Class Imbalance Assessment
- **Moderately Imbalanced** (~1:8.7 positive-to-negative ratio).
- Highly realistic for real-world cybercrime intervention forecasting.
- Strategy for future modeling phases: scale_pos_weight (~8.7) in XGBoost, balanced class weights in logistic baselines, and PR-AUC optimization. (No resampling applied in Phase 4).

## 14. Incomplete Observation Records
- **0 records** with incomplete observation (10,000 / 10,000 observable because withdrawal registry extends 46+ hours past the last complaint).

## 15. Invalid Target Records
- **0 records** (10,000 / 10,000 valid; `target_valid = 1`).

## 16. Leakage Columns
- Formally cataloged in `outputs/target_leakage_columns.csv`:
  - `future_withdrawal` (Designated Target)
  - `target_observation_complete` (Control flag)
  - `target_valid` (Control flag)
  - `is_linked_to_withdrawal` (Quarantined outcome marker)
  - `scenario` & `is_suspicious` (Excluded in Phase 2)

## 17. Unsafe Features
- Listed in `outputs/model_feature_candidates.csv`: `case_id` and `victim_account_id_masked` are quarantined as ID/PII tokens and prohibited from model fitting.

## 18. Manual Verification Result
- 20 representative case audits compiled in `outputs/target_manual_verification.csv` (10 local cashouts, 5 distant mule diversions, 5 delayed cashouts). 100% verified consistent with defined rules.

## 19. Dataset Limitations
- Localized target identifies local cashouts (10.27%); distant mule network cashouts (~55.5%) occur outside the 10km district radius and are classified as 0 for local intervention.

## 20. Readiness for Phase 5
- **Status:** **READY**
- Dataset is fully labeled, validated, and ready for **PHASE 5 — TEMPORAL TRAIN/VALIDATION/TEST SPLIT**.
