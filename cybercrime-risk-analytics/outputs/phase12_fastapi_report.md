# Phase 12 — FastAPI Model Serving Layer Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Executive Summary & Objective

Phase 12 implements a production-grade, highly secure, and asynchronous **FastAPI REST API serving layer** for the Cybercrime Predictive Analytics Framework. The API wraps the frozen Phase 11 XGBoost prediction pipeline (`models/xgboost_cybercrime_model.pkl`) and Phase 10 SHAP explainability engine (`src/explain_with_shap.py`) into high-performance RESTful endpoints.

### Core Architectural Principles:
1. **Zero Retraining & Zero Refitting:** The model pipeline and preprocessing `ColumnTransformer` are loaded **strictly once** at application startup via FastAPI's `lifespan` context manager and held in application state. Zero retraining or fitting occurs during any API request.
2. **Deterministic Calibration:** Propagates Phase 9 calibrated risk scores ($0\text{--}100$) and operational risk categories (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) identically to the offline model.
3. **Rigorous Input Validation & Leakage Prevention:** Built with Pydantic v2 schemas that enforce strict type checking, coordinate bounding ($[-90, 90]$ latitude, $[-180, 180]$ longitude), and reject target outcomes or post-event cashout fields (`future_withdrawal`, `withdrawal_timestamp`, `withdrawal_amount`).
4. **Hardened Security & PII Protection:** Automatically filters and rejects raw credentials (`card_number`, `pin`, `otp`, `cvv`, `password`). Stack traces, server file paths, and internal exceptions are completely masked behind standardized HTTP response envelopes.
5. **Comprehensive Automated Verification:** Verified with an exhaustive 55-test pytest suite (`tests/test_api.py`) covering standard operations, schema limits, malformed inputs, edge cases, and security boundaries.

---

## 2. API Architecture & Request Lifespan

```
                      Client Request (HTTP/JSON)
                                 │
                                 ▼
                     [Uvicorn ASGI Server]
                                 │
                                 ▼
                      [FastAPI Application]
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
  CORS Middleware                               Exception Handlers
(localhost origins only)                     (Masks stack traces & paths)
         │
         ▼
[Pydantic v2 Input Validation]
  ├─ Validates 64 incident-time features
  ├─ Validates coordinate bounds & hour ranges
  ├─ Rejects target outcomes (future_withdrawal, etc.)
  └─ Rejects banking credentials (cards, PIN, OTP, CVV)
         │
         ▼
[Singleton ModelState] (Pre-loaded at startup via lifespan)
  ├─ models/xgboost_cybercrime_model.pkl
  ├─ models/phase7_xgboost_metadata.json
  └─ Version fingerprint: v1.0.0-xgb-668c1916
         │
         ▼
[Inference Execution]
  ├─ preprocessor.transform() (TRAIN-fitted imputation & encoding)
  ├─ model.predict_proba()
  ├─ Risk scoring: round(prob * 100)
  ├─ Category: LOW / MODERATE / HIGH / CRITICAL
  └─ Optional: SHAP TreeExplainer local attribution
         │
         ▼
[Standardized Response Envelope] (JSON)
```

---

## 3. Endpoint Specifications

| Method | Endpoint | Description | Request Body | Response Status | Response Schema |
|---|---|---|---|---|---|
| `GET` | `/` | Service root & health banner | None | 200 OK | `ServiceInfoResponse` |
| `GET` | `/health` | Application & model health check | None | 200 OK | `HealthResponse` |
| `GET` | `/model/info` | Safe model metadata & risk thresholds | None | 200 OK | `ModelInfoResponse` |
| `POST` | `/predict` | Single complaint cashout risk prediction | `CybercrimeRecord` | 200 OK | `PredictionResponse` |
| `POST` | `/predict/batch` | Batch cashout risk prediction (max 100) | `BatchPredictionRequest` | 200 OK | `BatchPredictionResponse` |
| `POST` | `/explain` | Complaint prediction with SHAP attribution | `CybercrimeRecord` | 200 OK | `ExplainPredictionResponse` |

### Prohibited Input Fields (Auto-Rejected with HTTP 422/400):
- **Target & Future Cashout Leakage:** `future_withdrawal`, `withdrawal_timestamp`, `withdrawal_amount`, `withdrawal_status`, `is_linked_to_withdrawal`, `target_*`.
- **Sensitive Financial & Credential PII:** `card_number`, `pin`, `otp`, `cvv`, `password`, `account_id`, `ssn`.

---

## 4. Risk Scoring & Interpretation Calibration

Identical to Phase 9 risk calibration:

$$\text{risk\_score} = \text{round}(\text{probability} \times 100)$$

| Risk Score Range | Category | Operational Definition | Actionable Intervention Protocol |
|---|---|---|---|
| $0 - 39$ | `LOW` | Low likelihood of immediate local cash withdrawal | Standard logging; routine queue processing |
| $40 - 59$ | `MODERATE` | Elevated pattern indicators detected | Enhanced automated monitoring & velocity tracking |
| $60 - 79$ | `HIGH` | Strong spatio-temporal alignment with cashout clusters | Priority dispatch alert; cross-reference ATM hotspots |
| $80 - 100$ | `CRITICAL` | Severe imminent cashout probability | Immediate intervention flag; alert local field intelligence |

Every prediction response returns a standard disclaimer:
> *"Predictive assessment only. Indicates likelihood of future qualifying cash withdrawal; does not constitute proof of criminal guilt, individual intent, or ATM compromise."*

---

## 5. Automated Verification & Testing Suite

The API was validated using `pytest` and `httpx.ASGITransport` / `starlette.testclient.TestClient`. 
**Results: 55 passed in 5.64s.**

### Test Coverage Breakdown:
- **Service Banner (`TestRoot` — 4 tests):** Validates 200 status, required fields, operational status, and verifies that no internal filesystem paths are returned.
- **Health Diagnostics (`TestHealth` — 4 tests):** Validates 200 OK, verified `model_loaded: true`, and verifies zero stack traces on startup errors.
- **Model Metadata (`TestModelInfo` — 5 tests):** Verifies safe metadata publication, correct risk category definitions, and absolute absence of private credentials.
- **Single-Record Prediction (`TestPredictValid` — 8 tests):** Confirms 200 status, schema compliance, probability bounds $[0.0, 1.0]$, risk score calculation $\text{round}(P \times 100)$, category consistency, reference handling, and human-in-the-loop disclaimers.
- **Schema Defaults & Missing Features (`TestPredictMissingField` — 2 tests):** Confirms graceful processing when optional features are omitted (imputed via preprocessor).
- **Type Validation & Coordinate Bounds (`TestPredictInvalidType` — 4 tests):** Validates rejection of strings in numerical fields, rejection of out-of-bound latitudes ($[-90, 90]$) and longitudes ($[-180, 180]$), and rejection of invalid hours ($[0, 23]$).
- **Prohibited & Leakage Field Rejection (`TestPredictProhibitedFields` — 6 tests):** Validates automatic 422 rejection of `future_withdrawal`, `withdrawal_timestamp`, `withdrawal_amount`, `target_*`, `card_number`, and `pin`.
- **Batch Processing (`TestPredictBatch` — 7 tests):** Tests batch ingestion, preservation of record ordering, validation of batch sizes ($1 \le N \le 100$), rejection of empty batches, rejection of over-limit batches ($N > 100$), and model version attachment.
- **Explainability (`TestExplain` — 6 tests):** Tests SHAP attribution endpoint, positive/negative factor formatting, probability-to-score parity, and graceful fallback if TreeExplainer experiences sampling degradation.
- **Malformed Payloads (`TestMalformedRequest` — 5 tests):** Validates rejection of non-JSON requests, bad Content-Types, missing batch keys, empty POST bodies, and handling of unknown extra fields (`extra='ignore'`).
- **Security & Error Masking (`TestSecurity` — 4 tests):** Confirms absence of file paths, stack traces, and environment variables across 404, 422, and 500 error responses.

---

## 6. Audit & Validation Artifacts

The following audit logs and reports were generated and verified:
1. `outputs/phase12_model_loading_report.csv`: Confirms successful artifact discovery, checksum extraction, feature schema verification, and memory footprint.
2. `outputs/phase12_endpoint_test_results.csv`: Comprehensive log of all 26 endpoint integration cases with actual vs expected HTTP status codes (100% match).
3. `outputs/phase12_api_validation_report.csv`: 12-point functional check verifying model immutability, preprocessor freezing, and calibration consistency.
4. `outputs/phase12_security_validation.csv`: 11-point security verification confirming PII filtering, leakage guards, CORS enforcement, and exception shielding.
5. `outputs/predictions/api_prediction_log.csv`: Persistent, privacy-sanitized inference audit trail.

---

## 7. Operational Instructions

### Starting the Production Server:
```bash
# Start Uvicorn ASGI server on port 8000
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2

# For local development with auto-reload:
uvicorn api.main:app --reload --port 8000
```

### Interactive API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

### Example cURL Request:
```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "reference_id": "CMP-2026-001",
       "crime_type": "UPI Fraud",
       "fraud_amount": 75000.0,
       "victim_district": "Central",
       "latitude": 28.6139,
       "longitude": 77.2090,
       "event_hour": 14,
       "rolling_event_count_24h": 5
     }'
```

### Example Response:
```json
{
  "reference_id": "CMP-2026-001",
  "predicted_probability": 0.824,
  "risk_score": 82,
  "risk_category": "CRITICAL",
  "operational_interpretation": "CRITICAL RISK (Score: 82/100). Severe predicted probability of qualifying cash withdrawal within 24 hours. Immediate law enforcement dispatch recommended.",
  "model_version": "v1.0.0-xgb-668c1916",
  "disclaimer": "Predictive assessment only. Indicates likelihood of future qualifying cash withdrawal; does not constitute proof of criminal guilt, individual intent, or ATM compromise."
}
```
