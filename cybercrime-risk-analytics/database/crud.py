"""
Database CRUD Operations for Cybercrime Events and Prediction Storage
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, text, and_
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint

from datetime import datetime, timezone
import json
import math
from pathlib import Path
from database.models import CybercrimeEvent, PredictionResult, CybercrimeAlert, AlertAuditLog
from database.schemas import (
    CybercrimeEventCreate,
    PredictionResultCreate,
    AlertCreate,
    AlertRead,
    AlertStatusUpdate,
    AlertStatisticsResponse,
)

logger = logging.getLogger("cybercrime_api.database.crud")


def is_valid_coordinate(lat: Optional[float], lon: Optional[float]) -> bool:
    """Check if latitude and longitude are valid non-null WGS 84 coordinates."""
    if lat is None or lon is None:
        return False
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return (-90.0 <= lat_f <= 90.0) and (-180.0 <= lon_f <= 180.0)
    except (ValueError, TypeError):
        return False


def create_cybercrime_event(db: Session, event: CybercrimeEventCreate) -> CybercrimeEvent:
    """
    Insert a single CybercrimeEvent into the database.
    Converts valid (longitude, latitude) into PostGIS POINT (SRID 4326).
    If coordinates are invalid or missing, location is stored as NULL.
    """
    location_geom = None
    if is_valid_coordinate(event.latitude, event.longitude):
        # PostGIS expects ST_MakePoint(longitude, latitude)
        location_geom = ST_SetSRID(ST_MakePoint(float(event.longitude), float(event.latitude)), 4326)

    db_event = CybercrimeEvent(
        case_id=event.case_id,
        complaint_timestamp=event.complaint_timestamp,
        crime_type=event.crime_type,
        fraud_amount=event.fraud_amount,
        reported_by_authority=event.reported_by_authority,
        victim_state=event.victim_state,
        victim_district=event.victim_district,
        victim_area=event.victim_area,
        victim_area_id=event.victim_area_id,
        latitude=event.latitude if is_valid_coordinate(event.latitude, event.longitude) else None,
        longitude=event.longitude if is_valid_coordinate(event.latitude, event.longitude) else None,
        location=location_geom,
        is_linked_to_withdrawal=event.is_linked_to_withdrawal,
        future_withdrawal=event.future_withdrawal,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def batch_create_cybercrime_events(db: Session, records: List[Dict[str, Any]], batch_size: int = 500) -> Tuple[int, int]:
    """
    Batch insert cybercrime event records with transaction protection.
    Returns (inserted_count, rejected_count).
    """
    inserted = 0
    rejected = 0

    for i in range(0, len(records), batch_size):
        chunk = records[i:i + batch_size]
        chunk_objects = []
        for r in chunk:
            try:
                lat = r.get("latitude")
                lon = r.get("longitude")
                location_geom = None
                valid_geo = is_valid_coordinate(lat, lon)

                if valid_geo:
                    location_geom = ST_SetSRID(ST_MakePoint(float(lon), float(lat)), 4326)

                obj = CybercrimeEvent(
                    case_id=str(r["case_id"]),
                    complaint_timestamp=r["complaint_timestamp"],
                    crime_type=str(r["crime_type"]),
                    fraud_amount=float(r["fraud_amount"]),
                    reported_by_authority=int(r.get("reported_by_authority", 0)),
                    victim_state=r.get("victim_state"),
                    victim_district=r.get("victim_district"),
                    victim_area=r.get("victim_area"),
                    victim_area_id=r.get("victim_area_id"),
                    latitude=float(lat) if valid_geo else None,
                    longitude=float(lon) if valid_geo else None,
                    location=location_geom,
                    is_linked_to_withdrawal=int(r.get("is_linked_to_withdrawal", 0)),
                    future_withdrawal=r.get("future_withdrawal"),
                )
                chunk_objects.append(obj)
            except Exception as e:
                logger.warning(f"Error preparing record {r.get('case_id')}: {e}")
                rejected += 1

        if chunk_objects:
            try:
                db.bulk_save_objects(chunk_objects)
                db.commit()
                inserted += len(chunk_objects)
            except Exception as e:
                db.rollback()
                logger.error(f"Batch commit failed for chunk {i}: {e}")
                # Fallback: attempt one-by-one to isolate failures
                for obj in chunk_objects:
                    try:
                        db.add(obj)
                        db.commit()
                        inserted += 1
                    except Exception:
                        db.rollback()
                        rejected += 1

    return inserted, rejected


def create_prediction_result(db: Session, pred: PredictionResultCreate) -> PredictionResult:
    """
    Store an operational prediction result from the inference engine.
    Never stores sensitive data, passwords, PINs, or raw complaints.
    """
    location_geom = None
    if is_valid_coordinate(pred.latitude, pred.longitude):
        location_geom = ST_SetSRID(ST_MakePoint(float(pred.longitude), float(pred.latitude)), 4326)

    db_pred = PredictionResult(
        prediction_reference=pred.prediction_reference,
        prediction_timestamp=pred.prediction_timestamp,
        predicted_probability=float(pred.predicted_probability),
        risk_score=int(pred.risk_score),
        risk_category=pred.risk_category,
        operational_interpretation=pred.operational_interpretation,
        model_version=pred.model_version,
        latitude=float(pred.latitude) if is_valid_coordinate(pred.latitude, pred.longitude) else None,
        longitude=float(pred.longitude) if is_valid_coordinate(pred.latitude, pred.longitude) else None,
        location=location_geom,
        victim_district=pred.victim_district,
        crime_type=pred.crime_type,
    )
    db.add(db_pred)
    db.commit()
    db.refresh(db_pred)
    return db_pred


def get_database_stats(db: Session) -> Dict[str, Any]:
    """
    Compute aggregate database statistics without exposing raw rows.
    """
    try:
        total_events = db.query(func.count(CybercrimeEvent.id)).scalar() or 0
        events_with_loc = db.query(func.count(CybercrimeEvent.id)).filter(
            CybercrimeEvent.location.isnot(None)
        ).scalar() or 0
        
        coverage = (events_with_loc / total_events * 100.0) if total_events > 0 else 0.0
        total_preds = db.query(func.count(PredictionResult.id)).scalar() or 0

        latest_time = db.query(func.max(CybercrimeEvent.complaint_timestamp)).scalar()
        earliest_time = db.query(func.min(CybercrimeEvent.complaint_timestamp)).scalar()

        districts_cnt = db.query(func.count(func.distinct(CybercrimeEvent.victim_district))).scalar() or 0
        crime_types_cnt = db.query(func.count(func.distinct(CybercrimeEvent.crime_type))).scalar() or 0

        return {
            "total_events": total_events,
            "events_with_location": events_with_loc,
            "location_coverage_percent": round(coverage, 2),
            "total_predictions": total_preds,
            "latest_event_timestamp": latest_time.isoformat() if latest_time else None,
            "earliest_event_timestamp": earliest_time.isoformat() if earliest_time else None,
            "districts_count": districts_cnt,
            "crime_types_count": crime_types_cnt,
        }
    except Exception as e:
        logger.error(f"Failed to fetch database stats: {e}")
        raise


# ==============================================================================
# Phase 16 — Alert CRUD Operations & In-Memory / Local Cache Fallback
# ==============================================================================

_LOCAL_ALERTS_CACHE: Dict[str, Dict[str, Any]] = {}
_LOCAL_AUDIT_LOG: List[Dict[str, Any]] = []
_DB_HEALTHY_CACHE: Optional[bool] = None

# Path to the alerts CSV — single definition used by both reader and writer
_ALERTS_CSV_PATH = Path(__file__).resolve().parent.parent / "outputs" / "phase16_demo_alerts.csv"


def _sanitize_alert_record(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize alert dictionary so that NaN, Infinity, -Infinity,
    and invalid strings are converted to None (JSON null).
    """
    if not isinstance(alert, dict):
        return {}
    clean: Dict[str, Any] = {}
    for k, v in alert.items():
        if v is None:
            clean[k] = None
            continue
        if isinstance(v, float):
            clean[k] = None if (math.isnan(v) or math.isinf(v)) else v
            continue
        if isinstance(v, int):
            clean[k] = v
            continue
        s_val = str(v).strip()
        s_lower = s_val.lower()
        if s_lower in ("nan", "none", "null", ""):
            clean[k] = None
        elif s_lower in ("inf", "-inf", "infinity", "-infinity"):
            clean[k] = None
        elif k in ("latitude", "longitude", "predicted_probability"):
            try:
                flt = float(s_val)
                clean[k] = None if (math.isnan(flt) or math.isinf(flt)) else flt
            except (ValueError, TypeError):
                clean[k] = None
        elif k in ("risk_score", "event_count"):
            try:
                flt = float(s_val)
                clean[k] = None if (math.isnan(flt) or math.isinf(flt)) else int(round(flt))
            except (ValueError, TypeError):
                clean[k] = None
        else:
            clean[k] = v

    if not clean.get("operational_message"):
        clean["operational_message"] = "Analytical alert — authorized human review required."
    if not clean.get("created_at"):
        clean["created_at"] = datetime.now(timezone.utc)

    return clean


def _init_local_alerts_cache():
    """Load alerts from the CSV on startup with full sanitization."""
    if _ALERTS_CSV_PATH.exists():
        try:
            import pandas as pd
            df = pd.read_csv(_ALERTS_CSV_PATH)
            for _, r in df.iterrows():
                d = r.to_dict()
                aid = str(d.get("alert_id"))
                if aid and aid.lower() not in ("nan", "none", "null", ""):
                    _LOCAL_ALERTS_CACHE[aid] = _sanitize_alert_record(d)
        except Exception:
            pass


def _persist_alerts_cache_to_csv() -> None:
    """Write the full current _LOCAL_ALERTS_CACHE back to the alerts CSV.

    Uses an atomic write (temp file → rename) with direct fallback,
    ensuring that the CSV always reflects current state and survives crashes.
    Safe to call on every status update.
    """
    if not _LOCAL_ALERTS_CACHE:
        return
    try:
        import pandas as pd
        rows = list(_LOCAL_ALERTS_CACHE.values())
        df = pd.DataFrame(rows)
        # Write to a sibling temp file first, then rename atomically
        tmp_path = _ALERTS_CSV_PATH.with_suffix(".csv.tmp")
        df.to_csv(tmp_path, index=False)
        try:
            tmp_path.replace(_ALERTS_CSV_PATH)  # atomic on POSIX; best-effort on Windows
        except Exception:
            df.to_csv(_ALERTS_CSV_PATH, index=False)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        logger.debug("Alerts cache persisted to %s (%d rows)", _ALERTS_CSV_PATH, len(rows))
    except Exception as exc:
        logger.warning("Failed to persist alerts cache to CSV: %s", exc)


def reload_alerts_cache() -> int:
    """Reload _LOCAL_ALERTS_CACHE from outputs/phase16_demo_alerts.csv."""
    _init_local_alerts_cache()
    return len(_LOCAL_ALERTS_CACHE)


_init_local_alerts_cache()

def is_db_available() -> bool:
    global _DB_HEALTHY_CACHE
    if _DB_HEALTHY_CACHE is False:
        return False
    try:
        from database.connection import check_database_health
        health = check_database_health()
        _DB_HEALTHY_CACHE = (health.get("status") == "connected")
        return _DB_HEALTHY_CACHE
    except Exception:
        _DB_HEALTHY_CACHE = False
        return False

VALID_STATUS_TRANSITIONS = {
    "NEW": ["ACKNOWLEDGED", "DISMISSED"],
    "ACKNOWLEDGED": ["IN_REVIEW", "DISMISSED"],
    "IN_REVIEW": ["RESOLVED", "DISMISSED"],
    "RESOLVED": [],
    "DISMISSED": [],
}


def create_audit_entry(
    db: Optional[Session],
    alert_id: str,
    action: str,
    previous_status: Optional[str],
    new_status: str,
    actor_type: str = "SYSTEM",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Record an audit trail event for alert lifecycle state changes."""
    now = datetime.now(timezone.utc)
    entry_dict = {
        "alert_id": alert_id,
        "action": action,
        "previous_status": previous_status,
        "new_status": new_status,
        "timestamp": now,
        "actor_type": actor_type,
        "notes": notes,
    }
    _LOCAL_AUDIT_LOG.append(entry_dict)

    global _DB_HEALTHY_CACHE
    if db is not None and is_db_available():
        try:
            audit_obj = AlertAuditLog(
                alert_id=alert_id,
                action=action,
                previous_status=previous_status,
                new_status=new_status,
                timestamp=now,
                actor_type=actor_type,
                notes=notes,
            )
            db.add(audit_obj)
            db.commit()
        except Exception as exc:
            db.rollback()
            _DB_HEALTHY_CACHE = False
            logger.debug("Database audit write fallback to local cache: %s", exc)

    return entry_dict


def create_alert(db: Optional[Session], alert_data: AlertCreate) -> Dict[str, Any]:
    """
    Create and persist an analytical cybercrime alert.
    Writes to PostgreSQL if session is active; also syncs to memory store.
    """
    global _DB_HEALTHY_CACHE
    now = alert_data.created_at or datetime.now(timezone.utc)
    location_geom = None
    if is_valid_coordinate(alert_data.latitude, alert_data.longitude):
        location_geom = ST_SetSRID(ST_MakePoint(float(alert_data.longitude), float(alert_data.latitude)), 4326)

    alert_dict = alert_data.model_dump()
    alert_dict["created_at"] = now
    alert_dict["updated_at"] = now
    alert_dict["status"] = alert_dict.get("status") or "NEW"
    alert_dict["human_review_required"] = 1 if alert_dict.get("human_review_required", True) else 0

    _LOCAL_ALERTS_CACHE[alert_data.alert_id] = dict(alert_dict)

    if db is not None and is_db_available():
        try:
            db_alert = CybercrimeAlert(
                alert_id=alert_dict["alert_id"],
                alert_type=alert_dict["alert_type"],
                severity=alert_dict["severity"],
                status=alert_dict["status"],
                created_at=alert_dict["created_at"],
                updated_at=alert_dict["updated_at"],
                prediction_reference=alert_dict.get("prediction_reference"),
                hotspot_id=alert_dict.get("hotspot_id"),
                risk_score=alert_dict["risk_score"],
                predicted_probability=alert_dict.get("predicted_probability"),
                event_count=alert_dict.get("event_count"),
                dominant_category=alert_dict.get("dominant_category"),
                time_window_start=alert_dict.get("time_window_start"),
                time_window_end=alert_dict.get("time_window_end"),
                operational_message=alert_dict["operational_message"],
                human_review_required=alert_dict["human_review_required"],
                model_version=alert_dict.get("model_version"),
                latitude=alert_dict.get("latitude") if is_valid_coordinate(alert_dict.get("latitude"), alert_dict.get("longitude")) else None,
                longitude=alert_dict.get("longitude") if is_valid_coordinate(alert_dict.get("latitude"), alert_dict.get("longitude")) else None,
                location=location_geom,
            )
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)
            alert_dict["id"] = db_alert.id
        except Exception as exc:
            db.rollback()
            _DB_HEALTHY_CACHE = False
            logger.debug("Database alert write fallback to local cache: %s", exc)

    create_audit_entry(
        db=db,
        alert_id=alert_data.alert_id,
        action="GENERATE",
        previous_status=None,
        new_status="NEW",
        actor_type="SYSTEM",
        notes=f"Alert generated with severity {alert_data.severity}",
    )

    alert_dict["disclaimer"] = "Analytical alert — authorized human review required. Does not establish criminal activity."
    return alert_dict


def get_alert(db: Optional[Session], alert_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an alert by alert_id from PostgreSQL or local memory cache."""
    if db is not None:
        try:
            db_alert = db.query(CybercrimeAlert).filter(CybercrimeAlert.alert_id == alert_id).first()
            if db_alert:
                return {
                    "id": db_alert.id,
                    "alert_id": db_alert.alert_id,
                    "alert_type": db_alert.alert_type,
                    "severity": db_alert.severity,
                    "status": db_alert.status,
                    "created_at": db_alert.created_at,
                    "updated_at": db_alert.updated_at,
                    "prediction_reference": db_alert.prediction_reference,
                    "hotspot_id": db_alert.hotspot_id,
                    "risk_score": db_alert.risk_score,
                    "predicted_probability": db_alert.predicted_probability,
                    "event_count": db_alert.event_count,
                    "dominant_category": db_alert.dominant_category,
                    "time_window_start": db_alert.time_window_start,
                    "time_window_end": db_alert.time_window_end,
                    "operational_message": db_alert.operational_message,
                    "human_review_required": bool(db_alert.human_review_required),
                    "model_version": db_alert.model_version,
                    "latitude": db_alert.latitude,
                    "longitude": db_alert.longitude,
                    "disclaimer": "Analytical alert — authorized human review required. Does not establish criminal activity.",
                }
        except Exception as exc:
            logger.debug("Database query error, using local fallback: %s", exc)

    if alert_id in _LOCAL_ALERTS_CACHE:
        item = dict(_LOCAL_ALERTS_CACHE[alert_id])
        item["human_review_required"] = bool(item.get("human_review_required", True))
        item["disclaimer"] = "Analytical alert — authorized human review required. Does not establish criminal activity."
        return _sanitize_alert_record(item)
    return None


def get_alerts(
    db: Optional[Session],
    severity: Optional[str] = None,
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    hotspot_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[Dict[str, Any]], int]:
    """Query alerts with filtering and pagination."""
    limit = max(1, min(limit, 200))
    skip = max(0, skip)

    if db is not None:
        try:
            query = db.query(CybercrimeAlert)
            if severity:
                query = query.filter(CybercrimeAlert.severity == severity.upper())
            if status:
                query = query.filter(CybercrimeAlert.status == status.upper())
            if alert_type:
                query = query.filter(CybercrimeAlert.alert_type == alert_type)
            if hotspot_id:
                query = query.filter(CybercrimeAlert.hotspot_id == hotspot_id)
            if start_time:
                query = query.filter(CybercrimeAlert.created_at >= start_time)
            if end_time:
                query = query.filter(CybercrimeAlert.created_at <= end_time)

            total_count = query.count()
            results = query.order_by(CybercrimeAlert.created_at.desc()).offset(skip).limit(limit).all()
            
            alerts_list = []
            for a in results:
                alerts_list.append({
                    "id": a.id,
                    "alert_id": a.alert_id,
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "status": a.status,
                    "created_at": a.created_at,
                    "updated_at": a.updated_at,
                    "prediction_reference": a.prediction_reference,
                    "hotspot_id": a.hotspot_id,
                    "risk_score": a.risk_score,
                    "predicted_probability": a.predicted_probability,
                    "event_count": a.event_count,
                    "dominant_category": a.dominant_category,
                    "time_window_start": a.time_window_start,
                    "time_window_end": a.time_window_end,
                    "operational_message": a.operational_message,
                    "human_review_required": bool(a.human_review_required),
                    "model_version": a.model_version,
                    "latitude": a.latitude,
                    "longitude": a.longitude,
                    "disclaimer": "Analytical alert — authorized human review required. Does not establish criminal activity.",
                })
            return [_sanitize_alert_record(a) for a in alerts_list], total_count
        except Exception as exc:
            logger.debug("Database query error, using local fallback: %s", exc)

    # Local fallback query
    filtered = list(_LOCAL_ALERTS_CACHE.values())
    if severity:
        filtered = [a for a in filtered if str(a.get("severity", "")).upper() == severity.upper()]
    if status:
        filtered = [a for a in filtered if str(a.get("status", "")).upper() == status.upper()]
    if alert_type:
        filtered = [a for a in filtered if str(a.get("alert_type", "")) == alert_type]
    if hotspot_id:
        filtered = [a for a in filtered if str(a.get("hotspot_id", "")) == hotspot_id]
    if start_time:
        filtered = [a for a in filtered if a.get("created_at") and a["created_at"] >= start_time]
    if end_time:
        filtered = [a for a in filtered if a.get("created_at") and a["created_at"] <= end_time]

    # Sort descending by created_at
    filtered.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    total_count = len(filtered)
    paged = filtered[skip:skip + limit]
    for p in paged:
        p["human_review_required"] = bool(p.get("human_review_required", True))
        p["disclaimer"] = "Analytical alert — authorized human review required. Does not establish criminal activity."
    return [_sanitize_alert_record(p) for p in paged], total_count


def update_alert_status(
    db: Optional[Session],
    alert_id: str,
    new_status: str,
    actor_type: str = "AUTHORIZED_USER",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate and execute alert status transitions.
    Transitions:
      NEW -> ACKNOWLEDGED
      ACKNOWLEDGED -> IN_REVIEW
      IN_REVIEW -> RESOLVED
      NEW/ACKNOWLEDGED/IN_REVIEW -> DISMISSED
    """
    new_status = new_status.upper()
    current_alert = get_alert(db, alert_id)
    if not current_alert:
        raise KeyError(f"Alert with ID '{alert_id}' not found.")

    current_status = current_alert.get("status", "NEW").upper()

    if new_status == current_status:
        return current_alert

    allowed = VALID_STATUS_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid status transition from '{current_status}' to '{new_status}'. Allowed transitions: {allowed}"
        )

    # Forbid auto-resolving critical alerts
    if current_alert.get("severity") == "CRITICAL" and new_status == "RESOLVED" and actor_type == "SYSTEM":
        raise ValueError("Critical alerts cannot be resolved by SYSTEM. Authorized human review is strictly required.")

    now = datetime.now(timezone.utc)

    # Update database
    db_updated = False
    if db is not None and is_db_available():
        try:
            db_alert = db.query(CybercrimeAlert).filter(CybercrimeAlert.alert_id == alert_id).first()
            if db_alert:
                db_alert.status = new_status
                db_alert.updated_at = now
                db.commit()
                db.refresh(db_alert)
                db_updated = True
        except Exception as exc:
            db.rollback()
            logger.debug("Database update fallback to local: %s", exc)
            db_updated = False

    # Update local cache
    if alert_id in _LOCAL_ALERTS_CACHE:
        _LOCAL_ALERTS_CACHE[alert_id]["status"] = new_status
        _LOCAL_ALERTS_CACHE[alert_id]["updated_at"] = now.isoformat()
    elif current_alert:
        _LOCAL_ALERTS_CACHE[alert_id] = dict(current_alert)
        _LOCAL_ALERTS_CACHE[alert_id]["status"] = new_status
        _LOCAL_ALERTS_CACHE[alert_id]["updated_at"] = now.isoformat()

    # Persist the updated status to the CSV so it survives server restarts.
    # Prefer writing status updates to the real database table when working,
    # and use the CSV path as fallback when the DB is disconnected.
    if not db_updated:
        _persist_alerts_cache_to_csv()

    # Audit log
    action_map = {
        "ACKNOWLEDGED": "ACKNOWLEDGE",
        "IN_REVIEW": "REVIEW",
        "RESOLVED": "RESOLVE",
        "DISMISSED": "DISMISS",
    }
    create_audit_entry(
        db=db,
        alert_id=alert_id,
        action=action_map.get(new_status, "STATUS_CHANGE"),
        previous_status=current_status,
        new_status=new_status,
        actor_type=actor_type,
        notes=notes,
    )

    updated = get_alert(db, alert_id)
    return updated or current_alert


def acknowledge_alert(db: Optional[Session], alert_id: str, actor_type: str = "AUTHORIZED_USER", notes: Optional[str] = None) -> Dict[str, Any]:
    return update_alert_status(db, alert_id, "ACKNOWLEDGED", actor_type, notes)


def review_alert(db: Optional[Session], alert_id: str, actor_type: str = "AUTHORIZED_USER", notes: Optional[str] = None) -> Dict[str, Any]:
    return update_alert_status(db, alert_id, "IN_REVIEW", actor_type, notes)


def resolve_alert(db: Optional[Session], alert_id: str, actor_type: str = "AUTHORIZED_USER", notes: Optional[str] = None) -> Dict[str, Any]:
    return update_alert_status(db, alert_id, "RESOLVED", actor_type, notes)


def dismiss_alert(db: Optional[Session], alert_id: str, actor_type: str = "AUTHORIZED_USER", notes: Optional[str] = None) -> Dict[str, Any]:
    return update_alert_status(db, alert_id, "DISMISSED", actor_type, notes)


def get_alert_statistics(db: Optional[Session]) -> Dict[str, Any]:
    """Aggregate alert counts by severity, status, and alert type."""
    if db is not None:
        try:
            total = db.query(func.count(CybercrimeAlert.id)).scalar() or 0
            new_cnt = db.query(func.count(CybercrimeAlert.id)).filter(CybercrimeAlert.status == "NEW").scalar() or 0
            ack_cnt = db.query(func.count(CybercrimeAlert.id)).filter(CybercrimeAlert.status == "ACKNOWLEDGED").scalar() or 0
            rev_cnt = db.query(func.count(CybercrimeAlert.id)).filter(CybercrimeAlert.status == "IN_REVIEW").scalar() or 0
            res_cnt = db.query(func.count(CybercrimeAlert.id)).filter(CybercrimeAlert.status == "RESOLVED").scalar() or 0
            dis_cnt = db.query(func.count(CybercrimeAlert.id)).filter(CybercrimeAlert.status == "DISMISSED").scalar() or 0
            crit_cnt = db.query(func.count(CybercrimeAlert.id)).filter(CybercrimeAlert.severity == "CRITICAL").scalar() or 0
            high_cnt = db.query(func.count(CybercrimeAlert.id)).filter(CybercrimeAlert.severity == "HIGH").scalar() or 0

            type_counts = dict(
                db.query(CybercrimeAlert.alert_type, func.count(CybercrimeAlert.id))
                .group_by(CybercrimeAlert.alert_type)
                .all()
            )

            return {
                "total_alerts": total,
                "new_alerts": new_cnt,
                "critical_alerts": crit_cnt,
                "high_alerts": high_cnt,
                "acknowledged_alerts": ack_cnt,
                "in_review_alerts": rev_cnt,
                "resolved_alerts": res_cnt,
                "dismissed_alerts": dis_cnt,
                "alerts_by_type": type_counts,
            }
        except Exception as exc:
            logger.debug("Database stats error, using local fallback: %s", exc)

    # Local cache aggregation
    all_alerts = list(_LOCAL_ALERTS_CACHE.values())
    type_counts = {}
    for a in all_alerts:
        t = a.get("alert_type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_alerts": len(all_alerts),
        "new_alerts": sum(1 for a in all_alerts if a.get("status") == "NEW"),
        "critical_alerts": sum(1 for a in all_alerts if a.get("severity") == "CRITICAL"),
        "high_alerts": sum(1 for a in all_alerts if a.get("severity") == "HIGH"),
        "acknowledged_alerts": sum(1 for a in all_alerts if a.get("status") == "ACKNOWLEDGED"),
        "in_review_alerts": sum(1 for a in all_alerts if a.get("status") == "IN_REVIEW"),
        "resolved_alerts": sum(1 for a in all_alerts if a.get("status") == "RESOLVED"),
        "dismissed_alerts": sum(1 for a in all_alerts if a.get("status") == "DISMISSED"),
        "alerts_by_type": type_counts,
    }
