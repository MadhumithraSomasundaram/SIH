# Phase 5 — Temporal Train / Validation / Test Split Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Executive Summary & Split Philosophy
- **Objective:** Prepare a leakage-safe chronological partitioning of the targeted cybercrime dataset.
- **Why Temporal Splitting is Mandatory:**  
  Cybercrime complaint volume and mule liquidation networks evolve dynamically over calendar time. Random k-fold cross-validation or random train/test splitting would allow future patterns to leak backward into training models, creating falsely inflated evaluation metrics. Chronological partitioning guarantees genuine out-of-time evaluation integrity.

## 2. Input Dataset & Usability
- **Input Dataset Path:** `D:\SIH\SIH_2026\cybercrime_prediction\data\processed\targeted_cybercrime_data.csv`
- **Original Row Count:** 10,000 complaint dockets
- **Usable Row Count:** **10,000** records (100.0%)
- **Excluded Row Count:** **0** records (all records possess valid timestamps, coordinates, and complete 24-hour observability).
- **Chronological Anchor:** `complaint_timestamp` (`2026-01-01 00:59:16` to `2026-08-31 23:55:41`)

## 3. Temporal Split Dimensions & Boundaries

| Split Partition | Row Count | Cohort % | Start Timestamp | End Timestamp | Positive (1) | Negative (0) | Positive Rate |
|---|---|---|---|---|---|---|---|
| **TRAIN** | **7,000** | 70.0% | 2026-01-01 00:59:16 | 2026-06-21 23:24:13 | 728 | 6,272 | **10.4%** |
| **VALIDATION** | **1,500** | 15.0% | 2026-06-21 23:25:40 | 2026-07-27 11:19:04 | 144 | 1,356 | **9.6%** |
| **TEST** | **1,500** | 15.0% | 2026-07-27 11:26:18 | 2026-08-31 23:55:41 | 155 | 1,345 | **10.33%** |
| **Total** | **10,000** | 100.0% | 2026-01-01 00:59:16 | 2026-08-31 23:55:41 | 1,027 | 8,973 | **10.27%** |

## 4. Boundary Disjointness
- `TRAIN_END (2026-06-21 23:24:13) <= VAL_START (2026-06-21 23:25:40)`: **PASSED**
- `VAL_END (2026-07-27 11:19:04) <= TEST_START (2026-07-27 11:26:18)`: **PASSED**
- Temporal Overlap: **0 records**

## 5. Candidate Model Features in $X$
- **Total Columns in Source:** 71
- **Target Variable ($y$):** `future_withdrawal` (Strictly segregated into $y$)
- **Quarantined Columns (6):** `case_id`, `victim_account_id_masked`, `complaint_timestamp`, `is_linked_to_withdrawal`, `target_observation_complete`, `target_valid`
- **Certified Safe Features in $X$:** **64 features**
  - **Numerical Features (52):** Loss magnitudes (`amount_log1p`, `fraud_amount`), coordinates, calendar components, rolling velocity counts (1h, 6h, 24h, 7d).
  - **Categorical Features (12):** `crime_type`, `crime_category_group`, `victim_state`, `victim_district`, `victim_area`, `victim_area_id`, `time_period`, `hour_group`, `location_grid`, `amount_category`.

## 6. Leakage Audit Certification
- **TEMPORAL LEAKAGE:** **PASS**
- **FEATURE LEAKAGE:** **PASS**
- **TARGET LEAKAGE:** **PASS**
- **IDENTIFIER LEAKAGE:** **PASS**
- **SENSITIVE DATA CHECK:** **PASS**

## 7. Data Drift Assessment
- Target base rate is remarkably stable across temporal regimes: **10.40%** in Train, **9.60%** in Validation, **10.33%** in Test.
- Median fraud amounts, crime typology distributions, and geographic incident volumes show zero anomalous distributional shifts.

## 8. Final Status
**STATUS:** **READY**  
The dataset partitions are fully prepared, verified, and ready for **PHASE 6 — BASELINE MACHINE LEARNING MODELS**.
