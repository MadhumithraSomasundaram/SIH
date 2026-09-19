# Phase 1 Dataset Report — Problem Statement 26184
## Predictive Analytics Framework for Cybercrime → Cash Withdrawal Forecasting

---

## 1. Dataset Overview

Six CSV datasets located in `data/raw/`. The primary datasets for Problem 26184 are:
- **Fraud_Cases.csv** — cybercrime complaint registry
- **Withdrawals.csv** — ATM cash withdrawal records with geospatial coordinates
- **Transactions.csv** — fund transfer chain linking complaints to withdrawals
- **ATMs_Locations.csv** — ATM network with coordinates
- **Areas_Master.csv** — geographic area reference with centroids
- **Accounts.csv** — account-level baseline behaviour

---

## 2. Record Counts

| Dataset | Rows | Columns |
|---|---|---|
| Fraud_Cases | 10,000 | 11 |
| Withdrawals | 80,000 | 19 |
| Transactions | 300,000 | 8 |
| ATMs_Locations | 3,000 | 10 |
| Accounts | 30,000 | 11 |
| Areas_Master | 200 | 6 |

---

## 3. Features

### Fraud_Cases columns
case_id, complaint_timestamp, crime_type, scenario, victim_account_id, victim_state, victim_district, victim_area, victim_area_id, fraud_amount, reported_by_authority

### Withdrawals columns
withdrawal_id, case_id, account_id, atm_id, timestamp, amount, state, district, area, area_id, latitude, longitude, hour, day_of_week, is_weekend, is_night, scenario, is_suspicious, hour_timestamp

### Transactions columns
transaction_id, case_id, timestamp, from_account, to_account, amount, transaction_type, scenario

---

## 4. Data Types
See `outputs/dataset_profile.csv` for full per-column type detail.

---

## 5. Missing Values

| Dataset | Column | Missing Count | Missing % |
|---|---|---|---|
| Withdrawals | case_id | 51,386 | 64.2% |
| Withdrawals | All other | 0 | 0% |
| Fraud_Cases | All | 0 | 0% |
| Transactions | All | 0 | 0% |
| ATMs_Locations | All | 0 | 0% |
| Accounts | All | 0 | 0% |
| Areas_Master | All | 0 | 0% |

**Key finding**: `Withdrawals.case_id` is NULL for 51,386 records (64.2%)
— these are background (non-fraud-linked) withdrawals, which is expected.

---

## 6. Duplicate Records

All datasets: **0 duplicate rows** ✓

---

## 7. Geographic Coverage

- **States covered**: Andhra Pradesh, Karnataka, Kerala, Tamil Nadu (etc.)
- **Districts**: 40 unique districts
- **Areas**: 193 unique areas
- **ATMs**: 3,000 ATM locations with coordinates
- Latitude range: [8.4917, 17.7126]
- Longitude range: [74.4709, 83.2428]
- **Coverage**: South India (Karnataka, Tamil Nadu, Andhra Pradesh, Kerala, Telangana)
- Invalid coordinates: **0** ✓

---

## 8. Time Coverage

| Dataset | Earliest | Latest | Span |
|---|---|---|---|
| Fraud_Cases | 2026-01-01 | 2026-08-31 | 242 days |
| Withdrawals | 2026-01-01 | 2026-09-02 | 244 days |

---

## 9. Crime Categories

| Crime Type | Count | % |
|---|---|---|
| IMPERSONATION | 1,687 | 16.9% |
| UPI_FRAUD | 1,686 | 16.9% |
| ACCOUNT_TAKEOVER | 1,682 | 16.8% |
| PHISHING | 1,678 | 16.8% |
| OTHER_FINANCIAL_FRAUD | 1,661 | 16.6% |
| INVESTMENT_FRAUD | 1,606 | 16.1% |

---

## 10. Transaction / Withdrawal Information

| Metric | Fraud Amount | Withdrawal Amount |
|---|---|---|
| Min | ₹500.00 | ₹200.00 |
| Median | ₹7,921.10 | ₹1,227.28 |
| Mean | ₹15,470.98 | ₹1,895.62 |
| Max | ₹500,000.00 | ₹84,518.62 |

**Withdrawal case linkage**:
- Linked to fraud case: 28,614 (35.8%)
- Background (no case): 51,386 (64.2%)
- Suspicious flag: 18,132 (22.7%)

---

## 11. Potential Target Variable

**No pre-built target for Problem 26184 exists.**

Planned target: `future_withdrawal_24h`
- **Definition**: 1 = a qualifying cash withdrawal occurs at/near the relevant area within
  the next 24 hours after a cybercrime complaint is filed; 0 = no withdrawal.
- **Construction**: Phase 5 — spatial-temporal join of Fraud_Cases with Withdrawals
  using strict temporal cutoff to prevent leakage.

---

## 12. Data Leakage Candidates

| Column | Dataset | Risk | Reason |
|---|---|---|---|
| `is_suspicious` | Withdrawals | HIGH | Post-event flag |
| `scenario` | All tables | HIGH | Simulation label with full outcome knowledge |
| `case_id` | Withdrawals | MEDIUM | May not be assigned at prediction time |
| `future_suspicious_3h` | ML_Area_Hourly | CRITICAL | Directly forward-looking |
| `risk_category/score` | ML_Area_Hourly | CRITICAL | Prior model target — circular |

See `outputs/data_leakage_candidates.csv` for full details.

---

## 13. Data Quality Issues

| Issue | Finding |
|---|---|
| Missing values | Only `Withdrawals.case_id` (64.2% null — expected) |
| Duplicates | Zero in all datasets |
| Invalid coordinates | Zero |
| Negative amounts | Zero |
| Invalid dates | Zero |
| Future dates | Zero |
| Placeholder strings | Zero ("unknown", "N/A" etc.) |
| Extreme values | Present in amounts (expected — high-value fraud) |

**Overall data quality: EXCELLENT** ✓

---

## 14. Missing Information Required for Project

| Missing Feature | Impact | Mitigation |
|---|---|---|
| `future_withdrawal_24h` target | Cannot train model without it | Engineer in Phase 5 |
| Historical hotspot labels | No ground truth hotspot map | Derive from aggregated withdrawals |
| Real-time feed / streaming data | Static snapshot only | Use historical patterns |
| Victim → perpetrator ATM linkage | Direct chain not always available | Use case_id FK (partial) |

---

## 15. Recommendation for Phase 2

**Phase 2 — Data Cleaning:**
1. Handle `Withdrawals.case_id` nulls: keep as-is for background rows; flag with `is_fraud_linked`
2. Convert all datetime strings to proper `pd.Timestamp` objects
3. Encode categorical columns (`crime_type`, `scenario`, `account_type`, `atm_type`)
4. Standardise numerical features (amount, coordinates)
5. Merge Fraud_Cases ↔ Withdrawals on `case_id` to build master analysis table
6. Merge ATM coordinates into Withdrawals table
7. Validate join integrity (all case_ids match, etc.)

**DO NOT** proceed to Phase 2 until this report is reviewed and approved.
