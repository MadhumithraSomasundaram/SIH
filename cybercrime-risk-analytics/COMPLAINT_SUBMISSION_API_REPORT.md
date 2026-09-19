# Cybercrime Predictive Analytics Framework — Delivery Report
## Dynamic Complaint Submission API (`POST /complaints`)
**Problem Statement ID:** 26184  
**Date:** September 19, 2026  
**Lead Engineers:** Antigravity Senior Backend & ML Engineering Team  
**Evaluation Status:** PASS (18/18 Automated Tests Passed; 80/80 Regression Tests Passed)  

---

## Executive Summary

A secure, fully validated, and dynamic complaint intake endpoint—`POST /complaints`—has been successfully implemented into the FastAPI application.

This endpoint fulfills the complete 10-stage analytical sequence requested by Problem Statement 26184:
$$\text{Complaint Submission} \rightarrow \text{Validation} \rightarrow \text{Feature Generation} \rightarrow \text{ML Prediction} \rightarrow \text{Risk Score} \rightarrow \text{SHAP Attribution} \rightarrow \text{Predicted Locations} \rightarrow \text{Alerting} \rightarrow \text{Dual Storage} \rightarrow \text{API Response}$$

Zero working features were deleted or broken. The existing `/predict`, `/predict/batch`, `/explain`, `/gis/*`, `/alerts/*`, and `/bank/*` endpoints remain completely operational.

---

## 1. Files Inspected

1. `api/main.py`: FastAPI application lifespan, middleware, exception handlers, and router mounts.
2. `api/schemas.py`: Pydantic models for prediction, explanations, and model metadata.
3. `api/auth.py`: Lightweight API key (`X-API-Key`) and Bearer JWT authentication dependencies.
4. `api/analyst_routes.py`: Authorized analyst role checks (`require_role`), token generation, and audit logging.
5. `api/bank_routes.py`: Strict read-only banking role isolation (`BANK_ANALYST`).
6. `api/gis_routes.py`: Spatial DBSCAN hotspot clusters and ATM Haversine cross-referencing (`predicted_locations`).
7. `src/predict.py`: Frozen XGBoost inference pipeline, risk scoring, and local SHAP explainability.
8. `src/feature_engineering.py`: Time, spatial grid, category, and financial feature calculations.
9. `src/alert_engine.py`: Analytical alert rules (`evaluate_risk_alert`), cooldown checks, and deduplication (`deduplicate_alerts`).
10. `database/connection.py`, `database/models.py`, `database/crud.py`: PostgreSQL/PostGIS ORM models and CSV/in-memory fallback caching.
11. `tests/test_api.py`, `tests/test_authorization.py`, `tests/test_bank_interface.py`, `tests/test_predicted_locations.py`.

---

## 2. Files Modified & Created

| File Path | Nature of Change | Description |
| :--- | :--- | :--- |
| `src/complaint_feature_service.py` | **NEW** | Production feature engineering engine extracting all 64 model inputs dynamically from raw complaints at $T_0$. |
| `api/complaint_routes.py` | **NEW** | Secure `POST /complaints` route, request/response models, RBAC, spatial ATM mapping, and alert dispatch. |
| `tests/test_complaints_api.py` | **NEW** | Comprehensive 18-point verification test suite covering validation, prediction, SHAP, GIS, alerts, and security. |
| `api/main.py` | **MODIFIED** | Registered `complaint_router` under `/complaints` without altering existing routes. |
| `api/schemas.py` | **MODIFIED** | Re-exported `ComplaintSubmissionRequest` and `ComplaintSubmissionResponse`. |
| `api/backup_complaints_phase/` | **BACKUP** | Preserved pristine backups of `main.py` and `schemas.py`. |
| `COMPLAINT_SUBMISSION_API_REPORT.md` | **NEW** | Comprehensive delivery report. |

---

## 3. New Endpoint Details (`POST /complaints`)

- **HTTP Method:** `POST`
- **Path:** `/complaints`
- **Authentication:** Mandatory (Bearer JWT token or valid `X-API-Key`).
- **Authorization:** `ANALYST`, `SUPERVISOR`, `ADMIN` (HTTP 403 for `BANK_ANALYST`).
- **Success Code:** `201 Created`
- **Error Codes:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `409 Conflict` (duplicate), `422 Unprocessable Content`, `500 Internal Server Error`, `503 Service Unavailable`.

### Request Schema (`ComplaintSubmissionRequest`)

| Field Name | Type | Required | Description | Validation Constraints |
| :--- | :---: | :---: | :--- | :--- |
| `complaint_id` | `string` | Optional | Client-provided reference code | Sanitized alphanumeric; auto-generated if omitted |
| `complaint_timestamp` | `string` | **Yes** | Time incident occurred / reported | Valid ISO 8601 string (e.g. `2026-09-19T14:30:00Z`) |
| `fraud_amount` | `float` | **Yes** | Reported loss in INR | Strictly $> 0.0$, finite numerical value |
| `transaction_amount` | `float` | Optional | Specific transaction amount | Finite $\ge 0.0$ |
| `transaction_channel` | `string` | Optional | Transfer channel | UPI, IMPS, NEFT, RTGS, ATM, CARD, WALLET |
| `complaint_category` | `string` | **Yes** | Attack taxonomy | Valid category (e.g. `Online Financial Fraud`) |
| `sender_account_reference`| `string` | Optional | Victim account token | Sanitized reference (never raw PAN/PII) |
| `receiver_account_reference`| `string`| Optional | Mule account token | Sanitized counterparty reference |
| `bank_reference` | `string` | Optional | Bank identifier | Institution code |
| `state` | `string` | **Yes** | Incident state | Non-empty string |
| `district` | `string` | **Yes** | Incident district | Non-empty string |
| `city` | `string` | Optional | Locality / beat | Sub-locality name |
| `latitude` | `float` | Optional | WGS 84 latitude | Finite float in $[-90.0, 90.0]$ |
| `longitude` | `float` | Optional | WGS 84 longitude | Finite float in $[-180.0, 180.0]$ |
| `description` | `string` | Optional | Sanitized incident narrative | Max 2000 characters |

---

## 4. Feature Generation Pipeline (`src/complaint_feature_service.py`)

Raw intake fields are translated into the exact 64-feature vector expected by the model:
1. **Temporal Features:** Parses `complaint_timestamp` into `event_year`, `event_month`, `event_day`, `event_day_of_month`, `event_day_of_week`, `event_hour`, `event_minute`, `is_weekend`, `is_month_start`, `is_month_end`, `is_quarter_start`, `is_quarter_end`, `hour_group` (4h bins), and `time_period` (diurnal periods).
2. **Geographic Grids:** Computes `latitude_rounded`, `longitude_rounded` (~1.1 km cells), `location_grid` (e.g. `13.04_80.23`), `coordinate_precision`, `has_location`, and `missing_coordinate_flag`.
3. **Crime Typology:** Categorizes `crime_category_group` (PAYMENT_FRAUD, INVESTMENT_SCAM, CREDENTIAL_THEFT, SOCIAL_ENGINEERING) and domain indicators `is_financial_fraud`, `is_online_fraud`, `is_identity_related`, `is_transaction_related`.
4. **Financial Metrics:** Calculates `amount_log1p = log(1 + amount)`, `amount_is_zero`, `amount_is_high` ($> \text{INR } 38,206.47$), and `amount_category` (LOW, MEDIUM, HIGH, CRITICAL).
5. **Account Baselines:** Performs O(1) lookup on `Accounts.csv` or database store to link customer baseline parameters when `sender_account_reference` is provided.

---

## 5. ML Prediction & Risk Score

- **Model Loaded:** Serialized frozen XGBoost pipeline (`models/xgboost_cybercrime_model.pkl`).
- **Probability Output:** $P(\text{future\_withdrawal} = 1) \in [0.0, 1.0]$.
- **Risk Score Formula:** $\text{round}(\text{probability} \times 100) \in [0, 100]$.
- **Calibrated Risk Tiers:**
  - `LOW`: 0–39
  - `MODERATE`: 40–59
  - `HIGH`: 60–79
  - `CRITICAL`: 80–100
- **Operational Interpretation:** Standardized guidance generated automatically for law enforcement analysts.

---

## 6. Local SHAP Attribution

- Computes local feature attribution via `shap.TreeExplainer(clf)`.
- Extracts the top 5 positive risk contributors (features increasing risk score) and top 5 negative risk contributors.
- **Graceful Degradation:** If SHAP encounters an unexpected environment constraint, inference succeeds and returns `explanation_available: false` without failing the complaint intake.

---

## 7. Predicted Cashout Locations & ATM Cross-Referencing

- Reuses spatial analytics from `api/gis_routes.py`.
- Evaluates 40 DBSCAN hotspot clusters against the complaint's `district` and geographic coordinates.
- Cross-references each cluster centroid with **3,000 physical ATM locations** (`data/raw/ATMs_Locations.csv`) using vectorized Haversine distance.
- Returns candidate cashout locations with:
  - `cluster_id`
  - `district`
  - `latitude`, `longitude`
  - `distance_to_complaint_km`
  - `nearest_atm_id`, `nearest_atm_bank`, `nearest_atm_distance_km`
  - `risk_score`, `risk_category`
  - `location_source`: `"DBSCAN Spatial Hotspot Cluster (Estimate)"`
  - `prediction_timestamp`

> [!NOTE]
> **Advisory:** Clusters are analytical forecasts derived from spatial incident density. They are not guaranteed cashout locations and require authorized human verification.

---

## 8. Alert Generation & Cooldown Engine

- Connects directly to `src/alert_engine.py`.
- **Threshold Rule:** Complaints generating a `risk_score >= 60` automatically trigger an analytical alert (`HIGH_RISK_LOCATION` for scores 60–79; `CRITICAL_RISK_LOCATION` for scores 80–100).
- **Cooldown & Deduplication:** Enforces a 60-minute spatial-temporal cooldown via `deduplicate_alerts()`. Re-submissions from the same locality and risk tier within the active window are suppressed to prevent alarm fatigue.
- **Low Risk Behavior:** If `risk_score < 60`, `alert: { "created": false, "alert_id": null }` is returned.

---

## 9. Database Behavior & Fallback Handling

- **PostgreSQL / PostGIS Connected:**
  - Stores `CybercrimeEvent` in `cybercrime_events` table (converting WGS84 coordinates into PostGIS `POINT(lon, lat)` SRID 4326).
  - Stores `PredictionResult` in `prediction_results` table.
  - Stores `CybercrimeAlert` in `cybercrime_alerts` table if an alert was generated.
  - Returns `storage_mode: "POSTGRESQL_POSTGIS"`.
- **PostgreSQL Offline (Current Environment):**
  - Gracefully falls back to `storage_mode: "CSV_FALLBACK_DEV"`.
  - Records the complaint and prediction in `_SUBMITTED_COMPLAINTS_CACHE` and logs the analytical transaction to `outputs/predictions/api_prediction_log.csv`.
  - Zero crashes or HTTP 500 errors.

---

## 10. Security & RBAC Enforcement

| Role | Access Result | HTTP Status | Rationale |
| :--- | :---: | :---: | :--- |
| **Unauthenticated** | DENIED | **401 Unauthorized** | Missing or invalid token/API key |
| **ANALYST** | **GRANTED** | **201 Created** | Authorized analytical operational role |
| **SUPERVISOR** | **GRANTED** | **201 Created** | Supervisory operational review role |
| **ADMIN** | **GRANTED** | **201 Created** | Full administrative role |
| **BANK_ANALYST** | **DENIED** | **403 Forbidden** | Strict read-only isolation of banking portal |
| **System Key (`X-API-Key`)** | **GRANTED** | **201 Created** | Trusted machine-to-machine integration |

---

## 11. Automated Test Results

### Dedicated Complaint Submission Suite (`tests/test_complaints_api.py`)
Executed via `pytest tests/test_complaints_api.py -v`:

```text
tests/test_complaints_api.py::test_01_valid_complaint_submission PASSED  [  5%]
tests/test_complaints_api.py::test_02_missing_required_fields PASSED     [ 11%]
tests/test_complaints_api.py::test_03_invalid_timestamp PASSED           [ 16%]
tests/test_complaints_api.py::test_04_invalid_monetary_amount PASSED     [ 22%]
tests/test_complaints_api.py::test_05_invalid_coordinates PASSED         [ 27%]
tests/test_complaints_api.py::test_06_duplicate_complaint PASSED         [ 33%]
tests/test_complaints_api.py::test_07_feature_generation PASSED          [ 38%]
tests/test_complaints_api.py::test_08_prediction_integration PASSED      [ 44%]
tests/test_complaints_api.py::test_09_risk_score_calculation PASSED      [ 50%]
tests/test_complaints_api.py::test_10_shap_integration PASSED            [ 55%]
tests/test_complaints_api.py::test_11_predicted_location_integration PASSED [ 61%]
tests/test_complaints_api.py::test_12_alert_generation PASSED            [ 66%]
tests/test_complaints_api.py::test_13_database_failure_fallback PASSED   [ 72%]
tests/test_complaints_api.py::test_14_csv_fallback_behavior PASSED       [ 77%]
tests/test_complaints_api.py::test_15_authentication_failure PASSED      [ 83%]
tests/test_complaints_api.py::test_16_rbac_restrictions PASSED           [ 88%]
tests/test_complaints_api.py::test_17_nan_infinity_serialization PASSED  [ 94%]
tests/test_complaints_api.py::test_18_existing_predict_compatibility PASSED [100%]

======================= 18 passed, 7 warnings in 40.96s =======================
```

### Core Regression Test Suites
Executed across `test_transaction_features.py`, `test_leakage_audit.py`, `test_authorization.py`, `test_bank_interface.py`, and `test_predicted_locations.py`:

```text
======================= 80 passed, 3 warnings in 15.43s =======================
```

---

## 12. Known Limitations

1. **ATM Cash Inventory Telemetry:** ATMs are joined based on physical geolocation and 24x7 status. Live cash level or dispenser telemetry is outside the problem statement scope.
2. **PostgreSQL Service Host:** When PostgreSQL is stopped on the local machine, the API operates in `CSV_FALLBACK_DEV` mode. Once PostgreSQL is started with PostGIS enabled, the system automatically writes to the relational database without configuration changes.

---

## 13. Example Request & Response

### Example Request (`POST /complaints`)
```http
POST /complaints HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer <analyst_jwt_token>
Content-Type: application/json

{
  "complaint_timestamp": "2026-09-19T14:30:00Z",
  "fraud_amount": 75000.0,
  "complaint_category": "UPI_FRAUD",
  "state": "Tamil Nadu",
  "district": "Chennai",
  "city": "T Nagar",
  "latitude": 13.04,
  "longitude": 80.23,
  "sender_account_reference": "ACC000001",
  "transaction_channel": "UPI",
  "description": "Unauthorized transfer reported following malicious APK install."
}
```

### Example Response (`HTTP 201 Created`)
```json
{
  "complaint_id": "CMP-20260919-000001",
  "prediction_id": "PRED-20260919-000001",
  "status": "processed",
  "withdrawal_probability": 0.2701,
  "risk_score": 27,
  "risk_level": "LOW",
  "model_version": "v1.0.0-xgb-668c1916",
  "prediction_timestamp": "2026-09-19T14:30:00Z",
  "operational_interpretation": "Low predicted likelihood of a qualifying future withdrawal. Continue routine monitoring.",
  "predicted_locations": [
    {
      "cluster_id": 1,
      "district": "Chennai",
      "latitude": 13.0827,
      "longitude": 80.2707,
      "distance_to_complaint_km": 6.42,
      "nearest_atm_id": "ATM0123",
      "nearest_atm_bank": "SBI",
      "nearest_atm_distance_km": 0.35,
      "risk_score": 68,
      "risk_category": "HIGH",
      "location_source": "DBSCAN Spatial Hotspot Cluster (Estimate)",
      "prediction_timestamp": "2026-09-19T14:30:00Z"
    }
  ],
  "alert": {
    "created": false,
    "alert_id": null,
    "alert_type": null,
    "severity": null,
    "operational_message": null
  },
  "explanation_available": true,
  "top_risk_drivers": [
    {
      "rank": 6,
      "feature": "events_in_previous_7_days",
      "shap_value": 0.0966,
      "direction": "INCREASED_RISK"
    }
  ],
  "storage_mode": "CSV_FALLBACK_DEV",
  "disclaimer": "Predictions and estimated cashout locations are analytical risk signals for authorized human review only. Not proof of criminal activity. Does not guarantee future ATM withdrawals."
}
```
