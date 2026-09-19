"""
Phase 17 — Authorized Analyst Interface: FastAPI Routes
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Endpoints:
  POST /analyst/auth/login               — Prototype authentication
  GET  /analyst/auth/me                  — Current user info
  GET  /analyst/overview                 — Dashboard KPI stats
  GET  /analyst/alerts                   — Alert list (role-gated)
  GET  /analyst/alerts/{alert_id}        — Alert detail
  POST /analyst/investigations           — Create investigation
  GET  /analyst/investigations           — List investigations
  GET  /analyst/investigations/{inv_id}  — Investigation detail
  PATCH /analyst/investigations/{inv_id} — Update investigation
  POST /analyst/investigations/{inv_id}/notes    — Add note
  GET  /analyst/investigations/{inv_id}/timeline — Get timeline
  POST /analyst/investigations/{inv_id}/evidence — Add evidence
  GET  /analyst/investigations/{inv_id}/explanation — SHAP explanation
  GET  /analyst/audit                    — Audit log

SECURITY:
  - JWT prototype tokens (HS256) — clearly labeled as prototype
  - Role-based access control enforced on backend (not just frontend)
  - Never exposes passwords, PINs, OTPs, CVVs, card/account numbers
  - All HIGH/CRITICAL signals require human review
  - SQL injection protected via SQLAlchemy ORM
  - No automatic law-enforcement actions

DISCLAIMER:
  Prototype authentication — not production government authentication.
"""
from __future__ import annotations

import csv
import logging
import math
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.investigation_crud import (
    add_evidence,
    add_note,
    create_investigation,
    get_audit_log,
    get_evidence,
    get_investigation,
    get_investigations,
    get_notes,
    get_shap_top_features,
    get_timeline,
    get_user_by_username,
    log_audit,
    seed_demo_data,
    seed_demo_users,
    update_investigation,
    verify_password,
    record_outcome_feedback,
    get_investigation_outcomes,
    get_all_outcomes,
    get_outcome_statistics,
)
from database.investigation_schemas import (
    AuditLogRead,
    AnalystOverview,
    EvidenceCreate,
    EvidenceRead,
    ExplanationResponse,
    IntelligenceBriefResponse,
    InvestigationCreate,
    InvestigationDetail,
    InvestigationRead,
    InvestigationSummary,
    InvestigationUpdate,
    LoginRequest,
    NoteCreate,
    NoteRead,
    PaginatedAuditResponse,
    ShapFeature,
    TimelineEventRead,
    TokenResponse,
    UserRead,
    OutcomeFeedbackCreate,
    OutcomeFeedbackRead,
    OutcomeFeedbackStatistics,
    PaginatedFeedbackResponse,
)


logger = logging.getLogger("api.analyst")

# ─────────────────────────────────────────────────────────────────────────────
# JWT Configuration (Prototype — NOT production gov auth)
# ─────────────────────────────────────────────────────────────────────────────
_SECRET_KEY = os.getenv(
    "ANALYST_JWT_SECRET",
    "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184"
)
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ANALYST_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours

security = HTTPBearer(auto_error=False)

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
_ROUTES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _ROUTES_DIR.parent
OUTPUTS = PROJECT_ROOT / "outputs"

router = APIRouter(prefix="/analyst", tags=["Analyst Interface"])


# ─────────────────────────────────────────────────────────────────────────────
# Startup: seed demo data + users
# ─────────────────────────────────────────────────────────────────────────────
_demo_seeded = False


def _ensure_demo_data(db: Optional[Session] = None) -> None:
    global _demo_seeded
    if not _demo_seeded:
        seed_demo_data(db)
        seed_demo_users(db)
        _demo_seeded = True


# ─────────────────────────────────────────────────────────────────────────────
# JWT helpers
# ─────────────────────────────────────────────────────────────────────────────

def _create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _SECRET_KEY, algorithm=_ALGORITHM)


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
        )


def _get_optional_db():
    """Yield DB session if available, else None."""
    session_maker = None
    try:
        from database.connection import SessionLocal
        from database.crud import is_db_available
        if is_db_available():
            session_maker = SessionLocal
    except Exception:
        pass

    if session_maker is None:
        yield None
        return

    db = session_maker()
    try:
        yield db
    finally:
        db.close()



def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Optional[Session] = Depends(_get_optional_db),
) -> Dict[str, Any]:
    """Extract and validate JWT token. Returns user info dict."""
    _ensure_demo_data(db)
    if credentials is None:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
        )
    payload = _decode_token(credentials.credentials)
    username = payload.get("sub")
    role = payload.get("role", "ANALYST")
    if not username:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )
    return {"username": username, "role": role}


def require_role(*roles: str):
    """Dependency factory to enforce minimum role."""
    def _check(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {list(roles)}. "
                       f"Your role: {current_user['role']}",
            )
        return current_user
    return _check


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sanitize_alert_for_json(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes an alert dictionary for RFC 8259 JSON compliance.
    Converts float NaN, Infinity, -Infinity, and invalid string representations
    into JSON-compliant None (null), while strictly preserving valid 0, 0.0,
    integers, and valid floats.
    """
    if not isinstance(alert, dict):
        return {}

    cleaned: Dict[str, Any] = {}
    for k, v in alert.items():
        # None or pandas NA
        if v is None or pd.isna(v):
            cleaned[k] = None
            continue

        # Float / Int types
        if isinstance(v, (float, int)):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                cleaned[k] = None
            elif k in ("risk_score", "cluster_id_num") and isinstance(v, float):
                cleaned[k] = int(round(v))
            else:
                cleaned[k] = v
            continue

        # String representations
        s_val = str(v).strip()
        s_lower = s_val.lower()
        if s_lower in ("nan", "none", "null", ""):
            cleaned[k] = None
            continue
        if s_lower in ("inf", "-inf", "infinity", "-infinity"):
            cleaned[k] = None
            continue

        # Specific field type parsing
        if k in ("risk_score", "cluster_id_num"):
            try:
                flt = float(s_val)
                cleaned[k] = None if (math.isnan(flt) or math.isinf(flt)) else int(round(flt))
            except (ValueError, TypeError):
                cleaned[k] = None
        elif k in ("predicted_probability", "latitude", "longitude", "distance_to_atm_km"):
            try:
                flt = float(s_val)
                cleaned[k] = None if (math.isnan(flt) or math.isinf(flt)) else flt
            except (ValueError, TypeError):
                cleaned[k] = None
        elif k == "event_count":
            try:
                flt = float(s_val)
                cleaned[k] = None if (math.isnan(flt) or math.isinf(flt)) else int(flt)
            except (ValueError, TypeError):
                cleaned[k] = None
        elif k == "human_review_required":
            cleaned[k] = s_lower in ("true", "1", "yes")
        elif k in ("created_at", "updated_at", "time_window_start", "time_window_end"):
            if isinstance(v, datetime):
                cleaned[k] = v.isoformat()
            else:
                cleaned[k] = s_val
        else:
            cleaned[k] = s_val

    return cleaned


def _load_alerts_csv() -> List[Dict[str, Any]]:
    """Load demo alerts from Phase 16 CSV or in-memory fallback."""
    # Check if database/crud in-memory cache has active alerts
    try:
        from database.crud import _LOCAL_ALERTS_CACHE
        if _LOCAL_ALERTS_CACHE:
            return [_sanitize_alert_for_json(dict(a)) for a in _LOCAL_ALERTS_CACHE.values()]
    except Exception:
        pass

    p = OUTPUTS / "phase16_demo_alerts.csv"
    if not p.exists():
        return []
    try:
        df = pd.read_csv(p, dtype=str)
        df = df.where(df.notna(), None)
        records = df.to_dict("records")
        return [_sanitize_alert_for_json(r) for r in records]
    except Exception as exc:
        logger.error("_load_alerts_csv: %s", exc)
        return []


def _load_hotspot_summary() -> List[Dict[str, Any]]:
    p = OUTPUTS / "phase14_hotspot_summary.csv"
    if not p.exists():
        return []
    try:
        df = pd.read_csv(p)
        df = df.where(df.notna(), None)
        return df.to_dict("records")
    except Exception as exc:
        logger.error("_load_hotspot_summary: %s", exc)
        return []


def _get_alert_by_id(alert_id: str) -> Optional[Dict[str, Any]]:
    """Try DB first, fallback to memory cache and CSV."""
    try:
        from database.crud import get_alert, is_db_available
        from database.connection import SessionLocal
        if is_db_available():
            db = SessionLocal()
            try:
                a = get_alert(db=db, alert_id=alert_id)
                if a:
                    return _sanitize_alert_for_json(a)
            finally:
                db.close()
    except Exception as exc:
        logger.debug("DB alert lookup failed: %s", exc)
    # CSV / memory fallback
    alerts = _load_alerts_csv()
    target = next((a for a in alerts if a.get("alert_id") == alert_id), None)
    return _sanitize_alert_for_json(target) if target else None


_FORBIDDEN_SHAP_TOKENS = (
    "future_withdrawal", "is_linked_to_withdrawal", "withdrawal_timestamp",
    "withdrawal_amount", "target_", "withdrawal_status", "card", "pin",
    "otp", "cvv", "password", "account_id"
)

_CACHED_DEMO_INPUT_DF: Optional[pd.DataFrame] = None
_CACHED_FULL_FEATURES_DF: Optional[pd.DataFrame] = None
_CACHED_CLUSTERED_DF: Optional[pd.DataFrame] = None


def _clean_feature_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Strip leakage targets and forbidden credentials from input features."""
    cleaned: Dict[str, Any] = {}
    for k, v in raw.items():
        k_lower = str(k).lower()
        if any(tok in k_lower for tok in _FORBIDDEN_SHAP_TOKENS):
            continue
        if pd.isna(v) or v is None or str(v) == "nan":
            cleaned[k] = None
        else:
            cleaned[k] = v
    return cleaned


def _resolve_investigation_feature_record(
    inv: Dict[str, Any],
    alert: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve underlying record feature payload for an investigation / alert.
    Resolution order:
      1. data/demo/demo_prediction_input.csv (case_id == prediction_reference)
      2. data/processed/feature_engineered_cybercrime_data.csv (case_id == prediction_reference)
      3. outputs/phase14_clustered_events.csv mapping via hotspot_id -> representative complaint case_id
      4. Fallback demo record mapped by severity/priority tier
    """
    global _CACHED_DEMO_INPUT_DF, _CACHED_FULL_FEATURES_DF, _CACHED_CLUSTERED_DF

    raw_pred = inv.get("prediction_reference") or (alert.get("prediction_reference") if alert else None)
    pred_ref = str(raw_pred).strip() if (raw_pred is not None and not pd.isna(raw_pred)) else ""

    raw_hs = inv.get("hotspot_id") or (alert.get("hotspot_id") if alert else None)
    hotspot_id = str(raw_hs).strip() if (raw_hs is not None and not pd.isna(raw_hs)) else ""

    raw_sev = inv.get("severity") or (alert.get("severity") if alert else None) or "HIGH"
    severity = str(raw_sev).strip().upper() if not pd.isna(raw_sev) else "HIGH"

    demo_path = PROJECT_ROOT / "data" / "demo" / "demo_prediction_input.csv"
    full_path = PROJECT_ROOT / "data" / "processed" / "feature_engineered_cybercrime_data.csv"
    cluster_path = PROJECT_ROOT / "outputs" / "phase14_clustered_events.csv"

    # 1. Match prediction_reference in demo inputs
    if demo_path.exists():
        if _CACHED_DEMO_INPUT_DF is None:
            try:
                _CACHED_DEMO_INPUT_DF = pd.read_csv(demo_path)
            except Exception as exc:
                logger.warning("Could not read %s: %s", demo_path, exc)
        if _CACHED_DEMO_INPUT_DF is not None and pred_ref and "case_id" in _CACHED_DEMO_INPUT_DF.columns:
            m = _CACHED_DEMO_INPUT_DF[_CACHED_DEMO_INPUT_DF["case_id"] == pred_ref]
            if not m.empty:
                return _clean_feature_dict(m.iloc[0].to_dict())

    # 2. Match prediction_reference in full feature-engineered dataset
    if full_path.exists():
        if _CACHED_FULL_FEATURES_DF is None:
            try:
                _CACHED_FULL_FEATURES_DF = pd.read_csv(full_path)
            except Exception as exc:
                logger.warning("Could not read %s: %s", full_path, exc)
        if _CACHED_FULL_FEATURES_DF is not None and pred_ref and "case_id" in _CACHED_FULL_FEATURES_DF.columns:
            m = _CACHED_FULL_FEATURES_DF[_CACHED_FULL_FEATURES_DF["case_id"] == pred_ref]
            if not m.empty:
                return _clean_feature_dict(m.iloc[0].to_dict())

    # 3. Match via hotspot_id / cluster_id (e.g. HS-18 -> cluster 18)
    if hotspot_id and cluster_path.exists():
        if _CACHED_CLUSTERED_DF is None:
            try:
                _CACHED_CLUSTERED_DF = pd.read_csv(cluster_path)
            except Exception as exc:
                logger.warning("Could not read %s: %s", cluster_path, exc)
        if _CACHED_CLUSTERED_DF is not None and "cluster_id" in _CACHED_CLUSTERED_DF.columns:
            try:
                # Hotspot IDs are typically "HS-18" or "18"
                raw_num = hotspot_id.replace("HS-", "").replace("hs-", "").strip()
                if raw_num.isdigit():
                    c_id = int(raw_num)
                    c_matches = _CACHED_CLUSTERED_DF[_CACHED_CLUSTERED_DF["cluster_id"] == c_id]
                    if not c_matches.empty:
                        rep_case_id = str(c_matches.iloc[0]["case_id"]).strip()
                        if _CACHED_FULL_FEATURES_DF is not None and "case_id" in _CACHED_FULL_FEATURES_DF.columns:
                            fm = _CACHED_FULL_FEATURES_DF[_CACHED_FULL_FEATURES_DF["case_id"] == rep_case_id]
                            if not fm.empty:
                                return _clean_feature_dict(fm.iloc[0].to_dict())
            except Exception as exc:
                logger.debug("Cluster lookup failed for %s: %s", hotspot_id, exc)

    # 4. Fallback mapped by tier from demo inputs
    if _CACHED_DEMO_INPUT_DF is not None and not _CACHED_DEMO_INPUT_DF.empty:
        case_tier_map = {
            "CRITICAL": "DEMO_CASE_004_HIGH_PRIORITY",
            "HIGH": "DEMO_CASE_003_HIGH",
            "MODERATE": "DEMO_CASE_002_MODERATE",
            "LOW": "DEMO_CASE_001_LOW",
        }
        target_case = case_tier_map.get(severity, "DEMO_CASE_003_HIGH")
        m = _CACHED_DEMO_INPUT_DF[_CACHED_DEMO_INPUT_DF["case_id"] == target_case]
        if not m.empty:
            return _clean_feature_dict(m.iloc[0].to_dict())
        return _clean_feature_dict(_CACHED_DEMO_INPUT_DF.iloc[0].to_dict())

    return None


def _build_investigation_explanation(
    inv: Dict[str, Any],
    alert: Optional[Dict[str, Any]] = None,
    n_features: int = 10,
) -> Optional[ExplanationResponse]:
    """
    Generate a record-specific SHAP explanation for an investigation's linked alert/record.
    Calls explain_prediction() with local TreeExplainer, gracefully falling back to
    global feature ranking if computation cannot be completed.
    """
    investigation_id = inv.get("investigation_id", "")
    alert_id = inv.get("alert_id", "")
    risk_score = inv.get("risk_score")
    risk_category = inv.get("severity")
    predicted_probability = _parse_optional_float(alert.get("predicted_probability") if alert else None)

    features: List[Dict[str, Any]] = []

    # Attempt record-specific SHAP explanation
    record_dict = _resolve_investigation_feature_record(inv, alert)
    if record_dict:
        try:
            from api.dependencies import app_state, initialize_model_state
            if not (app_state.model_loaded and app_state.pipeline_loaded):
                try:
                    initialize_model_state()
                except Exception as init_exc:
                    logger.warning("Could not initialize model state for SHAP: %s", init_exc)

            if app_state.model_loaded and app_state.pipeline_loaded:
                from src.predict import explain_prediction
                shap_result = explain_prediction(record_dict, app_state.pipeline, app_state.metadata)
                if shap_result.get("status") == "SUCCESS":
                    contributors = shap_result.get("all_top_contributors", [])
                    for idx, c in enumerate(contributors[:n_features], start=1):
                        shap_val = float(c.get("shap_value", 0.0))
                        feat_name = c.get("feature", "")
                        human = feat_name.replace("_", " ").title()
                        direction = (
                            "Contributed toward higher model prediction"
                            if shap_val >= 0
                            else "Contributed toward lower model prediction"
                        )
                        features.append({
                            "rank": idx,
                            "feature": feat_name,
                            "mean_abs_shap_value": round(abs(shap_val), 6),
                            "direction": direction,
                            "human_label": human,
                        })
        except Exception as exc:
            logger.warning("Record-specific SHAP explanation failed for %s: %s", investigation_id, exc)

    # Fallback to static global SHAP ranking if record-specific explanation unavailable
    if not features:
        features = get_shap_top_features(n_features)

    if not features:
        return None

    return ExplanationResponse(
        investigation_id=investigation_id,
        alert_id=alert_id,
        risk_score=risk_score,
        risk_category=risk_category,
        predicted_probability=predicted_probability,
        top_features=[ShapFeature(**f) for f in features],
    )



def _get_all_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    hotspot_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Dict[str, Any]], int]:
    """Load alerts from DB or CSV fallback with full JSON sanitization."""
    try:
        from database.crud import get_alerts, is_db_available
        from database.connection import SessionLocal
        if is_db_available():
            db = SessionLocal()
            try:
                items, total = get_alerts(
                    db=db, severity=severity, status=status,
                    alert_type=alert_type, hotspot_id=hotspot_id,
                    skip=skip, limit=limit
                )
                cleaned = [_sanitize_alert_for_json(a) for a in items]
                return cleaned, total
            finally:
                db.close()
    except Exception as exc:
        logger.debug("DB alert query failed: %s", exc)
    # CSV / in-memory fallback
    alerts = _load_alerts_csv()
    if severity:
        alerts = [a for a in alerts if (a.get("severity") or "").upper() == severity.upper()]
    if status:
        alerts = [a for a in alerts if (a.get("status") or "").upper() == status.upper()]
    if alert_type:
        alerts = [a for a in alerts if (a.get("alert_type") or "").upper() == alert_type.upper()]
    if hotspot_id:
        alerts = [a for a in alerts if a.get("hotspot_id") == hotspot_id]
    total = len(alerts)
    return [_sanitize_alert_for_json(a) for a in alerts[skip:skip+limit]], total


def _parse_optional_float(v: Any) -> Optional[float]:
    """Safely parse float, rejecting NaN, Infinity, and invalid string tokens."""
    if v is None or pd.isna(v):
        return None
    s = str(v).strip().lower()
    if s in ("nan", "none", "null", "", "inf", "-inf", "infinity", "-infinity"):
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (ValueError, TypeError):
        return None


def _parse_optional_int(v: Any) -> Optional[int]:
    """Safely parse int, rejecting NaN, Infinity, and invalid string tokens."""
    try:
        f = _parse_optional_float(v)
        return int(round(f)) if f is not None else None
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# AUTH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Analyst Login (Prototype)",
    description=(
        "Prototype authentication for analyst interface. "
        "**NOT production government authentication.** "
        "For demonstration purposes only."
    ),
)
async def analyst_login(
    body: LoginRequest,
    db: Optional[Session] = Depends(_get_optional_db),
):
    # Trim whitespace
    username = (body.username or "").strip()
    password = body.password or ""

    if not username or not password:
        log_audit(db, "LOGIN", None, None, "UNKNOWN", "FAILURE", "Failed login attempt (empty credentials)")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    _ensure_demo_data(db)

    # Try DB user first
    user = get_user_by_username(db, username)

    # Fallback to demo credentials from environment / prototype catalog
    demo_creds = {
        os.getenv("DEMO_ANALYST_USER", "demo_analyst"): (
            os.getenv("DEMO_ANALYST_PASS", "AnalystDemo2026!"), "ANALYST", "Demo Analyst"
        ),
        "analyst_user": ("AnalystSecure2026!", "ANALYST", "Authorized LEA Analyst"),
        os.getenv("DEMO_SUPERVISOR_USER", "demo_supervisor"): (
            os.getenv("DEMO_SUPERVISOR_PASS", "SupervisorDemo2026!"), "SUPERVISOR", "Demo Supervisor"
        ),
        "supervisor_user": ("SupervisorSecure2026!", "SUPERVISOR", "LEA Supervisor"),
        os.getenv("DEMO_ADMIN_USER", "demo_admin"): (
            os.getenv("DEMO_ADMIN_PASS", "AdminDemo2026!"), "ADMIN", "Demo Admin"
        ),
        "admin_user": ("AdminSecure2026!", "ADMIN", "System Administrator"),
        os.getenv("DEMO_BANK_USER", "demo_bank"): (
            os.getenv("DEMO_BANK_PASS", "BankDemo2026!"), "BANK_ANALYST", "Demo Bank Analyst"
        ),
        "bank_user": ("BankSecure2026!", "BANK_ANALYST", "Institutional Bank Analyst"),
    }

    authenticated = False
    role = "ANALYST"
    display_name = username

    if user:
        if verify_password(password, user.hashed_password):
            authenticated = True
            role = user.role
            display_name = user.display_name or user.username
            try:
                from database.investigation_crud import update_last_login
                update_last_login(db, user)
            except Exception:
                pass
    elif username in demo_creds:
        expected_pass, expected_role, expected_name = demo_creds[username]
        if password == expected_pass:
            authenticated = True
            role = expected_role
            display_name = expected_name

    if not authenticated:
        log_audit(db, "LOGIN", None, None, "UNKNOWN", "FAILURE", f"Failed login attempt for {username}")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = _create_access_token({"sub": body.username, "role": role})
    log_audit(db, "LOGIN", None, None, role, "SUCCESS", f"Prototype login by {body.username}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=role,
        display_name=display_name,
    )


@router.get(
    "/auth/me",
    response_model=UserRead,
    summary="Current Analyst Info",
)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserRead(
        username=current_user["username"],
        display_name=current_user.get("display_name", current_user["username"]),
        role=current_user["role"],
        is_active=True,
        last_login=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/overview",
    response_model=AnalystOverview,
    summary="Analyst Dashboard Overview",
    description="Aggregated KPI statistics from alerts, investigations, and hotspots. "
                "All values from actual data sources — no fabricated statistics.",
)
async def analyst_overview(
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    t_start = time.perf_counter()

    alerts, total = _get_all_alerts(limit=2000)
    hotspots = _load_hotspot_summary()
    investigations, inv_total = get_investigations(db, limit=2000)

    # Alert counts
    critical = sum(1 for a in alerts if (a.get("severity") or "").upper() == "CRITICAL")
    high = sum(1 for a in alerts if (a.get("severity") or "").upper() == "HIGH")
    new_count = sum(1 for a in alerts if (a.get("status") or "").upper() == "NEW")
    in_review = sum(1 for a in alerts if (a.get("status") or "").upper() == "IN_REVIEW")

    # Risk scores
    risk_scores = [_parse_optional_float(a.get("risk_score")) for a in alerts]
    risk_scores = [r for r in risk_scores if r is not None]
    avg_risk = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else None

    # Hotspots
    high_risk_areas = sum(1 for h in hotspots if (h.get("hotspot_status") or "").startswith("HIGH"))

    # Investigations
    open_inv = sum(1 for i in investigations if i.get("status") == "OPEN")
    under_review_inv = sum(1 for i in investigations if i.get("status") == "UNDER_REVIEW")

    latency = round((time.perf_counter() - t_start) * 1000, 2)
    logger.info("overview query: %.1f ms", latency)

    log_audit(db, "VIEW_OVERVIEW", None, None, current_user["role"], "SUCCESS")

    return AnalystOverview(
        total_alerts=total,
        critical_alerts=critical,
        high_alerts=high,
        new_alerts=new_count,
        in_review_alerts=in_review,
        total_investigations=inv_total,
        open_investigations=open_inv,
        under_review_investigations=under_review_inv,
        analytical_hotspots=len(hotspots),
        high_risk_areas=high_risk_areas,
        average_risk_score=avg_risk,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ALERTS (Analyst-gated view)
# ─────────────────────────────────────────────────────────────────────────────

class PaginatedAlerts(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int
    disclaimer: str = (
        "Analytical signals for authorized human review only. "
        "Not proof of criminal activity."
    )


@router.get(
    "/alerts",
    summary="Analyst Alert List",
    description="Retrieve analytical alerts with filters. "
                "All HIGH and CRITICAL signals require authorized human review.",
)
async def analyst_list_alerts(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    hotspot_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    items, total = _get_all_alerts(severity, status, alert_type, hotspot_id, skip, limit)

    # Strip any sensitive fields and sanitize for JSON
    safe_fields = {
        "alert_id", "alert_type", "severity", "status", "risk_score",
        "predicted_probability", "event_count", "dominant_category",
        "time_window_start", "time_window_end", "operational_message",
        "human_review_required", "model_version", "hotspot_id",
        "created_at", "updated_at", "disclaimer", "latitude", "longitude",
    }
    cleaned = [{k: v for k, v in _sanitize_alert_for_json(a).items() if k in safe_fields} for a in items]

    log_audit(db, "VIEW_ALERT", "ALERT", "list", current_user["role"], "SUCCESS",
              f"Listed alerts (skip={skip},limit={limit})")

    return {
        "items": cleaned,
        "total": total,
        "skip": skip,
        "limit": limit,
        "disclaimer": "Analytical signals for authorized human review only. Not proof of criminal activity.",
    }


@router.get(
    "/alerts/{alert_id}",
    summary="Analyst Alert Detail",
    description="Retrieve a single alert for authorized analytical review.",
)
async def analyst_alert_detail(
    alert_id: str,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    alert = _get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )

    # Strip sensitive fields and sanitize for JSON
    safe_fields = {
        "alert_id", "alert_type", "severity", "status", "risk_score",
        "predicted_probability", "event_count", "dominant_category",
        "time_window_start", "time_window_end", "operational_message",
        "human_review_required", "model_version", "hotspot_id",
        "created_at", "updated_at", "disclaimer", "latitude", "longitude",
    }
    safe_alert = {k: v for k, v in _sanitize_alert_for_json(alert).items() if k in safe_fields}

    # Add operational disclaimer
    safe_alert["analytical_disclaimer"] = (
        "This is a model-derived analytical signal and does not establish criminal activity."
    )

    log_audit(db, "VIEW_ALERT", "ALERT", alert_id, current_user["role"], "SUCCESS")

    return safe_alert


# ─────────────────────────────────────────────────────────────────────────────
# INVESTIGATIONS
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/investigations",
    response_model=InvestigationRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create Investigation",
    description=(
        "Create an investigation linked to an analytical alert. "
        "Only one active investigation per alert is allowed. "
        "All HIGH/CRITICAL alerts require authorized human review."
    ),
)
async def create_investigation_endpoint(
    body: InvestigationCreate,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)

    # Validate alert exists
    alert = _get_alert_by_id(body.alert_id)
    if not alert:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{body.alert_id}' not found.",
        )

    try:
        inv = create_investigation(
            db=db,
            alert_id=body.alert_id,
            priority=body.priority,
            actor_role=current_user["role"],
            initial_note=body.initial_note,
            risk_score=_parse_optional_int(alert.get("risk_score")),
            severity=alert.get("severity"),
            dominant_category=alert.get("dominant_category"),
            hotspot_id=alert.get("hotspot_id"),
            prediction_reference=alert.get("prediction_reference"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return InvestigationRead(**inv)


@router.get(
    "/investigations",
    summary="List Investigations",
    description="Retrieve investigation records with optional filters.",
)
async def list_investigations(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    items, total = get_investigations(db, status=status, priority=priority, skip=skip, limit=limit)

    log_audit(db, "VIEW_INVESTIGATION", "INVESTIGATION", "list", current_user["role"], "SUCCESS")

    return {
        "items": [InvestigationSummary(**i).model_dump(mode="json") for i in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get(
    "/investigations/{investigation_id}",
    summary="Investigation Detail",
    description="Full investigation detail including notes, evidence, timeline, and model explanation.",
)
async def investigation_detail(
    investigation_id: str,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    notes = get_notes(db, investigation_id)
    evidence = get_evidence(db, investigation_id)
    timeline = get_timeline(db, investigation_id)

    # Build SHAP explanation (record-specific)
    alert = _get_alert_by_id(inv.get("alert_id", ""))
    explanation = _build_investigation_explanation(inv, alert, n_features=10)

    log_audit(db, "VIEW_INVESTIGATION", "INVESTIGATION", investigation_id, current_user["role"], "SUCCESS")

    detail = InvestigationDetail(
        investigation=InvestigationRead(**inv),
        notes=[NoteRead(**n) for n in notes],
        evidence=[EvidenceRead(**e) for e in evidence],
        timeline=[TimelineEventRead(**t) for t in timeline],
        explanation=explanation,
    )
    return detail.model_dump(mode="json")


@router.patch(
    "/investigations/{investigation_id}",
    response_model=InvestigationRead,
    summary="Update Investigation",
    description=(
        "Update investigation status, priority, review summary, or recommended next step. "
        "Status transitions are validated. CLOSED and DISMISSED require SUPERVISOR role. "
        "recommended_next_step must be analytical — NOT enforcement action."
    ),
)
async def update_investigation_endpoint(
    investigation_id: str,
    body: InvestigationUpdate,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    try:
        inv = update_investigation(
            db=db,
            investigation_id=investigation_id,
            actor_role=current_user["role"],
            status=body.status,
            priority=body.priority,
            review_summary=body.review_summary,
            recommended_next_step=body.recommended_next_step,
        )
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=str(exc))
    return InvestigationRead(**inv)


# ─────────────────────────────────────────────────────────────────────────────
# NOTES
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/investigations/{investigation_id}/notes",
    response_model=NoteRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Add Analyst Note",
    description=(
        "Add a timestamped analyst note to an investigation. "
        "Record only information necessary for the authorized investigation. "
        "Do not include account numbers, PINs, OTPs, CVVs, or unnecessary PII."
    ),
)
async def add_note_endpoint(
    investigation_id: str,
    body: NoteCreate,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    try:
        note = add_note(db, investigation_id, body.note, current_user["role"])
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    return NoteRead(**note)


@router.get(
    "/investigations/{investigation_id}/timeline",
    summary="Investigation Timeline",
    description="Chronological event timeline for an investigation.",
)
async def get_timeline_endpoint(
    investigation_id: str,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    timeline = get_timeline(db, investigation_id)
    log_audit(db, "VIEW_INVESTIGATION", "INVESTIGATION", investigation_id, current_user["role"], "SUCCESS")
    return {"investigation_id": investigation_id, "events": [TimelineEventRead(**t).model_dump(mode="json") for t in timeline]}


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/investigations/{investigation_id}/evidence",
    response_model=EvidenceRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Add Evidence Reference",
    description=(
        "Add a safe evidence reference to an investigation. "
        "Stores metadata/reference only — NOT raw sensitive evidence data. "
        "Do NOT include account numbers, PINs, CVVs, OTPs, full card numbers, or passwords."
    ),
)
async def add_evidence_endpoint(
    investigation_id: str,
    body: EvidenceCreate,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    try:
        ev = add_evidence(
            db, investigation_id,
            body.evidence_type, body.reference,
            body.description, body.integrity_hash,
            current_user["role"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    return EvidenceRead(**ev)


# ─────────────────────────────────────────────────────────────────────────────
# MODEL EXPLANATION (SHAP)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/investigations/{investigation_id}/explanation",
    response_model=ExplanationResponse,
    summary="Model Explanation (SHAP)",
    description=(
        "Retrieve XGBoost model SHAP explanation for the investigation's linked alert. "
        "Features describe model behavior — NOT real-world causality. "
        "Disclaimer: This is a model-derived analytical signal and does not establish criminal activity."
    ),
)
async def get_explanation(
    investigation_id: str,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    alert = _get_alert_by_id(inv.get("alert_id", ""))
    exp = _build_investigation_explanation(inv, alert, n_features=10)

    log_audit(db, "VIEW_EXPLANATION", "INVESTIGATION", investigation_id, current_user["role"], "SUCCESS")

    if exp:
        return exp

    # Fallback to empty/minimal ExplanationResponse if no explanation available
    return ExplanationResponse(
        investigation_id=investigation_id,
        alert_id=inv.get("alert_id", ""),
        risk_score=inv.get("risk_score"),
        risk_category=inv.get("severity"),
        predicted_probability=_parse_optional_float(alert.get("predicted_probability") if alert else None),
        top_features=[],
    )


# ─────────────────────────────────────────────────────────────────────────────
# STRUCTURED INTELLIGENCE BRIEF (Phase 6)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/investigations/{investigation_id}/intelligence-brief",
    response_model=IntelligenceBriefResponse,
    summary="Structured Intelligence Brief Generator",
    description=(
        "Compiles a comprehensive intelligence dossier for investigative review: "
        "case metadata, spatial hotspot & physical ATM proximity, calibrated model risk score, "
        "top SHAP explainability drivers, timeline events, evidence catalog, and audit trail."
    ),
)
@router.get(
    "/investigations/{investigation_id}/brief",
    response_model=IntelligenceBriefResponse,
    include_in_schema=False,
)
async def get_intelligence_brief(
    investigation_id: str,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    inv = get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    alert = _get_alert_by_id(inv.get("alert_id", ""))
    notes = get_notes(db, investigation_id)
    evidence = get_evidence(db, investigation_id)
    timeline = get_timeline(db, investigation_id)

    # SHAP feature extraction
    exp = _build_investigation_explanation(inv, alert, n_features=10)
    shap_list = []
    if exp and exp.top_features:
        for f in exp.top_features:
            shap_list.append({
                "rank": f.rank,
                "feature": f.feature,
                "contribution": f.direction,
                "impact_score": f.mean_abs_shap_value,
                "human_label": f.human_label,
            })

    # Spatial & ATM Intelligence
    hotspot_id = inv.get("hotspot_id") or (alert.get("hotspot_id") if alert else None) or "HS-18"
    district = inv.get("dominant_category") or (alert.get("victim_district") if alert else "Tiruchirappalli")

    from api.bank_routes import _get_atms_df, _haversine_km_matrix
    df_atms = _get_atms_df()

    lat = None
    lon = None
    if alert:
        lat = _parse_optional_float(alert.get("latitude"))
        lon = _parse_optional_float(alert.get("longitude"))
    if lat is None or lon is None:
        lat, lon = 10.7905, 78.7047

    nearby_atms = []
    atm_count_5km = 0
    nearest_atm_id = "N/A"
    nearest_atm_bank = "N/A"
    nearest_atm_dist = None

    if not df_atms.empty and lat is not None and lon is not None:
        atm_lats = df_atms["latitude"].to_numpy(dtype=float)
        atm_lons = df_atms["longitude"].to_numpy(dtype=float)
        dists = _haversine_km_matrix(np.array([lat]), np.array([lon]), atm_lats, atm_lons)[0]
        atm_count_5km = int((dists <= 5.0).sum())
        if len(dists) > 0:
            nearest_idx = int(np.argmin(dists))
            nearest_atm_dist = round(float(dists[nearest_idx]), 2)
            row = df_atms.iloc[nearest_idx]
            nearest_atm_id = str(row.get("atm_id", ""))
            nearest_atm_bank = str(row.get("bank_id", ""))

            for idx in np.argsort(dists)[:3]:
                r_atm = df_atms.iloc[int(idx)]
                nearby_atms.append({
                    "atm_id": str(r_atm.get("atm_id", "")),
                    "bank_id": str(r_atm.get("bank_id", "")),
                    "distance_km": round(float(dists[idx]), 2),
                    "is_24x7": bool(r_atm.get("is_24x7", 0) == 1),
                    "atm_type": str(r_atm.get("atm_type", "STANDALONE_ATM")),
                })

    spatial_intel = {
        "hotspot_id": hotspot_id,
        "assigned_district": district,
        "centroid_latitude": lat,
        "centroid_longitude": lon,
        "atms_within_5km": atm_count_5km,
        "nearest_atm_id": nearest_atm_id,
        "nearest_atm_bank": nearest_atm_bank,
        "nearest_atm_distance_km": nearest_atm_dist,
        "top_nearby_atms": nearby_atms,
    }

    now = datetime.now(timezone.utc)
    brief_ref = f"BRIEF-{now.strftime('%Y%m%d')}-{investigation_id}"
    audit_ref = f"AUD-BRIEF-{now.strftime('%Y%m%d')}-{investigation_id[-6:]}"

    log_audit(
        db,
        "GENERATE_INTELLIGENCE_BRIEF",
        "INVESTIGATION",
        investigation_id,
        current_user["role"],
        "SUCCESS",
        f"Generated intelligence brief {brief_ref}",
    )

    latest_note_text = notes[-1]["note"] if notes else inv.get("analyst_notes")

    return IntelligenceBriefResponse(
        brief_reference=brief_ref,
        generated_at=now,
        generated_by_role=current_user["role"],
        investigation_id=investigation_id,
        status=inv.get("status", "OPEN"),
        priority=inv.get("priority", "HIGH"),
        severity=inv.get("severity", "HIGH"),
        risk_score=inv.get("risk_score"),
        predicted_probability=_parse_optional_float(alert.get("predicted_probability") if alert else None),
        alert_id=inv.get("alert_id", ""),
        case_id=alert.get("case_id") if alert else None,
        complaint_timestamp=alert.get("complaint_timestamp") if alert else None,
        crime_category=(alert.get("crime_type") if alert else None) or inv.get("dominant_category"),

        victim_district=alert.get("victim_district") if alert else district,
        fraud_amount=_parse_optional_float(alert.get("fraud_amount") if alert else None),
        spatial_intelligence=spatial_intel,
        shap_explainability=shap_list,
        evidence_catalog=[EvidenceRead(**e).model_dump(mode="json") for e in evidence],
        timeline_summary=[TimelineEventRead(**t).model_dump(mode="json") for t in timeline],
        analyst_notes_count=len(notes),
        latest_note=latest_note_text,
        audit_trail_reference=audit_ref,
    )


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/audit",
    response_model=PaginatedAuditResponse,
    summary="Analyst Audit Log",
    description=(
        "Paginated audit event log. "
        "Accessible to SUPERVISOR and ADMIN roles. "
        "Never exposes credentials or sensitive data."
    ),
)
async def get_audit_log_endpoint(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(require_role("SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    items, total = get_audit_log(db, action=action, resource_type=resource_type,
                                 result=result, skip=skip, limit=limit)
    return PaginatedAuditResponse(
        items=[AuditLogRead(**a) for a in items],
        total=total,
        skip=skip,
        limit=limit,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HOTSPOT DETAIL (for analyst map integration)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/hotspots",
    summary="Analyst Hotspot Summary",
    description="Phase 14 DBSCAN hotspot summaries for analytical review.",
)
async def analyst_hotspots(
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    hotspots = _load_hotspot_summary()
    safe_fields = {
        "hotspot_rank", "cluster_id", "event_count", "average_risk_score",
        "maximum_risk_score", "latitude_centroid", "longitude_centroid",
        "time_range_start", "time_range_end", "hotspot_status",
        "high_risk_count", "critical_risk_count",
    }
    cleaned = [{k: v for k, v in h.items() if k in safe_fields} for h in hotspots]
    log_audit(db, "VIEW_HOTSPOT", "HOTSPOT", "list", current_user["role"], "SUCCESS")
    return {"hotspots": cleaned, "total": len(cleaned)}


# ─────────────────────────────────────────────────────────────────────────────
# OUTCOME FEEDBACK (Phase 11: Structured Feedback Loop)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/investigations/{inv_id}/outcomes",
    response_model=OutcomeFeedbackRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Record Investigation Outcome Feedback",
    description=(
        "Record post-intervention field outcome feedback for an investigation. "
        "Allows authorized law enforcement and cyber cell analysts to record "
        "whether a predicted withdrawal cashout was confirmed, thwarted by proactive patrol, "
        "or an unproductive patrol / false positive. "
        "Captures prevented financial loss and actual terminal ID without storing personal financial PII."
    ),
)
async def create_investigation_outcome(
    inv_id: str,
    payload: OutcomeFeedbackCreate,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    try:
        entry = record_outcome_feedback(
            db=db,
            investigation_id=inv_id,
            outcome_category=payload.outcome_category,
            notes=payload.notes,
            actual_amount_lost=payload.actual_amount_lost,
            amount_prevented=payload.amount_prevented,
            atm_id_actual=payload.atm_id_actual,
            actual_timestamp=payload.actual_timestamp,
            verified_by_supervisor=bool(payload.verified_by_supervisor or current_user["role"] in ("SUPERVISOR", "ADMIN")),
            actor_role=current_user["role"],
        )
        return OutcomeFeedbackRead(**entry)
    except ValueError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("create_investigation_outcome error: %s", exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record outcome feedback.",
        )


@router.get(
    "/investigations/{inv_id}/outcomes",
    response_model=List[OutcomeFeedbackRead],
    summary="Get Investigation Outcomes",
    description="Retrieve all outcome feedback records associated with an investigation.",
)
async def list_investigation_outcomes(
    inv_id: str,
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    inv = get_investigation(db, inv_id)
    if not inv:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{inv_id}' not found.",
        )
    items = get_investigation_outcomes(db, inv_id)
    return [OutcomeFeedbackRead(**i) for i in items]


@router.get(
    "/outcomes",
    response_model=PaginatedFeedbackResponse,
    summary="List All Outcome Feedbacks",
    description="Paginated list of all outcome feedback records across investigations with optional category filtering.",
)
async def list_all_outcomes(
    outcome_category: Optional[str] = Query(None, description="Filter by outcome category: CONFIRMED_CASHOUT, THWARTED_CASHOUT, FALSE_POSITIVE, UNPRODUCTIVE_PATROL, WRONG_LOCATION, OTHER"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    items, total = get_all_outcomes(
        db=db,
        outcome_category=outcome_category,
        skip=skip,
        limit=limit,
    )
    return PaginatedFeedbackResponse(
        items=[OutcomeFeedbackRead(**i) for i in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/outcomes/statistics",
    response_model=OutcomeFeedbackStatistics,
    summary="Get Outcome Feedback Statistics",
    description="Aggregated statistics, prevented loss totals, and empirical precision rate from post-intervention feedback.",
)
async def outcome_statistics(
    current_user: Dict[str, Any] = Depends(require_role("ANALYST", "SUPERVISOR", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    _ensure_demo_data(db)
    stats = get_outcome_statistics(db)
    return OutcomeFeedbackStatistics(**stats)

