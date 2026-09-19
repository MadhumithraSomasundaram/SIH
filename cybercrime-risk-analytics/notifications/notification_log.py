"""
Outbound Notification Log — Append-Only Dispatch Record
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Records every dispatch attempt across all four channels
(DASHBOARD, EMAIL, SMS, WEBHOOK) to outputs/notification_log.csv.
If the database is connected, also writes to the notification_log DB table
(if it exists); otherwise CSV is the sole persistent store.
"""
import csv
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cybercrime_api.notifications.notification_log")

# Append-only CSV that persists across server restarts
_NOTIFICATION_LOG_CSV = (
    Path(__file__).resolve().parent.parent / "outputs" / "notification_log.csv"
)

_CSV_COLUMNS = [
    "log_id",
    "alert_id",
    "channel",
    "status",
    "recipient_or_target",
    "simulation",
    "timestamp",
    "extra_info",
]

# In-memory log (per-process; populated on startup from CSV)
_NOTIFICATION_LOG: List[Dict[str, Any]] = []
_LOG_LOCK = threading.Lock()
_LOG_COUNTER = 0


def _load_log_from_csv() -> None:
    """Read existing log entries from CSV into _NOTIFICATION_LOG on startup."""
    global _LOG_COUNTER
    if not _NOTIFICATION_LOG_CSV.exists():
        return
    try:
        with open(_NOTIFICATION_LOG_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                _NOTIFICATION_LOG.append(dict(row))
        if _NOTIFICATION_LOG:
            # Restore counter to avoid log_id collisions
            last = _NOTIFICATION_LOG[-1].get("log_id", "LOG-0")
            try:
                _LOG_COUNTER = int(last.split("-")[-1])
            except (ValueError, AttributeError):
                _LOG_COUNTER = len(_NOTIFICATION_LOG)
    except Exception as exc:
        logger.warning("Failed to load notification log from CSV: %s", exc)


def _ensure_csv_header() -> None:
    """Create the CSV with header row if it does not yet exist."""
    if not _NOTIFICATION_LOG_CSV.exists():
        try:
            _NOTIFICATION_LOG_CSV.parent.mkdir(parents=True, exist_ok=True)
            with open(_NOTIFICATION_LOG_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
                writer.writeheader()
        except Exception as exc:
            logger.warning("Failed to create notification log CSV: %s", exc)


def _append_row_to_csv(row: Dict[str, Any]) -> None:
    """Append a single row to the CSV (thread-safe)."""
    try:
        with open(_NOTIFICATION_LOG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
            writer.writerow(row)
    except Exception as exc:
        logger.warning("Failed to append to notification log CSV: %s", exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def record_dispatch(
    alert_id: str,
    channel: str,
    status: str,
    recipient_or_target: str = "",
    simulation: bool = True,
    extra_info: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record one outbound dispatch attempt in the shared notification log.

    Args:
        alert_id:            The alert that triggered this dispatch.
        channel:             One of: DASHBOARD, EMAIL, SMS, WEBHOOK.
        status:              e.g. LOGGED, DRY_RUN, SIMULATED_DELIVERED,
                             SIMULATED_SENT, DISABLED, SENT, FAILED.
        recipient_or_target: Human-readable recipient or target system name.
        simulation:          True when no real external call was made.
        extra_info:          Free-text field for payload summary, error, etc.

    Returns:
        The log record dict (also appended to in-memory list and CSV).
    """
    global _LOG_COUNTER
    with _LOG_LOCK:
        _LOG_COUNTER += 1
        log_id = f"LOG-{_LOG_COUNTER:06d}"
        now = datetime.now(timezone.utc).isoformat()

        row = {
            "log_id": log_id,
            "alert_id": alert_id,
            "channel": channel,
            "status": status,
            "recipient_or_target": recipient_or_target,
            "simulation": simulation,
            "timestamp": now,
            "extra_info": extra_info or "",
        }
        _NOTIFICATION_LOG.append(row)
        _append_row_to_csv(row)

    logger.debug(
        "[NOTIFICATION_LOG] log_id=%s alert_id=%s channel=%s status=%s",
        log_id, alert_id, channel, status,
    )
    return row


def get_dispatch_log_for_alert(alert_id: str) -> List[Dict[str, Any]]:
    """Return all log entries for a specific alert_id, newest first."""
    with _LOG_LOCK:
        entries = [r for r in _NOTIFICATION_LOG if r.get("alert_id") == alert_id]
    return list(reversed(entries))


def get_full_dispatch_log(limit: int = 200) -> List[Dict[str, Any]]:
    """Return the most recent `limit` log entries across all alerts."""
    with _LOG_LOCK:
        snapshot = list(_NOTIFICATION_LOG)
    return list(reversed(snapshot))[:limit]


# ---------------------------------------------------------------------------
# Module initialisation
# ---------------------------------------------------------------------------
_ensure_csv_header()
_load_log_from_csv()
