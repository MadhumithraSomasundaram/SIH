"""
Phase 11 — Investigation Outcome Feedback & Ground-Truth Loop Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests cover:
  - Outcome feedback creation via API
  - Input validation (PII rejection, negative amounts, invalid categories)
  - Investigation outcome listing
  - Global paginated outcome listing with category filtering
  - Outcome feedback statistics & empirical precision calculation
  - Role-based access control (ANALYST/SUPERVISOR allowed, BANK_ANALYST forbidden, 401 unauthenticated)
  - Automatic timeline event (OUTCOME_LOGGED) generation
  - Audit logging (RECORD_OUTCOME_FEEDBACK)
  - CSV fallback persistence to phase21_outcome_feedback.csv
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client with mocked model loading."""
    try:
        from fastapi.testclient import TestClient
        with patch("api.dependencies.initialize_model_state") as mock_init:
            mock_init.return_value = None
            with patch("api.dependencies.app_state") as mock_state:
                mock_state.model_loaded = False
                mock_state.pipeline_loaded = False
                mock_state.load_error = "Test mode — model not loaded"
                from api.main import app
                return TestClient(app, raise_server_exceptions=False)
    except Exception as e:
        pytest.skip(f"Could not create test client: {e}")


@pytest.fixture(scope="module")
def analyst_token():
    from jose import jwt
    secret = os.getenv("ANALYST_JWT_SECRET",
                       "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184")
    return jwt.encode({"sub": "test_analyst", "role": "ANALYST"}, secret, algorithm="HS256")


@pytest.fixture(scope="module")
def supervisor_token():
    from jose import jwt
    secret = os.getenv("ANALYST_JWT_SECRET",
                       "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184")
    return jwt.encode({"sub": "test_supervisor", "role": "SUPERVISOR"}, secret, algorithm="HS256")


@pytest.fixture(scope="module")
def bank_token():
    from jose import jwt
    secret = os.getenv("ANALYST_JWT_SECRET",
                       "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184")
    return jwt.encode({"sub": "test_bank", "role": "BANK_ANALYST"}, secret, algorithm="HS256")


# ─── Tests ─────────────────────────────────────────────────────────────────────

def test_record_outcome_feedback_success(client, analyst_token):
    """Test recording a valid post-patrol outcome feedback."""
    inv_id = "INV-DEMO-00000001"
    payload = {
        "outcome_category": "THWARTED_CASHOUT",
        "notes": "Patrol team intercepted suspicious mule activity at ATM cluster. Cashout thwarted.",
        "amount_prevented": 85000.0,
        "actual_amount_lost": 0.0,
        "atm_id_actual": "ATM-0899",
    }
    resp = client.post(
        f"/analyst/investigations/{inv_id}/outcomes",
        json=payload,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["investigation_id"] == inv_id
    assert data["outcome_category"] == "THWARTED_CASHOUT"
    assert data["amount_prevented"] == 85000.0
    assert data["actual_amount_lost"] == 0.0
    assert data["atm_id_actual"] == "ATM-0899"
    assert "FBK-" in data["feedback_id"]
    assert data["reported_by_role"] == "ANALYST"


def test_record_outcome_invalid_category(client, analyst_token):
    """Invalid outcome category must be rejected."""
    inv_id = "INV-DEMO-00000001"
    payload = {
        "outcome_category": "SUPER_ILLEGAL_FRAUD",
        "notes": "Observed illicit cashout occurred.",
    }
    resp = client.post(
        f"/analyst/investigations/{inv_id}/outcomes",
        json=payload,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code in (400, 422)


def test_record_outcome_rejects_pii(client, analyst_token):
    """Notes containing sensitive authentication credentials (e.g. CVV, OTP) must be rejected."""
    inv_id = "INV-DEMO-00000001"
    payload = {
        "outcome_category": "CONFIRMED_CASHOUT",
        "notes": "Suspect used card PIN 1234 and stolen OTP 987654 to withdraw funds.",
    }
    resp = client.post(
        f"/analyst/investigations/{inv_id}/outcomes",
        json=payload,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code in (400, 422)


def test_record_outcome_rejects_negative_amount(client, analyst_token):
    """Negative prevented or loss amounts must fail validation."""
    inv_id = "INV-DEMO-00000001"
    payload = {
        "outcome_category": "THWARTED_CASHOUT",
        "notes": "Valid patrol report note with non-negative check.",
        "amount_prevented": -500.0,
    }
    resp = client.post(
        f"/analyst/investigations/{inv_id}/outcomes",
        json=payload,
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code in (400, 422)


def test_list_investigation_outcomes(client, analyst_token):
    """Get all outcomes for an investigation."""
    inv_id = "INV-DEMO-00000001"
    resp = client.get(
        f"/analyst/investigations/{inv_id}/outcomes",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(o["outcome_category"] == "THWARTED_CASHOUT" for o in data)


def test_list_all_outcomes_paginated(client, analyst_token):
    """Get global paginated outcomes across all investigations."""
    resp = client.get(
        "/analyst/outcomes?skip=0&limit=10",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_list_outcomes_category_filter(client, analyst_token):
    """Filter global outcomes by outcome_category."""
    resp = client.get(
        "/analyst/outcomes?outcome_category=CONFIRMED_CASHOUT",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for item in data["items"]:
        assert item["outcome_category"] == "CONFIRMED_CASHOUT"


def test_outcome_statistics_calculation(client, analyst_token):
    """Verify aggregated outcome telemetry and empirical precision rate."""
    resp = client.get(
        "/analyst/outcomes/statistics",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert resp.status_code == 200, resp.text
    stats = resp.json()
    assert stats["total_feedback_count"] >= 2
    assert "outcomes_by_category" in stats
    assert "operational_precision_rate" in stats
    assert 0.0 <= stats["operational_precision_rate"] <= 1.0
    assert stats["total_amount_prevented"] >= 0.0
    assert stats["total_actual_loss"] >= 0.0
    assert "disclaimer" in stats


def test_outcome_rbac_bank_analyst_forbidden(client, bank_token):
    """Bank analyst role must be rejected (403) from accessing law enforcement outcome feedback."""
    inv_id = "INV-DEMO-00000001"
    # POST
    resp_post = client.post(
        f"/analyst/investigations/{inv_id}/outcomes",
        json={"outcome_category": "CONFIRMED_CASHOUT", "notes": "Bank test note"},
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert resp_post.status_code == 403

    # GET
    resp_get = client.get(
        f"/analyst/investigations/{inv_id}/outcomes",
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert resp_get.status_code == 403

    # Global
    resp_all = client.get(
        "/analyst/outcomes",
        headers={"Authorization": f"Bearer {bank_token}"},
    )
    assert resp_all.status_code == 403


def test_outcome_unauthenticated_rejected(client):
    """Unauthenticated requests must be rejected with 401."""
    inv_id = "INV-DEMO-00000001"
    resp = client.get(f"/analyst/investigations/{inv_id}/outcomes")
    assert resp.status_code == 401


def test_outcome_generates_timeline_and_audit(client, supervisor_token):
    """Recording outcome feedback should generate an OUTCOME_LOGGED timeline event and an audit record."""
    inv_id = "INV-DEMO-00000002"
    payload = {
        "outcome_category": "UNPRODUCTIVE_PATROL",
        "notes": "Patrol dispatched to Tiruchirappalli beat; zero suspicious persons detected at ATM.",
        "verified_by_supervisor": True,
    }
    resp = client.post(
        f"/analyst/investigations/{inv_id}/outcomes",
        json=payload,
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    assert resp.status_code == 201

    # Check timeline
    timeline_resp = client.get(
        f"/analyst/investigations/{inv_id}/timeline",
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    timeline_data = timeline_resp.json()
    events = [e["event_type"] for e in timeline_data.get("events", [])]
    assert "OUTCOME_LOGGED" in events


    # Check audit log
    audit_resp = client.get(
        "/analyst/audit?action=RECORD_OUTCOME_FEEDBACK",
        headers={"Authorization": f"Bearer {supervisor_token}"},
    )
    assert audit_resp.status_code == 200
    items = audit_resp.json()["items"]
    assert len(items) >= 1
    assert any(a["action"] == "RECORD_OUTCOME_FEEDBACK" for a in items)


def test_csv_fallback_persistence():
    """Verify that phase21_outcome_feedback.csv is updated and readable."""
    from database.investigation_crud import _FEEDBACK_CSV_PATH
    assert _FEEDBACK_CSV_PATH.exists()
    assert _FEEDBACK_CSV_PATH.stat().st_size > 0
    content = _FEEDBACK_CSV_PATH.read_text(encoding="utf-8")
    assert "feedback_id" in content
    assert "THWARTED_CASHOUT" in content or "CONFIRMED_CASHOUT" in content
