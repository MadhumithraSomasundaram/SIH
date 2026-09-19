"""
Logger Notification Adapter
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import logging
import sys
from typing import Any, Dict
from notifications.base import BaseNotifier

logger = logging.getLogger("cybercrime_api.notifications.logger")


class LogNotifier(BaseNotifier):
    """Logs analytical alerts directly to application logger."""

    def __init__(self, enabled: bool = True):
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def dispatch(self, alert: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        sanitized = self.sanitize_payload(alert)
        alert_id = sanitized.get("alert_id", "UNKNOWN")
        severity = sanitized.get("severity", "LOW")
        score = sanitized.get("risk_score", "N/A")
        atype = sanitized.get("alert_type", "UNKNOWN")
        hotspot = sanitized.get("hotspot_id", "N/A")

        msg = (
            f"[ANALYTICAL ALERT] ID={alert_id} | Type={atype} | Severity={severity} | "
            f"RiskScore={score} | Hotspot={hotspot} | DryRun={dry_run}"
        )

        if severity in ("HIGH", "CRITICAL"):
            logger.warning(msg)
        else:
            logger.info(msg)

        return {
            "channel": "LOG",
            "status": "LOGGED",
            "dry_run": dry_run,
            "alert_id": alert_id,
            "severity": severity,
            "payload": sanitized,
        }
