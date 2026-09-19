"""
Phase 17 — Investigation & Analyst Interface: CRUD Operations
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Safe CRUD for:
  - analyst_users (prototype auth)
  - investigations
  - investigation_notes
  - investigation_evidence
  - investigation_timeline
  - analyst_audit_log

With CSV fallback support for demonstration without DB connectivity.

SAFETY:
  - Never log passwords or sensitive data
  - Enforce role-based transition rules
  - Use parameterized queries (SQLAlchemy ORM — SQL injection safe)
  - All HIGH/CRITICAL alerts require human review
"""
from __future__ import annotations

import csv
import hashlib
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bcrypt as _bcrypt
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from database.investigation_models import (
    AnalystUser,
    Investigation,
    InvestigationNote,
    InvestigationEvidence,
    InvestigationTimeline,
    AnalystAuditLog,
    InvestigationOutcomeFeedback,
)
from database.investigation_schemas import (
    INVESTIGATION_TRANSITIONS,
    TRANSITION_ROLE_REQUIREMENTS,
    VALID_INVESTIGATION_STATUSES,
    VALID_PRIORITIES,
    VALID_OUTCOME_CATEGORIES,
)


logger = logging.getLogger("cybercrime_api.investigation_crud")

# Password hashing helpers (bcrypt direct — avoids passlib+bcrypt>=4.0 compatibility issues)

# Paths
_CRUD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _CRUD_DIR.parent
OUTPUTS = PROJECT_ROOT / "outputs"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_id(prefix: str) -> str:
    """Generate a unique reference ID with date prefix."""
    date_str = _now().strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{date_str}-{short_uuid}"


def _is_db(db: Optional[Session]) -> bool:
    """Check if DB session is available."""
    if db is None:
        return False
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Auth / User CRUD
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """bcrypt-hash a password. Never call with plaintext storage intent."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def get_user_by_username(db: Optional[Session], username: str) -> Optional[AnalystUser]:
    if not _is_db(db):
        return None
    try:
        return db.query(AnalystUser).filter(AnalystUser.username == username).first()
    except Exception as exc:
        logger.error("get_user_by_username: %s", exc)
        return None


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str = "ANALYST",
    display_name: Optional[str] = None,
) -> AnalystUser:
    """Create a new analyst user with bcrypt-hashed password."""
    user = AnalystUser(
        username=username,
        display_name=display_name or username,
        role=role.upper(),
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: AnalystUser) -> None:
    try:
        user.last_login = _now()
        db.commit()
    except Exception as exc:
        logger.warning("update_last_login: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Demo User Seed (Prototype — clearly labeled)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_USERS = [
    {
        "username": os.getenv("DEMO_ANALYST_USER", "demo_analyst"),
        "password": os.getenv("DEMO_ANALYST_PASS", "AnalystDemo2026!"),
        "role": "ANALYST",
        "display_name": "Demo Analyst",
    },
    {
        "username": "analyst_user",
        "password": "AnalystSecure2026!",
        "role": "ANALYST",
        "display_name": "Authorized LEA Analyst",
    },
    {
        "username": os.getenv("DEMO_SUPERVISOR_USER", "demo_supervisor"),
        "password": os.getenv("DEMO_SUPERVISOR_PASS", "SupervisorDemo2026!"),
        "role": "SUPERVISOR",
        "display_name": "Demo Supervisor",
    },
    {
        "username": "supervisor_user",
        "password": "SupervisorSecure2026!",
        "role": "SUPERVISOR",
        "display_name": "LEA Supervisor",
    },
    {
        "username": os.getenv("DEMO_ADMIN_USER", "demo_admin"),
        "password": os.getenv("DEMO_ADMIN_PASS", "AdminDemo2026!"),
        "role": "ADMIN",
        "display_name": "Demo Admin",
    },
    {
        "username": "admin_user",
        "password": "AdminSecure2026!",
        "role": "ADMIN",
        "display_name": "System Administrator",
    },
    {
        "username": os.getenv("DEMO_BANK_USER", "demo_bank"),
        "password": os.getenv("DEMO_BANK_PASS", "BankDemo2026!"),
        "role": "BANK_ANALYST",
        "display_name": "Demo Bank Analyst",
    },
    {
        "username": "bank_user",
        "password": "BankSecure2026!",
        "role": "BANK_ANALYST",
        "display_name": "Institutional Bank Analyst",
    },
]


def seed_demo_users(db: Optional[Session]) -> None:
    """Seed prototype demo users if not present."""
    if not _is_db(db):
        logger.info("DB unavailable — skipping demo user seed.")
        return
    try:
        for u in DEMO_USERS:
            existing = get_user_by_username(db, u["username"])
            if not existing:
                create_user(db, u["username"], u["password"], u["role"], u["display_name"])
                logger.info("Seeded demo user: %s (%s)", u["username"], u["role"])
    except Exception as exc:
        logger.error("seed_demo_users failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Investigation CRUD
# ─────────────────────────────────────────────────────────────────────────────

# In-memory fallback for demo without DB
_DEMO_INVESTIGATIONS: List[Dict[str, Any]] = []
_DEMO_NOTES: List[Dict[str, Any]] = []
_DEMO_EVIDENCE: List[Dict[str, Any]] = []
_DEMO_TIMELINE: List[Dict[str, Any]] = []
_DEMO_AUDIT: List[Dict[str, Any]] = []

# Persistent fallback CSV path and lock for Analyst Audit Trail
_AUDIT_CSV_PATH = OUTPUTS / "phase17_analyst_audit_log.csv"
_audit_csv_lock = threading.Lock()
_AUDIT_CSV_FIELDS = [
    "audit_id",
    "timestamp",
    "action",
    "resource_type",
    "resource_id",
    "actor_role",
    "result",
    "detail",
]


def _init_demo_audit_from_csv() -> None:
    """Load persistent audit records from phase17_analyst_audit_log.csv into _DEMO_AUDIT."""
    global _DEMO_AUDIT
    if not _AUDIT_CSV_PATH.exists():
        return
    try:
        with _audit_csv_lock:
            with open(_AUDIT_CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                loaded = []
                for row in reader:
                    ts_str = row.get("timestamp")
                    try:
                        ts = datetime.fromisoformat(ts_str) if ts_str else _now()
                    except Exception:
                        ts = _now()
                    loaded.append({
                        "audit_id": row.get("audit_id"),
                        "timestamp": ts,
                        "action": row.get("action"),
                        "resource_type": row.get("resource_type") or None,
                        "resource_id": row.get("resource_id") or None,
                        "actor_role": row.get("actor_role", "ANALYST"),
                        "result": row.get("result", "SUCCESS"),
                        "detail": row.get("detail") or None,
                    })
                if loaded:
                    existing_ids = {a.get("audit_id") for a in _DEMO_AUDIT}
                    for item in loaded:
                        if item.get("audit_id") not in existing_ids:
                            _DEMO_AUDIT.append(item)
                            existing_ids.add(item.get("audit_id"))
    except Exception as exc:
        logger.warning("Failed loading audit log from CSV %s: %s", _AUDIT_CSV_PATH, exc)


def _append_audit_to_csv(entry: Dict[str, Any]) -> None:
    """Atomically append an audit log entry to the fallback CSV."""
    try:
        with _audit_csv_lock:
            file_exists = _AUDIT_CSV_PATH.exists()
            with open(_AUDIT_CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_AUDIT_CSV_FIELDS)
                if not file_exists or _AUDIT_CSV_PATH.stat().st_size == 0:
                    writer.writeheader()
                
                ts = entry.get("timestamp")
                if isinstance(ts, datetime):
                    ts_str = ts.isoformat()
                else:
                    ts_str = str(ts) if ts else _now().isoformat()
                
                writer.writerow({
                    "audit_id": entry.get("audit_id"),
                    "timestamp": ts_str,
                    "action": entry.get("action"),
                    "resource_type": entry.get("resource_type") or "",
                    "resource_id": entry.get("resource_id") or "",
                    "actor_role": entry.get("actor_role", "ANALYST"),
                    "result": entry.get("result", "SUCCESS"),
                    "detail": entry.get("detail") or "",
                })
    except Exception as exc:
        logger.error("Failed appending audit record to CSV: %s", exc)


def _sync_all_demo_audit_to_csv() -> None:
    """Write all current _DEMO_AUDIT records to the CSV if the CSV does not exist yet."""
    try:
        with _audit_csv_lock:
            if _AUDIT_CSV_PATH.exists() and _AUDIT_CSV_PATH.stat().st_size > 0:
                return
            with open(_AUDIT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_AUDIT_CSV_FIELDS)
                writer.writeheader()
                for entry in _DEMO_AUDIT:
                    ts = entry.get("timestamp")
                    if isinstance(ts, datetime):
                        ts_str = ts.isoformat()
                    else:
                        ts_str = str(ts) if ts else _now().isoformat()
                    writer.writerow({
                        "audit_id": entry.get("audit_id"),
                        "timestamp": ts_str,
                        "action": entry.get("action"),
                        "resource_type": entry.get("resource_type") or "",
                        "resource_id": entry.get("resource_id") or "",
                        "actor_role": entry.get("actor_role", "ANALYST"),
                        "result": entry.get("result", "SUCCESS"),
                        "detail": entry.get("detail") or "",
                    })
    except Exception as exc:
        logger.error("Failed writing initial audit log to CSV: %s", exc)


# Persistent fallback CSV path and lock for Outcome Feedback (Phase 11)
_DEMO_FEEDBACK: List[Dict[str, Any]] = []
_FEEDBACK_CSV_PATH = OUTPUTS / "phase21_outcome_feedback.csv"
_feedback_csv_lock = threading.Lock()
_FEEDBACK_CSV_FIELDS = [
    "feedback_id",
    "investigation_id",
    "alert_id",
    "hotspot_id",
    "outcome_category",
    "actual_amount_lost",
    "amount_prevented",
    "atm_id_actual",
    "actual_timestamp",
    "notes",
    "reported_by_role",
    "verified_by_supervisor",
    "created_at",
]


def _init_demo_feedback_from_csv() -> None:
    """Load persistent outcome feedback records from phase21_outcome_feedback.csv into _DEMO_FEEDBACK."""
    global _DEMO_FEEDBACK
    if not _FEEDBACK_CSV_PATH.exists():
        return
    try:
        with _feedback_csv_lock:
            with open(_FEEDBACK_CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                loaded = []
                for row in reader:
                    ts_str = row.get("created_at")
                    try:
                        ts = datetime.fromisoformat(ts_str) if ts_str else _now()
                    except Exception:
                        ts = _now()
                    act_ts_str = row.get("actual_timestamp")
                    try:
                        act_ts = datetime.fromisoformat(act_ts_str) if act_ts_str else None
                    except Exception:
                        act_ts = None
                    
                    lost = float(row["actual_amount_lost"]) if (row.get("actual_amount_lost") and row["actual_amount_lost"] != "None") else None
                    prev = float(row["amount_prevented"]) if (row.get("amount_prevented") and row["amount_prevented"] != "None") else None
                    verif = row.get("verified_by_supervisor", "False").lower() in ("true", "1", "yes")
                    
                    loaded.append({
                        "feedback_id": row.get("feedback_id"),
                        "investigation_id": row.get("investigation_id"),
                        "alert_id": row.get("alert_id"),
                        "hotspot_id": row.get("hotspot_id") or None,
                        "outcome_category": row.get("outcome_category", "OTHER"),
                        "actual_amount_lost": lost,
                        "amount_prevented": prev,
                        "atm_id_actual": row.get("atm_id_actual") or None,
                        "actual_timestamp": act_ts,
                        "notes": row.get("notes", ""),
                        "reported_by_role": row.get("reported_by_role", "ANALYST"),
                        "verified_by_supervisor": verif,
                        "created_at": ts,
                    })
                if loaded:
                    existing_ids = {a.get("feedback_id") for a in _DEMO_FEEDBACK}
                    for item in loaded:
                        if item.get("feedback_id") not in existing_ids:
                            _DEMO_FEEDBACK.append(item)
                            existing_ids.add(item.get("feedback_id"))
    except Exception as exc:
        logger.warning("Failed loading feedback log from CSV %s: %s", _FEEDBACK_CSV_PATH, exc)


def _append_feedback_to_csv(entry: Dict[str, Any]) -> None:
    """Atomically append an outcome feedback entry to the fallback CSV."""
    try:
        with _feedback_csv_lock:
            file_exists = _FEEDBACK_CSV_PATH.exists()
            with open(_FEEDBACK_CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_FEEDBACK_CSV_FIELDS)
                if not file_exists or _FEEDBACK_CSV_PATH.stat().st_size == 0:
                    writer.writeheader()
                
                ts = entry.get("created_at")
                ts_str = ts.isoformat() if isinstance(ts, datetime) else (str(ts) if ts else _now().isoformat())
                act_ts = entry.get("actual_timestamp")
                act_ts_str = act_ts.isoformat() if isinstance(act_ts, datetime) else (str(act_ts) if act_ts else "")
                
                writer.writerow({
                    "feedback_id": entry.get("feedback_id"),
                    "investigation_id": entry.get("investigation_id"),
                    "alert_id": entry.get("alert_id"),
                    "hotspot_id": entry.get("hotspot_id") or "",
                    "outcome_category": entry.get("outcome_category"),
                    "actual_amount_lost": str(entry.get("actual_amount_lost") if entry.get("actual_amount_lost") is not None else ""),
                    "amount_prevented": str(entry.get("amount_prevented") if entry.get("amount_prevented") is not None else ""),
                    "atm_id_actual": entry.get("atm_id_actual") or "",
                    "actual_timestamp": act_ts_str,
                    "notes": entry.get("notes") or "",
                    "reported_by_role": entry.get("reported_by_role", "ANALYST"),
                    "verified_by_supervisor": str(bool(entry.get("verified_by_supervisor", False))),
                    "created_at": ts_str,
                })
    except Exception as exc:
        logger.error("Failed appending feedback entry to CSV: %s", exc)


def _sync_all_demo_feedback_to_csv() -> None:
    """Write all in-memory demo feedback to the fallback CSV."""
    try:
        with _feedback_csv_lock:
            with open(_FEEDBACK_CSV_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=_FEEDBACK_CSV_FIELDS)
                writer.writeheader()
                for entry in _DEMO_FEEDBACK:
                    ts = entry.get("created_at")
                    ts_str = ts.isoformat() if isinstance(ts, datetime) else (str(ts) if ts else _now().isoformat())
                    act_ts = entry.get("actual_timestamp")
                    act_ts_str = act_ts.isoformat() if isinstance(act_ts, datetime) else (str(act_ts) if act_ts else "")
                    
                    writer.writerow({
                        "feedback_id": entry.get("feedback_id"),
                        "investigation_id": entry.get("investigation_id"),
                        "alert_id": entry.get("alert_id"),
                        "hotspot_id": entry.get("hotspot_id") or "",
                        "outcome_category": entry.get("outcome_category"),
                        "actual_amount_lost": str(entry.get("actual_amount_lost") if entry.get("actual_amount_lost") is not None else ""),
                        "amount_prevented": str(entry.get("amount_prevented") if entry.get("amount_prevented") is not None else ""),
                        "atm_id_actual": entry.get("atm_id_actual") or "",
                        "actual_timestamp": act_ts_str,
                        "notes": entry.get("notes") or "",
                        "reported_by_role": entry.get("reported_by_role", "ANALYST"),
                        "verified_by_supervisor": str(bool(entry.get("verified_by_supervisor", False))),
                        "created_at": ts_str,
                    })
    except Exception as exc:
        logger.error("Failed writing initial feedback log to CSV: %s", exc)


def create_investigation(

    db: Optional[Session],
    alert_id: str,
    priority: str,
    actor_role: str = "ANALYST",
    initial_note: Optional[str] = None,
    risk_score: Optional[int] = None,
    severity: Optional[str] = None,
    dominant_category: Optional[str] = None,
    hotspot_id: Optional[str] = None,
    prediction_reference: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new investigation linked to an alert.
    Validates: no duplicate active investigation for same alert.
    Returns dict representation.
    """
    # Check for duplicate active investigation
    existing = get_investigation_by_alert(db, alert_id)
    if existing and existing.get("status") not in ("CLOSED", "DISMISSED"):
        raise ValueError(
            f"An active investigation already exists for alert '{alert_id}' "
            f"(status: {existing.get('status')}). "
            "Close or dismiss it before creating a new one."
        )

    inv_id = _make_id("INV")
    now = _now()

    inv_data = {
        "investigation_id": inv_id,
        "alert_id": alert_id,
        "hotspot_id": hotspot_id,
        "prediction_reference": prediction_reference,
        "status": "OPEN",
        "priority": priority.upper(),
        "created_by_role": actor_role,
        "risk_score": risk_score,
        "severity": severity,
        "dominant_category": dominant_category,
        "analyst_notes": initial_note,
        "review_summary": None,
        "recommended_next_step": None,
        "created_at": now,
        "updated_at": now,
    }

    if _is_db(db):
        inv = Investigation(**inv_data)
        db.add(inv)
        db.commit()
        db.refresh(inv)
        result = _inv_to_dict(inv)
    else:
        _DEMO_INVESTIGATIONS.append(inv_data)
        result = inv_data.copy()

    # Create initial timeline event
    _add_timeline(db, inv_id, "INVESTIGATION_CREATED",
                  f"Investigation created for alert {alert_id} with priority {priority}.",
                  actor_role)

    # Add initial note if provided
    if initial_note:
        _add_note_internal(db, inv_id, initial_note, actor_role)

    # Audit
    log_audit(db, "CREATE_INVESTIGATION", "INVESTIGATION", inv_id, actor_role, "SUCCESS",
              f"Investigation created for alert {alert_id}")

    return result


def get_investigation_by_alert(db: Optional[Session], alert_id: str) -> Optional[Dict[str, Any]]:
    """Find the most recent investigation for an alert."""
    if _is_db(db):
        try:
            inv = (
                db.query(Investigation)
                .filter(Investigation.alert_id == alert_id)
                .order_by(Investigation.created_at.desc())
                .first()
            )
            return _inv_to_dict(inv) if inv else None
        except Exception as exc:
            logger.error("get_investigation_by_alert: %s", exc)
    # Fallback
    matches = [i for i in _DEMO_INVESTIGATIONS if i["alert_id"] == alert_id]
    return sorted(matches, key=lambda x: x["created_at"], reverse=True)[0] if matches else None


def get_investigation(db: Optional[Session], investigation_id: str) -> Optional[Dict[str, Any]]:
    if _is_db(db):
        try:
            inv = db.query(Investigation).filter(
                Investigation.investigation_id == investigation_id
            ).first()
            return _inv_to_dict(inv) if inv else None
        except Exception as exc:
            logger.error("get_investigation: %s", exc)
    return next((i for i in _DEMO_INVESTIGATIONS if i["investigation_id"] == investigation_id), None)


def get_investigations(
    db: Optional[Session],
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Dict[str, Any]], int]:
    if _is_db(db):
        try:
            q = db.query(Investigation)
            if status:
                q = q.filter(Investigation.status == status.upper())
            if priority:
                q = q.filter(Investigation.priority == priority.upper())
            total = q.count()
            items = q.order_by(Investigation.created_at.desc()).offset(skip).limit(limit).all()
            return [_inv_to_dict(i) for i in items], total
        except Exception as exc:
            logger.error("get_investigations: %s", exc)
    # Fallback
    items = _DEMO_INVESTIGATIONS
    if status:
        items = [i for i in items if i.get("status") == status.upper()]
    if priority:
        items = [i for i in items if i.get("priority") == priority.upper()]
    total = len(items)
    return sorted(items, key=lambda x: x["created_at"], reverse=True)[skip:skip+limit], total


def update_investigation(
    db: Optional[Session],
    investigation_id: str,
    actor_role: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    review_summary: Optional[str] = None,
    recommended_next_step: Optional[str] = None,
) -> Dict[str, Any]:
    """Update investigation with status transition validation."""
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise ValueError(f"Investigation '{investigation_id}' not found.")

    changes = []

    if status:
        old_status = inv["status"]
        allowed = INVESTIGATION_TRANSITIONS.get(old_status, [])
        if status not in allowed:
            raise ValueError(
                f"Invalid status transition: {old_status} → {status}. "
                f"Allowed: {allowed}"
            )
        # Check role permission for certain transitions
        required_roles = TRANSITION_ROLE_REQUIREMENTS.get(status, [])
        if required_roles and actor_role not in required_roles:
            raise PermissionError(
                f"Transition to '{status}' requires role: {required_roles}. "
                f"Current role: {actor_role}"
            )
        inv["status"] = status
        changes.append(f"Status changed: {old_status} → {status}")
        _add_timeline(db, investigation_id, "STATUS_CHANGED",
                      f"Investigation status changed from {old_status} to {status}.", actor_role)

    if priority:
        old_p = inv.get("priority")
        inv["priority"] = priority.upper()
        changes.append(f"Priority: {old_p} → {priority}")

    if review_summary is not None:
        inv["review_summary"] = review_summary
        changes.append("Review summary updated.")

    if recommended_next_step is not None:
        inv["recommended_next_step"] = recommended_next_step
        changes.append("Recommended next step updated.")

    inv["updated_at"] = _now()

    if _is_db(db):
        try:
            db_inv = db.query(Investigation).filter(
                Investigation.investigation_id == investigation_id
            ).first()
            if db_inv:
                for k, v in inv.items():
                    if k not in ("id",):
                        try:
                            setattr(db_inv, k, v)
                        except AttributeError:
                            pass
                db.commit()
                db.refresh(db_inv)
                inv = _inv_to_dict(db_inv)
        except Exception as exc:
            logger.error("update_investigation DB: %s", exc)

    log_audit(db, "UPDATE_INVESTIGATION", "INVESTIGATION", investigation_id, actor_role, "SUCCESS",
              "; ".join(changes))
    return inv


def _inv_to_dict(inv: Investigation) -> Dict[str, Any]:
    if inv is None:
        return {}
    return {
        "investigation_id": inv.investigation_id,
        "alert_id": inv.alert_id,
        "hotspot_id": inv.hotspot_id,
        "prediction_reference": inv.prediction_reference,
        "status": inv.status,
        "priority": inv.priority,
        "created_by_role": inv.created_by_role,
        "risk_score": inv.risk_score,
        "severity": inv.severity,
        "dominant_category": inv.dominant_category,
        "analyst_notes": inv.analyst_notes,
        "review_summary": inv.review_summary,
        "recommended_next_step": inv.recommended_next_step,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Notes CRUD
# ─────────────────────────────────────────────────────────────────────────────

def add_note(
    db: Optional[Session],
    investigation_id: str,
    note_text: str,
    actor_role: str = "ANALYST",
) -> Dict[str, Any]:
    """Add a timestamped analyst note to an investigation."""
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise ValueError(f"Investigation '{investigation_id}' not found.")

    result = _add_note_internal(db, investigation_id, note_text, actor_role)
    _add_timeline(db, investigation_id, "NOTE_ADDED", "Analyst note recorded.", actor_role)
    log_audit(db, "ADD_NOTE", "NOTE", result["note_id"], actor_role, "SUCCESS",
              f"Note added to investigation {investigation_id}")
    return result


def _add_note_internal(
    db: Optional[Session],
    investigation_id: str,
    note_text: str,
    actor_role: str,
) -> Dict[str, Any]:
    note_id = _make_id("NOTE")
    now = _now()
    note_data = {
        "note_id": note_id,
        "investigation_id": investigation_id,
        "note": note_text,
        "created_at": now,
        "actor_role": actor_role,
    }
    if _is_db(db):
        try:
            n = InvestigationNote(**note_data)
            db.add(n)
            db.commit()
            db.refresh(n)
            return _note_to_dict(n)
        except Exception as exc:
            logger.error("add_note DB: %s", exc)
    _DEMO_NOTES.append(note_data)
    return note_data.copy()


def get_notes(db: Optional[Session], investigation_id: str) -> List[Dict[str, Any]]:
    if _is_db(db):
        try:
            notes = (
                db.query(InvestigationNote)
                .filter(InvestigationNote.investigation_id == investigation_id)
                .order_by(InvestigationNote.created_at.asc())
                .all()
            )
            return [_note_to_dict(n) for n in notes]
        except Exception as exc:
            logger.error("get_notes: %s", exc)
    return [n for n in _DEMO_NOTES if n["investigation_id"] == investigation_id]


def _note_to_dict(n: InvestigationNote) -> Dict[str, Any]:
    return {
        "note_id": n.note_id,
        "investigation_id": n.investigation_id,
        "note": n.note,
        "created_at": n.created_at,
        "actor_role": n.actor_role,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Evidence CRUD
# ─────────────────────────────────────────────────────────────────────────────

def add_evidence(
    db: Optional[Session],
    investigation_id: str,
    evidence_type: str,
    reference: str,
    description: Optional[str] = None,
    integrity_hash: Optional[str] = None,
    actor_role: str = "ANALYST",
) -> Dict[str, Any]:
    """Add an evidence reference to an investigation."""
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise ValueError(f"Investigation '{investigation_id}' not found.")

    ev_id = _make_id("EVD")
    now = _now()
    ev_data = {
        "evidence_id": ev_id,
        "investigation_id": investigation_id,
        "evidence_type": evidence_type.upper(),
        "reference": reference,
        "description": description,
        "integrity_hash": integrity_hash,
        "created_at": now,
        "created_by_role": actor_role,
    }

    if _is_db(db):
        try:
            ev = InvestigationEvidence(**ev_data)
            db.add(ev)
            db.commit()
            db.refresh(ev)
            result = _evidence_to_dict(ev)
        except Exception as exc:
            logger.error("add_evidence DB: %s", exc)
            _DEMO_EVIDENCE.append(ev_data)
            result = ev_data.copy()
    else:
        _DEMO_EVIDENCE.append(ev_data)
        result = ev_data.copy()

    _add_timeline(db, investigation_id, "EVIDENCE_ADDED",
                  f"Evidence reference ({evidence_type}) added.", actor_role)
    log_audit(db, "ADD_EVIDENCE_REFERENCE", "EVIDENCE", ev_id, actor_role, "SUCCESS",
              f"Evidence reference added to investigation {investigation_id}")
    return result


def get_evidence(db: Optional[Session], investigation_id: str) -> List[Dict[str, Any]]:
    if _is_db(db):
        try:
            evs = (
                db.query(InvestigationEvidence)
                .filter(InvestigationEvidence.investigation_id == investigation_id)
                .order_by(InvestigationEvidence.created_at.asc())
                .all()
            )
            return [_evidence_to_dict(e) for e in evs]
        except Exception as exc:
            logger.error("get_evidence: %s", exc)
    return [e for e in _DEMO_EVIDENCE if e["investigation_id"] == investigation_id]


def _evidence_to_dict(e: InvestigationEvidence) -> Dict[str, Any]:
    return {
        "evidence_id": e.evidence_id,
        "investigation_id": e.investigation_id,
        "evidence_type": e.evidence_type,
        "reference": e.reference,
        "description": e.description,
        "integrity_hash": e.integrity_hash,
        "created_at": e.created_at,
        "created_by_role": e.created_by_role,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Timeline CRUD
# ─────────────────────────────────────────────────────────────────────────────

def _add_timeline(
    db: Optional[Session],
    investigation_id: str,
    event_type: str,
    description: str,
    actor_role: str = "SYSTEM",
) -> None:
    tl_id = _make_id("TL")
    now = _now()
    tl_data = {
        "timeline_id": tl_id,
        "investigation_id": investigation_id,
        "event_type": event_type,
        "description": description,
        "actor_role": actor_role,
        "timestamp": now,
    }
    if _is_db(db):
        try:
            tl = InvestigationTimeline(**tl_data)
            db.add(tl)
            db.commit()
            return
        except Exception as exc:
            logger.error("_add_timeline DB: %s", exc)
    _DEMO_TIMELINE.append(tl_data)


def get_timeline(db: Optional[Session], investigation_id: str) -> List[Dict[str, Any]]:
    if _is_db(db):
        try:
            items = (
                db.query(InvestigationTimeline)
                .filter(InvestigationTimeline.investigation_id == investigation_id)
                .order_by(InvestigationTimeline.timestamp.asc())
                .all()
            )
            return [_tl_to_dict(t) for t in items]
        except Exception as exc:
            logger.error("get_timeline: %s", exc)
    items = [t for t in _DEMO_TIMELINE if t["investigation_id"] == investigation_id]
    return sorted(items, key=lambda x: x["timestamp"])


def _tl_to_dict(t: InvestigationTimeline) -> Dict[str, Any]:
    return {
        "timeline_id": t.timeline_id,
        "investigation_id": t.investigation_id,
        "event_type": t.event_type,
        "description": t.description,
        "actor_role": t.actor_role,
        "timestamp": t.timestamp,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────────────────────────────────────

def log_audit(
    db: Optional[Session],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    actor_role: str,
    result: str = "SUCCESS",
    detail: Optional[str] = None,
) -> None:
    """Record an audit event. Never logs passwords or sensitive data."""
    audit_id = _make_id("AUD")
    now = _now()
    audit_data = {
        "audit_id": audit_id,
        "timestamp": now,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "actor_role": actor_role,
        "result": result,
        "detail": detail,
    }
    if _is_db(db):
        try:
            al = AnalystAuditLog(**audit_data)
            db.add(al)
            db.commit()
            return
        except Exception as exc:
            logger.error("log_audit DB: %s", exc)

    # In fallback mode: update memory AND durable disk store
    _DEMO_AUDIT.append(audit_data)
    _append_audit_to_csv(audit_data)


def get_audit_log(
    db: Optional[Session],
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    result: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[Dict[str, Any]], int]:
    if _is_db(db):
        try:
            q = db.query(AnalystAuditLog)
            if action:
                q = q.filter(AnalystAuditLog.action == action.upper())
            if resource_type:
                q = q.filter(AnalystAuditLog.resource_type == resource_type.upper())
            if result:
                q = q.filter(AnalystAuditLog.result == result.upper())
            total = q.count()
            items = q.order_by(AnalystAuditLog.timestamp.desc()).offset(skip).limit(limit).all()
            return [_audit_to_dict(a) for a in items], total
        except Exception as exc:
            logger.error("get_audit_log: %s", exc)

    # Fallback: ensure persistent CSV records are loaded
    _init_demo_audit_from_csv()
    items = list(_DEMO_AUDIT)
    if action:
        items = [a for a in items if a.get("action") == action.upper()]
    if resource_type:
        items = [a for a in items if (a.get("resource_type") or "").upper() == resource_type.upper()]
    if result:
        items = [a for a in items if (a.get("result") or "").upper() == result.upper()]

    # Ensure timestamp is datetime for schema compliance
    for item in items:
        if isinstance(item.get("timestamp"), str):
            try:
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
            except Exception:
                item["timestamp"] = _now()

    def _sort_ts(x: Dict[str, Any]) -> str:
        ts = x.get("timestamp")
        return ts.isoformat() if isinstance(ts, datetime) else str(ts or "")

    total = len(items)
    return sorted(items, key=_sort_ts, reverse=True)[skip:skip+limit], total


def _audit_to_dict(a: AnalystAuditLog) -> Dict[str, Any]:
    return {
        "audit_id": a.audit_id,
        "timestamp": a.timestamp,
        "action": a.action,
        "resource_type": a.resource_type,
        "resource_id": a.resource_id,
        "actor_role": a.actor_role,
        "result": a.result,
        "detail": a.detail,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SHAP Explanation (from Phase 10 outputs)
# ─────────────────────────────────────────────────────────────────────────────

def get_shap_top_features(n: int = 10) -> List[Dict[str, Any]]:
    """
    Load top N SHAP features from Phase 10 outputs.
    Returns safe model-explanation data only.
    NEVER returns raw model inputs, PII, or sensitive data.
    """
    shap_path = OUTPUTS / "phase10_global_shap_importance.csv"
    if not shap_path.exists():
        return []
    try:
        import csv as csv_mod
        features = []
        with open(shap_path, newline="", encoding="utf-8") as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                rank = int(row.get("rank", 99))
                if rank <= n:
                    feat_raw = row.get("feature", "")
                    mean_abs = float(row.get("mean_abs_shap_value", 0.0))
                    mean_val = float(row.get("mean_shap_value", 0.0))
                    # Convert raw feature name to human-readable label
                    human = feat_raw.replace("_", " ").title()
                    direction = (
                        "Contributed toward higher model prediction"
                        if mean_val >= 0
                        else "Contributed toward lower model prediction"
                    )
                    features.append({
                        "rank": rank,
                        "feature": feat_raw,
                        "mean_abs_shap_value": round(mean_abs, 6),
                        "direction": direction,
                        "human_label": human,
                    })
        return sorted(features, key=lambda x: x["rank"])[:n]
    except Exception as exc:
        logger.error("get_shap_top_features: %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Outcome Feedback CRUD (Phase 11)
# ─────────────────────────────────────────────────────────────────────────────

def _feedback_to_dict(f: InvestigationOutcomeFeedback) -> Dict[str, Any]:
    if f is None:
        return {}
    return {
        "feedback_id": f.feedback_id,
        "investigation_id": f.investigation_id,
        "alert_id": f.alert_id,
        "hotspot_id": f.hotspot_id,
        "outcome_category": f.outcome_category,
        "actual_amount_lost": f.actual_amount_lost,
        "amount_prevented": f.amount_prevented,
        "atm_id_actual": f.atm_id_actual,
        "actual_timestamp": f.actual_timestamp,
        "notes": f.notes,
        "reported_by_role": f.reported_by_role,
        "verified_by_supervisor": f.verified_by_supervisor,
        "created_at": f.created_at,
    }


def record_outcome_feedback(
    db: Optional[Session],
    investigation_id: str,
    outcome_category: str,
    notes: str,
    actual_amount_lost: Optional[float] = None,
    amount_prevented: Optional[float] = None,
    atm_id_actual: Optional[str] = None,
    actual_timestamp: Optional[datetime] = None,
    verified_by_supervisor: bool = False,
    actor_role: str = "ANALYST",
) -> Dict[str, Any]:
    """
    Record post-intervention ground-truth outcome feedback for an investigation.
    Emits an OUTCOME_LOGGED timeline event and logs to persistent audit trail.
    """
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise ValueError(f"Investigation '{investigation_id}' not found.")

    cat = outcome_category.upper()
    if cat not in VALID_OUTCOME_CATEGORIES:
        raise ValueError(
            f"Invalid outcome category '{outcome_category}'. "
            f"Must be one of {sorted(VALID_OUTCOME_CATEGORIES)}"
        )

    feedback_id = _make_id("FBK")
    now = _now()
    
    entry = {
        "feedback_id": feedback_id,
        "investigation_id": investigation_id,
        "alert_id": inv.get("alert_id", ""),
        "hotspot_id": inv.get("hotspot_id"),
        "outcome_category": cat,
        "actual_amount_lost": float(actual_amount_lost) if actual_amount_lost is not None else None,
        "amount_prevented": float(amount_prevented) if amount_prevented is not None else None,
        "atm_id_actual": atm_id_actual,
        "actual_timestamp": actual_timestamp or now,
        "notes": notes,
        "reported_by_role": actor_role,
        "verified_by_supervisor": bool(verified_by_supervisor),
        "created_at": now,
    }

    if _is_db(db):
        try:
            db_obj = InvestigationOutcomeFeedback(**entry)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            entry = _feedback_to_dict(db_obj)
        except Exception as exc:
            logger.error("record_outcome_feedback DB: %s", exc)

    # In fallback mode or after DB attempt: update in-memory and durable CSV
    _DEMO_FEEDBACK.append(entry)
    _append_feedback_to_csv(entry)

    # Add timeline event
    tl_msg = (
        f"Operational outcome logged: {cat}. Notes: {notes[:80]}..."
        if len(notes) > 80
        else f"Operational outcome logged: {cat}. Notes: {notes}"
    )
    _add_timeline(db, investigation_id, "OUTCOME_LOGGED", tl_msg, actor_role)

    # Audit log
    audit_detail = f"Outcome: {cat}; Prevented: {amount_prevented}; Loss: {actual_amount_lost}"
    log_audit(db, "RECORD_OUTCOME_FEEDBACK", "INVESTIGATION", investigation_id, actor_role, "SUCCESS", audit_detail)

    return entry


def get_investigation_outcomes(
    db: Optional[Session],
    investigation_id: str,
) -> List[Dict[str, Any]]:
    """Retrieve all outcome feedback entries for a specific investigation."""
    if _is_db(db):
        try:
            items = (
                db.query(InvestigationOutcomeFeedback)
                .filter(InvestigationOutcomeFeedback.investigation_id == investigation_id)
                .order_by(InvestigationOutcomeFeedback.created_at.desc())
                .all()
            )
            return [_feedback_to_dict(i) for i in items]
        except Exception as exc:
            logger.error("get_investigation_outcomes DB: %s", exc)

    _init_demo_feedback_from_csv()
    items = [f for f in _DEMO_FEEDBACK if f.get("investigation_id") == investigation_id]
    return sorted(items, key=lambda x: x.get("created_at") or _now(), reverse=True)


def get_all_outcomes(
    db: Optional[Session],
    outcome_category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Dict[str, Any]], int]:
    """Retrieve paginated outcome feedback across all investigations with optional category filtering."""
    if _is_db(db):
        try:
            q = db.query(InvestigationOutcomeFeedback)
            if outcome_category:
                q = q.filter(InvestigationOutcomeFeedback.outcome_category == outcome_category.upper())
            total = q.count()
            items = q.order_by(InvestigationOutcomeFeedback.created_at.desc()).offset(skip).limit(limit).all()
            return [_feedback_to_dict(i) for i in items], total
        except Exception as exc:
            logger.error("get_all_outcomes DB: %s", exc)

    _init_demo_feedback_from_csv()
    items = list(_DEMO_FEEDBACK)
    if outcome_category:
        items = [f for f in items if f.get("outcome_category") == outcome_category.upper()]
    total = len(items)
    sorted_items = sorted(items, key=lambda x: x.get("created_at") or _now(), reverse=True)
    return sorted_items[skip : skip + limit], total


def get_outcome_statistics(db: Optional[Session]) -> Dict[str, Any]:
    """Calculate aggregated post-intervention metrics, prevention figures, and empirical precision."""
    all_fbk, total = get_all_outcomes(db, skip=0, limit=10000)
    
    counts: Dict[str, int] = {cat: 0 for cat in VALID_OUTCOME_CATEGORIES}
    total_prevented = 0.0
    total_loss = 0.0
    verified_sup_count = 0

    for fb in all_fbk:
        cat = fb.get("outcome_category", "OTHER")
        if cat in counts:
            counts[cat] += 1
        else:
            counts[cat] = 1
        
        if fb.get("amount_prevented"):
            total_prevented += float(fb["amount_prevented"])
        if fb.get("actual_amount_lost"):
            total_loss += float(fb["actual_amount_lost"])
        if fb.get("verified_by_supervisor"):
            verified_sup_count += 1

    # Operational precision: (CONFIRMED_CASHOUT + THWARTED_CASHOUT) / Total actionable feedback
    actionable_signals = counts.get("CONFIRMED_CASHOUT", 0) + counts.get("THWARTED_CASHOUT", 0)
    non_actionable = counts.get("FALSE_POSITIVE", 0) + counts.get("UNPRODUCTIVE_PATROL", 0)
    total_evaluated = actionable_signals + non_actionable
    
    precision_rate = round(actionable_signals / total_evaluated, 4) if total_evaluated > 0 else 0.0

    return {
        "total_feedback_count": total,
        "outcomes_by_category": counts,
        "total_amount_prevented": round(total_prevented, 2),
        "total_actual_loss": round(total_loss, 2),
        "operational_precision_rate": precision_rate,
        "verified_supervisor_count": verified_sup_count,
        "disclaimer": (
            "Post-intervention outcome records for authorized analytical audit. "
            "Measures operational verification and does not establish individual criminal liability."
        )
    }


# ─────────────────────────────────────────────────────────────────────────────
# Demo Data Seed (Synthetic — clearly labeled)
# ─────────────────────────────────────────────────────────────────────────────

def seed_demo_data(db: Optional[Session]) -> None:
    """
    Seed synthetic demonstration investigations, notes, evidence, timeline, and outcome feedback.
    CLEARLY LABELED: SYNTHETIC DEMONSTRATION DATA — Not real banking or NCRP records.
    """
    global _DEMO_INVESTIGATIONS, _DEMO_NOTES, _DEMO_EVIDENCE, _DEMO_TIMELINE, _DEMO_AUDIT, _DEMO_FEEDBACK

    # Only seed if no data exists
    if _DEMO_INVESTIGATIONS:
        return

    logger.info("Seeding synthetic demonstration data (Phase 17 + Phase 11)...")

    # Investigation 1 — CRITICAL alert
    inv1_id = "INV-DEMO-00000001"
    inv1 = {
        "investigation_id": inv1_id,
        "alert_id": "ALT-000052",  # CRITICAL demo alert
        "hotspot_id": "HS-18",
        "prediction_reference": "PRED-DEMO-001",
        "status": "UNDER_REVIEW",
        "priority": "CRITICAL",
        "created_by_role": "ANALYST",
        "risk_score": 91,
        "severity": "CRITICAL",
        "dominant_category": "UPI_FRAUD",
        "analyst_notes": "[SYNTHETIC DEMO] Priority review initiated for high-probability ATM cashout signal.",
        "review_summary": "[SYNTHETIC DEMO] Coordinated patrol verification active at HS-18 cluster.",
        "recommended_next_step": "Field dispatch and ATM surveillance corroboration.",
        "created_at": datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc),
    }

    # Investigation 2 — HIGH alert
    inv2_id = "INV-DEMO-00000002"
    inv2 = {
        "investigation_id": inv2_id,
        "alert_id": "ALT-000001",
        "hotspot_id": "HS-03",
        "prediction_reference": "PRED-DEMO-002",
        "status": "OPEN",
        "priority": "HIGH",
        "created_by_role": "ANALYST",
        "risk_score": 78,
        "severity": "HIGH",
        "dominant_category": "PHISHING",
        "analyst_notes": "[SYNTHETIC DEMO] Initial intake review pending for alert ALT-000001.",
        "review_summary": None,
        "recommended_next_step": "Cross-reference banking network ATM logs within 2.5km.",
        "created_at": datetime(2026, 9, 15, 11, 0, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 9, 15, 11, 0, 0, tzinfo=timezone.utc),
    }

    _DEMO_INVESTIGATIONS.extend([inv1, inv2])

    # Notes for Investigation 1
    _DEMO_NOTES.extend([
        {
            "note_id": "NOTE-DEMO-001",
            "investigation_id": inv1_id,
            "note": "[SYNTHETIC DEMO] Case file created based on analytical alert ALT-000052. Priority CRITICAL assigned.",
            "created_at": datetime(2026, 9, 15, 10, 5, 0, tzinfo=timezone.utc),
            "actor_role": "ANALYST",
        },
        {
            "note_id": "NOTE-DEMO-002",
            "investigation_id": inv1_id,
            "note": "[SYNTHETIC DEMO] Patrol unit dispatched to HS-18 geographic vicinity for deterrence check.",
            "created_at": datetime(2026, 9, 15, 10, 30, 0, tzinfo=timezone.utc),
            "actor_role": "SUPERVISOR",
        },
    ])

    # Evidence references
    _DEMO_EVIDENCE.extend([
        {
            "evidence_id": "EVD-DEMO-001",
            "investigation_id": inv1_id,
            "evidence_type": "SYSTEM_LOG",
            "reference": "LOG-HS18-20260915-0900",
            "description": "[SYNTHETIC DEMO] System-generated analytical cluster report for HS-18.",
            "integrity_hash": None,
            "created_at": datetime(2026, 9, 15, 10, 10, 0, tzinfo=timezone.utc),
            "created_by_role": "ANALYST",
        },
    ])

    # Timeline for Investigation 1
    _DEMO_TIMELINE.extend([
        {"timeline_id": "TL-DEMO-001", "investigation_id": inv1_id, "event_type": "ALERT_GENERATED", "description": "Analytical alert ALT-000052 generated by Phase 16 alert engine.", "actor_role": "SYSTEM", "timestamp": datetime(2026, 9, 15, 9, 0, 0, tzinfo=timezone.utc)},
        {"timeline_id": "TL-DEMO-002", "investigation_id": inv1_id, "event_type": "INVESTIGATION_CREATED", "description": "Investigation created for alert ALT-000052 with priority CRITICAL.", "actor_role": "ANALYST", "timestamp": datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc)},
        {"timeline_id": "TL-DEMO-003", "investigation_id": inv1_id, "event_type": "NOTE_ADDED", "description": "Analyst note recorded.", "actor_role": "ANALYST", "timestamp": datetime(2026, 9, 15, 10, 5, 0, tzinfo=timezone.utc)},
        {"timeline_id": "TL-DEMO-004", "investigation_id": inv1_id, "event_type": "EVIDENCE_ADDED", "description": "Evidence reference (SYSTEM_LOG) added.", "actor_role": "ANALYST", "timestamp": datetime(2026, 9, 15, 10, 10, 0, tzinfo=timezone.utc)},
        {"timeline_id": "TL-DEMO-005", "investigation_id": inv1_id, "event_type": "STATUS_CHANGED", "description": "Investigation status changed from OPEN to UNDER_REVIEW.", "actor_role": "ANALYST", "timestamp": datetime(2026, 9, 15, 11, 0, 0, tzinfo=timezone.utc)},
        {"timeline_id": "TL-DEMO-006", "investigation_id": inv1_id, "event_type": "REVIEWED_MODEL_EXPLANATION", "description": "Analyst reviewed SHAP model explanation. No operational action taken.", "actor_role": "ANALYST", "timestamp": datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)},
    ])

    # Timeline for Investigation 2
    _DEMO_TIMELINE.extend([
        {"timeline_id": "TL-DEMO-007", "investigation_id": inv2_id, "event_type": "ALERT_GENERATED", "description": "Analytical alert ALT-000001 generated by Phase 16 alert engine.", "actor_role": "SYSTEM", "timestamp": datetime(2026, 9, 15, 10, 50, 0, tzinfo=timezone.utc)},
        {"timeline_id": "TL-DEMO-008", "investigation_id": inv2_id, "event_type": "INVESTIGATION_CREATED", "description": "Investigation created for alert ALT-000001 with priority HIGH.", "actor_role": "ANALYST", "timestamp": datetime(2026, 9, 15, 11, 0, 0, tzinfo=timezone.utc)},
    ])

    # Seed some audit events
    _DEMO_AUDIT.extend([
        {"audit_id": "AUD-DEMO-001", "timestamp": datetime(2026, 9, 15, 9, 55, 0, tzinfo=timezone.utc), "action": "LOGIN", "resource_type": None, "resource_id": None, "actor_role": "ANALYST", "result": "SUCCESS", "detail": "[SYNTHETIC DEMO] Prototype login event."},
        {"audit_id": "AUD-DEMO-002", "timestamp": datetime(2026, 9, 15, 10, 0, 0, tzinfo=timezone.utc), "action": "CREATE_INVESTIGATION", "resource_type": "INVESTIGATION", "resource_id": inv1_id, "actor_role": "ANALYST", "result": "SUCCESS", "detail": f"Investigation created for alert ALT-000052"},
        {"audit_id": "AUD-DEMO-003", "timestamp": datetime(2026, 9, 15, 10, 5, 0, tzinfo=timezone.utc), "action": "ADD_NOTE", "resource_type": "NOTE", "resource_id": "NOTE-DEMO-001", "actor_role": "ANALYST", "result": "SUCCESS", "detail": f"Note added to investigation {inv1_id}"},
        {"audit_id": "AUD-DEMO-004", "timestamp": datetime(2026, 9, 15, 11, 0, 0, tzinfo=timezone.utc), "action": "UPDATE_INVESTIGATION", "resource_type": "INVESTIGATION", "resource_id": inv1_id, "actor_role": "ANALYST", "result": "SUCCESS", "detail": "Status changed: OPEN → UNDER_REVIEW"},
        {"audit_id": "AUD-DEMO-005", "timestamp": datetime(2026, 9, 15, 11, 0, 0, tzinfo=timezone.utc), "action": "CREATE_INVESTIGATION", "resource_type": "INVESTIGATION", "resource_id": inv2_id, "actor_role": "ANALYST", "result": "SUCCESS", "detail": "Investigation created for alert ALT-000001"},
    ])

    _sync_all_demo_audit_to_csv()
    _init_demo_audit_from_csv()

    # Seed outcome feedback (Phase 11)
    _DEMO_FEEDBACK.extend([
        {
            "feedback_id": "FBK-DEMO-000001",
            "investigation_id": inv1_id,
            "alert_id": "ALT-000052",
            "hotspot_id": "HS-18",
            "outcome_category": "THWARTED_CASHOUT",
            "actual_amount_lost": 0.0,
            "amount_prevented": 120000.0,
            "atm_id_actual": "ATM-0492",
            "actual_timestamp": datetime(2026, 9, 15, 11, 45, 0, tzinfo=timezone.utc),
            "notes": "[SYNTHETIC DEMO] Joint field patrol and branch security alerted. Suspect attempted cashout at ATM-0492 but fled on police vehicle arrival. Loss prevented.",
            "reported_by_role": "ANALYST",
            "verified_by_supervisor": True,
            "created_at": datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc),
        },
        {
            "feedback_id": "FBK-DEMO-000002",
            "investigation_id": inv2_id,
            "alert_id": "ALT-000001",
            "hotspot_id": "HS-03",
            "outcome_category": "CONFIRMED_CASHOUT",
            "actual_amount_lost": 45000.0,
            "amount_prevented": 0.0,
            "atm_id_actual": "ATM-0114",
            "actual_timestamp": datetime(2026, 9, 15, 11, 15, 0, tzinfo=timezone.utc),
            "notes": "[SYNTHETIC DEMO] Field patrol verified withdrawal completed prior to arrival. CCTV journal confirmed mule transaction matching complaint details.",
            "reported_by_role": "ANALYST",
            "verified_by_supervisor": True,
            "created_at": datetime(2026, 9, 15, 12, 15, 0, tzinfo=timezone.utc),
        },
    ])

    _sync_all_demo_feedback_to_csv()
    _init_demo_feedback_from_csv()

    logger.info("Synthetic demonstration data seeded: 2 investigations, notes, evidence, timeline, outcome feedback.")
