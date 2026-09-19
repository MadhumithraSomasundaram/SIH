"""
Phase 16 — Alert API Integration Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import pytest
from starlette.testclient import TestClient

from api.main import app
from database.crud import create_alert
from database.schemas import AlertCreate


@pytest.fixture(scope="module")
def client():
    with TestClient(
        app,
        headers={"X-API-Key": "sih26184-dashboard-prototype-key-2026"},
    ) as c:
        yield c


@pytest.fixture(autouse=True)
def seed_test_alert():
    """Ensure at least one predictable test alert exists in local cache."""
    test_dto = AlertCreate(
        alert_id="ALT-TEST-9999",
        alert_type="CRITICAL_RISK_LOCATION",
        severity="CRITICAL",
        status="NEW",
        prediction_reference="CASE-SEED-01",
        risk_score=92,
        predicted_probability=0.92,
        operational_message="Test analytical alert for unit verification.",
        human_review_required=True,
    )
    create_alert(None, test_dto)


class TestAlertQueryEndpoints:
    """Tests for listing and filtering alerts."""

    def test_get_alerts_list(self, client):
        response = client.get("/alerts?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 1

    def test_get_alerts_severity_filter(self, client):
        response = client.get("/alerts?severity=CRITICAL")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["severity"] == "CRITICAL"

    def test_get_single_alert_success(self, client):
        response = client.get("/alerts/ALT-TEST-9999")
        assert response.status_code == 200
        data = response.json()
        assert data["alert_id"] == "ALT-TEST-9999"
        assert data["risk_score"] == 92
        assert "authorized human review required" in data["disclaimer"].lower()

    def test_get_single_alert_not_found(self, client):
        response = client.get("/alerts/ALT-NONEXISTENT")
        assert response.status_code == 404
        msg = response.json().get("message") or response.json().get("detail", "")
        assert "not found" in msg.lower()


class TestAlertLifecycleTransitions:
    """Tests for alert state machine workflow."""

    def test_valid_lifecycle_transitions(self, client):
        aid = "ALT-TEST-9999"

        # 1. Acknowledge
        r_ack = client.patch(f"/alerts/{aid}/acknowledge", json={"notes": "Analyst acknowledged"})
        assert r_ack.status_code == 200
        assert r_ack.json()["status"] == "ACKNOWLEDGED"

        # 2. Review
        r_rev = client.patch(f"/alerts/{aid}/review", json={"notes": "Investigating pattern"})
        assert r_rev.status_code == 200
        assert r_rev.json()["status"] == "IN_REVIEW"

        # 3. Resolve
        r_res = client.patch(f"/alerts/{aid}/resolve", json={"actor_type": "AUTHORIZED_USER", "notes": "Reviewed and concluded"})
        assert r_res.status_code == 200
        assert r_res.json()["status"] == "RESOLVED"

    def test_invalid_status_transition_rejected(self, client):
        # Setup a fresh alert
        aid = "ALT-TEST-INVALID"
        create_alert(None, AlertCreate(
            alert_id=aid,
            alert_type="HIGH_RISK_LOCATION",
            severity="HIGH",
            status="NEW",
            risk_score=70,
            operational_message="Testing transition error",
        ))

        # Attempt illegal transition: NEW -> RESOLVED directly
        res = client.patch(f"/alerts/{aid}/resolve", json={"notes": "Illegal skip"})
        assert res.status_code == 400
        msg = res.json().get("message") or res.json().get("detail", "")
        assert "invalid status transition" in msg.lower()

    def test_critical_auto_resolve_forbidden(self, client):
        aid = "ALT-CRIT-AUTORES"
        create_alert(None, AlertCreate(
            alert_id=aid,
            alert_type="CRITICAL_RISK_LOCATION",
            severity="CRITICAL",
            status="IN_REVIEW",
            risk_score=95,
            operational_message="Critical testing auto-resolve protection",
        ))

        # SYSTEM actor attempting to resolve CRITICAL alert must be rejected
        res = client.patch(f"/alerts/{aid}/resolve", json={"actor_type": "SYSTEM", "notes": "Automated close"})
        assert res.status_code == 400
        msg = res.json().get("message") or res.json().get("detail", "")
        assert "authorized human review is strictly required" in msg.lower()


class TestAlertStatisticsAndGeneration:
    """Tests for statistics and pipeline triggering."""

    def test_get_statistics(self, client):
        response = client.get("/alerts/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_alerts" in data
        assert "critical_alerts" in data
        assert "high_alerts" in data
        assert data["total_alerts"] >= 1

    def test_post_generate_dry_run(self, client):
        response = client.post("/alerts/generate?dry_run=true")
        assert response.status_code == 200
        data = response.json()
        assert "generated" in data
        assert "critical" in data
        assert "high" in data
        assert "duplicates_skipped" in data
        assert "disclaimer" in data

    def test_unauthenticated_alerts_returns_401(self):
        unauth = TestClient(app, raise_server_exceptions=False)
        response = unauth.get("/alerts")
        assert response.status_code == 401
        assert "Authentication required" in response.text


class TestAlertStatusPersistence:
    """Verifies that alert status updates persist to CSV and survive server reboots."""

    def test_alert_status_persists_to_csv_and_survives_restart(self, client):
        import pandas as pd
        from database.crud import (
            _ALERTS_CSV_PATH,
            _LOCAL_ALERTS_CACHE,
            reload_alerts_cache,
            create_alert,
        )
        from database.schemas import AlertCreate

        test_id = "ALT-TEST-PERSIST-01"
        test_dto = AlertCreate(
            alert_id=test_id,
            alert_type="HIGH_RISK_LOCATION",
            severity="HIGH",
            status="NEW",
            risk_score=75,
            operational_message="Persistence test alert",
            human_review_required=True,
        )
        create_alert(None, test_dto)

        # 1. Acknowledge the alert via PATCH endpoint
        res = client.patch(f"/alerts/{test_id}/acknowledge", json={"notes": "Analyst acknowledge"})
        assert res.status_code == 200
        assert res.json()["status"] == "ACKNOWLEDGED"

        # Verify it was written to CSV
        df = pd.read_csv(_ALERTS_CSV_PATH)
        match = df[df["alert_id"] == test_id]
        assert not match.empty, "Alert was not written to phase16_demo_alerts.csv"
        assert match.iloc[0]["status"] == "ACKNOWLEDGED"

        # 2. Simulate server restart: clear memory cache and re-initialize from CSV
        _LOCAL_ALERTS_CACHE.clear()
        assert test_id not in _LOCAL_ALERTS_CACHE

        reload_alerts_cache()
        assert test_id in _LOCAL_ALERTS_CACHE
        assert _LOCAL_ALERTS_CACHE[test_id]["status"] == "ACKNOWLEDGED"

        # Verify via GET endpoint
        res_get = client.get(f"/alerts/{test_id}")
        assert res_get.status_code == 200
        assert res_get.json()["status"] == "ACKNOWLEDGED"

        # 3. Transition to IN_REVIEW
        res_rev = client.patch(f"/alerts/{test_id}/review", json={"notes": "Analyst review"})
        assert res_rev.status_code == 200
        assert res_rev.json()["status"] == "IN_REVIEW"

        # Verify CSV updated
        df = pd.read_csv(_ALERTS_CSV_PATH)
        assert df[df["alert_id"] == test_id].iloc[0]["status"] == "IN_REVIEW"

        # Simulate second restart
        _LOCAL_ALERTS_CACHE.clear()
        reload_alerts_cache()
        assert _LOCAL_ALERTS_CACHE[test_id]["status"] == "IN_REVIEW"

        # 4. Resolve the alert
        res_res = client.patch(f"/alerts/{test_id}/resolve", json={"notes": "Analyst resolved"})
        assert res_res.status_code == 200
        assert res_res.json()["status"] == "RESOLVED"

        # Verify CSV updated
        df = pd.read_csv(_ALERTS_CSV_PATH)
        assert df[df["alert_id"] == test_id].iloc[0]["status"] == "RESOLVED"

        # Simulate third restart
        _LOCAL_ALERTS_CACHE.clear()
        reload_alerts_cache()
        assert _LOCAL_ALERTS_CACHE[test_id]["status"] == "RESOLVED"


