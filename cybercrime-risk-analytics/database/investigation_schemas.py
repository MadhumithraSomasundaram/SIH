"""
Phase 17 — Investigation & Analyst Interface: Pydantic Schemas
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

All schemas enforce:
  - No account numbers, card numbers, PINs, CVVs, OTPs
  - No unnecessary PII
  - Safe analytical references only
  - Proper field validation
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ─────────────────────────────────────────────────────────────────────────────
# Auth Schemas (Prototype only — not production government auth)
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., max_length=64, description="Analyst username")
    password: str = Field(..., max_length=256, description="Password — never logged or stored plaintext")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    display_name: Optional[str] = None
    disclaimer: str = "Prototype authentication — not production government authentication."


class UserRead(BaseModel):
    username: str
    display_name: Optional[str]
    role: str
    is_active: bool
    last_login: Optional[datetime]


# ─────────────────────────────────────────────────────────────────────────────
# Investigation Schemas
# ─────────────────────────────────────────────────────────────────────────────

VALID_INVESTIGATION_STATUSES = {
    "OPEN", "UNDER_REVIEW", "PENDING_VALIDATION", "CLOSED", "DISMISSED"
}
VALID_PRIORITIES = {"LOW", "MODERATE", "HIGH", "CRITICAL"}

# Valid status transitions
INVESTIGATION_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN": ["UNDER_REVIEW", "DISMISSED"],
    "UNDER_REVIEW": ["PENDING_VALIDATION", "DISMISSED"],
    "PENDING_VALIDATION": ["CLOSED", "DISMISSED", "UNDER_REVIEW"],
    "CLOSED": [],      # No automatic reopening
    "DISMISSED": [],   # No automatic reopening
}

# Roles required for status transitions
TRANSITION_ROLE_REQUIREMENTS: Dict[str, List[str]] = {
    "CLOSED": ["SUPERVISOR", "ADMIN"],
    "DISMISSED": ["SUPERVISOR", "ADMIN"],
}


class InvestigationCreate(BaseModel):
    alert_id: str = Field(..., max_length=64, description="Linked alert ID")
    priority: str = Field("MODERATE", description="Priority: LOW | MODERATE | HIGH | CRITICAL")
    initial_note: Optional[str] = Field(None, max_length=4096,
                                        description="Initial analyst note. "
                                                    "Record only authorized investigation info.")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(VALID_PRIORITIES)}")
        return v


class InvestigationUpdate(BaseModel):
    status: Optional[str] = Field(None, description="New status")
    priority: Optional[str] = Field(None, description="New priority")
    review_summary: Optional[str] = Field(None, max_length=8192)
    recommended_next_step: Optional[str] = Field(None, max_length=2048,
                                                  description="Analytical recommendation only — "
                                                              "NOT enforcement action")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.upper()
        if v not in VALID_INVESTIGATION_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_INVESTIGATION_STATUSES)}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.upper()
        if v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {sorted(VALID_PRIORITIES)}")
        return v


class InvestigationRead(BaseModel):
    investigation_id: str
    alert_id: str
    hotspot_id: Optional[str]
    prediction_reference: Optional[str]
    status: str
    priority: str
    created_by_role: str
    risk_score: Optional[int]
    severity: Optional[str]
    dominant_category: Optional[str]
    analyst_notes: Optional[str]
    review_summary: Optional[str]
    recommended_next_step: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationSummary(BaseModel):
    """Minimal summary for list views."""
    investigation_id: str
    alert_id: str
    status: str
    priority: str
    severity: Optional[str]
    dominant_category: Optional[str]
    risk_score: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Note Schemas
# ─────────────────────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=8192,
                      description="Analyst note. Record only information necessary "
                                  "for the authorized investigation.")


class NoteRead(BaseModel):
    note_id: str
    investigation_id: str
    note: str
    created_at: datetime
    actor_role: str

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Evidence Schemas
# ─────────────────────────────────────────────────────────────────────────────

VALID_EVIDENCE_TYPES = {
    "DATABASE_RECORD", "REPORT", "IMAGE_REFERENCE",
    "DOCUMENT_REFERENCE", "TRANSACTION_REFERENCE", "SYSTEM_LOG", "OTHER"
}


class EvidenceCreate(BaseModel):
    evidence_type: str = Field(..., description="Evidence type")
    reference: str = Field(..., max_length=512,
                           description="Safe reference (report number, DB record ID, etc.). "
                                       "Do NOT include account numbers, PINs, CVVs, OTPs, "
                                       "full card numbers, or passwords.")
    description: Optional[str] = Field(None, max_length=2048,
                                       description="Brief description — no sensitive data")
    integrity_hash: Optional[str] = Field(None, max_length=256,
                                          description="Optional SHA-256 integrity verification "
                                                      "reference (does not prove authenticity)")

    @field_validator("evidence_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_EVIDENCE_TYPES:
            raise ValueError(f"evidence_type must be one of {sorted(VALID_EVIDENCE_TYPES)}")
        return v


class EvidenceRead(BaseModel):
    evidence_id: str
    investigation_id: str
    evidence_type: str
    reference: str
    description: Optional[str]
    integrity_hash: Optional[str]
    created_at: datetime
    created_by_role: str

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Timeline Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TimelineEventRead(BaseModel):
    timeline_id: str
    investigation_id: str
    event_type: str
    description: str
    actor_role: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Audit Log Schemas
# ─────────────────────────────────────────────────────────────────────────────

class AuditLogRead(BaseModel):
    audit_id: str
    timestamp: datetime
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    actor_role: str
    result: str
    detail: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PaginatedAuditResponse(BaseModel):
    items: List[AuditLogRead]
    total: int
    skip: int
    limit: int


# ─────────────────────────────────────────────────────────────────────────────
# Overview Schema
# ─────────────────────────────────────────────────────────────────────────────

class AnalystOverview(BaseModel):
    total_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    new_alerts: int = 0
    in_review_alerts: int = 0
    total_investigations: int = 0
    open_investigations: int = 0
    under_review_investigations: int = 0
    analytical_hotspots: int = 0
    high_risk_areas: int = 0
    average_risk_score: Optional[float] = None
    data_disclaimer: str = (
        "SYNTHETIC DEMONSTRATION DATA. "
        "This prototype is an analytical decision-support system. "
        "Predictive risk scores and spatial hotspots are not proof of criminal activity "
        "and do not identify criminal responsibility."
    )
    authorized_system: str = "Authorized Analytical Decision Support"


# ─────────────────────────────────────────────────────────────────────────────
# Model Explanation Schema
# ─────────────────────────────────────────────────────────────────────────────

class ShapFeature(BaseModel):
    rank: int
    feature: str
    mean_abs_shap_value: float
    direction: str  # "Contributed toward higher model prediction" or "lower"
    human_label: str


class ExplanationResponse(BaseModel):
    investigation_id: str
    alert_id: str
    risk_score: Optional[int]
    risk_category: Optional[str]
    predicted_probability: Optional[float]
    top_features: List[ShapFeature]
    shap_disclaimer: str = (
        "Model explanations describe factors contributing to the model's prediction. "
        "They do not establish causality or criminal responsibility."
    )
    model_disclaimer: str = (
        "This is a model-derived analytical signal and does not establish criminal activity."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Investigation Detail (full composite)
# ─────────────────────────────────────────────────────────────────────────────

class InvestigationDetail(BaseModel):
    investigation: InvestigationRead
    notes: List[NoteRead]
    evidence: List[EvidenceRead]
    timeline: List[TimelineEventRead]
    explanation: Optional[ExplanationResponse]
    disclaimer: str = (
        "This prototype is an analytical decision-support system. "
        "Predictive risk scores and spatial hotspots are not proof of criminal activity "
        "and do not identify criminal responsibility. "
        "This prototype is not connected to live NCRP, banking, ATM, or financial institution systems."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Structured Intelligence Brief Schema (Phase 6)
# ─────────────────────────────────────────────────────────────────────────────

class IntelligenceBriefResponse(BaseModel):
    brief_reference: str
    generated_at: datetime
    generated_by_role: str
    investigation_id: str
    status: str
    priority: str
    severity: str
    risk_score: Optional[int] = None
    predicted_probability: Optional[float] = None
    alert_id: str
    case_id: Optional[str] = None
    complaint_timestamp: Optional[str] = None
    crime_category: Optional[str] = None
    victim_district: Optional[str] = None
    fraud_amount: Optional[float] = None
    spatial_intelligence: Dict[str, Any]
    shap_explainability: List[Dict[str, Any]]
    evidence_catalog: List[Dict[str, Any]]
    timeline_summary: List[Dict[str, Any]]
    analyst_notes_count: int
    latest_note: Optional[str] = None
    audit_trail_reference: str
    disclaimer: str = (
        "Analytical intelligence brief for authorized law enforcement review only. "
        "Does not constitute legal proof of criminal activity. "
        "Independent human investigation is required before operational deployment."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Outcome Feedback Schemas (Phase 11)
# ─────────────────────────────────────────────────────────────────────────────

VALID_OUTCOME_CATEGORIES = {
    "CONFIRMED_CASHOUT",
    "THWARTED_CASHOUT",
    "FALSE_POSITIVE",
    "UNPRODUCTIVE_PATROL",
    "WRONG_LOCATION",
    "OTHER",
}


class OutcomeFeedbackCreate(BaseModel):
    outcome_category: str = Field(..., description="Outcome: CONFIRMED_CASHOUT | THWARTED_CASHOUT | FALSE_POSITIVE | UNPRODUCTIVE_PATROL | WRONG_LOCATION | OTHER")
    notes: str = Field(..., min_length=3, max_length=4096, description="Field patrol observations or post-intervention notes. Must not contain PII.")
    actual_amount_lost: Optional[float] = Field(None, ge=0.0, description="Observed illicit cashout amount in INR if confirmed")
    amount_prevented: Optional[float] = Field(None, ge=0.0, description="Estimated loss prevented in INR if thwarted")
    atm_id_actual: Optional[str] = Field(None, max_length=64, description="Target or observed ATM ID (e.g. ATM-0492)")
    actual_timestamp: Optional[datetime] = Field(None, description="Observed time of event or patrol verification")
    verified_by_supervisor: Optional[bool] = Field(False, description="Whether outcome has been corroborated by supervisory review")

    @field_validator("outcome_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_OUTCOME_CATEGORIES:
            raise ValueError(f"outcome_category must be one of {sorted(VALID_OUTCOME_CATEGORIES)}")
        return v

    @field_validator("notes")
    @classmethod
    def validate_no_pii(cls, v: str) -> str:
        lower = v.lower()
        for forbidden in ["cvv", "otp", "card pin", "account password"]:
            if forbidden in lower:
                raise ValueError(f"Notes must not contain sensitive authentication credentials ({forbidden}).")
        return v


class OutcomeFeedbackRead(BaseModel):
    feedback_id: str
    investigation_id: str
    alert_id: str
    hotspot_id: Optional[str] = None
    outcome_category: str
    actual_amount_lost: Optional[float] = None
    amount_prevented: Optional[float] = None
    atm_id_actual: Optional[str] = None
    actual_timestamp: Optional[datetime] = None
    notes: str
    reported_by_role: str
    verified_by_supervisor: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedFeedbackResponse(BaseModel):
    items: List[OutcomeFeedbackRead]
    total: int
    skip: int
    limit: int


class OutcomeFeedbackStatistics(BaseModel):
    total_feedback_count: int
    outcomes_by_category: Dict[str, int]
    total_amount_prevented: float
    total_actual_loss: float
    operational_precision_rate: float
    verified_supervisor_count: int
    disclaimer: str = (
        "Post-intervention outcome records for authorized analytical audit. "
        "Measures operational verification and does not establish individual criminal liability."
    )


