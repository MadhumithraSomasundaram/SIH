"""
Secure Banking Interface Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests the read-only Banking Interface and BANK_ANALYST role:
1. Authentication with demo_bank credentials and JWT token issuance.
2. Authorization enforcement:
   - BANK_ANALYST can access /bank/alerts.
   - ADMIN can access /bank/alerts.
   - ANALYST is rejected (403) on /bank/alerts.
   - SUPERVISOR is rejected (403) on /bank/alerts.
   - Unauthenticated access is rejected (401).
3. Reverse role isolation:
   - BANK_ANALYST is rejected (403) from /analyst/* endpoints.
4. ATM proximity filtering:
   - Alerts are linked only to hotspots within proximity radius of specified bank ATMs.
   - Configurable radius parameter alters matched hotspot/alert count.
   - Severity filter works correctly.
5. Mandatory Disclaimer:
   - Every response contains: "Analytical alert — authorized human review required. Does not establish criminal activity."
"""
import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client with mocked model dependencies."""
    with patch("api.dependencies.initialize_model_state") as mock_init:
        mock_init.return_value = None
        with patch("api.dependencies.app_state") as mock_state:
            mock_state.model_loaded = False
            mock_state.pipeline_loaded = False
            mock_state.load_error = "Test mode — model not loaded"
            from api.main import app
            return TestClient(app, raise_server_exceptions=False)


def make_token(role: str, username: str = "test_user") -> str:
    """Create test JWT token using identical secret and algorithm as analyst routes."""
    from jose import jwt
    secret = os.getenv(
        "ANALYST_JWT_SECRET",
        "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184"
    )
    return jwt.encode({"sub": username, "role": role}, secret, algorithm="HS256")


def auth_headers(role: str, username: str = "test_user") -> dict:
    return {"Authorization": f"Bearer {make_token(role, username)}"}


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestBankAuthentication:
    """Authentication tests for the banking role."""

    def test_demo_bank_login_success(self, client):
        """demo_bank can log in and receives JWT with role BANK_ANALYST."""
        resp = client.post("/bank/auth/login", json={
            "username": "demo_bank",
            "password": "BankDemo2026!"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "BANK_ANALYST"
        assert "Demo Bank Analyst" in data.get("display_name", "")

    def test_demo_bank_login_via_analyst_route_success(self, client):
        """Unified auth: demo_bank can also authenticate via /analyst/auth/login."""
        resp = client.post("/analyst/auth/login", json={
            "username": "demo_bank",
            "password": "BankDemo2026!"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "BANK_ANALYST"

    def test_demo_bank_invalid_password_rejected(self, client):
        """Invalid password for demo_bank is rejected with 401."""
        resp = client.post("/bank/auth/login", json={
            "username": "demo_bank",
            "password": "WrongPassword2026!"
        })
        assert resp.status_code == 401

    def test_bank_me_endpoint_returns_bank_analyst_info(self, client):
        """GET /bank/auth/me returns current user profile."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/bank/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "demo_bank"
        assert data["role"] == "BANK_ANALYST"


class TestBankAuthorizationAndIsolation:
    """Role-based access control and bi-directional isolation."""

    def test_unauthenticated_bank_alerts_rejected(self, client):
        """Unauthenticated requests to /bank/alerts receive 401."""
        resp = client.get("/bank/alerts")
        assert resp.status_code == 401

    def test_bank_analyst_can_access_bank_alerts(self, client):
        """BANK_ANALYST has permission for /bank/alerts."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/bank/alerts", headers=headers)
        assert resp.status_code == 200

    def test_admin_can_access_bank_alerts(self, client):
        """ADMIN has administrative permission for /bank/alerts."""
        headers = auth_headers("ADMIN", "demo_admin")
        resp = client.get("/bank/alerts", headers=headers)
        assert resp.status_code == 200

    def test_analyst_cannot_access_bank_alerts(self, client):
        """Role isolation: standard ANALYST is forbidden (403) from /bank/alerts."""
        headers = auth_headers("ANALYST", "demo_analyst")
        resp = client.get("/bank/alerts", headers=headers)
        assert resp.status_code == 403
        data = resp.json()
        err_text = data.get("message") or data.get("detail", "")
        assert "Access denied" in err_text

    def test_supervisor_cannot_access_bank_alerts(self, client):
        """Role isolation: SUPERVISOR is forbidden (403) from /bank/alerts."""
        headers = auth_headers("SUPERVISOR", "demo_supervisor")
        resp = client.get("/bank/alerts", headers=headers)
        assert resp.status_code == 403

    def test_bank_analyst_cannot_access_analyst_overview(self, client):
        """Reverse isolation: BANK_ANALYST is forbidden (403) from /analyst/overview."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/analyst/overview", headers=headers)
        assert resp.status_code == 403

    def test_bank_analyst_cannot_access_analyst_alerts(self, client):
        """Reverse isolation: BANK_ANALYST is forbidden (403) from /analyst/alerts."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/analyst/alerts", headers=headers)
        assert resp.status_code == 403

    def test_bank_analyst_cannot_create_investigations(self, client):
        """Reverse isolation: BANK_ANALYST cannot write or create investigations."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.post("/analyst/investigations", headers=headers, json={
            "alert_id": "ALT-000001",
            "priority": "HIGH"
        })
        assert resp.status_code == 403

    def test_bank_analyst_cannot_access_audit_log(self, client):
        """Reverse isolation: BANK_ANALYST is forbidden (403) from /analyst/audit."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/analyst/audit", headers=headers)
        assert resp.status_code == 403


class TestBankAlertsProximityFiltering:
    """Tests for ATM proximity spatial filtering."""

    def test_bank_alerts_default_parameters(self, client):
        """GET /bank/alerts returns alerts scoped to BANK001 within 5.0km by default."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/bank/alerts", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["bank_id"] == "BANK001"
        assert data["radius_km"] == 5.0
        assert data["total_bank_atms"] > 0
        assert data["total_matching_hotspots"] > 0
        assert len(data["alerts"]) > 0

        # Check alert attributes
        first_alert = data["alerts"][0]
        assert "alert_id" in first_alert
        assert "severity" in first_alert
        assert "nearest_atm_id" in first_alert
        assert "distance_to_atm_km" in first_alert
        assert first_alert["distance_to_atm_km"] <= 5.0

    def test_configurable_radius_filter(self, client):
        """Smaller radius matches fewer or equal hotspots/alerts than larger radius."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp_small = client.get("/bank/alerts?bank_id=BANK001&radius_km=0.2", headers=headers)
        resp_large = client.get("/bank/alerts?bank_id=BANK001&radius_km=5.0", headers=headers)

        assert resp_small.status_code == 200
        assert resp_large.status_code == 200

        data_small = resp_small.json()
        data_large = resp_large.json()

        assert data_small["total_matching_hotspots"] <= data_large["total_matching_hotspots"]
        assert data_small["total_alerts"] <= data_large["total_alerts"]

    def test_severity_filter(self, client):
        """Filter by severity returns only alerts matching that severity."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/bank/alerts?bank_id=BANK001&severity=CRITICAL", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        for alert in data["alerts"]:
            assert alert["severity"] == "CRITICAL"

    def test_unknown_bank_id_returns_empty(self, client):
        """Unknown bank_id returns valid structure with 0 ATMs and 0 alerts."""
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/bank/alerts?bank_id=NONEXISTENT_BANK", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_bank_atms"] == 0
        assert data["total_matching_hotspots"] == 0
        assert data["total_alerts"] == 0
        assert data["alerts"] == []


class TestMandatoryDisclaimer:
    """Verify mandatory analytical disclaimer on all bank responses."""

    def test_mandatory_disclaimer_in_response(self, client):
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        resp = client.get("/bank/alerts", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        expected_disclaimer = "Analytical alert — authorized human review required. Does not establish criminal activity."
        assert data["disclaimer"] == expected_disclaimer
        for alert in data["alerts"]:
            assert alert["disclaimer"] == expected_disclaimer
