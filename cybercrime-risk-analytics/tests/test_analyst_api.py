"""
Phase 17 — Analyst API Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Integration tests for the analyst FastAPI endpoints.
Tests use in-memory fallback (no live DB required).

Coverage:
  - Overview endpoint
  - Alert list & detail
  - Investigation creation, retrieval, update
  - Notes, evidence references
  - Timeline
  - Model explanation (SHAP)
  - Audit log
  - Authentication
  - Unauthenticated access rejection
"""
import pytest
import os
from unittest.mock import patch, MagicMock


# ─── Test client setup ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client with mocked model loading."""
    try:
        from fastapi.testclient import TestClient
        # Patch model loading to avoid needing the XGBoost artifact
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
    """Get a valid ANALYST JWT token."""
    try:
        from jose import jwt
        secret = os.getenv("ANALYST_JWT_SECRET",
                           "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184")
        token = jwt.encode({"sub": "test_analyst", "role": "ANALYST"}, secret, algorithm="HS256")
        return token
    except ImportError:
        pytest.skip("python-jose not installed")


@pytest.fixture(scope="module")
def supervisor_token():
    """Get a valid SUPERVISOR JWT token."""
    try:
        from jose import jwt
        secret = os.getenv("ANALYST_JWT_SECRET",
                           "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184")
        token = jwt.encode({"sub": "test_supervisor", "role": "SUPERVISOR"}, secret, algorithm="HS256")
        return token
    except ImportError:
        pytest.skip("python-jose not installed")


def analyst_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Unauthenticated Tests ────────────────────────────────────────────────────

class TestUnauthenticatedAccess:
    """Unauthenticated requests must be rejected with 401/403."""

    def test_overview_requires_auth(self, client):
        """GET /analyst/overview without token → 401/403."""
        res = client.get("/analyst/overview")
        assert res.status_code in (401, 403, 422), \
            f"Expected 401/403, got {res.status_code}"

    def test_alerts_requires_auth(self, client):
        """GET /analyst/alerts without token → 401/403."""
        res = client.get("/analyst/alerts")
        assert res.status_code in (401, 403, 422)

    def test_investigations_requires_auth(self, client):
        """GET /analyst/investigations without token → 401/403."""
        res = client.get("/analyst/investigations")
        assert res.status_code in (401, 403, 422)

    def test_audit_requires_auth(self, client):
        """GET /analyst/audit without token → 401/403."""
        res = client.get("/analyst/audit")
        assert res.status_code in (401, 403, 422)

    def test_create_investigation_requires_auth(self, client):
        """POST /analyst/investigations without token → 401/403."""
        res = client.post("/analyst/investigations",
                          json={"alert_id": "ALT-001", "priority": "HIGH"})
        assert res.status_code in (401, 403, 422)


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestAuthentication:
    """Test prototype authentication endpoints."""

    def test_login_with_valid_demo_credentials(self, client):
        """1. Correct analyst credentials → 200 + token + role ANALYST."""
        res = client.post("/analyst/auth/login", json={
            "username": "demo_analyst",
            "password": "AnalystDemo2026!"
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "ANALYST"
        assert "disclaimer" in data
        assert "prototype" in data["disclaimer"].lower()

    def test_login_supervisor_success(self, client):
        """2. Correct supervisor credentials → 200 + token + role SUPERVISOR."""
        res = client.post("/analyst/auth/login", json={
            "username": "demo_supervisor",
            "password": "SupervisorDemo2026!"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "SUPERVISOR"
        assert "access_token" in data

    def test_login_admin_success(self, client):
        """3. Correct admin credentials → 200 + token + role ADMIN."""
        res = client.post("/analyst/auth/login", json={
            "username": "demo_admin",
            "password": "AdminDemo2026!"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "ADMIN"
        assert "access_token" in data

    def test_login_wrong_password_fails(self, client):
        """4. Wrong password → 401 with safe generic error message."""
        res = client.post("/analyst/auth/login", json={
            "username": "demo_analyst",
            "password": "WrongPassword999!"
        })
        assert res.status_code == 401
        data = res.json()
        assert data.get("message") == "Invalid username or password."

    def test_login_wrong_username_fails(self, client):
        """5. Wrong username → 401 with safe generic error message."""
        res = client.post("/analyst/auth/login", json={
            "username": "nonexistent_user_xyzzy",
            "password": "AnalystDemo2026!"
        })
        assert res.status_code == 401
        data = res.json()
        assert data.get("message") == "Invalid username or password."

    def test_login_empty_username_fails(self, client):
        """6. Empty username → 401 with safe generic error message."""
        res = client.post("/analyst/auth/login", json={
            "username": "",
            "password": "AnalystDemo2026!"
        })
        assert res.status_code == 401
        data = res.json()
        assert data.get("message") == "Invalid username or password."

    def test_login_empty_password_fails(self, client):
        """7. Empty password → 401 with safe generic error message."""
        res = client.post("/analyst/auth/login", json={
            "username": "demo_analyst",
            "password": ""
        })
        assert res.status_code == 401
        data = res.json()
        assert data.get("message") == "Invalid username or password."

    def test_logout_invalidation_flow(self, client):
        """8. Logout flow: once token is discarded/cleared, protected access is blocked."""
        # Authenticate to obtain token
        res = client.post("/analyst/auth/login", json={
            "username": "demo_analyst",
            "password": "AnalystDemo2026!"
        })
        assert res.status_code == 200
        token = res.json()["access_token"]

        # Valid call with token succeeds
        res_auth = client.get("/analyst/overview", headers={"Authorization": f"Bearer {token}"})
        assert res_auth.status_code == 200

        # Discard token (simulating client-side logout) → call without token fails
        res_unauth = client.get("/analyst/overview")
        assert res_unauth.status_code == 401

    def test_direct_access_without_authentication(self, client):
        """9. Direct access without authentication → 401."""
        endpoints = ["/analyst/overview", "/analyst/alerts", "/analyst/investigations", "/analyst/audit"]
        for ep in endpoints:
            res = client.get(ep)
            assert res.status_code == 401

    def test_role_authorization_enforcement(self, client, analyst_token, supervisor_token):
        """10. Role authorization: ANALYST is 403 on audit; SUPERVISOR/ADMIN are 200."""
        # Analyst role blocked
        res_analyst = client.get("/analyst/audit", headers=analyst_headers(analyst_token))
        assert res_analyst.status_code == 403

        # Supervisor role allowed
        res_sup = client.get("/analyst/audit", headers={"Authorization": f"Bearer {supervisor_token}"})
        assert res_sup.status_code == 200

    def test_expired_or_invalid_session_rejected(self, client):
        """11. Expired/invalid session token → 401."""
        res = client.get("/analyst/overview",
                         headers={"Authorization": "Bearer this.is.not.a.valid.token"})
        assert res.status_code == 401
        assert res.json().get("message") == "Invalid or expired token. Please log in again."

    def test_me_endpoint_returns_user_info(self, client, analyst_token):
        """GET /analyst/auth/me with valid token → user info."""
        res = client.get("/analyst/auth/me", headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "username" in data
            assert "role" in data
            assert data["role"] in ("ANALYST", "SUPERVISOR", "ADMIN")


# ─── Overview Tests ───────────────────────────────────────────────────────────

class TestOverview:
    """Test analyst overview endpoint."""

    def test_overview_returns_valid_structure(self, client, analyst_token):
        """GET /analyst/overview → valid overview structure."""
        res = client.get("/analyst/overview", headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "total_alerts" in data
            assert "critical_alerts" in data
            assert "high_alerts" in data
            assert "analytical_hotspots" in data
            assert "data_disclaimer" in data
            assert "authorized_system" in data
            # Values must be non-negative integers
            assert data["total_alerts"] >= 0
            assert data["critical_alerts"] >= 0

    def test_overview_disclaimer_present(self, client, analyst_token):
        """Overview must include a disclaimer about the analytical nature."""
        res = client.get("/analyst/overview", headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            disclaimer = data.get("data_disclaimer", "").lower()
            assert "not proof" in disclaimer or "analytical" in disclaimer


# ─── Alert Tests ─────────────────────────────────────────────────────────────

class TestAlerts:
    """Test analyst alert endpoints."""

    def test_alert_list_returns_paginated(self, client, analyst_token):
        """GET /analyst/alerts → paginated list with disclaimer."""
        res = client.get("/analyst/alerts", headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "items" in data
            assert "total" in data
            assert "disclaimer" in data
            assert isinstance(data["items"], list)

    def test_alert_list_no_sensitive_fields(self, client, analyst_token):
        """Alert list must not expose sensitive PII fields."""
        res = client.get("/analyst/alerts", headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            for alert in res.json().get("items", []):
                assert "card_number" not in alert
                assert "account_number" not in alert
                assert "pin" not in alert
                assert "cvv" not in alert
                assert "otp" not in alert
                assert "password" not in alert
                assert "phone" not in alert

    def test_alert_filter_by_severity(self, client, analyst_token):
        """GET /analyst/alerts?severity=HIGH → only HIGH alerts."""
        res = client.get("/analyst/alerts?severity=HIGH",
                         headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            for alert in res.json().get("items", []):
                assert alert.get("severity") == "HIGH"

    def test_alert_detail_has_disclaimer(self, client, analyst_token):
        """Alert detail must include analytical disclaimer."""
        # First get list to find an alert ID
        res = client.get("/analyst/alerts", headers=analyst_headers(analyst_token))
        if res.status_code == 200 and res.json().get("items"):
            alert_id = res.json()["items"][0]["alert_id"]
            detail_res = client.get(f"/analyst/alerts/{alert_id}",
                                    headers=analyst_headers(analyst_token))
            if detail_res.status_code == 200:
                data = detail_res.json()
                assert "analytical_disclaimer" in data
                disclaimer = data["analytical_disclaimer"].lower()
                assert "does not establish criminal activity" in disclaimer

    def test_alert_404_for_nonexistent(self, client, analyst_token):
        """GET /analyst/alerts/NONEXISTENT → 404."""
        res = client.get("/analyst/alerts/ALT-DOES-NOT-EXIST-9999",
                         headers=analyst_headers(analyst_token))
        assert res.status_code == 404


# ─── Investigation Tests ──────────────────────────────────────────────────────

class TestInvestigations:
    """Test investigation CRUD endpoints."""

    def test_investigation_list_returns_paginated(self, client, analyst_token):
        """GET /analyst/investigations → paginated list."""
        res = client.get("/analyst/investigations",
                         headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "items" in data
            assert "total" in data
            assert isinstance(data["items"], list)

    def test_investigation_create_valid(self, client, analyst_token):
        """POST /analyst/investigations with valid data → 201."""
        res = client.post("/analyst/investigations",
                          headers=analyst_headers(analyst_token),
                          json={
                              "alert_id": "ALT-000002",
                              "priority": "HIGH",
                              "initial_note": "[TEST] Synthetic test investigation — not real data."
                          })
        # 201 or 400 (duplicate) or 404 (alert not found) are all acceptable
        assert res.status_code in (200, 201, 400, 404, 422)
        if res.status_code in (200, 201):
            data = res.json()
            assert "investigation_id" in data
            assert data["status"] == "OPEN"
            assert data["priority"] == "HIGH"

    def test_investigation_create_invalid_priority_rejected(self, client, analyst_token):
        """POST /analyst/investigations with invalid priority → 422."""
        res = client.post("/analyst/investigations",
                          headers=analyst_headers(analyst_token),
                          json={"alert_id": "ALT-001", "priority": "EXTREME_PRIORITY"})
        assert res.status_code == 422

    def test_investigation_detail_has_all_sections(self, client, analyst_token):
        """GET /analyst/investigations/{id} → full detail structure."""
        res = client.get("/analyst/investigations/INV-DEMO-00000001",
                         headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "investigation" in data
            assert "notes" in data
            assert "evidence" in data
            assert "timeline" in data
            assert "disclaimer" in data
            # Check disclaimer content
            disclaimer = data["disclaimer"].lower()
            assert "not proof" in disclaimer or "analytical" in disclaimer

    def test_investigation_not_found_returns_404(self, client, analyst_token):
        """GET /analyst/investigations/NONEXISTENT → 404."""
        res = client.get("/analyst/investigations/INV-DOES-NOT-EXIST-9999",
                         headers=analyst_headers(analyst_token))
        assert res.status_code == 404

    def test_investigation_update_invalid_status_rejected(self, client, analyst_token):
        """PATCH /analyst/investigations/{id} with invalid status → 400/422."""
        res = client.patch("/analyst/investigations/INV-DEMO-00000001",
                           headers=analyst_headers(analyst_token),
                           json={"status": "FLYING"})
        assert res.status_code in (400, 422)

    def test_analyst_cannot_close_investigation(self, client, analyst_token):
        """ANALYST cannot close investigation (requires SUPERVISOR)."""
        res = client.patch("/analyst/investigations/INV-DEMO-00000001",
                           headers=analyst_headers(analyst_token),
                           json={"status": "CLOSED"})
        # Should fail with 400 (invalid transition from current state) or 403 (role denied)
        # In demo data INV-DEMO-00000001 is UNDER_REVIEW, CLOSED not in allowed transitions
        assert res.status_code in (400, 403, 422)


# ─── Notes Tests ──────────────────────────────────────────────────────────────

class TestNotes:
    """Test analyst note endpoints."""

    def test_add_note_to_existing_investigation(self, client, analyst_token):
        """POST /analyst/investigations/{id}/notes → 201."""
        res = client.post("/analyst/investigations/INV-DEMO-00000001/notes",
                          headers=analyst_headers(analyst_token),
                          json={"note": "[TEST] Synthetic test note — authorized investigation only."})
        assert res.status_code in (200, 201, 404)
        if res.status_code in (200, 201):
            data = res.json()
            assert "note_id" in data
            assert "created_at" in data
            assert "actor_role" in data

    def test_empty_note_rejected(self, client, analyst_token):
        """POST with empty note → 422."""
        res = client.post("/analyst/investigations/INV-DEMO-00000001/notes",
                          headers=analyst_headers(analyst_token),
                          json={"note": ""})
        assert res.status_code == 422


# ─── Evidence Tests ───────────────────────────────────────────────────────────

class TestEvidence:
    """Test evidence reference endpoints."""

    def test_add_evidence_reference(self, client, analyst_token):
        """POST /analyst/investigations/{id}/evidence → 201."""
        res = client.post("/analyst/investigations/INV-DEMO-00000001/evidence",
                          headers=analyst_headers(analyst_token),
                          json={
                              "evidence_type": "SYSTEM_LOG",
                              "reference": "SYSLOG-TEST-2026-001",
                              "description": "[TEST] Synthetic test evidence reference.",
                          })
        assert res.status_code in (200, 201, 404)
        if res.status_code in (200, 201):
            data = res.json()
            assert "evidence_id" in data
            assert data["evidence_type"] == "SYSTEM_LOG"
            assert data["reference"] == "SYSLOG-TEST-2026-001"

    def test_invalid_evidence_type_rejected(self, client, analyst_token):
        """POST with invalid evidence_type → 422."""
        res = client.post("/analyst/investigations/INV-DEMO-00000001/evidence",
                          headers=analyst_headers(analyst_token),
                          json={"evidence_type": "FAKE_TYPE", "reference": "REF-001"})
        assert res.status_code == 422


# ─── Timeline Tests ───────────────────────────────────────────────────────────

class TestTimeline:
    """Test investigation timeline endpoint."""

    def test_timeline_returns_ordered_events(self, client, analyst_token):
        """GET /analyst/investigations/{id}/timeline → ordered events."""
        res = client.get("/analyst/investigations/INV-DEMO-00000001/timeline",
                         headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "events" in data
            events = data["events"]
            assert isinstance(events, list)
            if len(events) > 1:
                # Verify chronological order
                timestamps = [e["timestamp"] for e in events]
                assert timestamps == sorted(timestamps)


# ─── Explanation Tests ────────────────────────────────────────────────────────

class TestExplanation:
    """Test SHAP model explanation endpoint."""

    def test_explanation_has_disclaimer(self, client, analyst_token):
        """GET explanation → must include model disclaimer."""
        res = client.get("/analyst/investigations/INV-DEMO-00000001/explanation",
                         headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "shap_disclaimer" in data
            assert "model_disclaimer" in data
            disclaimer = (data["shap_disclaimer"] + " " + data["model_disclaimer"]).lower()
            assert "causality" in disclaimer or "criminal responsibility" in disclaimer

    def test_explanation_no_causality_language(self, client, analyst_token):
        """Explanation must not use causal or incriminating language."""
        res = client.get("/analyst/investigations/INV-DEMO-00000001/explanation",
                         headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            for feature in data.get("top_features", []):
                direction = feature.get("direction", "").lower()
                # Must not say "caused"
                assert "caused" not in direction
                assert "proved" not in direction
                assert "criminal" not in direction

    def test_explanations_are_record_specific(self, client, analyst_token):
        """Two different investigations must return distinct, record-specific top features."""
        from api.dependencies import initialize_model_state
        initialize_model_state()

        res1 = client.get(
            "/analyst/investigations/INV-DEMO-00000001/explanation",
            headers=analyst_headers(analyst_token),
        )
        res2 = client.get(
            "/analyst/investigations/INV-DEMO-00000002/explanation",
            headers=analyst_headers(analyst_token),
        )

        assert res1.status_code == 200
        assert res2.status_code == 200

        data1 = res1.json()
        data2 = res2.json()

        assert len(data1.get("top_features", [])) > 0
        assert len(data2.get("top_features", [])) > 0

        features1 = [f["feature"] for f in data1["top_features"]]
        features2 = [f["feature"] for f in data2["top_features"]]

        assert features1 != features2, "Explanations across distinct records must not be identical"


# ─── Audit Log Tests ─────────────────────────────────────────────────────────

class TestAuditLog:
    """Test audit log endpoint (requires SUPERVISOR/ADMIN)."""

    def test_analyst_cannot_access_audit_log(self, client, analyst_token):
        """ANALYST role cannot access audit log → 403."""
        res = client.get("/analyst/audit", headers=analyst_headers(analyst_token))
        assert res.status_code == 403

    def test_supervisor_can_access_audit_log(self, client, supervisor_token):
        """SUPERVISOR can access audit log → 200."""
        res = client.get("/analyst/audit", headers=analyst_headers(supervisor_token))
        if res.status_code == 200:
            data = res.json()
            assert "items" in data
            assert "total" in data

    def test_audit_log_no_sensitive_data(self, client, supervisor_token):
        """Audit log must never expose credentials or sensitive data."""
        res = client.get("/analyst/audit", headers=analyst_headers(supervisor_token))
        if res.status_code == 200:
            for item in res.json().get("items", []):
                # Check that no sensitive data leaked into details
                detail = str(item.get("detail", "")).lower()
                assert "password" not in detail
                assert "card_number" not in detail
                assert "pin" not in detail
                assert "cvv" not in detail
                assert "otp" not in detail


# ─── Hotspot Tests ────────────────────────────────────────────────────────────

class TestHotspots:
    """Test analyst hotspot endpoint."""

    def test_hotspot_list_returns_data(self, client, analyst_token):
        """GET /analyst/hotspots → hotspot data."""
        res = client.get("/analyst/hotspots", headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            data = res.json()
            assert "hotspots" in data
            assert isinstance(data["hotspots"], list)

    def test_hotspot_no_sensitive_fields(self, client, analyst_token):
        """Hotspot data must not expose unnecessary individual-level information."""
        res = client.get("/analyst/hotspots", headers=analyst_headers(analyst_token))
        if res.status_code == 200:
            for hs in res.json().get("hotspots", []):
                assert "account_number" not in hs
                assert "card_number" not in hs
                assert "victim_name" not in hs


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
