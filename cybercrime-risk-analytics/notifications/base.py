"""
Base Notifier Interface
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

FORBIDDEN_SENSITIVE_FIELDS = {
    "account_number", "account_no", "bank_account", "card_number", "card_no",
    "pin", "otp", "cvv", "password", "victim_phone", "phone_number",
    "email_address", "aadhar_number", "pan_number", "ssn"
}

ALLOWED_ALERT_FIELDS = {
    "alert_id", "alert_type", "severity", "status", "created_at", "updated_at",
    "prediction_reference", "hotspot_id", "risk_score", "predicted_probability",
    "event_count", "dominant_category", "time_window_start", "time_window_end",
    "operational_message", "human_review_required", "model_version",
    "latitude", "longitude", "disclaimer"
}


class BaseNotifier(ABC):
    """Abstract base class for all notification adapters."""

    @abstractmethod
    def is_enabled(self) -> bool:
        """Returns True if this notification adapter is active."""
        pass

    @abstractmethod
    def dispatch(self, alert: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """
        Dispatches notification for an analytical alert.
        Must return dispatch metadata including status, channel, and sanitized payload.
        """
        pass

    @staticmethod
    def sanitize_payload(alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters out any sensitive PII or unapproved fields.
        Ensures strict privacy and non-exposure of financial credentials.
        """
        sanitized = {}
        for k, v in alert.items():
            k_lower = str(k).lower()
            if k_lower in FORBIDDEN_SENSITIVE_FIELDS:
                continue
            if k in ALLOWED_ALERT_FIELDS:
                sanitized[k] = v

        if "disclaimer" not in sanitized:
            sanitized["disclaimer"] = (
                "This alert is a model-derived analytical signal and does not establish "
                "criminal activity or identify a criminal."
            )
        return sanitized
