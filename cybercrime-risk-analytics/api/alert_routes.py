"""
Phase 16 — FastAPI Alert API Endpoints
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Endpoints for analytical alert delivery, status lifecycle transitions,
and generation:
  GET   /alerts
  GET   /alerts/{alert_id}
  POST  /alerts/generate
  PATCH /alerts/{alert_id}/acknowledge
  PATCH /alerts/{alert_id}/review
  PATCH /alerts/{alert_id}/resolve
  PATCH /alerts/{alert_id}/dismiss
  GET   /alerts/statistics
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db, check_database_health
from database.crud import (
    get_alert,
    get_alerts,
    update_alert_status,
    acknowledge_alert,
    review_alert,
    resolve_alert,
    dismiss_alert,
    get_alert_statistics,
    is_db_available,
    _sanitize_alert_record,
)
from database.schemas import (
    AlertRead,
    AlertStatusUpdate,
    AlertStatisticsResponse,
    AlertGenerationSummary,
)
from src.alert_engine import run_alert_generation, load_configuration
from notifications import notification_log as notif_log
from api.auth import require_api_key, _SECRET_KEY, _ALGORITHM

logger = logging.getLogger("api.alerts")
_bearer_scheme = HTTPBearer(auto_error=False)


def _forbid_bank_analyst(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme)):
    """Blocks BANK_ANALYST role from mutating or acknowledging analyst alerts."""
    if credentials and credentials.credentials:
        try:
            from jose import jwt
            payload = jwt.decode(credentials.credentials, _SECRET_KEY, algorithms=[_ALGORITHM])
            role = str(payload.get("role", "")).upper()
            if role == "BANK_ANALYST":
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Access denied. BANK_ANALYST role cannot update or acknowledge analyst alerts.",
                )
        except HTTPException:
            raise
        except Exception:
            pass

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
    dependencies=[Depends(require_api_key)],
)


class PaginatedAlertsResponse(BaseModel):
    items: List[AlertRead]
    total: int
    skip: int
    limit: int
    disclaimer: str = "Analytical signals for authorized human review only. Not proof of criminal activity."


class DispatchLogEntry(BaseModel):
    """One outbound dispatch attempt recorded in the notification log."""
    log_id: str
    alert_id: str
    channel: str
    status: str
    recipient_or_target: Optional[str] = None
    simulation: bool = True
    timestamp: str
    extra_info: Optional[str] = None


class DispatchLogResponse(BaseModel):
    alert_id: str
    total_entries: int
    entries: List[DispatchLogEntry]
    channels_seen: List[str]
    simulation_notice: str = (
        "SMS and Webhook entries are fully simulated. "
        "No real carrier or external endpoint was contacted."
    )
    disclaimer: str = (
        "Dispatch log is a prototype simulation record for PS ID 26184. "
        "Analytical signals for authorized human review only."
    )


class AlertConfigResponse(BaseModel):
    risk_thresholds: Dict[str, Any]
    hotspot_thresholds: Dict[str, Any]
    surge_detection: Dict[str, Any]
    cooldown_minutes: Dict[str, Any]
    deduplication: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    notifications: Dict[str, Any]
    enabled_alert_types: List[str]
    human_review_required_severities: List[str]
    simulation_mode: bool = True
    disclaimer: str = (
        "Alert rule thresholds govern analytical triage prioritization for authorized decision-support. "
        "Alert generation does not establish legal guilt or replace human oversight."
    )


class DispatchSummaryResponse(BaseModel):
    total_dispatches: int
    by_channel: Dict[str, int]
    by_status: Dict[str, int]
    simulation_mode: bool = True
    simulation_notice: str = (
        "Outbound dispatches (SMS, Email, Webhook) operate under prototype simulation. "
        "No live external telecom or webhook endpoint was contacted."
    )
    disclaimer: str = (
        "Analytical dispatch records are maintained for prototype testing and audit trail verification."
    )


def _get_optional_db():
    """Yields DB session if database is connected, else None."""
    if not is_db_available():
        yield None
        return
    try:
        from database.connection import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception:
        yield None


# ---------------------------------------------------------------------------
# GET /alerts — Filtered and paginated alerts
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=PaginatedAlertsResponse,
    summary="List Analytical Alerts",
    description="Query analytical alerts with filtering by severity, status, type, hotspot, and date range.",
)
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MODERATE, HIGH, CRITICAL"),
    alert_status: Optional[str] = Query(None, alias="status", description="Filter by status: NEW, ACKNOWLEDGED, IN_REVIEW, RESOLVED, DISMISSED"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    hotspot_id: Optional[str] = Query(None, description="Filter by hotspot ID (e.g. HS-01)"),
    start_time: Optional[datetime] = Query(None, description="Earliest generation time"),
    end_time: Optional[datetime] = Query(None, description="Latest generation time"),
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(50, ge=1, le=200, description="Page limit (max 200)"),
    db: Optional[Session] = Depends(_get_optional_db),
):
    try:
        items, total = get_alerts(
            db=db,
            severity=severity,
            status=alert_status,
            alert_type=alert_type,
            hotspot_id=hotspot_id,
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit,
        )
        cleaned_items = [AlertRead(**_sanitize_alert_record(a)) for a in items]

        return PaginatedAlertsResponse(
            items=cleaned_items,
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as exc:
        logger.error("Error listing alerts: %s", exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts.",
        )


# ---------------------------------------------------------------------------
# GET /alerts/statistics — Aggregates by severity, status, and type
# ---------------------------------------------------------------------------
@router.get(
    "/statistics",
    response_model=AlertStatisticsResponse,
    summary="Alert Aggregated Statistics",
    description="Returns aggregate counts of alerts across status and severity tiers.",
)
async def alert_statistics(
    db: Optional[Session] = Depends(_get_optional_db),
):
    try:
        stats = get_alert_statistics(db=db)
        return AlertStatisticsResponse(**stats)
    except Exception as exc:
        logger.error("Error calculating alert statistics: %s", exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate alert statistics.",
        )


# ---------------------------------------------------------------------------
# GET /alerts/config — Active alert rule configuration & threshold values
# ---------------------------------------------------------------------------
@router.get(
    "/config",
    response_model=AlertConfigResponse,
    summary="Get Alert Rule Configuration",
    description="Returns active risk thresholds, cooldown intervals, deduplication policies, and simulation flags.",
)
async def get_alert_configuration():
    try:
        cfg = load_configuration()
        return AlertConfigResponse(
            risk_thresholds=cfg.get("risk_thresholds", {}),
            hotspot_thresholds=cfg.get("hotspot_thresholds", {}),
            surge_detection=cfg.get("surge_detection", {}),
            cooldown_minutes=cfg.get("cooldown_minutes", {}),
            deduplication=cfg.get("deduplication", {}),
            rate_limiting=cfg.get("rate_limiting", {}),
            notifications=cfg.get("notifications", {}),
            enabled_alert_types=cfg.get("enabled_alert_types", []),
            human_review_required_severities=cfg.get("human_review_required_severities", []),
            simulation_mode=True,
        )
    except Exception as exc:
        logger.error("Error retrieving alert configuration: %s", exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alert configuration.",
        )


# ---------------------------------------------------------------------------
# GET /alerts/dispatch-summary — Aggregate dispatch telemetry across channels
# ---------------------------------------------------------------------------
@router.get(
    "/dispatch-summary",
    response_model=DispatchSummaryResponse,
    summary="Get Outbound Dispatch Summary",
    description="Returns aggregate counts of simulated and logged dispatches across all notification channels.",
)
async def get_dispatch_summary():
    try:
        entries = notif_log.get_full_dispatch_log(limit=10000)
        by_channel: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for entry in entries:
            ch = entry.get("channel", "UNKNOWN")
            st = entry.get("status", "UNKNOWN")
            by_channel[ch] = by_channel.get(ch, 0) + 1
            by_status[st] = by_status.get(st, 0) + 1

        return DispatchSummaryResponse(
            total_dispatches=len(entries),
            by_channel=by_channel,
            by_status=by_status,
            simulation_mode=True,
        )
    except Exception as exc:
        logger.error("Error summarizing dispatch log: %s", exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dispatch summary.",
        )


# ---------------------------------------------------------------------------
# POST /alerts/generate — Trigger alert generation pipeline
# ---------------------------------------------------------------------------
@router.post(
    "/generate",
    response_model=AlertGenerationSummary,
    summary="Generate Analytical Alerts",
    description="Loads current predictive risk signals and hotspot data, evaluates rules, deduplicates, and creates alerts.",
)
async def generate_alerts(
    dry_run: bool = Query(True, description="When True, notifications are logged/dry-run only"),
    db: Optional[Session] = Depends(_get_optional_db),
):
    try:
        cfg = load_configuration()
        alerts, summary = run_alert_generation(config=cfg, db_session=db, dry_run=dry_run)
        return AlertGenerationSummary(
            generated=summary.get("total_generated", len(alerts)),
            critical=summary.get("critical_count", 0),
            high=summary.get("high_count", 0),
            moderate=summary.get("moderate_count", 0),
            duplicates_skipped=summary.get("duplicates_skipped", 0),
            cooldown_skipped=summary.get("cooldown_skipped", 0),
        )
    except Exception as exc:
        logger.error("Alert generation failed: %s", exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Alert generation encountered an internal error.",
        )


# ---------------------------------------------------------------------------
# GET /alerts/{alert_id} — Single alert detail
# ---------------------------------------------------------------------------
@router.get(
    "/{alert_id}",
    response_model=AlertRead,
    summary="Get Alert Detail",
    description="Fetch a single alert record by alert_id.",
)
async def get_single_alert(
    alert_id: str,
    db: Optional[Session] = Depends(_get_optional_db),
):
    alert = get_alert(db=db, alert_id=alert_id)
    if not alert:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return AlertRead(**_sanitize_alert_record(alert))


# ---------------------------------------------------------------------------
# GET /alerts/{alert_id}/dispatch-log — Per-channel dispatch status
# ---------------------------------------------------------------------------
@router.get(
    "/{alert_id}/dispatch-log",
    response_model=DispatchLogResponse,
    summary="Get Alert Dispatch Log",
    description="Retrieve per-channel delivery history for an alert (SMS, Webhook, Log).",
)
async def get_alert_dispatch_log(alert_id: str):
    alert = get_alert(None, alert_id)
    if not alert:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found.")

    entries = notif_log.get_entries_for_alert(alert_id)
    dispatch_entries = [
        DispatchLogEntry(
            log_id=e.get("log_id", ""),
            alert_id=e.get("alert_id", alert_id),
            channel=e.get("channel", "UNKNOWN"),
            status=e.get("status", "UNKNOWN"),
            recipient_or_target=e.get("recipient_or_target"),
            simulation=bool(e.get("simulation", True)),
            timestamp=str(e.get("timestamp", "")),
            extra_info=e.get("extra_info"),
        )
        for e in entries
    ]
    channels_seen = list({e.channel for e in dispatch_entries})

    return DispatchLogResponse(
        alert_id=alert_id,
        total_entries=len(dispatch_entries),
        entries=dispatch_entries,
        channels_seen=channels_seen,
    )


# ---------------------------------------------------------------------------
# PATCH /alerts/{alert_id}/acknowledge — Transition NEW -> ACKNOWLEDGED
# ---------------------------------------------------------------------------
@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertRead,
    summary="Acknowledge Alert",
    description="Transitions alert status from NEW to ACKNOWLEDGED.",
    dependencies=[Depends(_forbid_bank_analyst)],
)
async def acknowledge_single_alert(
    alert_id: str,
    body: AlertStatusUpdate = AlertStatusUpdate(),
    db: Optional[Session] = Depends(_get_optional_db),
):
    try:
        updated = acknowledge_alert(
            db=db,
            alert_id=alert_id,
            actor_type=body.actor_type,
            notes=body.notes or "Alert acknowledged by analyst.",
        )
        return AlertRead(**_sanitize_alert_record(updated))
    except KeyError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Error acknowledging alert %s: %s", alert_id, exc)
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update alert status.")


# ---------------------------------------------------------------------------
# PATCH /alerts/{alert_id}/review — Transition ACKNOWLEDGED -> IN_REVIEW
# ---------------------------------------------------------------------------
@router.patch(
    "/{alert_id}/review",
    response_model=AlertRead,
    summary="Mark Alert In Review",
    description="Transitions alert status to IN_REVIEW.",
    dependencies=[Depends(_forbid_bank_analyst)],
)
async def review_single_alert(
    alert_id: str,
    body: AlertStatusUpdate = AlertStatusUpdate(),
    db: Optional[Session] = Depends(_get_optional_db),
):
    try:
        updated = review_alert(
            db=db,
            alert_id=alert_id,
            actor_type=body.actor_type,
            notes=body.notes or "Alert assigned to analytical review.",
        )
        return AlertRead(**_sanitize_alert_record(updated))
    except KeyError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Error setting alert %s in review: %s", alert_id, exc)
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update alert status.")


# ---------------------------------------------------------------------------
# PATCH /alerts/{alert_id}/resolve — Transition IN_REVIEW -> RESOLVED
# ---------------------------------------------------------------------------
@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertRead,
    summary="Resolve Alert",
    description="Resolves alert after authorized human analytical review.",
    dependencies=[Depends(_forbid_bank_analyst)],
)
async def resolve_single_alert(
    alert_id: str,
    body: AlertStatusUpdate = AlertStatusUpdate(),
    db: Optional[Session] = Depends(_get_optional_db),
):
    try:
        updated = resolve_alert(
            db=db,
            alert_id=alert_id,
            actor_type=body.actor_type,
            notes=body.notes or "Alert analytical review resolved.",
        )
        return AlertRead(**_sanitize_alert_record(updated))
    except KeyError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Error resolving alert %s: %s", alert_id, exc)
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update alert status.")


# ---------------------------------------------------------------------------
# PATCH /alerts/{alert_id}/dismiss — Transition -> DISMISSED
# ---------------------------------------------------------------------------
@router.patch(
    "/{alert_id}/dismiss",
    response_model=AlertRead,
    summary="Dismiss Alert",
    description="Dismisses alert with analyst rationale note.",
    dependencies=[Depends(_forbid_bank_analyst)],
)
async def dismiss_single_alert(
    alert_id: str,
    body: AlertStatusUpdate = AlertStatusUpdate(),
    db: Optional[Session] = Depends(_get_optional_db),
):
    try:
        updated = dismiss_alert(
            db=db,
            alert_id=alert_id,
            actor_type=body.actor_type,
            notes=body.notes or "Alert dismissed by analyst.",
        )
        return AlertRead(**_sanitize_alert_record(updated))
    except KeyError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Error dismissing alert %s: %s", alert_id, exc)
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update alert status.")
