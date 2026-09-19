"""
Secure Banking Interface: FastAPI Routes
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Provides an authorized, read-only interface for banking institutions to monitor
predictive alerts and geospatial hotspots within proximity of their physical ATM networks.

ROLES & ACCESS:
  - BANK_ANALYST : Read-only access to scoped bank alerts and ATM proximity analytics.
  - ADMIN        : Full administrative access.
  - ANALYST / SUPERVISOR : Forbidden (403) from bank-specific routes (role isolation).

CONSTRAINTS:
  - Zero write access: BANK_ANALYST cannot acknowledge, resolve, dismiss, or modify alerts.
  - Reuses JWT auth and require_role() from api.analyst_routes — no parallel auth system.
  - Mandatory disclaimer on every response:
    "Analytical alert — authorized human review required. Does not establish criminal activity."
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Direct reuse of existing auth, session, and role check patterns
from api.analyst_routes import (
    analyst_login,
    get_current_user,
    require_role,
    _get_optional_db,
    _load_alerts_csv,
    _load_hotspot_summary,
    _parse_optional_float,
    _parse_optional_int,
)
from database.investigation_schemas import LoginRequest, TokenResponse, UserRead

logger = logging.getLogger("api.bank")

_ROUTES_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _ROUTES_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

router = APIRouter(prefix="/bank", tags=["Secure Banking Interface"])

_MANDATORY_DISCLAIMER = (
    "Analytical alert — authorized human review required. Does not establish criminal activity."
)


# ─────────────────────────────────────────────────────────────────────────────
# Spatial Geometry & Data Caches
# ─────────────────────────────────────────────────────────────────────────────

_CACHED_ATMS_DF: Optional[pd.DataFrame] = None
_CACHED_HOTSPOTS_DF: Optional[pd.DataFrame] = None


def _get_atms_df() -> pd.DataFrame:
    """Load and cache physical ATM dataset."""
    global _CACHED_ATMS_DF
    if _CACHED_ATMS_DF is not None:
        return _CACHED_ATMS_DF

    candidates = [
        DATA_DIR / "processed" / "cleaned_atms_locations.csv",
        DATA_DIR / "raw" / "ATMs_Locations.csv",
    ]
    for path in candidates:
        if path.exists():
            try:
                df = pd.read_csv(path)
                # Ensure lat/lon are numeric
                df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
                df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
                df["bank_id"] = df["bank_id"].astype(str).str.strip().str.upper()
                df = df.dropna(subset=["latitude", "longitude"])
                _CACHED_ATMS_DF = df
                logger.info("Loaded %d ATM records from %s", len(df), path.name)
                return _CACHED_ATMS_DF
            except Exception as exc:
                logger.error("Error reading ATM data from %s: %s", path, exc)

    logger.warning("No ATM locations file found!")
    _CACHED_ATMS_DF = pd.DataFrame()
    return _CACHED_ATMS_DF


def _haversine_km_matrix(
    lats1: np.ndarray, lons1: np.ndarray,
    lats2: np.ndarray, lons2: np.ndarray
) -> np.ndarray:
    """
    Vectorized Haversine distance calculation in kilometers.
    Returns 2D matrix of shape (len(points1), len(points2)).
    """
    r = 6371.0  # Earth mean radius in km
    lat1_r = np.radians(lats1)[:, np.newaxis]
    lon1_r = np.radians(lons1)[:, np.newaxis]
    lat2_r = np.radians(lats2)[np.newaxis, :]
    lon2_r = np.radians(lons2)[np.newaxis, :]

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return r * c


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Response Models
# ─────────────────────────────────────────────────────────────────────────────

class BankAlertItem(BaseModel):
    alert_id: str
    alert_type: str
    severity: str
    status: str
    risk_score: Optional[int] = None
    predicted_probability: Optional[float] = None
    event_count: Optional[float] = None
    dominant_category: Optional[str] = None
    hotspot_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nearest_atm_id: Optional[str] = None
    distance_to_atm_km: Optional[float] = None
    operational_message: Optional[str] = None
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    created_at: Optional[str] = None
    disclaimer: str = _MANDATORY_DISCLAIMER


class HotspotProximitySummary(BaseModel):
    hotspot_id: str
    cluster_id: int
    latitude_centroid: float
    longitude_centroid: float
    nearest_atm_id: str
    min_distance_km: float
    nearby_atms_count: int


class BankAlertsResponse(BaseModel):
    disclaimer: str = _MANDATORY_DISCLAIMER
    bank_id: str
    radius_km: float
    total_bank_atms: int
    total_matching_hotspots: int
    total_alerts: int
    returned_count: int
    matching_hotspots: List[HotspotProximitySummary]
    alerts: List[BankAlertItem]
    synthetic_demonstration: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Auth Endpoints (Reusing analyst login and JWT generation)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Bank Interface Login",
    description="Authenticate banking institution credentials. Reuses core JWT auth.",
)
async def bank_login(
    body: LoginRequest,
    db: Optional[Session] = Depends(_get_optional_db),
):
    """
    Direct reuse of prototype authentication logic.
    Issues JWT with standard roles, including BANK_ANALYST.
    """
    return await analyst_login(body=body, db=db)


@router.get(
    "/auth/me",
    response_model=UserRead,
    summary="Current Bank User Info",
)
async def get_bank_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserRead(
        username=current_user["username"],
        display_name=current_user.get("display_name", current_user["username"]),
        role=current_user["role"],
        is_active=True,
        last_login=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Read-Only Banking Alerts Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/alerts",
    response_model=BankAlertsResponse,
    summary="Bank ATM Scoped Predictive Alerts",
    description=(
        "Read-only endpoint returning predictive alerts linked to hotspots within a "
        "configurable radius of ATM locations belonging to a specific bank. "
        "Role-gated to BANK_ANALYST and ADMIN."
    ),
)
async def get_bank_alerts(
    bank_id: str = Query("BANK001", description="Bank identifier (e.g. BANK001, BANK002, etc.)"),
    radius_km: float = Query(5.0, ge=0.1, le=50.0, description="ATM proximity radius in km to hotspots"),
    severity: Optional[str] = Query(None, description="Optional severity filter (CRITICAL, HIGH, MODERATE, LOW)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    current_user: Dict[str, Any] = Depends(require_role("BANK_ANALYST", "ADMIN")),
    db: Optional[Session] = Depends(_get_optional_db),
):
    """
    1. Filter ATM network to the specified bank_id.
    2. Load geospatial analytical hotspots.
    3. Calculate Haversine proximity matrix between bank ATMs and hotspot centroids.
    4. Filter alerts linked to hotspots within radius_km of any bank ATM.
    5. Return enriched read-only response with mandatory analytical disclaimer.
    """
    bank_id_clean = (bank_id or "").strip().upper()

    # 1. Fetch ATMs for bank
    atms_df = _get_atms_df()
    if atms_df.empty:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ATM location reference data unavailable.",
        )

    bank_atms = atms_df[atms_df["bank_id"] == bank_id_clean]
    total_bank_atms = len(bank_atms)

    if total_bank_atms == 0:
        return BankAlertsResponse(
            disclaimer=_MANDATORY_DISCLAIMER,
            bank_id=bank_id_clean,
            radius_km=radius_km,
            total_bank_atms=0,
            total_matching_hotspots=0,
            total_alerts=0,
            returned_count=0,
            matching_hotspots=[],
            alerts=[],
            synthetic_demonstration=True,
        )

    # 2. Fetch analytical hotspots
    hotspots_raw = _load_hotspot_summary()
    if not hotspots_raw:
        return BankAlertsResponse(
            disclaimer=_MANDATORY_DISCLAIMER,
            bank_id=bank_id_clean,
            radius_km=radius_km,
            total_bank_atms=total_bank_atms,
            total_matching_hotspots=0,
            total_alerts=0,
            returned_count=0,
            matching_hotspots=[],
            alerts=[],
            synthetic_demonstration=True,
        )

    hotspots_df = pd.DataFrame(hotspots_raw)
    hotspots_df["latitude_centroid"] = pd.to_numeric(hotspots_df["latitude_centroid"], errors="coerce")
    hotspots_df["longitude_centroid"] = pd.to_numeric(hotspots_df["longitude_centroid"], errors="coerce")
    hotspots_df = hotspots_df.dropna(subset=["latitude_centroid", "longitude_centroid"]).reset_index(drop=True)

    # 3. Compute distance matrix: ATMs (rows) x Hotspots (cols)
    atm_lats = bank_atms["latitude"].values
    atm_lons = bank_atms["longitude"].values
    atm_ids = bank_atms["atm_id"].values

    hs_lats = hotspots_df["latitude_centroid"].values
    hs_lons = hotspots_df["longitude_centroid"].values

    dist_matrix = _haversine_km_matrix(atm_lats, atm_lons, hs_lats, hs_lons)
    # dist_matrix shape: (len(atms), len(hotspots))

    # For each hotspot (col), find min distance to any bank ATM and the nearest ATM
    min_distances_to_atm = np.min(dist_matrix, axis=0)
    nearest_atm_idx = np.argmin(dist_matrix, axis=0)

    # Hotspots within radius_km
    within_radius_mask = min_distances_to_atm <= radius_km
    matched_hs_indices = np.where(within_radius_mask)[0]

    matched_hotspots_meta: Dict[str, Dict[str, Any]] = {}
    matched_hotspots_list: List[HotspotProximitySummary] = []

    for idx in matched_hs_indices:
        hs_row = hotspots_df.iloc[idx]
        cluster_id = int(hs_row["cluster_id"])
        hs_id_str = f"HS-{cluster_id}"
        min_dist = round(float(min_distances_to_atm[idx]), 3)
        near_atm = str(atm_ids[nearest_atm_idx[idx]])
        nearby_count = int(np.sum(dist_matrix[:, idx] <= radius_km))

        summary = HotspotProximitySummary(
            hotspot_id=hs_id_str,
            cluster_id=cluster_id,
            latitude_centroid=round(float(hs_row["latitude_centroid"]), 6),
            longitude_centroid=round(float(hs_row["longitude_centroid"]), 6),
            nearest_atm_id=near_atm,
            min_distance_km=min_dist,
            nearby_atms_count=nearby_count,
        )
        matched_hotspots_list.append(summary)
        matched_hotspots_meta[hs_id_str] = {
            "nearest_atm_id": near_atm,
            "min_distance_km": min_dist,
        }
        # Also map integer string e.g. "24" in case alerts reference it without "HS-"
        matched_hotspots_meta[str(cluster_id)] = matched_hotspots_meta[hs_id_str]

    # 4. Load alerts and filter to matched hotspots
    all_alerts = _load_alerts_csv()
    bank_scoped_alerts: List[Dict[str, Any]] = []

    for a in all_alerts:
        raw_hs = str(a.get("hotspot_id") or "").strip()
        if not raw_hs or raw_hs == "nan":
            continue

        if raw_hs in matched_hotspots_meta:
            meta = matched_hotspots_meta[raw_hs]
            alert_copy = dict(a)
            alert_copy["nearest_atm_id"] = meta["nearest_atm_id"]
            alert_copy["distance_to_atm_km"] = meta["min_distance_km"]
            bank_scoped_alerts.append(alert_copy)

    # Optional severity filter
    if severity:
        sev_clean = severity.strip().upper()
        bank_scoped_alerts = [
            a for a in bank_scoped_alerts
            if (a.get("severity") or "").upper() == sev_clean
        ]

    total_matched_alerts = len(bank_scoped_alerts)
    paginated_alerts = bank_scoped_alerts[skip : skip + limit]

    # Construct alert items
    alert_items: List[BankAlertItem] = []
    for a in paginated_alerts:
        item = BankAlertItem(
            alert_id=str(a.get("alert_id")),
            alert_type=str(a.get("alert_type") or "WITHDRAWAL_HOTSPOT"),
            severity=str(a.get("severity") or "HIGH").upper(),
            status=str(a.get("status") or "NEW").upper(),
            risk_score=_parse_optional_int(a.get("risk_score")),
            predicted_probability=_parse_optional_float(a.get("predicted_probability")),
            event_count=_parse_optional_float(a.get("event_count")),
            dominant_category=a.get("dominant_category"),
            hotspot_id=a.get("hotspot_id"),
            latitude=_parse_optional_float(a.get("latitude")),
            longitude=_parse_optional_float(a.get("longitude")),
            nearest_atm_id=a.get("nearest_atm_id"),
            distance_to_atm_km=a.get("distance_to_atm_km"),
            operational_message=a.get("operational_message"),
            time_window_start=a.get("time_window_start"),
            time_window_end=a.get("time_window_end"),
            created_at=a.get("created_at"),
            disclaimer=_MANDATORY_DISCLAIMER,
        )
        alert_items.append(item)

    return BankAlertsResponse(
        disclaimer=_MANDATORY_DISCLAIMER,
        bank_id=bank_id_clean,
        radius_km=radius_km,
        total_bank_atms=total_bank_atms,
        total_matching_hotspots=len(matched_hotspots_list),
        total_alerts=total_matched_alerts,
        returned_count=len(alert_items),
        matching_hotspots=matched_hotspots_list,
        alerts=alert_items,
        synthetic_demonstration=True,
    )
