# Phase 2 — Data Cleaning and Standardization Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Dataset Before Cleaning
- **Raw File:** `data/raw/Fraud_Cases.csv`
- **Rows:** 10,000
- **Columns:** 11
- **Original Columns:** `case_id`, `complaint_timestamp`, `crime_type`, `scenario`, `victim_account_id`, `victim_state`, `victim_district`, `victim_area`, `victim_area_id`, `fraud_amount`, `reported_by_authority`

## 2. Duplicate Records
- **Duplicates found:** 0
- **Duplicates removed:** 0
- **Post-cleaning Duplicates:** 0

## 3. Missing Values
- **Missing Values Before Cleaning:** 0
- **Missing Values After Cleaning:** 0
- **Missing Value Handling:** All categorical and textual columns verified free of blank/null placeholders. Background withdrawal `case_id` nulls preserved deliberately as domain-valid non-fraud entries.

## 4. Numerical Cleaning
- **Columns Processed:** `fraud_amount`, `reported_by_authority`
- **Invalid values:** 0
- **Suspicious values:** 0 (zero negatives, zero non-numeric corruptions)
- **Amount Range:** Min ₹500.00 | Median ₹7921.10 | Mean ₹15470.98 | Max ₹500000.00

## 5. Date/Time Cleaning
- **Columns Processed:** `complaint_timestamp`
- **Standardized Format:** `YYYY-MM-DD HH:MM:SS` (ISO-8601 preserved with full seconds precision)
- **Invalid dates:** 0
- **Future dates:** 0 (All timestamps bounded within 2026-01-01 to 2026-08-31)
- **Feature Status:** No temporal features (e.g. `hour`, `day_of_week`) extracted — strictly deferred to Phase 3.

## 6. Geospatial Cleaning
- **Valid Coordinates:** 10,000 / 10,000 (100.0%)
- **Invalid Coordinates:** 0
- **Missing Coordinates:** 0
- **Coordinate Bounds:** Latitude [8.4917°, 17.7126° N] | Longitude [74.4709°, 83.2428° E] (South India region)
- **Coordinate Enrichment:** Area centroid coordinates from `Areas_Master.csv` attached to ensure spatial continuity.

## 7. Categorical Standardization
- **Columns Processed:** `crime_type` (6 types), `victim_state` (4 states), `victim_district` (40 districts), `victim_area` (193 areas), `victim_area_id` (200 area IDs)
- **Formatting Actions:** Whitespace stripped, casing standardized, exact referential match with `Areas_Master` verified (100% foreign key integrity).

## 8. Sensitive Information Protection
- **Columns Masked:** `victim_account_id` replaced with cryptographic pseudonym `victim_account_id_masked` (`ACC_ANON_<SHA256_8>`).
- **Raw PII Exclusion:** No plain account numbers, passwords, card numbers, or personal credentials retained in processed output.

## 9. Data Leakage Isolation
- **Excluded Columns:** `scenario` (Fraud_Cases), `is_suspicious` (Withdrawals post-event flag)
- **Reasoning:** `scenario` is a synthetic simulation archetype label containing omniscient cashout outcome dynamics unavailable at complaint intake. Registered in `data/processed/excluded_columns.csv`.

## 10. Outlier Analysis
- **Target Column:** `fraud_amount`
- **Methodology:** Tukey's Interquartile Range (IQR = ₹13,799.76; Upper Bound = ₹38,206.47)
- **Outlier Count:** 861 (8.61%)
- **Action:** Retained without deletion. Financial cybercrime inherently exhibits heavy-tailed fraud amounts; truncation would discard critical high-severity attack patterns.

## 11. Final Dataset
- **Cleaned Dataset Path:** `data/processed/cleaned_cybercrime_data.csv`
- **Rows:** 10,000
- **Columns:** 13
- **Cleaned Feature Schema:**
  1. `case_id` (ID)
  2. `complaint_timestamp` (Datetime)
  3. `crime_type` (Categorical)
  4. `fraud_amount` (Float64)
  5. `reported_by_authority` (Binary)
  6. `victim_state` (Categorical)
  7. `victim_district` (Categorical)
  8. `victim_area` (Categorical)
  9. `victim_area_id` (Categorical / FK)
  10. `latitude` (Float64)
  11. `longitude` (Float64)
  12. `victim_account_id_masked` (Pseudonymized String)
  13. `is_linked_to_withdrawal` (Binary Metadata)

## 12. Data Quality Score
- **Completeness:** 100.0%
- **Validity:** 100.0%
- **Consistency:** 100.0%
- **Uniqueness:** 100.0%
- **Geographic Validity:** 100.0%
- **Temporal Validity:** 100.0%
- **COMPOSITE DATA QUALITY SCORE:** **100.0%**

## 13. Remaining Issues for Phase 3
1. Target engineering: spatial-temporal joining of complaints with downstream withdrawals to construct the forward-looking prediction target (`future_withdrawal_24h` / `target_area_id`).
2. Temporal feature engineering (hour-of-day, day-of-week, weekend flags, time since last incident).
3. Geospatial distance and cluster density feature computation between victim centroid and candidate ATM zones.
4. Categorical frequency encoding or one-hot encoding for `crime_type` and high-cardinality `area_id`.
5. Robust log-transform scaling for heavy-tailed `fraud_amount`.

## 14. Recommendation
**The cleaned dataset is 100% validated, standardized, and structurally sound. It is fully ready for Phase 3 — Feature Engineering.**
