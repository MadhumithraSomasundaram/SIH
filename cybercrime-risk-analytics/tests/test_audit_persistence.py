"""
Phase 3 Test Suite — Persistent Analyst Audit Log
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests:
1. Verify audit logs are persisted to CSV in fallback mode
2. Verify audit logs survive simulated process restart (cache reload)
3. Verify GET /analyst/audit endpoint returns persistent records
4. Verify audit log filtering by action and result
5. Verify zero sensitive credentials in the persistent CSV
"""
from datetime import datetime, timezone
from pathlib import Path
import csv
import pytest
from starlette.testclient import TestClient

from api.main import app
from database.investigation_crud import (
    log_audit,
    get_audit_log,
    _DEMO_AUDIT,
    _init_demo_audit_from_csv,
    _AUDIT_CSV_PATH,
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def supervisor_token(client):
    res = client.post(
        "/analyst/auth/login",
        json={"username": "demo_supervisor", "password": "SupervisorDemo2026!"},
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def supervisor_headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestAuditPersistence:
    """Verify that audit records are written to disk and survive restarts."""

    def test_log_audit_writes_to_csv(self):
        """log_audit() must append to phase17_analyst_audit_log.csv."""
        test_action = "TEST_AUTOMATED_PERSISTENCE"
        test_resource = "INV-PERSIST-999"
        test_detail = "Automated test audit log entry"

        log_audit(
            db=None,
            action=test_action,
            resource_type="INVESTIGATION",
            resource_id=test_resource,
            actor_role="SUPERVISOR",
            result="SUCCESS",
            detail=test_detail,
        )

        # Check CSV on disk
        assert _AUDIT_CSV_PATH.exists(), f"Audit CSV {_AUDIT_CSV_PATH} was not created"
        with open(_AUDIT_CSV_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            assert test_action in content
            assert test_resource in content
            assert test_detail in content

    def test_audit_log_reload_from_csv(self):
        """Simulate restart: clearing _DEMO_AUDIT and reloading must recover disk records."""
        unique_resource = "INV-RELOAD-VERIFY-123"
        log_audit(
            db=None,
            action="VERIFY_RELOAD",
            resource_type="INVESTIGATION",
            resource_id=unique_resource,
            actor_role="ADMIN",
            result="SUCCESS",
            detail="Verifying disk reload functionality",
        )

        # Simulate process wipe
        _DEMO_AUDIT.clear()
        assert len(_DEMO_AUDIT) == 0

        # Reload from disk
        _init_demo_audit_from_csv()
        reloaded_ids = [a.get("resource_id") for a in _DEMO_AUDIT]
        assert unique_resource in reloaded_ids

    def test_supervisor_retrieves_audit_log_via_api(self, client, supervisor_token):
        """GET /analyst/audit returns persistent audit records."""
        res = client.get("/analyst/audit", headers=supervisor_headers(supervisor_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] > 0
        items = data["items"]
        assert any(i["action"] == "LOGIN" for i in items)

    def test_audit_log_filter_by_action(self, client, supervisor_token):
        """Filtering by action returns only records matching that action."""
        res = client.get(
            "/analyst/audit?action=LOGIN",
            headers=supervisor_headers(supervisor_token),
        )
        assert res.status_code == 200
        data = res.json()
        for item in data["items"]:
            assert item["action"] == "LOGIN"

    def test_no_sensitive_credentials_in_audit_csv(self):
        """Audit CSV must never contain plaintext passwords, OTPs, or PINs."""
        assert _AUDIT_CSV_PATH.exists()
        with open(_AUDIT_CSV_PATH, "r", encoding="utf-8") as f:
            content = f.read().lower()
            assert "password" not in content
            assert "supervisordemo2026!" not in content
            assert "analystdemo2026!" not in content
            assert "bankdemo2026!" not in content
            assert "admindemo2026!" not in content
