"""
SMS Notification Adapter — Fully Simulated (No Real Carrier)
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

SIMULATION NOTICE:
  This adapter does NOT call any real SMS carrier API (no Twilio, AWS SNS,
  MSG91, or any other provider). It is a controlled prototype simulation
  required for the SIH 26184 prototype, which must demonstrate multi-channel
  dispatch capability without live credentials or external network calls.

  Every dispatch call produces a structured log record with
  status = "SIMULATED_DELIVERED". This is intentional and honest — judges
  should be informed that SMS dispatch is simulated end-to-end.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from notifications.base import BaseNotifier

logger = logging.getLogger("cybercrime_api.notifications.sms")


# ---------------------------------------------------------------------------
# Simulated recipient role → placeholder number mapping
# Real deployments would read these from a secure secrets store.
# ---------------------------------------------------------------------------
SIMULATED_RECIPIENTS = {
    "LEA_SUPERVISOR": "+91-XXXXXXXXXX-LEA",
    "I4C_ONCALL": "+91-XXXXXXXXXX-I4C",
    "BANK_FMS_CONTACT": "+91-XXXXXXXXXX-BANK",
    "ANALYST_ONCALL": "+91-XXXXXXXXXX-ANALYST",
}


class SMSNotifier(BaseNotifier):
    """
    Simulated SMS adapter for dispatching analytical alerts to LEAs,
    banks, I4C, and on-call analysts.

    Follows the same interface pattern as EmailNotifier (notifications/email.py).
    All dispatches are fully simulated — no carrier API is invoked.
    Status is always "SIMULATED_DELIVERED" to clearly communicate prototype mode.
    """

    # Always enabled: simulation requires no external credentials.
    SIMULATION_MODE = True

    def __init__(self, recipient_role: str = "LEA_SUPERVISOR"):
        """
        Args:
            recipient_role: Key into SIMULATED_RECIPIENTS.
                            Determines which placeholder number appears in logs.
        """
        self.recipient_role = recipient_role
        self.recipient_placeholder = SIMULATED_RECIPIENTS.get(
            recipient_role, "+91-XXXXXXXXXX-UNKNOWN"
        )

    def is_enabled(self) -> bool:
        """SMS simulation is always active for the prototype."""
        return True

    def format_sms_body(self, alert: Dict[str, Any]) -> str:
        """Compose a concise, non-sensitive SMS message body."""
        sanitized = self.sanitize_payload(alert)
        alert_id = sanitized.get("alert_id", "N/A")
        severity = sanitized.get("severity", "UNKNOWN")
        risk_score = sanitized.get("risk_score", "N/A")
        msg = sanitized.get("operational_message", "Review analytical alert.")
        return (
            f"[CYBERCRIME ALERT] {severity} | ID:{alert_id} | Score:{risk_score}\n"
            f"{msg[:120]}\n"
            "Dashboard: http://127.0.0.1:8000/dashboard/\n"
            "ANALYTICAL SIGNAL — Human review required."
        )

    def dispatch(self, alert: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """
        Simulate SMS dispatch.

        SIMULATION: No real SMS is sent regardless of dry_run value.
        Status is always SIMULATED_DELIVERED. The dry_run flag is accepted
        for interface compatibility but does not change behaviour.
        """
        sanitized = self.sanitize_payload(alert)
        alert_id = sanitized.get("alert_id", "UNKNOWN")
        body = self.format_sms_body(sanitized)
        now = datetime.now(timezone.utc).isoformat()

        # ----------------------------------------------------------------
        # SIMULATION: structured log record only — NO external network call.
        # ----------------------------------------------------------------
        record = {
            "channel": "SMS",
            "simulation": True,                      # explicitly labelled
            "status": "SIMULATED_DELIVERED",
            "recipient_role": self.recipient_role,
            "recipient": self.recipient_placeholder,
            "alert_id": alert_id,
            "message": body,
            "timestamp": now,
            "disclaimer": (
                "PROTOTYPE SIMULATION — No real SMS was dispatched. "
                "Production deployment requires a licensed SMS gateway."
            ),
        }

        logger.info(
            "[SIMULATED SMS] alert_id=%s | recipient_role=%s | status=SIMULATED_DELIVERED",
            alert_id,
            self.recipient_role,
        )
        return record
