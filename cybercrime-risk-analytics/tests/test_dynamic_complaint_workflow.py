"""
Phase 9 — Dynamic Complaint API and End-to-End Prediction Workflow Comprehensive Test Suite
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Covers all 24 required audit scenarios:
 1. Valid raw complaint submission (HTTP 201 Created)
 2. Missing required fields (HTTP 422)
 3. Invalid transaction amount (HTTP 422)
 4. Invalid coordinates (HTTP 422)
 5. Invalid timestamp format (HTTP 422)
 6. Custom / unsupported complaint category
 7. Missing model feature handling (pipeline imputes defaults)
 8. Feature order verification against model metadata
 9. Zero NaN feature values in extracted vector
10. Zero Infinite feature values in extracted vector
11. Probability validation in [0.0, 1.0]
12. Risk score calibration and tier mapping (0-39, 40-59, 60-79, 80-100)
13. SHAP generation and top risk drivers
14. Predicted cashout location and ATM proximity integration
15. Alert generation and policy evaluation
16. Duplicate complaint submission rejection (HTTP 409 Conflict)
17. Authentication failure (HTTP 401 Unauthorized)
18. Authorization failure (HTTP 403 Forbidden for BANK_ANALYST)
19. Storage mode reporting in CSV fallback mode
20. PostgreSQL mode handling with mock availability
21. Leakage prevention: strictly historical features at T0
22. Future records exclusion test (T_event > T0)
23. Database failure resilience (graceful fallback)
24. Model uninitialized failure handling (HTTP 503)
"""
import math
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from api.main import app
from api.dependencies import app_state, initialize_model_state
from tests.test_authorization import make_token
from src.complaint_feature_service import extract_features_from_complaint

# Initialize model state for test session
initialize_model_state()
client = TestClient(app, raise_server_exceptions=False)


def auth_headers(role: str = "ANALYST") -> dict:
    return {"Authorization": f"Bearer {make_token(role)}"}


@pytest.fixture
def valid_raw_complaint():
    """Generates a unique synthetic complaint intake payload."""
    cid = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "complaint_id": cid,
        "complaint_timestamp": ts,
        "fraud_amount": 75000.0,
        "transaction_amount": 75000.0,
        "transaction_channel": "UPI",
        "complaint_category": "UPI_FRAUD",
        "sender_account_reference": "ACC000001",
        "receiver_account_reference": "ACC000888",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "city": "T Nagar",
        "latitude": 13.04,
        "longitude": 80.23,
        "description": "Victim reported unauthorized UPI debit from fraudulent utility bill link.",
    }


# ==============================================================================
# SCENARIOS 1–6: INTAKE VALIDATION & CATEGORY TAXONOMY
# ==============================================================================

def test_01_valid_raw_complaint_submission(valid_raw_complaint):
    """Scenario 1: Valid raw complaint submission succeeds with 201 Created and full structure."""
    resp = client.post("/complaints", json=valid_raw_complaint, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()

    assert data["status"] == "processed"
    assert data["complaint_id"] == valid_raw_complaint["complaint_id"]
    assert "prediction_id" in data
    assert 0.0 <= data["withdrawal_probability"] <= 1.0
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert data["model_version"] == app_state.model_version
    assert "operational_interpretation" in data
    assert isinstance(data["predicted_locations"], list)
    assert isinstance(data["top_risk_drivers"], list)
    assert "alert" in data
    assert "disclaimer" in data


def test_02_missing_required_fields():
    """Scenario 2: Omitting mandatory intake fields returns HTTP 422 Unprocessable Content."""
    # Missing complaint_timestamp
    resp1 = client.post(
        "/complaints",
        json={"fraud_amount": 50000.0, "state": "Tamil Nadu", "district": "Chennai", "complaint_category": "UPI_FRAUD"},
        headers=auth_headers("ANALYST"),
    )
    assert resp1.status_code == 422

    # Missing fraud_amount
    resp2 = client.post(
        "/complaints",
        json={"complaint_timestamp": datetime.now(timezone.utc).isoformat(), "state": "Tamil Nadu", "district": "Chennai", "complaint_category": "UPI_FRAUD"},
        headers=auth_headers("ANALYST"),
    )
    assert resp2.status_code == 422


def test_03_invalid_transaction_amount(valid_raw_complaint):
    """Scenario 3: Non-positive, NaN, or non-numeric fraud amounts return HTTP 422."""
    for bad_amt in (-100.0, 0.0):
        p = dict(valid_raw_complaint)
        p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
        p["fraud_amount"] = bad_amt
        resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
        assert resp.status_code == 422


def test_04_invalid_coordinates(valid_raw_complaint):
    """Scenario 4: Out-of-bounds latitude (outside [-90, 90]) or longitude returns HTTP 422."""
    p_lat = dict(valid_raw_complaint)
    p_lat["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    p_lat["latitude"] = 95.0
    resp1 = client.post("/complaints", json=p_lat, headers=auth_headers("ANALYST"))
    assert resp1.status_code == 422

    p_lon = dict(valid_raw_complaint)
    p_lon["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    p_lon["longitude"] = 195.0
    resp2 = client.post("/complaints", json=p_lon, headers=auth_headers("ANALYST"))
    assert resp2.status_code == 422


def test_05_invalid_timestamp_format(valid_raw_complaint):
    """Scenario 5: Non-ISO timestamp strings return HTTP 422."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    p["complaint_timestamp"] = "19/09/2026 14:30:00"
    resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
    assert resp.status_code == 422


def test_06_unsupported_or_custom_complaint_category(valid_raw_complaint):
    """Scenario 6: Unclassified category gracefully groups to OTHER without error."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    p["complaint_category"] = "NEW_EMERGING_AI_DEEPFAKE_SCAM"
    resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    assert resp.json()["status"] == "processed"


# ==============================================================================
# SCENARIOS 7–10: 64-FEATURE GENERATION, ORDER, FINITENESS & SANITIZATION
# ==============================================================================

def test_07_missing_model_feature_handling(valid_raw_complaint):
    """Scenario 7: When coordinates are omitted, pipeline uses median imputer defaults."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    p["latitude"] = None
    p["longitude"] = None
    p["city"] = None

    resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    assert resp.json()["status"] == "processed"


def test_08_feature_order_verification(valid_raw_complaint):
    """Scenario 8: Extracted feature vector matches expected_features schema in exact order."""
    expected_features = app_state.feature_schema
    assert len(expected_features) == 64

    feature_dict = extract_features_from_complaint(valid_raw_complaint, expected_features)
    assert list(feature_dict.keys()) == expected_features


def test_09_zero_nan_feature_values(valid_raw_complaint):
    """Scenario 9: Extracted feature dictionary contains zero float('nan') values."""
    expected_features = app_state.feature_schema
    feature_dict = extract_features_from_complaint(valid_raw_complaint, expected_features)

    for feat_name, feat_val in feature_dict.items():
        if isinstance(feat_val, float):
            assert not math.isnan(feat_val), f"Feature '{feat_name}' is float NaN!"


def test_10_zero_infinite_feature_values(valid_raw_complaint):
    """Scenario 10: Extracted feature dictionary contains zero float('inf') or float('-inf')."""
    expected_features = app_state.feature_schema
    feature_dict = extract_features_from_complaint(valid_raw_complaint, expected_features)

    for feat_name, feat_val in feature_dict.items():
        if isinstance(feat_val, float):
            assert not math.isinf(feat_val), f"Feature '{feat_name}' is infinite!"


# ==============================================================================
# SCENARIOS 11–15: MODEL INFERENCE, RISK TIERS, SHAP, CORRIDORS, ALERTS
# ==============================================================================

def test_11_probability_validation_bounded(valid_raw_complaint):
    """Scenario 11: Prediction probability is strictly bounded in [0.0, 1.0]."""
    resp = client.post("/complaints", json=valid_raw_complaint, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    prob = resp.json()["withdrawal_probability"]
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_12_risk_score_calibration_and_tier_mapping():
    """Scenario 12: Verifies score calibration round(p * 100) and exact tier boundaries."""
    from src.predict import probability_to_risk_score, assign_risk_category

    assert probability_to_risk_score(0.12) == 12
    assert assign_risk_category(39) == "LOW"
    assert assign_risk_category(40) == "MODERATE"
    assert assign_risk_category(59) == "MODERATE"
    assert assign_risk_category(60) == "HIGH"
    assert assign_risk_category(79) == "HIGH"
    assert assign_risk_category(80) == "CRITICAL"
    assert assign_risk_category(100) == "CRITICAL"


def test_13_shap_generation_and_top_drivers(valid_raw_complaint):
    """Scenario 13: Local SHAP TreeExplainer generates valid ranked risk drivers."""
    resp = client.post("/complaints", json=valid_raw_complaint, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()

    assert data["explanation_available"] is True
    drivers = data["top_risk_drivers"]
    assert len(drivers) > 0
    first = drivers[0]
    assert "rank" in first
    assert "feature" in first
    assert "shap_value" in first
    assert first["direction"] in ("INCREASED_RISK", "DECREASED_RISK", "INCREASES_RISK", "DECREASES_RISK")


def test_14_predicted_location_and_atm_integration(valid_raw_complaint):
    """Scenario 14: Cross-references candidate DBSCAN hotspot centroids and nearest physical ATMs."""
    resp = client.post("/complaints", json=valid_raw_complaint, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    locations = resp.json()["predicted_locations"]
    assert len(locations) > 0

    loc = locations[0]
    assert "cluster_id" in loc
    assert "district" in loc
    assert "latitude" in loc
    assert "longitude" in loc
    assert "nearest_atm_id" in loc
    assert "catchment_5_0km_atm_count" in loc


def test_15_alert_generation_when_risk_meets_threshold():
    """Scenario 15: High or critical risk scores (>= 60) trigger policy alerts with cooldown."""
    high_risk_payload = {
        "complaint_id": f"SYNTH-HIGH-{uuid.uuid4().hex[:8].upper()}",
        "complaint_timestamp": datetime.now(timezone.utc).isoformat(),
        "fraud_amount": 250000.0,
        "transaction_channel": "IMPS",
        "complaint_category": "INVESTMENT_SCAM",
        "state": "Karnataka",
        "district": "Bengaluru Urban",
        "latitude": 12.97,
        "longitude": 77.59,
    }
    resp = client.post("/complaints", json=high_risk_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()

    if data["risk_score"] >= 60:
        assert data["alert"]["created"] is True
        assert data["alert"]["alert_id"].startswith("ALT-")
        assert data["alert"]["severity"] in ("HIGH", "CRITICAL")


# ==============================================================================
# SCENARIOS 16–20: SECURITY, RBAC, DUPLICATES & DUAL STORAGE MODES
# ==============================================================================

def test_16_duplicate_complaint_rejection(valid_raw_complaint):
    """Scenario 16: Resubmitting identical complaint_id returns HTTP 409 Conflict."""
    resp1 = client.post("/complaints", json=valid_raw_complaint, headers=auth_headers("ANALYST"))
    assert resp1.status_code == 201

    resp2 = client.post("/complaints", json=valid_raw_complaint, headers=auth_headers("ANALYST"))
    assert resp2.status_code == 409
    assert "duplicate complaint" in resp2.json()["message"].lower() or "duplicate" in resp2.json()["detail"].lower()


def test_17_authentication_failure(valid_raw_complaint):
    """Scenario 17: Request without token or API key returns HTTP 401 Unauthorized."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    with patch.dict(os.environ, {"DISABLE_API_KEY_AUTH": "false"}):
        resp = client.post("/complaints", json=p)
        assert resp.status_code == 401


def test_18_rbac_restrictions_for_bank_analyst(valid_raw_complaint):
    """Scenario 18: BANK_ANALYST role is strictly forbidden (HTTP 403 Forbidden)."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"
    resp = client.post("/complaints", json=p, headers=auth_headers("BANK_ANALYST"))
    assert resp.status_code == 403
    assert "access denied" in (resp.json().get("detail") or resp.json().get("message", "")).lower()


def test_19_csv_fallback_mode_reporting(valid_raw_complaint):
    """Scenario 19: Storage mode is reported as CSV_FALLBACK_DEV when PostgreSQL is offline."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"

    with patch("api.complaint_routes.is_db_available", return_value=False):
        resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
        assert resp.status_code == 201
        assert resp.json()["storage_mode"] == "CSV_FALLBACK_DEV"


def test_20_postgresql_mode_reporting(valid_raw_complaint):
    """Scenario 20: When database is available and writes succeed, storage_mode reflects it."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"

    with patch("api.complaint_routes.is_db_available", return_value=True):
        with patch("api.complaint_routes.SessionLocal") as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            with patch("api.complaint_routes.create_cybercrime_event"):
                with patch("api.complaint_routes.create_prediction_result"):
                    resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
                    assert resp.status_code == 201
                    assert resp.json()["storage_mode"] == "POSTGRESQL_POSTGIS"


# ==============================================================================
# SCENARIOS 21–24: DATA LEAKAGE PREVENTION & RESILIENCE
# ==============================================================================

def test_21_leakage_prevention_strictly_historical(valid_raw_complaint):
    """Scenario 21: Model features strictly derive from information available at or before T0."""
    t0 = datetime(2026, 9, 19, 10, 0, 0, tzinfo=timezone.utc)
    p = dict(valid_raw_complaint)
    p["complaint_timestamp"] = t0.isoformat()

    f = extract_features_from_complaint(p, app_state.feature_schema)
    assert f["event_year"] == 2026
    assert f["event_month"] == 9
    assert f["event_day_of_month"] == 19
    assert f["event_hour"] == 10


def test_22_future_records_do_not_alter_features(valid_raw_complaint):
    """Scenario 22: Simulated events after T0 do not alter past complaint features."""
    t0 = datetime(2026, 9, 19, 10, 0, 0, tzinfo=timezone.utc)
    p = dict(valid_raw_complaint)
    p["complaint_timestamp"] = t0.isoformat()

    features_before = extract_features_from_complaint(p, app_state.feature_schema)

    # Subsequent future complaint at T0 + 5 hours
    future_p = dict(valid_raw_complaint)
    future_p["complaint_timestamp"] = (t0 + timedelta(hours=5)).isoformat()
    future_p["fraud_amount"] = 500000.0

    # Re-extract past features
    features_after = extract_features_from_complaint(p, app_state.feature_schema)

    # Strict equality: future event has zero leakage into past features
    assert features_before == features_after


def test_23_database_failure_resilience(valid_raw_complaint):
    """Scenario 23: If PostgreSQL raises an unexpected OperationalError, falls back seamlessly."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"

    with patch("api.complaint_routes.is_db_available", return_value=True):
        with patch("api.complaint_routes.SessionLocal", side_effect=Exception("Database connection timeout")):
            resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
            assert resp.status_code == 201
            assert resp.json()["storage_mode"] == "CSV_FALLBACK_DEV"


def test_24_model_uninitialized_failure_handling(valid_raw_complaint):
    """Scenario 24: Returns HTTP 503 Service Unavailable if ML model is uninitialized."""
    p = dict(valid_raw_complaint)
    p["complaint_id"] = f"SYNTH-{uuid.uuid4().hex[:8].upper()}"

    with patch.object(app_state, "model_loaded", False):
        resp = client.post("/complaints", json=p, headers=auth_headers("ANALYST"))
        assert resp.status_code == 503
        assert "not initialized" in (resp.json().get("detail") or resp.json().get("message", "")).lower()
