"""
Phase 16 — Alert Engine Unit Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import pytest
from datetime import datetime, timezone

from src.alert_engine import (
    assign_alert_severity,
    validate_alert_inputs,
    evaluate_risk_alert,
    evaluate_hotspot_alert,
    evaluate_withdrawal_alert,
    evaluate_activity_surge,
    deduplicate_alerts,
    load_configuration,
    create_alert,
)


@pytest.fixture
def config():
    return load_configuration()


class TestSeverityAssignment:
    """Tests risk score mapping to operational tiers."""

    def test_severity_tiers(self):
        assert assign_alert_severity(10) == "LOW"
        assert assign_alert_severity(39) == "LOW"
        assert assign_alert_severity(40) == "MODERATE"
        assert assign_alert_severity(59) == "MODERATE"
        assert assign_alert_severity(60) == "HIGH"
        assert assign_alert_severity(79) == "HIGH"
        assert assign_alert_severity(80) == "CRITICAL"
        assert assign_alert_severity(100) == "CRITICAL"


class TestInputValidation:
    """Tests schema and bounds checking on candidate records."""

    def test_valid_record(self):
        rec = {"risk_score": 75, "latitude": 12.97, "longitude": 77.59}
        valid, err = validate_alert_inputs(rec)
        assert valid is True
        assert err is None

    def test_missing_score(self):
        rec = {"latitude": 12.97}
        valid, err = validate_alert_inputs(rec)
        assert valid is False
        assert "Missing risk_score" in err

    def test_out_of_bounds_score(self):
        rec = {"risk_score": 150}
        valid, err = validate_alert_inputs(rec)
        assert valid is False
        assert "out of bounds" in err

    def test_invalid_coordinates(self):
        rec = {"risk_score": 65, "latitude": 95.0, "longitude": 77.0}
        valid, err = validate_alert_inputs(rec)
        assert valid is False
        assert "Coordinates out of bounds" in err


class TestRuleEvaluation:
    """Tests evaluation logic for location, hotspot, and withdrawal alerts."""

    def test_critical_location_alert(self, config):
        row = {
            "risk_score": 85,
            "predicted_probability": 0.85,
            "case_id": "TEST_CASE_001",
            "victim_district": "Bengaluru Urban",
            "crime_type": "UPI_FRAUD",
        }
        alert = evaluate_risk_alert(row, config, 1)
        assert alert is not None
        assert alert["alert_type"] == "CRITICAL_RISK_LOCATION"
        assert alert["severity"] == "CRITICAL"
        assert alert["human_review_required"] is True

    def test_high_location_alert(self, config):
        row = {
            "risk_score": 65,
            "case_id": "TEST_CASE_002",
            "victim_district": "Mysuru",
        }
        alert = evaluate_risk_alert(row, config, 2)
        assert alert is not None
        assert alert["alert_type"] == "HIGH_RISK_LOCATION"
        assert alert["severity"] == "HIGH"

    def test_low_risk_ignored(self, config):
        row = {"risk_score": 25, "case_id": "TEST_CASE_003"}
        alert = evaluate_risk_alert(row, config, 3)
        assert alert is None

    def test_hotspot_critical_alert(self, config):
        hs = {
            "cluster_id": 10,
            "average_risk_score": 82.5,
            "event_count": 30,
            "critical_risk_count": 1,
            "latitude_centroid": 12.9,
            "longitude_centroid": 77.5,
        }
        alert = evaluate_hotspot_alert(hs, None, config, 4)
        assert alert is not None
        assert alert["alert_type"] == "HOTSPOT_CRITICAL_RISK"
        assert alert["severity"] == "CRITICAL"

    def test_hotspot_elevated_alert(self, config):
        hs = {
            "cluster_id": 11,
            "average_risk_score": 62.0,
            "event_count": 25,
            "high_risk_count": 2,
            "latitude_centroid": 13.0,
            "longitude_centroid": 77.6,
        }
        alert = evaluate_hotspot_alert(hs, None, config, 5)
        assert alert is not None
        assert alert["alert_type"] == "HOTSPOT_ELEVATED_RISK"
        assert alert["severity"] == "HIGH"

    def test_withdrawal_alert(self, config):
        wh = {
            "cluster_id": 5,
            "withdrawal_event_count": 25,
            "average_risk_score": 65.0,
            "centroid_latitude": 13.2,
            "centroid_longitude": 79.1,
        }
        alert = evaluate_withdrawal_alert(wh, config, 6)
        assert alert is not None
        assert alert["alert_type"] == "WITHDRAWAL_HOTSPOT"
        assert alert["severity"] == "HIGH"

    def test_activity_surge_unavailable(self, config):
        res = evaluate_activity_surge(config)
        assert res["available"] is False
        assert "sufficient temporal history" in res["message"].lower()


class TestDeduplicationAndCooldown:
    """Tests duplicate collision avoidance and cooldown suppression."""

    def test_intra_batch_deduplication(self, config):
        now_str = datetime.now(timezone.utc).isoformat()
        alert1 = {
            "alert_id": "ALT-001",
            "alert_type": "HIGH_RISK_LOCATION",
            "hotspot_id": None,
            "prediction_reference": "CASE-100",
            "severity": "HIGH",
            "created_at": now_str,
        }
        alert2 = dict(alert1)
        alert2["alert_id"] = "ALT-002"

        unique, dup_skipped, cd_skipped = deduplicate_alerts([alert1, alert2], [], config)
        assert len(unique) == 1
        assert dup_skipped == 1

    def test_cooldown_suppression(self, config):
        now = datetime.now(timezone.utc)
        existing = [{
            "alert_id": "ALT-OLD",
            "alert_type": "CRITICAL_RISK_LOCATION",
            "hotspot_id": None,
            "prediction_reference": "CASE-200",
            "severity": "CRITICAL",
            "created_at": now,
        }]

        cand = {
            "alert_id": "ALT-NEW",
            "alert_type": "CRITICAL_RISK_LOCATION",
            "hotspot_id": None,
            "prediction_reference": "CASE-200",
            "severity": "CRITICAL",
            "created_at": now,
        }

        unique, dup_skipped, cd_skipped = deduplicate_alerts([cand], existing, config)
        assert len(unique) == 0
        assert cd_skipped == 1
