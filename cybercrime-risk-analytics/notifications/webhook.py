"""
Webhook / API Notification Adapter — Fully Simulated (No Real HTTP Calls)
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

SIMULATION NOTICE:
  This adapter does NOT make any real outbound HTTP POST to any external
  system (no LEA portal, no bank FMS, no I4C gateway). It is a controlled
  prototype simulation required for SIH 26184 to demonstrate multi-channel
  API dispatch capability without live endpoints or credentials.

  Every dispatch call produces a structured log record with
  status = "SIMULATED_SENT". This is intentional and honest.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from notifications.base import BaseNotifier

logger = logging.getLogger("cybercrime_api.notifications.webhook")


# ---------------------------------------------------------------------------
# Simulated target systems — stand-ins for real LEA / bank / I4C endpoints.
# Real deployments would read URLs and auth tokens from a secrets manager.
# ---------------------------------------------------------------------------
SIMULATED_TARGETS = {
    "LEA_PORTAL": {
        "url": "https://lea-portal.example.gov.in/api/alerts",   # placeholder
        "description": "Law Enforcement Agency Analytical Portal",
        "auth_type": "API_KEY",
    },
    "BANK_FMS_SIMULATED": {
        "url": "https://bank-fms.example.com/api/fraud-alerts",   # placeholder
        "description": "Bank Fraud Management System (Simulated)",
        "auth_type": "BEARER_TOKEN",
    },
    "I4C_GATEWAY": {
        "url": "https://i4c.mha.gov.in/api/cybercrime-alerts",   # placeholder
        "description": "Indian Cybercrime Coordination Centre Gateway",
        "auth_type": "MUTUAL_TLS",
    },
}


class WebhookNotifier(BaseNotifier):
    """
    Simulated webhook/API dispatcher for multi-agency alert fan-out.

    Implements the same BaseNotifier interface as EmailNotifier and SMSNotifier.
    Can target one or more simulated external systems per call.

    All dispatches are fully simulated — no real HTTP request is made.
    Status is always "SIMULATED_SENT" to clearly communicate prototype mode.
    """

    SIMULATION_MODE = True

    def __init__(self, target_systems: Optional[List[str]] = None):
        """
        Args:
            target_systems: List of keys from SIMULATED_TARGETS to notify.
                            Defaults to LEA_PORTAL and BANK_FMS_SIMULATED.
        """
        if target_systems is None:
            target_systems = ["LEA_PORTAL", "BANK_FMS_SIMULATED"]
        self.target_systems = [t for t in target_systems if t in SIMULATED_TARGETS]

    def is_enabled(self) -> bool:
        """Webhook simulation is always active for the prototype."""
        return True

    def _build_payload(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Build a sanitized, non-sensitive JSON-serializable payload for webhook dispatch.

        All values are explicitly converted to JSON-safe types (str for datetimes etc.)
        so that downstream json.dumps calls never raise TypeError.
        """
        sanitized = self.sanitize_payload(alert)

        def _safe(v: Any) -> Any:
            """Convert non-JSON-native values to strings."""
            if v is None or isinstance(v, (bool, int, float, str)):
                return v
            return str(v)

        return {
            "schema_version": "1.0",
            "source": "CybercrimeRiskAnalytics_PS26184",
            "event_type": "ANALYTICAL_ALERT",
            "alert_id": _safe(sanitized.get("alert_id")),
            "severity": _safe(sanitized.get("severity")),
            "alert_type": _safe(sanitized.get("alert_type")),
            "risk_score": _safe(sanitized.get("risk_score")),
            "predicted_probability": _safe(sanitized.get("predicted_probability")),
            "hotspot_id": _safe(sanitized.get("hotspot_id")),
            "dominant_category": _safe(sanitized.get("dominant_category")),
            "time_window_start": _safe(sanitized.get("time_window_start")),
            "time_window_end": _safe(sanitized.get("time_window_end")),
            "operational_message": _safe(sanitized.get("operational_message")),
            "human_review_required": bool(sanitized.get("human_review_required", True)),
            "model_version": _safe(sanitized.get("model_version")),
            "generated_at": _safe(sanitized.get("created_at")),
            "disclaimer": _safe(sanitized.get("disclaimer")),
        }

    def dispatch(self, alert: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """
        Simulate webhook dispatch to all configured target systems.

        SIMULATION: No real HTTP POST is made regardless of dry_run value.
        Status is always SIMULATED_SENT. The dry_run flag is accepted for
        interface compatibility but does not alter behaviour.

        Returns a combined record covering all target systems dispatched.
        """
        sanitized = self.sanitize_payload(alert)
        alert_id = sanitized.get("alert_id", "UNKNOWN")
        payload = self._build_payload(sanitized)
        payload_summary = {
            "alert_id": payload.get("alert_id"),
            "severity": payload.get("severity"),
            "alert_type": payload.get("alert_type"),
            "risk_score": payload.get("risk_score"),
        }
        now = datetime.now(timezone.utc).isoformat()

        per_target_results = []
        for target_key in self.target_systems:
            target_info = SIMULATED_TARGETS[target_key]

            # ----------------------------------------------------------------
            # SIMULATION: structured log record only — NO real HTTP POST.
            # ----------------------------------------------------------------
            result = {
                "target_system": target_key,
                "target_url": target_info["url"],
                "target_description": target_info["description"],
                "status": "SIMULATED_SENT",
                "http_method": "POST",
                "simulated_http_status": 200,
                "payload_bytes": len(json.dumps(payload, default=str)),
            }
            per_target_results.append(result)
            logger.info(
                "[SIMULATED WEBHOOK] alert_id=%s | target=%s (%s) | status=SIMULATED_SENT",
                alert_id,
                target_key,
                target_info["description"],
            )

        return {
            "channel": "WEBHOOK",
            "simulation": True,                    # explicitly labelled
            "status": "SIMULATED_SENT",
            "alert_id": alert_id,
            "targets_dispatched": per_target_results,
            "payload_summary": payload_summary,
            "timestamp": now,
            "disclaimer": (
                "PROTOTYPE SIMULATION — No real webhook POST was made. "
                "Production deployment requires configured LEA/bank endpoints and credentials."
            ),
        }
