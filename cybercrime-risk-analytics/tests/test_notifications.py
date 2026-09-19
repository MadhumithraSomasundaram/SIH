"""
Phase 16 — Notification Layer Unit Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import pytest
from notifications.base import BaseNotifier, FORBIDDEN_SENSITIVE_FIELDS
from notifications.logger import LogNotifier
from notifications.email import EmailNotifier
from notifications.sms import SMSNotifier
from notifications.webhook import WebhookNotifier
from notifications.dispatcher import NotificationDispatcher


class TestPayloadSanitization:
    """Verifies strict scrubbing of sensitive credentials and PII."""

    def test_sensitive_fields_scrubbed(self):
        raw_payload = {
            "alert_id": "ALT-000100",
            "alert_type": "CRITICAL_RISK_LOCATION",
            "severity": "CRITICAL",
            "risk_score": 90,
            "card_number": "4111222233334444",
            "pin": "1234",
            "otp": "999999",
            "cvv": "123",
            "password": "secret_password",
            "account_number": "1234567890",
            "victim_phone": "9876543210",
        }

        sanitized = BaseNotifier.sanitize_payload(raw_payload)

        # Approved fields remain
        assert sanitized["alert_id"] == "ALT-000100"
        assert sanitized["severity"] == "CRITICAL"
        assert sanitized["risk_score"] == 90
        assert "disclaimer" in sanitized

        # Forbidden fields are stripped
        for f in FORBIDDEN_SENSITIVE_FIELDS:
            assert f not in sanitized


class TestLogNotifier:
    """Verifies application log notifier operation."""

    def test_log_dispatch_dry_run(self):
        notifier = LogNotifier(enabled=True)
        alert = {
            "alert_id": "ALT-LOG-01",
            "alert_type": "HIGH_RISK_LOCATION",
            "severity": "HIGH",
            "risk_score": 72,
        }
        res = notifier.dispatch(alert, dry_run=True)
        assert res["channel"] == "LOG"
        assert res["status"] == "LOGGED"
        assert res["dry_run"] is True


class TestEmailNotifierSafety:
    """Verifies email adapter remains disabled by default and dry-run safe."""

    def test_email_notifier_disabled_by_default(self):
        notifier = EmailNotifier()
        # Default without explicit env credentials is disabled
        assert notifier.is_enabled() is False

    def test_email_dry_run_transmission(self):
        notifier = EmailNotifier()
        alert = {
            "alert_id": "ALT-EMAIL-01",
            "alert_type": "CRITICAL_RISK_LOCATION",
            "severity": "CRITICAL",
            "risk_score": 95,
            "dominant_category": "INVESTMENT_SCAM",
            "operational_message": "Immediate analyst review recommended.",
        }
        res = notifier.dispatch(alert, dry_run=True)
        assert res["channel"] == "EMAIL"
        assert res["dry_run"] is True
        assert res["status"] == "DRY_RUN"
        assert "Simulated transmission" in res["disclaimer"]
        assert "[CRITICAL]" in res["subject"]


class TestNotificationDispatcher:
    """Verifies multi-channel coordination."""

    def test_dispatcher_orchestration(self):
        dispatcher = NotificationDispatcher(log_enabled=True, email_enabled=False)
        alert = {
            "alert_id": "ALT-DISP-01",
            "alert_type": "WITHDRAWAL_HOTSPOT",
            "severity": "HIGH",
            "risk_score": 68,
        }
        results = dispatcher.dispatch_alert(alert, dry_run=True)
        assert len(results) >= 2
        channels = [r["channel"] for r in results]
        assert "LOG" in channels
        assert "EMAIL" in channels
        assert "SMS" in channels
        assert "WEBHOOK" in channels


class TestSMSNotifier:
    """Verifies simulated SMS notification adapter."""

    def test_sms_simulation_dispatch(self):
        notifier = SMSNotifier(recipient_role="LEA_SUPERVISOR")
        alert = {
            "alert_id": "ALT-SMS-01",
            "alert_type": "HIGH_RISK_LOCATION",
            "severity": "HIGH",
            "risk_score": 75,
            "card_number": "4111222233334444",  # Must be stripped
        }
        res = notifier.dispatch(alert)
        assert res["channel"] == "SMS"
        assert res["status"] == "SIMULATED_DELIVERED"
        assert res["simulation"] is True
        assert "card_number" not in res.get("sanitized_payload", {})
        assert res["recipient_role"] == "LEA_SUPERVISOR"


class TestWebhookNotifier:
    """Verifies simulated Webhook notification adapter."""

    def test_webhook_simulation_dispatch(self):
        notifier = WebhookNotifier(target_systems=["LEA_PORTAL", "BANK_FMS_SIMULATED"])
        alert = {
            "alert_id": "ALT-HOOK-01",
            "alert_type": "CRITICAL_RISK_LOCATION",
            "severity": "CRITICAL",
            "risk_score": 90,
            "pin": "1234",  # Must be stripped
        }
        res = notifier.dispatch(alert)
        assert res["channel"] == "WEBHOOK"
        assert res["status"] == "SIMULATED_SENT"
        assert res["simulation"] is True
        assert len(res["targets_dispatched"]) == 2
        target_names = [t["target_system"] for t in res["targets_dispatched"]]
        assert "LEA_PORTAL" in target_names
        assert "BANK_FMS_SIMULATED" in target_names
        assert "pin" not in res.get("sanitized_payload", {})

