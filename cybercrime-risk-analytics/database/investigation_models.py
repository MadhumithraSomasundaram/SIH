"""
Phase 17 — Investigation & Analyst Interface: SQLAlchemy ORM Models
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

New tables (non-destructive — CREATE TABLE IF NOT EXISTS):
  - analyst_users             : Prototype user/role store (hashed passwords)
  - investigations            : Investigation records linked to alerts
  - investigation_notes       : Analyst notes per investigation
  - investigation_evidence    : Safe evidence/reference metadata
  - investigation_timeline    : Timestamped event log per investigation
  - analyst_audit_log         : System-wide analyst action audit trail

SAFETY RULES:
  - Does NOT store account numbers, card numbers, PINs, CVVs, OTPs
  - Does NOT store unnecessary PII
  - Does NOT modify or drop existing Phase 13/16 tables
  - All HIGH/CRITICAL signals require authorized human review
  - Prototype authentication only — not production government auth
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Index, Boolean, ForeignKey
)
from database.connection import Base


# ─────────────────────────────────────────────────────────────────────────────
# Analyst Users (Prototype — NOT production government identity)
# ─────────────────────────────────────────────────────────────────────────────
class AnalystUser(Base):
    """
    Prototype analyst user store.
    Roles: ANALYST | SUPERVISOR | ADMIN
    Passwords are bcrypt-hashed — never stored in plaintext.
    CLEARLY LABELED: Prototype authentication — not production government auth.
    """
    __tablename__ = "analyst_users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True,
                      doc="Unique username — no email, phone, or sensitive PII")
    display_name = Column(String(128), nullable=True,
                          doc="Display name for UI — no sensitive PII")
    role = Column(String(32), nullable=False, default="ANALYST",
                  doc="Role: ANALYST | SUPERVISOR | ADMIN")
    hashed_password = Column(String(256), nullable=False,
                             doc="bcrypt hash — never plaintext")
    is_active = Column(Boolean, default=True, doc="Account active status")
    created_at = Column(DateTime,
                        default=lambda: datetime.now(timezone.utc),
                        doc="Account creation timestamp")
    last_login = Column(DateTime, nullable=True, doc="Last successful login")

    __table_args__ = (
        Index("ix_analyst_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<AnalystUser(username='{self.username}', role='{self.role}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Investigations
# ─────────────────────────────────────────────────────────────────────────────
class Investigation(Base):
    """
    Core investigation record.
    Linked to an analytical alert and optionally a DBSCAN hotspot.

    DOES NOT:
    - Identify a person as criminal
    - Automatically accuse anyone
    - Store account/card/CVV/PIN/OTP/passwords
    - Store unnecessary PII

    All fields are safe analytical references only.
    """
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    investigation_id = Column(String(64), unique=True, nullable=False, index=True,
                              doc="Unique investigation reference (e.g. INV-20260916-000001)")
    alert_id = Column(String(64), nullable=False, index=True,
                      doc="Linked analytical alert reference (from cybercrime_alerts)")
    hotspot_id = Column(String(64), nullable=True, index=True,
                        doc="Optional linked Phase 14 DBSCAN cluster ID")
    prediction_reference = Column(String(64), nullable=True,
                                  doc="Optional safe prediction reference")

    # Status workflow: OPEN → UNDER_REVIEW → PENDING_VALIDATION → CLOSED | DISMISSED
    status = Column(String(32), nullable=False, default="OPEN", index=True,
                    doc="Status: OPEN | UNDER_REVIEW | PENDING_VALIDATION | CLOSED | DISMISSED")

    # Priority: LOW | MODERATE | HIGH | CRITICAL
    priority = Column(String(32), nullable=False, default="MODERATE", index=True,
                      doc="Investigation priority: LOW | MODERATE | HIGH | CRITICAL")

    # Actor (role only — no unnecessary PII)
    created_by_role = Column(String(32), nullable=False, default="ANALYST",
                             doc="Role of analyst who created investigation")

    # Risk summary (from alert — denormalized for performance)
    risk_score = Column(Integer, nullable=True, doc="Alert risk score [0-100]")
    severity = Column(String(32), nullable=True, doc="Alert severity level")
    dominant_category = Column(String(64), nullable=True,
                               doc="Dominant crime category from alert/hotspot")

    # Analyst workspace
    analyst_notes = Column(Text, nullable=True,
                           doc="Running analyst notes — record only authorized investigation info")
    review_summary = Column(Text, nullable=True,
                            doc="Final review summary — authorized conclusions only")
    recommended_next_step = Column(Text, nullable=True,
                                   doc="Analytical recommendation — NOT automatic enforcement")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        index=True, doc="Investigation creation timestamp")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        doc="Last update timestamp")

    __table_args__ = (
        Index("ix_investigations_alert_status", "alert_id", "status"),
        Index("ix_investigations_priority_created", "priority", "created_at"),
        Index("ix_investigations_hotspot", "hotspot_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Investigation(id='{self.investigation_id}', "
            f"alert='{self.alert_id}', status='{self.status}')>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Investigation Notes
# ─────────────────────────────────────────────────────────────────────────────
class InvestigationNote(Base):
    """
    Analyst notes linked to an investigation.
    Notes are timestamped and auditable.
    Display prompt: 'Record only information necessary for the authorized investigation.'
    """
    __tablename__ = "investigation_notes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    note_id = Column(String(64), unique=True, nullable=False, index=True,
                     doc="Unique note reference")
    investigation_id = Column(String(64), nullable=False, index=True,
                              doc="Linked investigation ID")
    note = Column(Text, nullable=False,
                  doc="Analyst note text — no sensitive PII, account numbers, etc.")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        index=True, doc="Note creation timestamp")
    actor_role = Column(String(32), nullable=False, default="ANALYST",
                        doc="Role of note author — no unnecessary personal identity")

    __table_args__ = (
        Index("ix_notes_investigation_created", "investigation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<InvestigationNote(note_id='{self.note_id}', inv='{self.investigation_id}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Investigation Evidence References
# ─────────────────────────────────────────────────────────────────────────────
class InvestigationEvidence(Base):
    """
    Safe evidence reference/metadata store.
    Stores REFERENCES only — not the actual sensitive evidence data.

    DOES NOT store:
    - Passwords, OTPs, PINs, CVVs
    - Full card/account numbers
    - Unnecessary PII
    - Actual file content (reference only)

    Evidence types:
      DATABASE_RECORD | REPORT | IMAGE_REFERENCE |
      DOCUMENT_REFERENCE | TRANSACTION_REFERENCE |
      SYSTEM_LOG | OTHER
    """
    __tablename__ = "investigation_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    evidence_id = Column(String(64), unique=True, nullable=False, index=True,
                         doc="Unique evidence reference ID")
    investigation_id = Column(String(64), nullable=False, index=True,
                              doc="Linked investigation ID")
    evidence_type = Column(String(64), nullable=False,
                           doc="Type: DATABASE_RECORD | REPORT | IMAGE_REFERENCE | "
                               "DOCUMENT_REFERENCE | TRANSACTION_REFERENCE | SYSTEM_LOG | OTHER")
    reference = Column(String(512), nullable=False,
                       doc="Safe reference string (e.g. report number, DB record ID)")
    description = Column(Text, nullable=True,
                         doc="Brief description of evidence — no sensitive data")
    integrity_hash = Column(String(256), nullable=True,
                            doc="Optional SHA-256 integrity verification reference. "
                                "Does not prove authenticity — reference only.")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        index=True, doc="Evidence reference creation timestamp")
    created_by_role = Column(String(32), nullable=False, default="ANALYST",
                             doc="Role of analyst who added reference")

    __table_args__ = (
        Index("ix_evidence_investigation_type", "investigation_id", "evidence_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<InvestigationEvidence(id='{self.evidence_id}', "
            f"type='{self.evidence_type}', inv='{self.investigation_id}')>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Investigation Timeline
# ─────────────────────────────────────────────────────────────────────────────
class InvestigationTimeline(Base):
    """
    Ordered event log per investigation.
    Each milestone or analyst action creates a timeline entry.
    Immutable once created — audit history must not be modified.
    """
    __tablename__ = "investigation_timeline"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    timeline_id = Column(String(64), unique=True, nullable=False, index=True,
                         doc="Unique timeline entry ID")
    investigation_id = Column(String(64), nullable=False, index=True,
                              doc="Linked investigation ID")

    # Event types for timeline
    event_type = Column(String(64), nullable=False,
                        doc="Event: ALERT_GENERATED | INVESTIGATION_CREATED | "
                            "STATUS_CHANGED | NOTE_ADDED | EVIDENCE_ADDED | "
                            "REVIEWED_ALERT | REVIEWED_HOTSPOT | "
                            "REVIEWED_MODEL_EXPLANATION | ESCALATED | "
                            "REQUESTED_VALIDATION | CLOSED | DISMISSED")
    description = Column(Text, nullable=False, doc="Human-readable event description")
    actor_role = Column(String(32), nullable=False, default="SYSTEM",
                        doc="Actor role: SYSTEM | ANALYST | SUPERVISOR | ADMIN")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       index=True, doc="Event timestamp")

    __table_args__ = (
        Index("ix_timeline_investigation_timestamp", "investigation_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<InvestigationTimeline(inv='{self.investigation_id}', "
            f"event='{self.event_type}', ts='{self.timestamp}')>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Analyst Audit Log
# ─────────────────────────────────────────────────────────────────────────────
class AnalystAuditLog(Base):
    """
    System-wide immutable audit trail.
    Every significant analyst action creates an audit event.

    Actions logged:
      LOGIN | VIEW_ALERT | ACKNOWLEDGE_ALERT | CREATE_INVESTIGATION |
      UPDATE_INVESTIGATION | ADD_NOTE | ADD_EVIDENCE_REFERENCE |
      VIEW_EXPLANATION | ESCALATE | RESOLVE | DISMISS |
      REVIEWED_ALERT | REVIEWED_HOTSPOT | REVIEWED_MODEL_EXPLANATION |
      REQUESTED_VALIDATION | CLOSED_INVESTIGATION | DISMISSED_ALERT

    NEVER logs:
      - Passwords (plaintext or hashed)
      - Sensitive request bodies
      - PINs, OTPs, CVVs, account/card numbers
    """
    __tablename__ = "analyst_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    audit_id = Column(String(64), unique=True, nullable=False, index=True,
                      doc="Unique audit event ID")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                       index=True, doc="Audit event timestamp")
    action = Column(String(64), nullable=False, index=True,
                    doc="Audit action code")
    resource_type = Column(String(64), nullable=True,
                           doc="Resource type: ALERT | INVESTIGATION | NOTE | EVIDENCE | AUDIT")
    resource_id = Column(String(64), nullable=True, index=True,
                         doc="Safe resource identifier")
    actor_role = Column(String(32), nullable=False, default="ANALYST",
                        doc="Actor role — no sensitive personal identity")
    result = Column(String(32), nullable=False, default="SUCCESS",
                    doc="Result: SUCCESS | FAILURE | DENIED")
    detail = Column(Text, nullable=True,
                    doc="Optional non-sensitive detail — no credentials or PII")

    __table_args__ = (
        Index("ix_analyst_audit_action_time", "action", "timestamp"),
        Index("ix_analyst_audit_resource", "resource_type", "resource_id"),
        Index("ix_analyst_audit_result", "result"),
    )

    def __repr__(self) -> str:
        return (
            f"<AnalystAuditLog(id='{self.audit_id}', action='{self.action}', "
            f"resource='{self.resource_id}', result='{self.result}')>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Investigation Outcome Feedback (Phase 11)
# ─────────────────────────────────────────────────────────────────────────────
class InvestigationOutcomeFeedback(Base):
    """
    Post-intervention ground-truth operational outcome feedback.
    Captures field outcomes (e.g. confirmed withdrawal, thwarted cashout,
    unproductive patrol, false positive) for institutional transparency,
    empirical evaluation, and model calibration without leaking unverified labels.

    DOES NOT store card numbers, account numbers, PINs, CVVs, OTPs, or passwords.
    """
    __tablename__ = "investigation_outcome_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    feedback_id = Column(String(64), unique=True, nullable=False, index=True,
                         doc="Unique feedback identifier (e.g. FBK-20260919-000001)")
    investigation_id = Column(String(64), nullable=False, index=True,
                              doc="Associated investigation reference ID")
    alert_id = Column(String(64), nullable=False, index=True,
                      doc="Associated alert reference ID")
    hotspot_id = Column(String(64), nullable=True, index=True,
                        doc="Optional associated hotspot ID")
    outcome_category = Column(String(64), nullable=False, index=True,
                              doc="Outcome: CONFIRMED_CASHOUT | THWARTED_CASHOUT | FALSE_POSITIVE | UNPRODUCTIVE_PATROL | WRONG_LOCATION | OTHER")
    actual_amount_lost = Column(Float, nullable=True,
                                doc="Observed financial loss in INR if confirmed")
    amount_prevented = Column(Float, nullable=True,
                              doc="Estimated financial loss prevented in INR if thwarted")
    atm_id_actual = Column(String(64), nullable=True,
                           doc="Observed ATM/terminal reference if applicable")
    actual_timestamp = Column(DateTime, nullable=True,
                              doc="Timestamp of observed event/patrol check")
    notes = Column(Text, nullable=False,
                   doc="Operational report / field observation notes — zero PII")
    reported_by_role = Column(String(32), nullable=False, default="ANALYST",
                              doc="Reporting actor role")
    verified_by_supervisor = Column(Boolean, default=False,
                                    doc="Supervisor verification status")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        index=True, doc="Feedback logging timestamp")

    __table_args__ = (
        Index("ix_feedback_inv_created", "investigation_id", "created_at"),
        Index("ix_feedback_category_created", "outcome_category", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<InvestigationOutcomeFeedback(id='{self.feedback_id}', "
            f"inv='{self.investigation_id}', category='{self.outcome_category}')>"
        )

