"""
Phase 8 — Alerts and Notification System Fixes Unit & Integration Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests cover:
1. JSON RFC 8259 compliance (No bare NaN / Infinity in responses).
2. GET /analyst/alerts serialization and field sanitization.
3. GET /analyst/alerts/{alert_id} found (200) vs missing (404).
4. Alert status transitions and error handling (404 for unknown, 400 for invalid).
5. Role-based access control (RBAC): BANK_ANALYST forbidden (403) from mutating/listing analyst alerts.
6. Calibration & validation: exact thresholds (0-39, 40-59, 60-79, 80-100) and NaN rejection.
7. Cooldown & deduplication: cooldown window adherence and escalation support.
"""
import json
import math
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database.crud import (
    _LOCAL_ALERTS_CACHE,
    _sanitize_alert_record,
    get_alert,
    get_alerts,
    update_alert_status,
)
from src.alert_engine import (
    assign_alert_severity,
    deduplicate_alerts,
    make_dedup_key,
    validate_alert_inputs,
)


# ─────────────────────────────────────────────────────────────────────────────
# Test Tokens and Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_test_token(role: str, username: str = "test_user") -> str:
    """Generates test JWT token matching analyst routes configuration."""
    from jose import jwt
    secret = os.getenv(
        "ANALYST_JWT_SECRET",
        "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184",
    )
    return jwt.encode({"sub": username, "role": role}, secret, algorithm="HS256")


def auth_headers(role: str, username: str = "test_user") -> dict:
    return {"Authorization": f"Bearer {make_test_token(role, username)}"}


@pytest.fixture(scope="module")
def client():
    """Create FastAPI test client with mocked model dependencies."""
    with patch("api.dependencies.initialize_model_state") as mock_init:
        mock_init.return_value = None
        with patch("api.dependencies.app_state") as mock_state:
            mock_state.model_loaded = False
            mock_state.pipeline_loaded = False
            mock_state.load_error = "Test mode"
            from api.main import app
            return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────────────────────
# 1. JSON Sanitization & NaN Immunity Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAlertSerializationAndNaNImmunity:
    """Verifies that alerts containing float NaN, Inf, and invalid strings are sanitized."""

    def test_sanitize_alert_record_replaces_nan_with_none(self):
        raw_alert = {
            "alert_id": "ALT-TEST-NAN",
            "risk_score": float("nan"),
            "predicted_probability": float("nan"),
            "latitude": float("nan"),
            "longitude": float("nan"),
            "status": "NEW",
            "severity": "HIGH",
            "operational_message": "Test message with invalid numeric values",
        }
        sanitized = _sanitize_alert_record(raw_alert)

        assert sanitized["risk_score"] is None
        assert sanitized["predicted_probability"] is None
        assert sanitized["latitude"] is None
        assert sanitized["longitude"] is None
        assert sanitized["status"] == "NEW"

        # Verify strict RFC 8259 serialization (allow_nan=False must not raise)
        serialized = json.dumps(sanitized, allow_nan=False, default=str)
        assert ": NaN" not in serialized and ":NaN" not in serialized and " NaN" not in serialized
        assert "null" in serialized

    def test_sanitize_alert_record_preserves_valid_zero_and_numbers(self):
        raw_alert = {
            "alert_id": "ALT-TEST-ZERO",
            "risk_score": 0,
            "predicted_probability": 0.0,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "event_count": 0,
            "status": "NEW",
        }
        sanitized = _sanitize_alert_record(raw_alert)

        assert sanitized["risk_score"] == 0
        assert sanitized["predicted_probability"] == 0.0
        assert sanitized["latitude"] == 12.9716
        assert sanitized["longitude"] == 77.5946
        assert sanitized["event_count"] == 0

    def test_get_analyst_alerts_returns_rfc8259_json(self, client):
        """GET /analyst/alerts returns 200 and strict JSON without bare NaN tokens."""
        # Inject an alert with float NaN directly into cache
        _LOCAL_ALERTS_CACHE["ALT-NAN-INJECTED"] = {
            "alert_id": "ALT-NAN-INJECTED",
            "alert_type": "HIGH_RISK_LOCATION",
            "severity": "HIGH",
            "status": "NEW",
            "risk_score": float("nan"),
            "predicted_probability": float("nan"),
            "latitude": float("nan"),
            "longitude": float("nan"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        headers = auth_headers("ANALYST", "test_analyst")
        res = client.get("/analyst/alerts", headers=headers)
        assert res.status_code == 200

        # Strict JSON deserialization check
        raw_text = res.text
        # Assert no bare NaN tokens as per RFC 8259
        assert " NaN" not in raw_text
        assert ":NaN" not in raw_text
        assert ": NaN" not in raw_text
        assert " Infinity" not in raw_text

        data = json.loads(raw_text)
        assert "items" in data
        assert isinstance(data["items"], list)

        # Check that injected alert has None/null values
        injected = next((a for a in data["items"] if a.get("alert_id") == "ALT-NAN-INJECTED"), None)
        if injected:
            assert injected["risk_score"] is None
            assert injected["predicted_probability"] is None
            assert injected["latitude"] is None

    def test_get_single_alert_found_and_sanitized(self, client):
        """GET /analyst/alerts/{alert_id} returns 200 with sanitized data."""
        # Setup clean test alert
        _LOCAL_ALERTS_CACHE["ALT-TEST-SINGLE"] = {
            "alert_id": "ALT-TEST-SINGLE",
            "alert_type": "CRITICAL_RISK_LOCATION",
            "severity": "CRITICAL",
            "status": "NEW",
            "risk_score": 88,
            "predicted_probability": 0.88,
            "latitude": 13.0827,
            "longitude": 80.2707,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        headers = auth_headers("ANALYST")
        res = client.get("/analyst/alerts/ALT-TEST-SINGLE", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["alert_id"] == "ALT-TEST-SINGLE"
        assert data["risk_score"] == 88
        assert "analytical_disclaimer" in data

    def test_get_single_alert_not_found(self, client):
        """GET /analyst/alerts/{alert_id} returns 404 for non-existent alert."""
        headers = auth_headers("ANALYST")
        res = client.get("/analyst/alerts/ALT-NON-EXISTENT-9999", headers=headers)
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Alert Status Transition & Workflow Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAlertStatusTransitions:
    """Verifies valid and invalid status transitions on /alerts/{alert_id}/*."""

    def test_transition_unknown_alert_returns_404(self, client):
        """Attempting to acknowledge an unknown alert returns 404."""
        headers = auth_headers("ANALYST")
        res = client.patch(
            "/alerts/ALT-UNKNOWN-404/acknowledge",
            headers=headers,
            json={"notes": "Test acknowledgment", "actor_type": "ANALYST"},
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_valid_status_progression(self, client):
        """Transitions NEW -> ACKNOWLEDGED -> IN_REVIEW -> RESOLVED."""
        alert_id = "ALT-WORKFLOW-TEST"
        _LOCAL_ALERTS_CACHE[alert_id] = {
            "alert_id": alert_id,
            "alert_type": "HIGH_RISK_LOCATION",
            "severity": "HIGH",
            "status": "NEW",
            "risk_score": 70,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        headers = auth_headers("ANALYST")

        # 1. NEW -> ACKNOWLEDGED
        res1 = client.patch(f"/alerts/{alert_id}/acknowledge", headers=headers, json={})
        assert res1.status_code == 200
        assert res1.json()["status"] == "ACKNOWLEDGED"

        # 2. ACKNOWLEDGED -> IN_REVIEW
        res2 = client.patch(f"/alerts/{alert_id}/review", headers=headers, json={})
        assert res2.status_code == 200
        assert res2.json()["status"] == "IN_REVIEW"

        # 3. IN_REVIEW -> RESOLVED
        res3 = client.patch(f"/alerts/{alert_id}/resolve", headers=headers, json={})
        assert res3.status_code == 200
        assert res3.json()["status"] == "RESOLVED"

    def test_invalid_status_transition_returns_400(self, client):
        """Attempting an invalid transition (e.g. NEW -> RESOLVED directly) returns 400."""
        alert_id = "ALT-INVALID-TRANSITION"
        _LOCAL_ALERTS_CACHE[alert_id] = {
            "alert_id": alert_id,
            "alert_type": "HIGH_RISK_LOCATION",
            "severity": "HIGH",
            "status": "NEW",
            "risk_score": 70,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        headers = auth_headers("ANALYST")
        # Direct resolution without ACK or IN_REVIEW must be rejected
        res = client.patch(f"/alerts/{alert_id}/resolve", headers=headers, json={})
        assert res.status_code == 400
        assert "invalid status transition" in res.json()["detail"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Role-Based Access Control (RBAC) Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAlertRBAC:
    """Verifies that BANK_ANALYST cannot access or modify analytical alerts."""

    def test_bank_analyst_cannot_list_analyst_alerts(self, client):
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        res = client.get("/analyst/alerts", headers=headers)
        assert res.status_code == 403
        assert "access denied" in res.json()["detail"].lower()

    def test_bank_analyst_cannot_acknowledge_alerts(self, client):
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        res = client.patch("/alerts/ALT-000001/acknowledge", headers=headers, json={})
        assert res.status_code == 403

    def test_bank_analyst_cannot_resolve_alerts(self, client):
        headers = auth_headers("BANK_ANALYST", "demo_bank")
        res = client.patch("/alerts/ALT-000001/resolve", headers=headers, json={})
        assert res.status_code == 403

    def test_authorized_analysts_have_access(self, client):
        for role in ("ANALYST", "SUPERVISOR", "ADMIN"):
            headers = auth_headers(role, f"user_{role.lower()}")
            res = client.get("/analyst/alerts", headers=headers)
            assert res.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 4. Severity Calibration & Threshold Boundary Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSeverityCalibrationAndValidation:
    """Tests risk score boundaries (0-39, 40-59, 60-79, 80-100) and input validation."""

    def test_exact_threshold_boundaries(self):
        assert assign_alert_severity(0) == "LOW"
        assert assign_alert_severity(39) == "LOW"
        assert assign_alert_severity(40) == "MODERATE"
        assert assign_alert_severity(59) == "MODERATE"
        assert assign_alert_severity(60) == "HIGH"
        assert assign_alert_severity(79) == "HIGH"
        assert assign_alert_severity(80) == "CRITICAL"
        assert assign_alert_severity(100) == "CRITICAL"

    def test_invalid_and_nan_scores_fallback_to_low(self):
        assert assign_alert_severity(None) == "LOW"
        assert assign_alert_severity(float("nan")) == "LOW"
        assert assign_alert_severity(float("inf")) == "LOW"
        assert assign_alert_severity("invalid_score") == "LOW"

    def test_validate_alert_inputs_rejects_nan_and_inf(self):
        rec_nan = {"risk_score": float("nan")}
        valid, err = validate_alert_inputs(rec_nan)
        assert valid is False
        assert "nan or infinite" in err.lower()

        rec_inf = {"risk_score": float("inf")}
        valid, err = validate_alert_inputs(rec_inf)
        assert valid is False
        assert "nan or infinite" in err.lower()

    def test_validate_alert_inputs_rejects_out_of_bounds(self):
        valid_low, err_low = validate_alert_inputs({"risk_score": -5})
        assert valid_low is False
        assert "out of bounds" in err_low.lower()

        valid_high, err_high = validate_alert_inputs({"risk_score": 105})
        assert valid_high is False
        assert "out of bounds" in err_high.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Cooldown & Escalation Deduplication Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCooldownAndDeduplication:
    """Tests spatial-temporal cooldown and priority escalation."""

    def test_cooldown_suppresses_same_severity_within_window(self):
        config = {
            "cooldown_minutes": {"critical": 30, "high": 60, "moderate": 120, "low": 240}
        }
        t0 = datetime.now(timezone.utc)
        existing = [{
            "alert_id": "ALT-EXISTING-1",
            "alert_type": "HIGH_RISK_LOCATION",
            "prediction_reference": "CORRIDOR-001",
            "severity": "HIGH",
            "created_at": t0.isoformat(),
        }]

        # Candidate arrived 25 minutes later (cooldown is 60 min for HIGH)
        t_cand = t0 + timedelta(minutes=25)
        candidate = {
            "alert_id": "ALT-CAND-1",
            "alert_type": "HIGH_RISK_LOCATION",
            "prediction_reference": "CORRIDOR-001",
            "severity": "HIGH",
            "created_at": t_cand.isoformat(),
        }

        unique, dups, cd_skipped = deduplicate_alerts([candidate], existing, config)
        assert len(unique) == 0
        assert cd_skipped == 1

    def test_alert_allowed_after_cooldown_expires(self):
        config = {
            "cooldown_minutes": {"critical": 30, "high": 60, "moderate": 120, "low": 240}
        }
        t0 = datetime.now(timezone.utc)
        existing = [{
            "alert_id": "ALT-EXISTING-2",
            "alert_type": "HIGH_RISK_LOCATION",
            "prediction_reference": "CORRIDOR-002",
            "severity": "HIGH",
            "created_at": t0.isoformat(),
        }]

        # Candidate arrived 65 minutes later (cooldown 60 min expired)
        t_cand = t0 + timedelta(minutes=65)
        candidate = {
            "alert_id": "ALT-CAND-2",
            "alert_type": "HIGH_RISK_LOCATION",
            "prediction_reference": "CORRIDOR-002",
            "severity": "HIGH",
            "created_at": t_cand.isoformat(),
        }

        unique, dups, cd_skipped = deduplicate_alerts([candidate], existing, config)
        assert len(unique) == 1
        assert cd_skipped == 0

    def test_escalation_bypasses_cooldown(self):
        """If risk escalates from HIGH to CRITICAL, the critical alert must NOT be suppressed."""
        config = {
            "cooldown_minutes": {"critical": 30, "high": 60, "moderate": 120, "low": 240}
        }
        t0 = datetime.now(timezone.utc)
        existing = [{
            "alert_id": "ALT-EXISTING-3",
            "alert_type": "HIGH_RISK_LOCATION",
            "prediction_reference": "CORRIDOR-003",
            "severity": "HIGH",
            "created_at": t0.isoformat(),
        }]

        # Candidate arrived 15 minutes later, but escalated to CRITICAL
        t_cand = t0 + timedelta(minutes=15)
        candidate = {
            "alert_id": "ALT-CAND-3",
            "alert_type": "HIGH_RISK_LOCATION",
            "prediction_reference": "CORRIDOR-003",
            "severity": "CRITICAL",
            "created_at": t_cand.isoformat(),
        }

        unique, dups, cd_skipped = deduplicate_alerts([candidate], existing, config)
        assert len(unique) == 1
        assert cd_skipped == 0
        assert unique[0]["severity"] == "CRITICAL"
