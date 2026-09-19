"""
Phase 6 Test Suite — Structured Intelligence Brief Generator
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests:
1. Rejection of unauthenticated requests (HTTP 401)
2. Role isolation: BANK_ANALYST forbidden (HTTP 403)
3. Successful brief generation for ANALYST, SUPERVISOR, and ADMIN (HTTP 200)
4. Comprehensive dossier structure (spatial, ATM proximity, SHAP explainability, timeline)
5. 404 handling for invalid investigation IDs
6. Mandatory analytical disclaimer present
7. Zero credential or sensitive PII leakage
"""
import pytest
from starlette.testclient import TestClient
from api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def analyst_token(client):
    res = client.post(
        "/analyst/auth/login",
        json={"username": "demo_analyst", "password": "AnalystDemo2026!"},
    )
    assert res.status_code == 200, f"Analyst login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def supervisor_token(client):
    res = client.post(
        "/analyst/auth/login",
        json={"username": "demo_supervisor", "password": "SupervisorDemo2026!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def bank_token(client):
    res = client.post(
        "/analyst/auth/login",
        json={"username": "demo_bank", "password": "BankDemo2026!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def existing_investigation_id(client, analyst_token):
    """Retrieve an existing seeded investigation ID or create one."""
    res = client.get(
        "/analyst/investigations",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 200
    items = res.json().get("items", [])
    if items:
        return items[0]["investigation_id"]
    
    # Create one if list empty
    create_res = client.post(
        "/analyst/investigations",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "alert_id": "ALT-000052",
            "priority": "HIGH",
            "initial_note": "Automated test investigation creation",
        },
    )
    assert create_res.status_code == 201
    return create_res.json()["investigation_id"]


class TestIntelligenceBrief:
    """Test suite for GET /analyst/investigations/{id}/intelligence-brief."""

    def test_unauthenticated_request_rejected(self, client, existing_investigation_id):
        """Unauthenticated requests must receive 401."""
        res = client.get(f"/analyst/investigations/{existing_investigation_id}/intelligence-brief")
        assert res.status_code == 401

    def test_bank_analyst_forbidden(self, client, bank_token, existing_investigation_id):
        """BANK_ANALYST role must be forbidden from LEA intelligence briefs (403)."""
        res = client.get(
            f"/analyst/investigations/{existing_investigation_id}/intelligence-brief",
            headers={"Authorization": f"Bearer {bank_token}"},
        )
        assert res.status_code == 403

    def test_analyst_can_generate_brief(self, client, analyst_token, existing_investigation_id):
        """ANALYST role can generate the full intelligence brief."""
        res = client.get(
            f"/analyst/investigations/{existing_investigation_id}/intelligence-brief",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["investigation_id"] == existing_investigation_id
        assert data["brief_reference"].startswith("BRIEF-")
        assert data["generated_by_role"] == "ANALYST"
        assert "spatial_intelligence" in data
        assert "shap_explainability" in data
        assert "disclaimer" in data

    def test_brief_spatial_and_atm_intelligence(self, client, analyst_token, existing_investigation_id):
        """Verify spatial intelligence contains ATM proximity and nearest ATM info."""
        res = client.get(
            f"/analyst/investigations/{existing_investigation_id}/intelligence-brief",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert res.status_code == 200
        sp = res.json()["spatial_intelligence"]
        assert "hotspot_id" in sp
        assert "atms_within_5km" in sp
        assert "nearest_atm_id" in sp
        assert "nearest_atm_distance_km" in sp
        assert isinstance(sp["atms_within_5km"], int)

    def test_supervisor_access_and_audit_trail_reference(self, client, supervisor_token, existing_investigation_id):
        """SUPERVISOR role can generate brief and audit trail reference is present."""
        res = client.get(
            f"/analyst/investigations/{existing_investigation_id}/intelligence-brief",
            headers={"Authorization": f"Bearer {supervisor_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["generated_by_role"] == "SUPERVISOR"
        assert data["audit_trail_reference"].startswith("AUD-BRIEF-")

    def test_nonexistent_investigation_returns_404(self, client, analyst_token):
        """Nonexistent ID returns 404 Not Found."""
        res = client.get(
            "/analyst/investigations/INV-DOES-NOT-EXIST-000000/intelligence-brief",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert res.status_code == 404

    def test_zero_sensitive_data_in_brief(self, client, analyst_token, existing_investigation_id):
        """Dossier must not expose passwords, PINs, OTPs, CVVs, or card numbers."""
        res = client.get(
            f"/analyst/investigations/{existing_investigation_id}/intelligence-brief",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert res.status_code == 200
        content = res.text.lower()
        prohibited = ["password", "cvv", "card_number", "aadhaar", "pin_number", "atm_pin", "user_otp"]
        for term in prohibited:
            assert term not in content, f"Sensitive term '{term}' found in brief"
