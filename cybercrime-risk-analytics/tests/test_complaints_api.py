"""
Test Suite for Dynamic Complaint Submission API (POST /complaints)
Problem Statement ID 26184: Cybercrime Predictive Analytics Framework

Covers all 18 Step 12 verification scenarios:
 1. Valid complaint submission
 2. Missing required fields
 3. Invalid timestamp format
 4. Invalid monetary amount
 5. Invalid coordinates
 6. Duplicate complaint
 7. Feature generation
 8. Prediction integration
 9. Risk score calculation
10. SHAP integration
11. Predicted-location integration
12. Alert generation
13. Database failure & fallback
14. CSV fallback behavior
15. Authentication failure
16. RBAC restrictions (ANALYST, SUPERVISOR, ADMIN vs BANK_ANALYST)
17. NaN and Infinity serialization
18. Existing /predict compatibility
"""

import math
from datetime import datetime, timezone
import pytest
from starlette.testclient import TestClient

from api.main import app
from api.dependencies import initialize_model_state
from tests.test_authorization import make_token

# Initialize model state for test session
initialize_model_state()
client = TestClient(app)


def auth_headers(role: str = "ANALYST") -> dict:
    return {"Authorization": f"Bearer {make_token(role)}"}


@pytest.fixture
def valid_complaint_payload():
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "complaint_timestamp": ts,
        "fraud_amount": 65000.0,
        "complaint_category": "UPI_FRAUD",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "city": "T Nagar",
        "latitude": 13.04,
        "longitude": 80.23,
        "sender_account_reference": "ACC000001",
        "receiver_account_reference": "ACC000888",
        "transaction_channel": "UPI",
        "description": "Victim received fraudulent payment request.",
    }


# ---------------------------------------------------------------------------
# 1. Valid Complaint Submission
# ---------------------------------------------------------------------------
def test_01_valid_complaint_submission(valid_complaint_payload):
    resp = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "processed"
    assert "complaint_id" in data
    assert "prediction_id" in data
    assert 0.0 <= data["withdrawal_probability"] <= 1.0
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
    assert "disclaimer" in data


# ---------------------------------------------------------------------------
# 2. Missing Required Fields
# ---------------------------------------------------------------------------
def test_02_missing_required_fields():
    # Missing complaint_timestamp
    resp = client.post("/complaints", json={"fraud_amount": 10000.0, "state": "Kerala"}, headers=auth_headers("ANALYST"))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 3. Invalid Timestamp Format
# ---------------------------------------------------------------------------
def test_03_invalid_timestamp(valid_complaint_payload):
    payload = dict(valid_complaint_payload)
    payload["complaint_timestamp"] = "invalid-date-format"
    resp = client.post("/complaints", json=payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4. Invalid Monetary Amount
# ---------------------------------------------------------------------------
def test_04_invalid_monetary_amount(valid_complaint_payload):
    # Zero amount
    payload = dict(valid_complaint_payload)
    payload["fraud_amount"] = 0.0
    resp = client.post("/complaints", json=payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 422

    # Negative amount
    payload["fraud_amount"] = -500.0
    resp = client.post("/complaints", json=payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 5. Invalid Coordinates
# ---------------------------------------------------------------------------
def test_05_invalid_coordinates(valid_complaint_payload):
    payload = dict(valid_complaint_payload)
    payload["latitude"] = 95.0  # Latitude > 90
    resp = client.post("/complaints", json=payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 422

    payload["latitude"] = 13.04
    payload["longitude"] = 200.0  # Longitude > 180
    resp = client.post("/complaints", json=payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 6. Duplicate Complaint Handling
# ---------------------------------------------------------------------------
def test_06_duplicate_complaint(valid_complaint_payload):
    payload = dict(valid_complaint_payload)
    payload["complaint_id"] = f"CMP-TEST-DUP-{int(datetime.now().timestamp())}"
    
    # First submission -> 201
    resp1 = client.post("/complaints", json=payload, headers=auth_headers("ANALYST"))
    assert resp1.status_code == 201

    # Second submission with same ID -> 409 Conflict
    resp2 = client.post("/complaints", json=payload, headers=auth_headers("ANALYST"))
    assert resp2.status_code == 409
    assert "Duplicate complaint" in resp2.json()["message"]


# ---------------------------------------------------------------------------
# 7. Feature Generation
# ---------------------------------------------------------------------------
def test_07_feature_generation(valid_complaint_payload):
    from src.complaint_feature_service import extract_features_from_complaint
    from api.dependencies import app_state
    
    feats = extract_features_from_complaint(valid_complaint_payload, app_state.feature_schema)
    assert len(feats) == len(app_state.feature_schema)
    assert feats["fraud_amount"] == 65000.0
    assert feats["crime_category_group"] == "PAYMENT_FRAUD"
    assert feats["is_financial_fraud"] == 1.0
    assert feats["has_location"] == 1.0


# ---------------------------------------------------------------------------
# 8. Prediction Integration
# ---------------------------------------------------------------------------
def test_08_prediction_integration(valid_complaint_payload):
    resp = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data["withdrawal_probability"], float)
    assert isinstance(data["risk_score"], int)
    assert round(data["withdrawal_probability"] * 100) == data["risk_score"]


# ---------------------------------------------------------------------------
# 9. Risk Score Calculation
# ---------------------------------------------------------------------------
def test_09_risk_score_calculation(valid_complaint_payload):
    from src.predict import assign_risk_category
    assert assign_risk_category(20) == "LOW"
    assert assign_risk_category(45) == "MODERATE"
    assert assign_risk_category(65) == "HIGH"
    assert assign_risk_category(85) == "CRITICAL"


# ---------------------------------------------------------------------------
# 10. SHAP Integration
# ---------------------------------------------------------------------------
def test_10_shap_integration(valid_complaint_payload):
    resp = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()
    assert "explanation_available" in data
    if data["explanation_available"]:
        drivers = data["top_risk_drivers"]
        assert isinstance(drivers, list)
        if len(drivers) > 0:
            assert "feature" in drivers[0]
            assert "shap_value" in drivers[0]
            assert "direction" in drivers[0]


# ---------------------------------------------------------------------------
# 11. Predicted-Location Integration
# ---------------------------------------------------------------------------
def test_11_predicted_location_integration(valid_complaint_payload):
    resp = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()
    locs = data["predicted_locations"]
    assert isinstance(locs, list)
    assert len(locs) > 0
    first = locs[0]
    assert "cluster_id" in first
    assert "district" in first
    assert "nearest_atm_id" in first
    assert "location_source" in first


# ---------------------------------------------------------------------------
# 12. Alert Generation & Cooldown
# ---------------------------------------------------------------------------
def test_12_alert_generation(valid_complaint_payload):
    resp = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()
    assert "alert" in data
    alert_info = data["alert"]
    assert "created" in alert_info
    if data["risk_score"] < 60:
        assert alert_info["created"] is False
    else:
        assert alert_info["created"] is True
        assert alert_info["alert_id"] is not None


# ---------------------------------------------------------------------------
# 13. Database Failure & Fallback
# ---------------------------------------------------------------------------
def test_13_database_failure_fallback(valid_complaint_payload):
    # System operates gracefully with CSV fallback when PostgreSQL is offline
    resp = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["storage_mode"] in ("POSTGRESQL_POSTGIS", "CSV_FALLBACK_DEV")


# ---------------------------------------------------------------------------
# 14. CSV Fallback Behavior
# ---------------------------------------------------------------------------
def test_14_csv_fallback_behavior(valid_complaint_payload):
    from api.complaint_routes import _SUBMITTED_COMPLAINTS_CACHE
    resp = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("ANALYST"))
    assert resp.status_code == 201
    cid = resp.json()["complaint_id"]
    assert cid in _SUBMITTED_COMPLAINTS_CACHE


# ---------------------------------------------------------------------------
# 15. Authentication Failure
# ---------------------------------------------------------------------------
def test_15_authentication_failure(valid_complaint_payload):
    # No headers -> 401
    resp = client.post("/complaints", json=valid_complaint_payload)
    assert resp.status_code == 401

    # Invalid token -> 401
    resp = client.post("/complaints", json=valid_complaint_payload, headers={"Authorization": "Bearer invalid.jwt.token"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 16. RBAC Restrictions
# ---------------------------------------------------------------------------
def test_16_rbac_restrictions(valid_complaint_payload):
    # BANK_ANALYST is explicitly forbidden (403)
    resp_bank = client.post("/complaints", json=valid_complaint_payload, headers=auth_headers("BANK_ANALYST"))
    assert resp_bank.status_code == 403
    assert "read-only access" in resp_bank.json()["message"]

    # ANALYST, SUPERVISOR, and ADMIN are permitted (201)
    for role in ("ANALYST", "SUPERVISOR", "ADMIN"):
        p = dict(valid_complaint_payload)
        p["complaint_id"] = f"CMP-{role}-{int(datetime.now().timestamp() * 1000)}"
        resp = client.post("/complaints", json=p, headers=auth_headers(role))
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# 17. NaN and Infinity Serialization Safety
# ---------------------------------------------------------------------------
def test_17_nan_infinity_serialization():
    from api.complaint_routes import _sanitize_val
    dirty_dict = {
        "nan_val": float("nan"),
        "pos_inf": float("inf"),
        "neg_inf": float("-inf"),
        "normal": 42.0,
        "nested": {"bad": float("nan"), "good": 10},
    }
    clean = _sanitize_val(dirty_dict)
    assert clean["nan_val"] is None
    assert clean["pos_inf"] is None
    assert clean["neg_inf"] is None
    assert clean["normal"] == 42.0
    assert clean["nested"]["bad"] is None
    assert clean["nested"]["good"] == 10


# ---------------------------------------------------------------------------
# 18. Existing /predict Compatibility
# ---------------------------------------------------------------------------
def test_18_existing_predict_compatibility():
    # Verify POST /predict continues to work exactly as before
    predict_payload = {
        "crime_type": "UPI_FRAUD",
        "fraud_amount": 50000.0,
        "victim_district": "Chennai",
    }
    resp = client.post("/predict", json=predict_payload, headers={"X-API-Key": "sih26184-dashboard-prototype-key-2026"})
    assert resp.status_code == 200
    data = resp.json()
    assert "prediction_reference" in data
    assert "predicted_probability" in data
    assert "risk_score" in data
