# Phase 3 — Feature Engineering and Spatio-Temporal Feature Creation Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Input Dataset Path
- `data/processed/cleaned_cybercrime_data.csv`

## 2. Input Row Count
- **10,000** rows

## 3. Input Column Count
- **13** columns

## 4. Output Row Count
- **10,000** rows (100% row preservation)

## 5. Output Column Count
- **68** columns

## 6. Number of Features Created
- **55 newly engineered features** (across 8 distinct functional domains)

## 7. Time Features Created (13 features)
- `event_year`, `event_month`, `event_day`, `event_day_of_month`, `event_day_of_week` (0=Mon, 6=Sun)
- `event_hour`, `event_minute`
- `is_weekend`, `is_month_start`, `is_month_end`, `is_quarter_start`, `is_quarter_end`
- `hour_group`: 4-hour chronological cyclical segments (`00-03`, `04-07`, `08-11`, `12-15`, `16-19`, `20-23`)
- `time_period`: Domain circadian segments (`early_morning` [00-06], `morning` [06-12], `afternoon` [12-17], `evening` [17-21], `night` [21-24])

## 8. Geographic Features Created (5 features)
- `latitude_rounded`, `longitude_rounded`: Coordinates rounded to 2 decimal places (~1.1 km spatial precision)
- `location_grid`: Simple compound string identifier `rounded_lat_rounded_lon`
- `coordinate_precision`: `district_area_centroid`
- `geographic_region`: `South_India`

## 9. Crime Features Created (5 features)
- `crime_category_group`: Attack vector taxonomy (`PAYMENT_FRAUD`, `INVESTMENT_SCAM`, `CREDENTIAL_THEFT`, `SOCIAL_ENGINEERING`)
- `is_financial_fraud`: Binary indicator for loss-direct crimes
- `is_online_fraud`: Binary indicator for network/web-based attacks
- `is_identity_related`: Binary indicator for impersonation and credential theft
- `is_transaction_related`: Binary indicator for payment rail exploitation

## 10. Financial Features Created (4 features)
- `amount_log1p`: Log-transformed loss magnitude ($\log(1 + \text{fraud\_amount})$)
- `amount_category`: Risk bracket (`LOW` < ₹5k, `MEDIUM` ₹5k-₹20k, `HIGH` ₹20k-₹50k, `CRITICAL` > ₹50k)
- `amount_is_zero`: Zero loss indicator
- `amount_is_high`: High-loss indicator (> ₹38,206.47, Phase 2 IQR threshold)

## 11. Historical Activity Features Created (9 features)
*Strictly sorted chronologically; each row i accesses only past records j < i; current row is excluded.*
- `previous_event_count`: Cumulative number of prior complaints recorded in the system
- `time_since_previous_event_hours`: Elapsed operational time since immediately preceding incident
- `events_in_previous_1_day`: Total incidents reported across all regions in prior 24 hours
- `events_in_previous_3_days`: Total incidents in prior 72 hours
- `events_in_previous_7_days`: Total incidents in prior 7 days
- `events_in_previous_30_days`: Total incidents in prior 30 days
- `previous_activity_by_location`: Cumulative prior complaints in the same `victim_area_id`
- `previous_activity_by_district`: Cumulative prior complaints in the same `victim_district`
- `previous_activity_by_crime_category`: Cumulative prior complaints for the same `crime_type`

## 12. Rolling Features Created (6 features)
- `rolling_event_count_1h`: Past complaints within 1-hour window
- `rolling_event_count_6h`: Past complaints within 6-hour window
- `rolling_event_count_24h`: Past complaints within 24-hour window
- `rolling_event_count_7d`: Past complaints within 7-day window
- `rolling_location_event_count_24h`: Velocity of complaints in this specific area in prior 24 hours
- `rolling_crime_event_count_7d`: Trend velocity for this crime typology in prior 7 days

## 13. Missingness Features Created (6 features)
- `has_location`, `has_timestamp`, `has_amount`, `has_crime_category`, `has_district`, `missing_coordinate_flag`

## 14. Features Not Created and Why
- **Geohash:** Not created because no third-party geohash library is installed; replaced with documented `location_grid` (`lat_rounded_lon_rounded`).
- **Future Withdrawal Target (`future_withdrawal_24h`):** Explicitly prohibited in Phase 3 instructions; deferred to Phase 5.
- **DBSCAN Spatial Cluster Labels:** Prohibited in Phase 3 instructions; deferred to unsupervised modeling.
- **One-Hot Encoded Columns:** Deferred to Phase 6 to ensure encoders are fitted strictly on training folds to prevent distribution leakage.

## 15. Columns Excluded
- `scenario` (simulation label) and `is_suspicious` (investigator label) were excluded in Phase 2 and recorded in `data/processed/excluded_columns.csv`.
- `case_id` and `victim_account_id_masked` are quarantined as ID/PII tokens and flagged unsafe for direct ML estimation.

## 16. Leakage Checks
- **Chronological Sorting:** All records sorted chronologically by `complaint_timestamp`.
- **Exclusion of Current Row:** In all historical and rolling counts, the upper evaluation index is $i-1$, strictly excluding row $i$.
- **Zero Future Information:** Verification confirmed zero future dates or downstream withdrawal outcomes were accessed.

## 17. Missing-Value Handling
- Zero missing values exist in the engineered dataset (initial lag `time_since_previous_event_hours` filled with 0.0).

## 18. Constant and Redundant Features
- **Constant Features (8):** `event_year` (2026), `geographic_region` (South_India), `has_location` (1), `has_timestamp` (1), `has_amount` (1), `has_crime_category` (1), `has_district` (1), `missing_coordinate_flag` (0).
- **Collinear Pairs:** 21 pairs exceeded $|r| > 0.85$ (e.g. `event_day` and `event_day_of_month`, nested multi-day rolling counts). Retained for tree-based models and documented for Phase 4 feature selection.

## 19. Dataset Limitations
- Captures regional coverage in South India.
- High cardinality spatial area IDs (200 areas) will require frequency or target encoding during model training.

## 20. Readiness for Phase 4
- **Status:** **READY**
- The feature matrix is complete, validated, leakage-safe, and ready for exploratory data analysis.

## 21. Exact Command to Reproduce
```bash
python src/feature_engineering.py
```
