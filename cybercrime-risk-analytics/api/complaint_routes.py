"""
Phase Complaints API: Secure, Validated, Dynamic Complaint Submission Endpoint
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Route:
  POST /complaints — Dynamic complaint submission with full analytical pipeline:
    Complaint Submission
           ↓
    Input Validation
           ↓
    Feature Generation
           ↓
    ML Prediction
           ↓
    Risk Score (0–100) & Category
           ↓
    SHAP Feature Attribution
           ↓
    Predicted Cashout Locations
           ↓
    Alert Generation & Cooldown
           ↓
    Database Storage (PostgreSQL or CSV fallback)
           ↓
    API Response

SECURITY & RBAC:
  - Authorized Roles: ANALYST, SUPERVISOR, ADMIN (or valid X-API-Key)
  - Forbidden Role: BANK_ANALYST (HTTP 403 Forbidden - strict read-only banking separation)
  - Unauthenticated: HTTP 401 Unauthorized
  - Sanitized PII: Never logs account numbers, passwords, PINs, OTPs, CVVs
"""

from __future__ import annotations

import logging
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status as http_status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

# Path bootstrap
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.dependencies import AppState, get_app_state
from api.auth import _DASHBOARD_API_KEY, _SECRET_KEY, _ALGORITHM, _verify_jwt
from database.connection import get_db, SessionLocal
from database.crud import (
    is_db_available,
    create_cybercrime_event,
    create_prediction_result,
    create_alert as db_create_alert,
    _LOCAL_ALERTS_CACHE,
)
from database.schemas import CybercrimeEventCreate, PredictionResultCreate, AlertCreate
from src.predict import (
    predict_single_record,
    explain_prediction,
    probability_to_risk_score,
    assign_risk_category,
    generate_interpretation,
)
from src.complaint_feature_service import extract_features_from_complaint
from src.alert_engine import load_configuration, evaluate_risk_alert, deduplicate_alerts

logger = logging.getLogger("api.complaints")

router = APIRouter(prefix="/complaints", tags=["Complaints"])

bearer_scheme = HTTPBearer(auto_error=False)

# In-memory registry for duplicate submission detection and offline storage
_SUBMITTED_COMPLAINTS_CACHE: Dict[str, Dict[str, Any]] = {}
_complaint_counter = 0

MANDATORY_DISCLAIMER = (
    "Predictions and estimated cashout locations are analytical risk signals for authorized "
    "human review only. Not proof of criminal activity. Does not guarantee future ATM withdrawals."
)


# ==============================================================================
# 1. REQUEST & RESPONSE SCHEMAS
# ==============================================================================

class ComplaintSubmissionRequest(BaseModel):
    """
    Strictly validated incoming raw cybercrime complaint payload.
    """
    complaint_id: Optional[str] = Field(
        None,
        description="Optional unique complaint reference. If omitted, the system auto-generates one.",
        example="CMP-20260919-000123",
    )
    complaint_timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when the incident occurred or was reported.",
        example="2026-09-19T14:30:00Z",
    )
    fraud_amount: float = Field(
        ...,
        gt=0.0,
        description="Financial loss amount in INR (must be > 0).",
        example=75000.0,
    )
    transaction_amount: Optional[float] = Field(
        None,
        ge=0.0,
        description="Optional specific transaction amount associated with complaint.",
        example=75000.0,
    )
    transaction_channel: Optional[str] = Field(
        None,
        description="Payment or transfer channel (UPI, IMPS, NEFT, RTGS, ATM, CARD, NET_BANKING, WALLET).",
        example="UPI",
    )
    complaint_category: str = Field(
        ...,
        description="Standard cybercrime classification taxonomy.",
        example="Online Financial Fraud",
    )
    sender_account_reference: Optional[str] = Field(
        None,
        description="Victim or origin account reference code (sanitized token, not cleartext PAN).",
        example="ACC000001",
    )
    receiver_account_reference: Optional[str] = Field(
        None,
        description="Destination or mule account reference code.",
        example="ACC000999",
    )
    bank_reference: Optional[str] = Field(
        None,
        description="Origin or target financial institution identifier.",
        example="BANK001",
    )
    state: str = Field(
        ...,
        description="State where the victim or incident is located.",
        example="Tamil Nadu",
    )
    district: str = Field(
        ...,
        description="District where the incident is reported.",
        example="Chennai",
    )
    city: Optional[str] = Field(
        None,
        description="City, town, or administrative beat locality.",
        example="T Nagar",
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="WGS 84 latitude coordinate [-90 to 90].",
        example=13.04,
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="WGS 84 longitude coordinate [-180 to 180].",
        example=80.23,
    )
    transaction_timestamp: Optional[str] = Field(
        None,
        description="Optional ISO 8601 timestamp when transaction occurred.",
        example="2026-09-19T14:15:00Z",
    )
    transaction_reference: Optional[str] = Field(
        None,
        description="Optional synthetic or anonymized transaction identifier.",
        example="TXN-20260919-998811",
    )
    reported_status: Optional[str] = Field(
        "REPORTED",
        description="Initial complaint status (REPORTED, UNDER_REVIEW, ESCALATED).",
        example="REPORTED",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional sanitized narrative of the complaint (max 2000 chars).",
        example="Victim reported unauthorized UPI transfer following a fraudulent utility bill link.",
    )

    @field_validator("complaint_timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("complaint_timestamp cannot be empty.")
        clean_v = v.replace("Z", "+00:00")
        try:
            datetime.fromisoformat(clean_v)
        except Exception as exc:
            raise ValueError(
                f"Invalid timestamp format '{v}'. Must be a valid ISO 8601 string (e.g. '2026-09-19T14:30:00Z')."
            ) from exc
        return v

    @field_validator("transaction_timestamp")
    @classmethod
    def validate_txn_timestamp_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not v.strip():
            return None
        clean_v = v.replace("Z", "+00:00")
        try:
            datetime.fromisoformat(clean_v)
        except Exception as exc:
            raise ValueError(
                f"Invalid transaction_timestamp format '{v}'. Must be a valid ISO 8601 string."
            ) from exc
        return v

    @field_validator("fraud_amount")
    @classmethod
    def validate_amount_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("fraud_amount must be a finite numerical value.")
        if v <= 0:
            raise ValueError("fraud_amount must be greater than zero.")
        return v

    @field_validator("latitude")
    @classmethod
    def validate_latitude_finite(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("latitude must be a finite numerical coordinate.")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude_finite(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("longitude must be a finite numerical coordinate.")
        return v


class PredictedCashoutLocation(BaseModel):
    rank: Optional[int] = None
    cluster_id: int
    district: str
    latitude: float
    longitude: float
    distance_to_complaint_km: Optional[float] = None
    nearest_atm_id: Optional[str] = None
    nearest_atm_bank: Optional[str] = None
    nearest_atm_distance_km: Optional[float] = None
    nearest_atm_latitude: Optional[float] = None
    nearest_atm_longitude: Optional[float] = None
    catchment_2_5km_atm_count: Optional[int] = None
    catchment_5_0km_atm_count: Optional[int] = None
    risk_score: int
    risk_category: str
    ranking_score: Optional[int] = None
    ranking_label: Optional[str] = None
    location_source: str = "DBSCAN Spatial Hotspot Cluster (Estimate)"
    prediction_timestamp: str


class ComplaintAlertInfo(BaseModel):
    created: bool
    alert_id: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    operational_message: Optional[str] = None


class RiskDriver(BaseModel):
    rank: int
    feature: str
    shap_value: float
    direction: str


class ComplaintSubmissionResponse(BaseModel):
    complaint_id: str
    prediction_id: str
    status: str = "processed"
    withdrawal_probability: float
    risk_score: int
    risk_level: str
    model_version: str
    prediction_timestamp: str
    operational_interpretation: str
    predicted_locations: List[PredictedCashoutLocation]
    alert: ComplaintAlertInfo
    explanation_available: bool
    top_risk_drivers: List[RiskDriver]
    storage_mode: str
    disclaimer: str = MANDATORY_DISCLAIMER


# ==============================================================================
# 2. SECURITY, RBAC & SERIALIZATION HELPERS
# ==============================================================================

def _next_complaint_id() -> str:
    global _complaint_counter
    _complaint_counter += 1
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"CMP-{today}-{_complaint_counter:06d}"


def _sanitize_val(v: Any) -> Any:
    """Recursively sanitize NaN, Infinity, and numpy datatypes for strict JSON safety."""
    if v is None:
        return None
    if isinstance(v, (float, np.floating)):
        if math.isnan(v) or math.isinf(v):
            return None
        return float(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, dict):
        return {k: _sanitize_val(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_sanitize_val(val) for val in v]
    return v


def require_complaint_submission_role(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """
    Enforces authentication and strict RBAC:
    - ANALYST, SUPERVISOR, ADMIN are authorized.
    - BANK_ANALYST is explicitly rejected with HTTP 403 Forbidden.
    - Unauthenticated requests return HTTP 401 Unauthorized.
    """
    # 1. Environment bypass (dev/testing)
    if os.getenv("DISABLE_API_KEY_AUTH", "").lower() in ("true", "1", "yes"):
        return {"username": "dev_test_user", "role": "ANALYST"}

    # 2. Trusted API Key (System integration)
    if x_api_key and x_api_key == _DASHBOARD_API_KEY:
        return {"username": "system_service", "role": "SYSTEM_ADMIN"}

    # 3. JWT Bearer Token Check
    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            from jose import jwt, JWTError
            payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
            username = payload.get("sub")
            role = payload.get("role", "UNKNOWN")
            
            # Check BANK_ANALYST role restriction
            if role == "BANK_ANALYST":
                logger.warning("Access denied: BANK_ANALYST attempted complaint submission.")
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Access denied. BANK_ANALYST has read-only access and cannot submit complaints.",
                )
            
            # Allow authorized operational roles
            if role in ("ANALYST", "SUPERVISOR", "ADMIN"):
                return {"username": username, "role": role}

            logger.warning("Access denied for role: %s", role)
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Insufficient permissions for role '{role}'. Required: ANALYST, SUPERVISOR, or ADMIN.",
            )
        except JWTError:
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 4. Unauthenticated
    logger.warning("Unauthorized complaint submission attempt — missing credentials.")
    raise HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide Authorization: Bearer <analyst JWT> or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ==============================================================================
# 3. SPATIAL PREDICTED LOCATIONS SERVICE
# ==============================================================================

def _calc_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two coordinates in kilometers."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


def get_nearby_predicted_locations(
    district: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    prediction_time: str,
    limit: int = 5,
) -> List[PredictedCashoutLocation]:
    """
    Retrieves candidate cashout hotspots cross-referenced with physical ATMs
    using the centralized spatial cashout analytics service.
    """
    from src.spatial_cashout_service import get_candidate_cashout_locations

    candidates = get_candidate_cashout_locations(
        district=district,
        complaint_lat=lat,
        complaint_lon=lon,
        prediction_time=prediction_time,
        top_k=limit,
    )

    results = []
    for c in candidates:
        results.append(PredictedCashoutLocation(
            rank=c.get("rank"),
            cluster_id=c["cluster_id"],
            district=c["district"],
            latitude=c["latitude"],
            longitude=c["longitude"],
            distance_to_complaint_km=c.get("distance_to_complaint_km"),
            nearest_atm_id=c.get("nearest_atm_id"),
            nearest_atm_bank=c.get("nearest_atm_bank"),
            nearest_atm_distance_km=c.get("nearest_atm_distance_km"),
            nearest_atm_latitude=c.get("nearest_atm_latitude"),
            nearest_atm_longitude=c.get("nearest_atm_longitude"),
            catchment_2_5km_atm_count=c.get("catchment_2_5km_atm_count"),
            catchment_5_0km_atm_count=c.get("catchment_5_0km_atm_count"),
            risk_score=c["risk_score"],
            risk_category=c["risk_category"],
            ranking_score=c.get("ranking_score"),
            ranking_label=c.get("ranking_label"),
            location_source="DBSCAN Spatial Hotspot Cluster (Estimate)",
            prediction_timestamp=prediction_time,
        ))

    return results


# ==============================================================================
# 4. POST /complaints ENDPOINT
# ==============================================================================

@router.post(
    "",
    response_model=ComplaintSubmissionResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Submit Raw Cybercrime Complaint for Predictive Analysis",
    description=(
        "Accepts raw complaint intake data and executes the end-to-end predictive pipeline:\n"
        "1. Validates intake timestamps, monetary amounts, and coordinates.\n"
        "2. Automatically derives all 64 model features (cyclic time, spatial grids, category flags).\n"
        "3. Calls frozen XGBoost pipeline to calculate withdrawal probability and risk score.\n"
        "4. Generates local SHAP explanations for top risk drivers.\n"
        "5. Identifies candidate physical cashout locations and nearest ATMs.\n"
        "6. Triggers analytical alert if risk meets threshold (risk_score >= 60).\n"
        "7. Persists records to PostgreSQL/PostGIS (or local fallback cache if offline).\n\n"
        "**Authorized Roles:** `ANALYST`, `SUPERVISOR`, `ADMIN`\n"
        "**Forbidden:** `BANK_ANALYST` (read-only institution role)"
    ),
)
async def submit_complaint(
    complaint: ComplaintSubmissionRequest,
    user: Dict[str, Any] = Depends(require_complaint_submission_role),
    state: AppState = Depends(get_app_state),
):
    t_start = time.perf_counter()

    if not state.model_loaded or not state.pipeline_loaded:
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model is not initialized. Please contact system administrator.",
        )

    # 1. Establish Complaint ID & Check for Duplicates
    cid = complaint.complaint_id.strip() if complaint.complaint_id else _next_complaint_id()
    if cid in _SUBMITTED_COMPLAINTS_CACHE:
        logger.warning("Duplicate complaint rejected: %s", cid)
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Duplicate complaint submission: complaint_id '{cid}' has already been processed.",
        )

    complaint_dict = complaint.model_dump()
    complaint_dict["complaint_id"] = cid

    # 2. Dynamic Feature Generation
    try:
        model_input_dict = extract_features_from_complaint(
            complaint_dict,
            expected_features=state.feature_schema,
        )
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Feature extraction failed for complaint %s", cid)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature generation failed: {str(exc)[:120]}",
        )

    # 3. Model Prediction & Risk Scoring
    try:
        pred_res = predict_single_record(model_input_dict, state.pipeline, state.metadata)
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Prediction failed for complaint %s", cid)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction inference.",
        )

    prob = float(pred_res["probability"])
    score = int(pred_res["risk_score"])
    category = str(pred_res["risk_category"])
    interpretation = str(pred_res["operational_interpretation"])
    pred_id = f"PRED-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{cid[-6:]}"

    # 4. SHAP Explanation
    shap_drivers = []
    shap_available = False
    try:
        shap_res = explain_prediction(model_input_dict, state.pipeline, state.metadata)
        if shap_res.get("status") == "SUCCESS":
            shap_available = True
            pos_contribs = shap_res.get("top_positive_contributors", [])
            for item in pos_contribs[:5]:
                shap_drivers.append(RiskDriver(
                    rank=int(item["rank"]),
                    feature=str(item["feature"]),
                    shap_value=round(float(item["shap_value"]), 4),
                    direction=str(item["direction"]),
                ))
    except Exception as exc:
        logger.warning("SHAP explanation unavailable for complaint %s: %s", cid, exc)

    # 5. Predicted Locations & ATM Cross-Referencing
    pred_locations = get_nearby_predicted_locations(
        district=complaint.district,
        lat=complaint.latitude,
        lon=complaint.longitude,
        prediction_time=complaint.complaint_timestamp,
        limit=5,
    )

    # 6. Alert Generation & Cooldown
    alert_config = load_configuration()
    alert_row = {
        "case_id": cid,
        "prediction_reference": pred_id,
        "risk_score": score,
        "predicted_probability": prob,
        "victim_district": complaint.district,
        "crime_type": complaint.complaint_category,
        "complaint_timestamp": complaint.complaint_timestamp,
        "latitude": complaint.latitude,
        "longitude": complaint.longitude,
        "model_version": state.model_version,
    }
    raw_alert = evaluate_risk_alert(alert_row, alert_config, alert_counter=len(_LOCAL_ALERTS_CACHE) + 1)
    
    alert_info = ComplaintAlertInfo(created=False)
    if raw_alert is not None:
        # Check cooldown & deduplication
        existing_list = list(_LOCAL_ALERTS_CACHE.values()) if isinstance(_LOCAL_ALERTS_CACHE, dict) else _LOCAL_ALERTS_CACHE
        unique_alerts, dups, cd_skipped = deduplicate_alerts([raw_alert], existing_list, alert_config)
        if unique_alerts:
            final_alert = unique_alerts[0]
            if isinstance(_LOCAL_ALERTS_CACHE, dict):
                _LOCAL_ALERTS_CACHE[final_alert["alert_id"]] = final_alert
            else:
                _LOCAL_ALERTS_CACHE.append(final_alert)
            alert_info = ComplaintAlertInfo(
                created=True,
                alert_id=final_alert["alert_id"],
                alert_type=final_alert["alert_type"],
                severity=final_alert["severity"],
                operational_message=final_alert["operational_message"],
            )
        else:
            logger.info("Alert generation suppressed by cooldown/dedup for complaint %s", cid)

    # 7. Database Persistence
    storage_mode = "CSV_FALLBACK_DEV"
    db_available = is_db_available()

    if db_available:
        try:
            with SessionLocal() as db_session:
                # 7a. Insert CybercrimeEvent
                dt_obj = datetime.fromisoformat(complaint.complaint_timestamp.replace("Z", "+00:00"))
                event_dto = CybercrimeEventCreate(
                    case_id=cid,
                    complaint_timestamp=dt_obj,
                    crime_type=complaint.complaint_category,
                    fraud_amount=complaint.fraud_amount,
                    reported_by_authority=0,
                    victim_state=complaint.state,
                    victim_district=complaint.district,
                    victim_area=complaint.city,
                    latitude=complaint.latitude,
                    longitude=complaint.longitude,
                )
                create_cybercrime_event(db_session, event_dto)

                # 7b. Insert PredictionResult
                pred_dto = PredictionResultCreate(
                    prediction_reference=cid,
                    prediction_timestamp=datetime.now(timezone.utc),
                    predicted_probability=prob,
                    risk_score=score,
                    risk_category=category,
                    operational_interpretation=interpretation,
                    model_version=state.model_version,
                    latitude=complaint.latitude,
                    longitude=complaint.longitude,
                    victim_district=complaint.district,
                    crime_type=complaint.complaint_category,
                )
                create_prediction_result(db_session, pred_dto)

                # 7c. Insert Alert if created
                if alert_info.created and raw_alert:
                    alert_dto = AlertCreate(
                        alert_id=raw_alert["alert_id"],
                        alert_type=raw_alert["alert_type"],
                        severity=raw_alert["severity"],
                        prediction_reference=cid,
                        risk_score=score,
                        predicted_probability=prob,
                        event_count=1,
                        dominant_category=complaint.complaint_category,
                        operational_message=raw_alert["operational_message"],
                        model_version=state.model_version,
                        latitude=complaint.latitude,
                        longitude=complaint.longitude,
                    )
                    db_create_alert(db_session, alert_dto)

            storage_mode = "POSTGRESQL_POSTGIS"
        except Exception as db_err:
            logger.warning("Database write failed for complaint %s: %s. Switched to fallback mode.", cid, db_err)
            storage_mode = "CSV_FALLBACK_DEV"

    # Always update in-memory cache for duplicate tracking and fast lookup
    _SUBMITTED_COMPLAINTS_CACHE[cid] = {
        "complaint_id": cid,
        "prediction_id": pred_id,
        "risk_score": score,
        "risk_category": category,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_by": user.get("username"),
    }

    latency_ms = (time.perf_counter() - t_start) * 1000
    logger.info(
        "POST /complaints | id=%s | score=%d | cat=%s | alert=%s | storage=%s | latency=%.1fms",
        cid, score, category, alert_info.created, storage_mode, latency_ms,
    )

    response_dict = {
        "complaint_id": cid,
        "prediction_id": pred_id,
        "status": "processed",
        "withdrawal_probability": round(prob, 4),
        "risk_score": score,
        "risk_level": category,
        "model_version": state.model_version,
        "prediction_timestamp": complaint.complaint_timestamp,
        "operational_interpretation": interpretation,
        "predicted_locations": [loc.model_dump() for loc in pred_locations],
        "alert": alert_info.model_dump(),
        "explanation_available": shap_available,
        "top_risk_drivers": [d.model_dump() for d in shap_drivers],
        "storage_mode": storage_mode,
        "disclaimer": MANDATORY_DISCLAIMER,
    }

    sanitized = _sanitize_val(response_dict)
    return ComplaintSubmissionResponse(**sanitized)
