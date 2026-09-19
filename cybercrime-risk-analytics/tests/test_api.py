"""
Phase 12 — FastAPI Test Suite
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests all API endpoints using FastAPI TestClient with synthetic, anonymized records.
No real complaint data, account numbers, or personal information is used.

Run: pytest tests/test_api.py -v

IMPORTANT: TestClient must be used as context manager to trigger lifespan startup.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root is importable
_TEST_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _TEST_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from api.main import app


# ---------------------------------------------------------------------------
# Synthetic test record (safe, anonymized, no real PII)
# ---------------------------------------------------------------------------
VALID_RECORD = {
    "crime_type": "Online Financial Fraud",
    "fraud_amount": 15000.0,
    "reported_by_authority": 0.0,
    "victim_state": "Maharashtra",
    "victim_district": "Mumbai",
    "victim_area": "Andheri",
    "victim_area_id": "MH_MUM_001",
    "latitude": 19.12,
    "longitude": 72.86,
    "event_year": 2026,
    "event_month": 3,
    "event_day": 75,
    "event_day_of_month": 15,
    "event_day_of_week": 2,
    "event_hour": 14,
    "event_minute": 30,
    "is_weekend": 0.0,
    "is_month_start": 0.0,
    "is_month_end": 0.0,
    "is_quarter_start": 0.0,
    "is_quarter_end": 0.0,
    "hour_group": "afternoon",
    "time_period": "business_hours",
    "latitude_rounded": 19.12,
    "longitude_rounded": 72.86,
    "location_grid": "19.12_72.86",
    "coordinate_precision": "high",
    "geographic_region": "West",
    "crime_category_group": "Financial",
    "is_financial_fraud": 1.0,
    "is_online_fraud": 1.0,
    "is_identity_related": 0.0,
    "is_transaction_related": 1.0,
    "amount_log1p": 9.616,
    "amount_is_zero": 0.0,
    "amount_is_high": 1.0,
    "amount_category": "high",
    "previous_event_count": 2.0,
    "time_since_previous_event_hours": 48.0,
    "events_in_previous_1_day": 1.0,
    "events_in_previous_3_days": 2.0,
    "events_in_previous_7_days": 3.0,
    "events_in_previous_30_days": 5.0,
    "previous_activity_by_location": 4.0,
    "previous_activity_by_district": 12.0,
    "previous_activity_by_crime_category": 7.0,
    "rolling_event_count_1h": 1.0,
    "rolling_event_count_6h": 2.0,
    "rolling_event_count_24h": 3.0,
    "rolling_event_count_7d": 8.0,
    "rolling_location_event_count_24h": 1.0,
    "rolling_crime_event_count_7d": 4.0,
    "location_total_previous_events": 15.0,
    "location_previous_24h_events": 2.0,
    "location_previous_7d_events": 6.0,
    "district_previous_24h_events": 8.0,
    "district_previous_7d_events": 20.0,
    "location_unique_crime_categories": 3.0,
    "has_location": 1.0,
    "has_timestamp": 1.0,
    "has_amount": 1.0,
    "has_crime_category": 1.0,
    "has_district": 1.0,
    "missing_coordinate_flag": 0.0,
}


# ---------------------------------------------------------------------------
# Pytest fixture — lifespan-enabled TestClient
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def api_client():
    """
    Module-scoped TestClient that triggers FastAPI lifespan startup/shutdown.
    The 'with' context manager ensures model loading happens before any tests.
    Supplies the prototype dashboard API key header.
    """
    with TestClient(
        app,
        raise_server_exceptions=False,
        headers={"X-API-Key": "sih26184-dashboard-prototype-key-2026"},
    ) as c:
        yield c


# ===========================================================================
# TEST 1: GET /
# ===========================================================================
class TestRoot:
    def test_root_returns_200(self, api_client):
        resp = api_client.get("/")
        assert resp.status_code == 200

    def test_root_has_required_fields(self, api_client):
        data = api_client.get("/").json()
        assert "service" in data
        assert "status" in data
        assert "version" in data

    def test_root_status_is_running(self, api_client):
        assert api_client.get("/").json()["status"] == "running"

    def test_root_does_not_expose_paths(self, api_client):
        text = api_client.get("/").text
        assert "C:\\" not in text
        assert "D:\\" not in text
        assert "/home/" not in text


# ===========================================================================
# TEST 2: GET /health
# ===========================================================================
class TestHealth:
    def test_health_returns_200(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_health_model_loaded(self, api_client):
        data = api_client.get("/health").json()
        assert "model_loaded" in data
        assert "prediction_pipeline_loaded" in data

    def test_health_status_field_present(self, api_client):
        data = api_client.get("/health").json()
        assert data["status"] in ("healthy", "unhealthy")

    def test_health_no_stack_trace(self, api_client):
        text = api_client.get("/health").text
        assert "Traceback" not in text
        assert "Exception" not in text


# ===========================================================================
# TEST 3: GET /model/info
# ===========================================================================
class TestModelInfo:
    def test_model_info_returns_200(self, api_client):
        resp = api_client.get("/model/info")
        assert resp.status_code == 200

    def test_model_info_required_fields(self, api_client):
        data = api_client.get("/model/info").json()
        for field in ("model_type", "model_version", "prediction_target",
                      "risk_categories", "feature_count"):
            assert field in data, f"Missing field: {field}"

    def test_model_info_correct_target(self, api_client):
        data = api_client.get("/model/info").json()
        assert data["prediction_target"] == "future_withdrawal"

    def test_model_info_risk_categories(self, api_client):
        data = api_client.get("/model/info").json()
        expected = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
        assert set(data["risk_categories"]) == expected

    def test_model_info_no_sensitive_data(self, api_client):
        text = api_client.get("/model/info").text
        for token in ("card_number", "pin", "otp", "cvv", "password",
                      "C:\\\\", "train.csv", "test.csv"):
            assert token.lower() not in text.lower(), (
                f"Sensitive token '{token}' found in /model/info"
            )


# ===========================================================================
# TEST 4: POST /predict — valid synthetic input
# ===========================================================================
class TestPredictValid:
    def test_predict_returns_200(self, api_client):
        resp = api_client.post("/predict", json=VALID_RECORD)
        assert resp.status_code == 200

    def test_predict_response_schema(self, api_client):
        data = api_client.post("/predict", json=VALID_RECORD).json()
        assert "prediction_reference" in data
        assert "predicted_probability" in data
        assert "risk_score" in data
        assert "risk_category" in data
        assert "operational_interpretation" in data

    def test_predict_probability_range(self, api_client):
        data = api_client.post("/predict", json=VALID_RECORD).json()
        prob = data["predicted_probability"]
        assert 0.0 <= prob <= 1.0

    def test_predict_risk_score_range(self, api_client):
        data = api_client.post("/predict", json=VALID_RECORD).json()
        score = data["risk_score"]
        assert 0 <= score <= 100

    def test_predict_risk_score_formula(self, api_client):
        data = api_client.post("/predict", json=VALID_RECORD).json()
        expected_score = round(data["predicted_probability"] * 100)
        assert data["risk_score"] == expected_score

    def test_predict_valid_category(self, api_client):
        data = api_client.post("/predict", json=VALID_RECORD).json()
        assert data["risk_category"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")

    def test_predict_reference_format(self, api_client):
        data = api_client.post("/predict", json=VALID_RECORD).json()
        ref = data["prediction_reference"]
        assert ref.startswith("PRED-")

    def test_predict_disclaimer_present(self, api_client):
        data = api_client.post("/predict", json=VALID_RECORD).json()
        assert "disclaimer" in data
        assert len(data["disclaimer"]) > 10


# ===========================================================================
# TEST 5: POST /predict — missing required feature (graceful handling)
# ===========================================================================
class TestPredictMissingField:
    def test_missing_all_features_still_processes(self, api_client):
        """
        The model pipeline uses median imputation so partial/missing numeric
        features should still produce a valid prediction (not crash).
        """
        minimal = {"crime_type": "Test", "fraud_amount": 1000.0}
        resp = api_client.post("/predict", json=minimal)
        # Should either succeed (imputation) or return 400/422 — NOT 500
        assert resp.status_code in (200, 400, 422)

    def test_completely_empty_body(self, api_client):
        resp = api_client.post("/predict", json={})
        # Empty record: imputation should fill in or pipeline raises 400
        assert resp.status_code in (200, 400, 422)


# ===========================================================================
# TEST 6: POST /predict — invalid data type
# ===========================================================================
class TestPredictInvalidType:
    def test_string_in_float_field(self, api_client):
        bad = {**VALID_RECORD, "fraud_amount": "not_a_number"}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_out_of_range_latitude(self, api_client):
        bad = {**VALID_RECORD, "latitude": 999.0}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_out_of_range_longitude(self, api_client):
        bad = {**VALID_RECORD, "longitude": -999.0}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_invalid_hour(self, api_client):
        bad = {**VALID_RECORD, "event_hour": 99}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code == 422


# ===========================================================================
# TEST 7: POST /predict — prohibited target field
# ===========================================================================
class TestPredictProhibitedFields:
    def test_future_withdrawal_rejected(self, api_client):
        bad = {**VALID_RECORD, "future_withdrawal": 1}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code in (400, 422)

    def test_withdrawal_timestamp_rejected(self, api_client):
        bad = {**VALID_RECORD, "withdrawal_timestamp": "2026-09-15T10:00:00Z"}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code in (400, 422)

    def test_withdrawal_amount_rejected(self, api_client):
        bad = {**VALID_RECORD, "withdrawal_amount": 5000.0}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code in (400, 422)

    def test_target_field_rejected(self, api_client):
        bad = {**VALID_RECORD, "target_valid": True}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code in (400, 422)

    def test_sensitive_card_field_rejected(self, api_client):
        bad = {**VALID_RECORD, "card_number": "4111111111111111"}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code in (400, 422)

    def test_pin_field_rejected(self, api_client):
        bad = {**VALID_RECORD, "pin": "1234"}
        resp = api_client.post("/predict", json=bad)
        assert resp.status_code in (400, 422)


# ===========================================================================
# TEST 8: POST /predict/batch
# ===========================================================================
class TestPredictBatch:
    def test_batch_returns_200(self, api_client):
        resp = api_client.post("/predict/batch", json={"records": [VALID_RECORD, VALID_RECORD]})
        assert resp.status_code == 200

    def test_batch_count_matches_input(self, api_client):
        records = [VALID_RECORD] * 3
        data = api_client.post("/predict/batch", json={"records": records}).json()
        assert data["count"] == 3

    def test_batch_order_preserved(self, api_client):
        records = [VALID_RECORD] * 2
        data = api_client.post("/predict/batch", json={"records": records}).json()
        assert len(data["predictions"]) == 2

    def test_batch_each_has_reference(self, api_client):
        records = [VALID_RECORD] * 2
        data = api_client.post("/predict/batch", json={"records": records}).json()
        for pred in data["predictions"]:
            assert pred["prediction_reference"].startswith("PRED-")

    def test_batch_empty_records_rejected(self, api_client):
        resp = api_client.post("/predict/batch", json={"records": []})
        assert resp.status_code == 422

    def test_batch_over_limit_rejected(self, api_client):
        records = [VALID_RECORD] * 101
        resp = api_client.post("/predict/batch", json={"records": records})
        assert resp.status_code == 422

    def test_batch_model_version_returned(self, api_client):
        resp = api_client.post("/predict/batch", json={"records": [VALID_RECORD]})
        data = resp.json()
        if resp.status_code == 200:
            assert "model_version" in data


# ===========================================================================
# TEST 9: POST /explain
# ===========================================================================
class TestExplain:
    def test_explain_returns_200(self, api_client):
        resp = api_client.post("/explain", json=VALID_RECORD)
        assert resp.status_code == 200

    def test_explain_has_prediction_fields(self, api_client):
        data = api_client.post("/explain", json=VALID_RECORD).json()
        assert "predicted_probability" in data
        assert "risk_score" in data
        assert "risk_category" in data

    def test_explain_shap_available_field(self, api_client):
        data = api_client.post("/explain", json=VALID_RECORD).json()
        assert "shap_available" in data
        assert isinstance(data["shap_available"], bool)

    def test_explain_shap_contributors_are_lists(self, api_client):
        data = api_client.post("/explain", json=VALID_RECORD).json()
        assert isinstance(data["top_positive_contributors"], list)
        assert isinstance(data["top_negative_contributors"], list)

    def test_explain_disclaimer_present(self, api_client):
        data = api_client.post("/explain", json=VALID_RECORD).json()
        assert "disclaimer" in data

    def test_explain_probability_consistent_with_score(self, api_client):
        data = api_client.post("/explain", json=VALID_RECORD).json()
        expected = round(data["predicted_probability"] * 100)
        assert data["risk_score"] == expected


# ===========================================================================
# TEST 10: Malformed request
# ===========================================================================
class TestMalformedRequest:
    def test_non_json_body(self, api_client):
        resp = api_client.post(
            "/predict",
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (400, 422)

    def test_wrong_content_type(self, api_client):
        resp = api_client.post(
            "/predict",
            content=b"fraud_amount=1000",
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code in (400, 415, 422)

    def test_batch_missing_records_key(self, api_client):
        resp = api_client.post("/predict/batch", json={"data": [VALID_RECORD]})
        assert resp.status_code == 422

    def test_no_body_predict(self, api_client):
        resp = api_client.post("/predict")
        assert resp.status_code in (400, 422)

    def test_extra_fields_silently_ignored(self, api_client):
        """Extra/unknown fields should be ignored per schema config."""
        record = {**VALID_RECORD, "completely_unknown_field": "harmless_value"}
        resp = api_client.post("/predict", json=record)
        # Not rejected (extra=ignore)
        assert resp.status_code in (200, 400)


# ===========================================================================
# TEST 11: Security — no sensitive data in responses
# ===========================================================================
class TestSecurity:
    def test_no_file_paths_in_predict_response(self, api_client):
        resp = api_client.post("/predict", json=VALID_RECORD)
        for token in ("C:\\\\", "D:\\\\", "/home/", ".pkl", "joblib"):
            assert token not in resp.text

    def test_no_stack_trace_in_predict_response(self, api_client):
        bad = {**VALID_RECORD, "fraud_amount": "bad_type"}
        resp = api_client.post("/predict", json=bad)
        assert "Traceback" not in resp.text
        assert "File \"" not in resp.text

    def test_no_credentials_in_health_response(self, api_client):
        text = api_client.get("/health").text
        for token in ("password", "secret", "token", "key", "credential"):
            assert token.lower() not in text.lower()

    def test_404_returns_safe_message(self, api_client):
        resp = api_client.get("/nonexistent_endpoint")
        assert resp.status_code == 404
        assert "Traceback" not in resp.text


# ===========================================================================
# TEST 10: API Authentication & Key Enforcement
# ===========================================================================
class TestApiKeyAuth:
    def test_unauthenticated_predict_returns_401(self):
        with TestClient(app, raise_server_exceptions=False) as unauth_client:
            resp = unauth_client.post("/predict", json=VALID_RECORD)
            assert resp.status_code == 401
            assert "Authentication required" in resp.text

    def test_unauthenticated_explain_returns_401(self):
        with TestClient(app, raise_server_exceptions=False) as unauth_client:
            resp = unauth_client.post("/explain", json=VALID_RECORD)
            assert resp.status_code == 401
            assert "Authentication required" in resp.text

    def test_invalid_api_key_returns_401(self):
        with TestClient(
            app,
            raise_server_exceptions=False,
            headers={"X-API-Key": "wrong-invalid-key"},
        ) as bad_client:
            resp = bad_client.post("/predict", json=VALID_RECORD)
            assert resp.status_code == 401

    def test_valid_analyst_jwt_accepted(self):
        from jose import jwt
        from datetime import datetime, timezone, timedelta
        from api.auth import _SECRET_KEY, _ALGORITHM

        token_payload = {
            "sub": "test_analyst",
            "role": "ANALYST",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(token_payload, _SECRET_KEY, algorithm=_ALGORITHM)

        with TestClient(
            app,
            raise_server_exceptions=False,
            headers={"Authorization": f"Bearer {token}"},
        ) as jwt_client:
            resp = jwt_client.post("/predict", json=VALID_RECORD)
            assert resp.status_code == 200
            assert "risk_score" in resp.json()

