"""
Email Notification Adapter (Disabled by default / Dry-Run safe)
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional, Tuple

from notifications.base import BaseNotifier

logger = logging.getLogger("cybercrime_api.notifications.email")


class EmailNotifier(BaseNotifier):
    """
    SMTP Email adapter for dispatching analytical alerts to authorized human analysts.
    Disabled by default. When enabled, requires valid environment variables.
    Never exposes passwords, account numbers, card details, or sensitive PII.
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_EMAIL_ALERTS", "false").lower() in ("true", "1", "yes")
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_addr = os.getenv("ALERT_EMAIL_FROM", "alerts@cybercrime-analytics.local")
        self.to_addr = os.getenv("ALERT_EMAIL_TO", "analyst-oncall@cybercrime-analytics.local")

    def is_enabled(self) -> bool:
        return self.enabled and bool(self.smtp_host) and bool(self.from_addr)

    def format_email_content(self, alert: Dict[str, Any]) -> Tuple[str, str]:
        """Generate safe subject and body text without sensitive data."""
        sanitized = self.sanitize_payload(alert)
        severity = sanitized.get("severity", "LOW")
        alert_id = sanitized.get("alert_id", "N/A")
        risk_score = sanitized.get("risk_score", "N/A")
        hotspot_id = sanitized.get("hotspot_id", "N/A")
        dominant_cat = sanitized.get("dominant_category", "N/A")
        time_window = f"{sanitized.get('time_window_start', 'N/A')} to {sanitized.get('time_window_end', 'N/A')}"
        operational_msg = sanitized.get("operational_message", "Review analytical indicators.")

        subject = f"[{severity}] Cybercrime Predictive Analytical Alert — {alert_id}"

        body = f"""A {severity} model-derived analytical alert has been generated.

Alert ID: {alert_id}
Alert Type: {sanitized.get('alert_type', 'N/A')}
Risk Score: {risk_score}
Risk Category: {severity}
Analytical Hotspot: {hotspot_id}
Time Window: {time_window}
Dominant Category: {dominant_cat}

Operational Guidance:
{operational_msg}

Recommended Action:
Prioritize authorized human review in the Cybercrime Analytics Dashboard.

----------------------------------------------------------------------
Disclaimer:
This alert is a model-derived analytical signal and does not establish
criminal activity or identify a criminal. No automated punitive or
financial interventions have been taken.
----------------------------------------------------------------------
"""
        return subject, body

    def dispatch(self, alert: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """Dispatch email or return simulated transmission in dry-run mode."""
        sanitized = self.sanitize_payload(alert)
        subject, body = self.format_email_content(sanitized)

        if dry_run or not self.is_enabled():
            return {
                "channel": "EMAIL",
                "status": "DRY_RUN" if dry_run else "DISABLED",
                "dry_run": dry_run,
                "recipient": self.to_addr,
                "subject": subject,
                "body_preview": body[:180] + "...",
                "disclaimer": "Simulated transmission. No external message sent.",
            }

        # Real SMTP delivery only when explicitly enabled and not dry_run
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = self.to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.from_addr, [self.to_addr], msg.as_string())

            logger.info("Email alert dispatched to %s for alert %s", self.to_addr, sanitized.get("alert_id"))
            return {
                "channel": "EMAIL",
                "status": "SENT",
                "dry_run": False,
                "recipient": self.to_addr,
                "subject": subject,
            }
        except Exception as exc:
            logger.error("Failed to send email alert: %s", exc)
            return {
                "channel": "EMAIL",
                "status": "FAILED",
                "dry_run": False,
                "error": "Failed to send email. Check SMTP credentials.",
            }
