"""
Notification Dispatcher
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Co-ordinates fan-out across four notification channels:
  1. LOG      — application logger (always active, zero external calls)
  2. EMAIL    — SMTP adapter (disabled by default; dry-run safe)
  3. SMS      — SIMULATED dispatcher (no real carrier; SIMULATED_DELIVERED)
  4. WEBHOOK  — SIMULATED dispatcher (no real HTTP POST; SIMULATED_SENT)

Every dispatch attempt — real or simulated — is recorded in the shared
outbound notification log (notifications/notification_log.py).
"""
import logging
from typing import Any, Dict, List

from notifications.base import BaseNotifier
from notifications.logger import LogNotifier
from notifications.email import EmailNotifier
from notifications.sms import SMSNotifier
from notifications.webhook import WebhookNotifier
import notifications.notification_log as notif_log

logger = logging.getLogger("cybercrime_api.notifications.dispatcher")


class NotificationDispatcher:
    """
    Coordinates dispatch of analytical alerts across all configured channels.

    Default behaviour:
      - LOG    : always active
      - EMAIL  : dry-run (no real email sent unless ENABLE_EMAIL_ALERTS=true)
      - SMS    : always active in simulation mode (SIMULATED_DELIVERED)
      - WEBHOOK: always active in simulation mode (SIMULATED_SENT)
    """

    def __init__(
        self,
        log_enabled: bool = True,
        email_enabled: bool = False,
        sms_recipient_roles: List[str] = None,
        webhook_targets: List[str] = None,
    ):
        """
        Args:
            log_enabled:         Enable the LOG channel (default True).
            email_enabled:       Unused here — email adapter self-manages via
                                 ENABLE_EMAIL_ALERTS env-var.  Kept for
                                 backwards-compatibility with existing callers.
            sms_recipient_roles: List of recipient role keys for SMSNotifier.
                                 Defaults to ["LEA_SUPERVISOR", "I4C_ONCALL"].
            webhook_targets:     List of target system keys for WebhookNotifier.
                                 Defaults to ["LEA_PORTAL", "BANK_FMS_SIMULATED"].
        """
        if sms_recipient_roles is None:
            sms_recipient_roles = ["LEA_SUPERVISOR", "I4C_ONCALL"]
        if webhook_targets is None:
            webhook_targets = ["LEA_PORTAL", "BANK_FMS_SIMULATED"]

        self.notifiers: List[BaseNotifier] = [
            LogNotifier(enabled=log_enabled),
            EmailNotifier(),
        ]
        # One SMSNotifier per recipient role so each gets its own log record
        self.sms_notifiers: List[SMSNotifier] = [
            SMSNotifier(recipient_role=role) for role in sms_recipient_roles
        ]
        # Single WebhookNotifier fans out to all targets internally
        self.webhook_notifier = WebhookNotifier(target_systems=webhook_targets)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_alert_id(result: Dict[str, Any], alert: Dict[str, Any]) -> str:
        return (
            result.get("alert_id")
            or alert.get("alert_id")
            or "UNKNOWN"
        )

    @staticmethod
    def _log_result(alert_id: str, result: Dict[str, Any]) -> None:
        """Write a single dispatch result into the shared notification log."""
        channel = result.get("channel", "UNKNOWN")
        status = result.get("status", "UNKNOWN")
        simulation = result.get("simulation", False)

        # Build a human-readable recipient / target summary
        if channel == "SMS":
            recipient_or_target = result.get("recipient", result.get("recipient_role", ""))
        elif channel == "WEBHOOK":
            targets = result.get("targets_dispatched", [])
            recipient_or_target = ", ".join(t.get("target_system", "") for t in targets)
        elif channel == "EMAIL":
            recipient_or_target = result.get("recipient", "")
        else:
            recipient_or_target = result.get("notifier", "")

        # Compact extra info (payload summary, errors, etc.)
        extra_parts = []
        if result.get("error"):
            extra_parts.append(f"error={result['error']}")
        if result.get("payload_summary"):
            ps = result["payload_summary"]
            extra_parts.append(
                f"sev={ps.get('severity')} score={ps.get('risk_score')}"
            )
        if result.get("dry_run") is not None:
            extra_parts.append(f"dry_run={result['dry_run']}")
        extra_info = " | ".join(extra_parts) if extra_parts else None

        notif_log.record_dispatch(
            alert_id=alert_id,
            channel=channel,
            status=status,
            recipient_or_target=recipient_or_target,
            simulation=simulation,
            extra_info=extra_info,
        )

    # ------------------------------------------------------------------
    # Public dispatch
    # ------------------------------------------------------------------

    def dispatch_alert(self, alert: Dict[str, Any], dry_run: bool = True) -> List[Dict[str, Any]]:
        """
        Fan out alert across all active notification channels and record
        every result in the shared outbound notification log.

        Args:
            alert:   Sanitized alert dict (must contain alert_id).
            dry_run: Passed to each adapter.  SMS and Webhook adapters are
                     always simulated regardless of this flag.

        Returns:
            List of per-channel dispatch result dicts.
        """
        results: List[Dict[str, Any]] = []

        # ---- 1. LOG + EMAIL (existing notifiers) ----
        for notifier in self.notifiers:
            try:
                res = notifier.dispatch(alert, dry_run=dry_run)
                results.append(res)
                alert_id = self._extract_alert_id(res, alert)
                self._log_result(alert_id, res)
            except Exception as exc:
                logger.error("Notifier error in %s: %s", type(notifier).__name__, exc)
                err_res = {
                    "channel": type(notifier).__name__.upper().replace("NOTIFIER", ""),
                    "status": "ERROR",
                    "error": "Notifier failed during execution.",
                }
                results.append(err_res)
                notif_log.record_dispatch(
                    alert_id=alert.get("alert_id", "UNKNOWN"),
                    channel=err_res["channel"],
                    status="ERROR",
                    extra_info=str(exc)[:200],
                )

        # ---- 2. SMS (simulated — one record per recipient role) ----
        for sms in self.sms_notifiers:
            try:
                res = sms.dispatch(alert, dry_run=dry_run)
                results.append(res)
                alert_id = self._extract_alert_id(res, alert)
                self._log_result(alert_id, res)
            except Exception as exc:
                logger.error("SMSNotifier error (role=%s): %s", sms.recipient_role, exc)
                err_res = {
                    "channel": "SMS",
                    "status": "ERROR",
                    "recipient_role": sms.recipient_role,
                    "error": "SMS notifier failed.",
                }
                results.append(err_res)
                notif_log.record_dispatch(
                    alert_id=alert.get("alert_id", "UNKNOWN"),
                    channel="SMS",
                    status="ERROR",
                    recipient_or_target=sms.recipient_role,
                    extra_info=str(exc)[:200],
                )

        # ---- 3. WEBHOOK (simulated — covers all configured target systems) ----
        try:
            res = self.webhook_notifier.dispatch(alert, dry_run=dry_run)
            results.append(res)
            alert_id = self._extract_alert_id(res, alert)
            self._log_result(alert_id, res)
        except Exception as exc:
            logger.error("WebhookNotifier error: %s", exc)
            err_res = {
                "channel": "WEBHOOK",
                "status": "ERROR",
                "error": "Webhook notifier failed.",
            }
            results.append(err_res)
            notif_log.record_dispatch(
                alert_id=alert.get("alert_id", "UNKNOWN"),
                channel="WEBHOOK",
                status="ERROR",
                extra_info=str(exc)[:200],
            )

        return results
