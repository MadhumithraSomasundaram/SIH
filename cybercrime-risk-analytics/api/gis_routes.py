"""
Phase 15 — GIS Risk Heatmap Dashboard: FastAPI GIS Endpoints
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Serves map-safe, privacy-preserving geographic analytical data for the dashboard.

Primary data source: CSV outputs from Phase 9 and Phase 14 (always available).
Optional enrichment: PostgreSQL/PostGIS (graceful fallback if offline).

Endpoints:
    GET /gis/summary            — Dashboard KPI statistics
    GET /gis/events             — Filtered event GeoJSON (max 2000)
    GET /gis/risk-heatmap       — District-aggregated risk heatmap GeoJSON
    GET /gis/hotspots           — Phase 14 DBSCAN hotspot GeoJSON
    GET /gis/hotspots/{id}      — Single hotspot detail
    GET /gis/filters            — Available filter option values
    GET /gis/statistics         — Chart data

IMPORTANT:
- No PII: no account numbers, card numbers, PINs, OTPs, CVVs, passwords
- No model retraining
- No future data leakage
- Hotspot clusters are ANALYTICAL only — not proven criminal zones
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from api.auth import require_api_key

logger = logging.getLogger("api.gis")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ROUTER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _ROUTER_DIR.parent
OUTPUTS = PROJECT_ROOT / "outputs"

# ---------------------------------------------------------------------------
# Data Loading — loaded once at import time (CSV always available)
# ---------------------------------------------------------------------------

def _load_clustered_events() -> pd.DataFrame:
    """Load Phase 14 clustered events (safe columns only)."""
    p = OUTPUTS / "phase14_clustered_events.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, usecols=[
        "case_id", "complaint_timestamp", "crime_type", "victim_district",
        "latitude", "longitude", "cluster_id",
        "is_linked_to_withdrawal", "future_withdrawal",
        "risk_score", "risk_category",
        "event_hour", "event_day_of_week", "crime_category_group",
    ])
    df["complaint_timestamp"] = pd.to_datetime(df["complaint_timestamp"], errors="coerce")
    return df


def _load_hotspot_summary() -> pd.DataFrame:
    p = OUTPUTS / "phase14_hotspot_summary.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_cluster_stats() -> pd.DataFrame:
    p = OUTPUTS / "phase14_cluster_statistics.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_temporal_summary() -> pd.DataFrame:
    p = OUTPUTS / "phase14_hotspot_temporal_summary.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_withdrawal_hotspots() -> pd.DataFrame:
    p = OUTPUTS / "phase14_withdrawal_hotspots.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_risk_hotspot_summary() -> pd.DataFrame:
    p = OUTPUTS / "phase14_hotspot_risk_summary.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_location_risk() -> pd.DataFrame:
    p = OUTPUTS / "phase9_location_risk_summary.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_hotspots_geojson() -> dict:
    p = OUTPUTS / "phase14_hotspots_geojson.geojson"
    if not p.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(p) as f:
        return json.load(f)


# Pre-load at import time (cached for request lifetime)
_df_events: Optional[pd.DataFrame] = None
_df_hotspots: Optional[pd.DataFrame] = None
_df_cluster_stats: Optional[pd.DataFrame] = None
_df_temporal: Optional[pd.DataFrame] = None
_df_location_risk: Optional[pd.DataFrame] = None
_geojson_hotspots: Optional[dict] = None
_df_mule_patterns: Optional[pd.DataFrame] = None


def _load_mule_pattern_accounts() -> pd.DataFrame:
    """Load rule-based heuristic mule pattern accounts output."""
    p = OUTPUTS / "phase_mule_pattern_accounts.csv"
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not load mule pattern accounts CSV: %s", exc)
        return pd.DataFrame()


_CACHED_GIS_ATMS: Optional[pd.DataFrame] = None


def _load_gis_atms() -> pd.DataFrame:
    """Load physical ATM dataset from raw or processed CSV."""
    global _CACHED_GIS_ATMS
    if _CACHED_GIS_ATMS is not None:
        return _CACHED_GIS_ATMS
    candidates = [
        PROJECT_ROOT / "data" / "processed" / "cleaned_atms_locations.csv",
        PROJECT_ROOT / "data" / "raw" / "ATMs_Locations.csv",
    ]
    for p in candidates:
        if p.exists():
            try:
                df = pd.read_csv(p)
                df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
                df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
                df = df.dropna(subset=["latitude", "longitude"])
                _CACHED_GIS_ATMS = df
                logger.info("Loaded %d physical ATM locations from %s", len(df), p.name)
                return _CACHED_GIS_ATMS
            except Exception as exc:
                logger.error("Failed loading ATM locations from %s: %s", p, exc)
    return pd.DataFrame()


def _calc_haversine_km(lat1: float, lon1: float, lats2: np.ndarray, lons2: np.ndarray) -> np.ndarray:
    """Vectorized Haversine distance between one point and array of points in km."""
    r = 6371.0
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lats2_r = np.radians(lats2)
    lons2_r = np.radians(lons2)

    dlat = lats2_r - lat1_r
    dlon = lons2_r - lon1_r

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lats2_r) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    return r * c



def _load_events_from_db() -> Optional[pd.DataFrame]:
    """Attempt to load events directly from live PostgreSQL database when connected."""
    try:
        from database.connection import SessionLocal
        from database.crud import is_db_available
        if not is_db_available():
            return None
        db = SessionLocal()
        try:
            from database.models import CybercrimeEvent
            count = db.query(CybercrimeEvent.id).count()
            if count == 0:
                return None
            rows = db.query(
                CybercrimeEvent.case_id,
                CybercrimeEvent.complaint_timestamp,
                CybercrimeEvent.crime_type,
                CybercrimeEvent.victim_district,
                CybercrimeEvent.latitude,
                CybercrimeEvent.longitude,
                CybercrimeEvent.is_linked_to_withdrawal,
                CybercrimeEvent.future_withdrawal,
            ).limit(10000).all()
            if rows:
                records = []
                for r in rows:
                    records.append({
                        "case_id": r.case_id,
                        "complaint_timestamp": r.complaint_timestamp,
                        "crime_type": r.crime_type,
                        "victim_district": r.victim_district,
                        "latitude": r.latitude,
                        "longitude": r.longitude,
                        "is_linked_to_withdrawal": r.is_linked_to_withdrawal,
                        "future_withdrawal": r.future_withdrawal,
                    })
                df = pd.DataFrame(records)
                df["complaint_timestamp"] = pd.to_datetime(df["complaint_timestamp"], errors="coerce")
                return df
        finally:
            db.close()
    except Exception as exc:
        logger.debug("Database event query failed, falling back to CSV: %s", exc)
    return None


def _get_events() -> pd.DataFrame:
    global _df_events
    if _df_events is None or _df_events.empty:
        db_df = _load_events_from_db()
        if db_df is not None and not db_df.empty:
            _df_events = db_df
        else:
            _df_events = _load_clustered_events()
    return _df_events


def _get_hotspot_summary() -> pd.DataFrame:
    global _df_hotspots
    if _df_hotspots is None or _df_hotspots.empty:
        _df_hotspots = _load_hotspot_summary()
    return _df_hotspots


def _get_cluster_stats() -> pd.DataFrame:
    global _df_cluster_stats
    if _df_cluster_stats is None or _df_cluster_stats.empty:
        _df_cluster_stats = _load_cluster_stats()
    return _df_cluster_stats


def _get_temporal() -> pd.DataFrame:
    global _df_temporal
    if _df_temporal is None or _df_temporal.empty:
        _df_temporal = _load_temporal_summary()
    return _df_temporal


def _get_location_risk() -> pd.DataFrame:
    global _df_location_risk
    if _df_location_risk is None or _df_location_risk.empty:
        _df_location_risk = _load_location_risk()
    return _df_location_risk


def _get_geojson_hotspots() -> dict:
    global _geojson_hotspots
    if _geojson_hotspots is None:
        _geojson_hotspots = _load_hotspots_geojson()
    return _geojson_hotspots


def _get_mule_patterns() -> pd.DataFrame:
    global _df_mule_patterns
    if _df_mule_patterns is None or _df_mule_patterns.empty:
        _df_mule_patterns = _load_mule_pattern_accounts()
    return _df_mule_patterns


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if (f != f or abs(f) == float("inf")) else round(f, 6)
    except (TypeError, ValueError):
        return None


def _safe_int(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


SAFE_FIELDS_BLACKLIST = {
    "account_number", "card_number", "cvv", "pin", "otp", "password",
    "phone", "email", "victim_phone", "victim_email",
}

DISCLAIMER = (
    "Analytical signal only. Does not establish that criminal activity occurred, "
    "identify a criminal, or guarantee a future withdrawal. "
    "Authorized human review required."
)

MULE_PATTERN_METHOD = "rule_based_heuristic_fan_in_pattern"
MULE_PATTERN_DISCLAIMER = (
    "Simplified heuristic indicator only — not a validated mule detection system. "
    "Does not establish account involvement in fraud. "
    "Multi-hop graph-based tracing is a planned future capability, not implemented here."
)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(
    prefix="/gis",
    tags=["GIS Dashboard"],
    dependencies=[Depends(require_api_key)],
)


# ==============================================================================
# GET /gis/summary
# ==============================================================================
@router.get(
    "/summary",
    summary="Dashboard KPI Summary",
    description="Returns top-level KPI statistics for the GIS dashboard. Uses Phase 9 risk scores and Phase 14 hotspot data.",
)
async def gis_summary(
    start_time: Optional[str] = Query(None, description="ISO datetime, e.g. 2026-01-01"),
    end_time: Optional[str] = Query(None, description="ISO datetime, e.g. 2026-08-31"),
    crime_category: Optional[str] = Query(None, description="crime_category_group value"),
    crime_type: Optional[str] = Query(None, description="crime_type value"),
    risk_category: Optional[str] = Query(None, description="LOW|MODERATE|HIGH|CRITICAL"),
    min_risk_score: Optional[int] = Query(None, ge=0, le=100),
    max_risk_score: Optional[int] = Query(None, ge=0, le=100),
    hotspot_id: Optional[int] = Query(None, description="cluster_id from Phase 14"),
    hotspot_only: Optional[bool] = Query(None, description="Filter to events belonging to an analytical hotspot cluster"),
):
    t0 = time.time()
    df = _get_events().copy()
    df_hs = _get_hotspot_summary()

    if df.empty:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Analytical data not available.")

    # Apply filters if provided
    if start_time:
        try:
            st = pd.to_datetime(start_time)
            df = df[df["complaint_timestamp"] >= st]
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid start_time format. Use ISO datetime.")

    if end_time:
        try:
            et = pd.to_datetime(end_time)
            df = df[df["complaint_timestamp"] <= et]
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid end_time format. Use ISO datetime.")

    if crime_category and "crime_category_group" in df.columns:
        df = df[df["crime_category_group"].str.upper() == crime_category.upper()]

    if crime_type and "crime_type" in df.columns:
        df = df[df["crime_type"].str.upper() == crime_type.upper()]

    if risk_category and "risk_category" in df.columns:
        df = df[df["risk_category"] == risk_category.upper()]

    if min_risk_score is not None and "risk_score" in df.columns:
        df = df[df["risk_score"].fillna(0) >= min_risk_score]

    if max_risk_score is not None and "risk_score" in df.columns:
        df = df[df["risk_score"].fillna(0) <= max_risk_score]

    if hotspot_id is not None and "cluster_id" in df.columns:
        df = df[df["cluster_id"] == hotspot_id]

    if hotspot_only and "cluster_id" in df.columns:
        df = df[df["cluster_id"] > 0]

    if df.empty:
        return {
            "total_analytical_records": 0,
            "risk_scored_records": 0,
            "high_risk_records": 0,
            "critical_risk_records": 0,
            "hotspot_count": 0,
            "average_risk_score": None,
            "top_crime_category": "N/A",
            "highest_risk_area": "N/A",
            "data_time_range": {"start": None, "end": None},
            "withdrawal_events": 0,
            "data_source": "Phase 9 risk scores + Phase 14 DBSCAN (historical/prototype data)",
            "response_time_ms": round((time.time() - t0) * 1000, 1),
        }

    total = len(df)
    risk_present = df["risk_score"].notna() if "risk_score" in df.columns else pd.Series([False]*total)
    high_risk = int((df["risk_category"] == "HIGH").sum()) if "risk_category" in df.columns else 0
    critical_risk = int((df["risk_category"] == "CRITICAL").sum()) if "risk_category" in df.columns else 0
    avg_risk = round(float(df.loc[risk_present, "risk_score"].mean()), 2) if risk_present.any() else None
    ts = df["complaint_timestamp"].dropna() if "complaint_timestamp" in df.columns else pd.Series()
    
    top_district = "N/A"
    if "victim_district" in df.columns and not df["victim_district"].dropna().empty:
        subset = df.loc[risk_present & (df["risk_category"].isin(["HIGH", "CRITICAL"])), "victim_district"]
        if not subset.empty:
            top_district = subset.value_counts().index[0]
        else:
            top_district = df["victim_district"].value_counts().index[0]

    top_crime = "N/A"
    if "crime_category_group" in df.columns and not df["crime_category_group"].dropna().empty:
        top_crime = df["crime_category_group"].value_counts().index[0]

    if "cluster_id" in df.columns:
        filtered_hotspots = int(df.loc[df["cluster_id"] > 0, "cluster_id"].nunique())
        has_cluster_filter = (hotspot_id is not None or hotspot_only or crime_category or risk_category)
        hotspot_cnt = filtered_hotspots if has_cluster_filter else len(df_hs)
    else:
        hotspot_cnt = len(df_hs)

    return {
        "total_analytical_records": total,
        "risk_scored_records": int(risk_present.sum()),
        "high_risk_records": high_risk,
        "critical_risk_records": critical_risk,
        "hotspot_count": hotspot_cnt,
        "average_risk_score": avg_risk,
        "top_crime_category": top_crime,
        "highest_risk_area": top_district,
        "data_time_range": {
            "start": ts.min().isoformat() if not ts.empty else None,
            "end": ts.max().isoformat() if not ts.empty else None,
        },
        "withdrawal_events": int(df["future_withdrawal"].sum()) if "future_withdrawal" in df.columns else None,
        "data_source": "Phase 9 risk scores + Phase 14 DBSCAN (historical/prototype data)",
        "response_time_ms": round((time.time() - t0) * 1000, 1),
    }


# ==============================================================================
# GET /gis/events
# ==============================================================================
@router.get(
    "/events",
    summary="Filtered Event GeoJSON",
    description=(
        "Returns map-safe event records as GeoJSON FeatureCollection. "
        "Max 2000 records. Supports filtering by date, crime, risk, and cluster."
    ),
)
async def gis_events(
    start_time: Optional[str] = Query(None, description="ISO datetime, e.g. 2026-01-01"),
    end_time: Optional[str] = Query(None, description="ISO datetime, e.g. 2026-08-31"),
    crime_category: Optional[str] = Query(None, description="crime_category_group value"),
    crime_type: Optional[str] = Query(None, description="crime_type value"),
    risk_category: Optional[str] = Query(None, description="LOW|MODERATE|HIGH|CRITICAL"),
    min_risk_score: Optional[int] = Query(None, ge=0, le=100),
    max_risk_score: Optional[int] = Query(None, ge=0, le=100),
    hotspot_id: Optional[int] = Query(None, description="cluster_id from Phase 14"),
    hotspot_only: Optional[bool] = Query(None, description="Filter to events belonging to an analytical hotspot cluster"),
    limit: int = Query(2000, ge=1, le=5000, description="Max records (default 2000)"),
):
    t0 = time.time()
    df = _get_events().copy()

    if df.empty:
        return {"type": "FeatureCollection", "features": [], "total": 0}

    # Validate risk_category
    valid_risk_cats = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    if risk_category and risk_category.upper() not in valid_risk_cats:
        raise HTTPException(status_code=422, detail=f"risk_category must be one of {sorted(valid_risk_cats)}")

    # Apply filters
    if start_time:
        try:
            st = pd.to_datetime(start_time)
            df = df[df["complaint_timestamp"] >= st]
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid start_time format. Use ISO datetime.")

    if end_time:
        try:
            et = pd.to_datetime(end_time)
            df = df[df["complaint_timestamp"] <= et]
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid end_time format. Use ISO datetime.")

    if crime_category:
        df = df[df["crime_category_group"].str.upper() == crime_category.upper()]

    if crime_type:
        df = df[df["crime_type"].str.upper() == crime_type.upper()]

    if risk_category:
        df = df[df["risk_category"] == risk_category.upper()]

    if min_risk_score is not None:
        df = df[df["risk_score"].fillna(0) >= min_risk_score]

    if max_risk_score is not None:
        df = df[df["risk_score"].fillna(0) <= max_risk_score]

    if hotspot_id is not None:
        df = df[df["cluster_id"] == hotspot_id]

    if hotspot_only:
        df = df[df["cluster_id"].notna() & (df["cluster_id"] >= 0)]

    total_filtered = len(df)
    df = df.head(limit)

    features = []
    for _, row in df.iterrows():
        lat = _safe_float(row.get("latitude"))
        lon = _safe_float(row.get("longitude"))
        if lat is None or lon is None:
            continue
        ts = row.get("complaint_timestamp")
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "case_id": str(row.get("case_id", "")),
                "complaint_timestamp": ts.isoformat() if pd.notna(ts) else None,
                "crime_type": str(row.get("crime_type", "")),
                "crime_category_group": str(row.get("crime_category_group", "")),
                "victim_district": str(row.get("victim_district", "")),
                "cluster_id": _safe_int(row.get("cluster_id")),
                "risk_score": _safe_int(row.get("risk_score")),
                "risk_category": str(row.get("risk_category", "")) if pd.notna(row.get("risk_category")) else None,
                "is_linked_to_withdrawal": bool(row.get("is_linked_to_withdrawal", False)),
                "event_hour": _safe_int(row.get("event_hour")),
                "disclaimer": DISCLAIMER,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "total_matching": total_filtered,
        "records_returned": len(features),
        "limit": limit,
        "response_time_ms": round((time.time() - t0) * 1000, 1),
    }


def _is_valid_coord(lat: Optional[float], lon: Optional[float]) -> bool:
    """Validate geographic coordinate bounds: -90<=lat<=90, -180<=lon<=180, not (0,0)."""
    if lat is None or lon is None:
        return False
    if lat == 0.0 and lon == 0.0:
        return False
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return False
    return True


# ==============================================================================
# GET /gis/risk-heatmap
# ==============================================================================
@router.get(
    "/risk-heatmap",
    summary="District-Aggregated Risk & Density Heatmap GeoJSON",
    description=(
        "Returns district-level aggregated risk/density data for heatmap visualization. "
        "Supports dynamic filtering by date, crime category, risk tier, and metric. "
        "Preserves 40-district default baseline for backwards compatibility."
    ),
)
async def gis_risk_heatmap(
    start_time: Optional[str] = Query(None, description="ISO datetime, e.g. 2026-01-01"),
    end_time: Optional[str] = Query(None, description="ISO datetime, e.g. 2026-08-31"),
    crime_category: Optional[str] = Query(None, description="crime_category_group value"),
    crime_type: Optional[str] = Query(None, description="crime_type value"),
    risk_category: Optional[str] = Query(None, description="LOW|MODERATE|HIGH|CRITICAL"),
    min_risk_score: Optional[int] = Query(None, ge=0, le=100),
    max_risk_score: Optional[int] = Query(None, ge=0, le=100),
    hotspot_id: Optional[int] = Query(None, description="cluster_id from Phase 14"),
    hotspot_only: Optional[bool] = Query(None, description="Filter to events belonging to an analytical hotspot"),
    metric: Optional[str] = Query("risk", description="risk (predictive score) or density (complaint volume)"),
):
    t0 = time.time()
    has_filters = any([
        start_time, end_time, crime_category, crime_type, risk_category,
        min_risk_score is not None, max_risk_score is not None,
        hotspot_id is not None, hotspot_only,
        metric and metric.lower() == "density",
    ])

    df_ev = _get_events()
    df_loc = _get_location_risk()
    df_cs = _get_cluster_stats()

    # Pre-build district centroid lookup
    district_centroid: Dict[str, Dict[str, Optional[float]]] = {}
    if not df_ev.empty:
        grp = df_ev.groupby("victim_district").agg(
            lat=("latitude", "mean"),
            lon=("longitude", "mean"),
        ).reset_index()
        for _, r in grp.iterrows():
            lat_v = _safe_float(r["lat"])
            lon_v = _safe_float(r["lon"])
            if _is_valid_coord(lat_v, lon_v):
                district_centroid[str(r["victim_district"])] = {"lat": lat_v, "lon": lon_v}

    # Fallback to cluster stats centroids if needed
    if not df_cs.empty:
        for _, r in df_cs.iterrows():
            cid = _safe_int(r["cluster_id"])
            lat_v = _safe_float(r["latitude_centroid"])
            lon_v = _safe_float(r["longitude_centroid"])
            if cid is not None and _is_valid_coord(lat_v, lon_v):
                # also map by cluster_id if needed
                pass

    # Baseline dictionary for district risk fallbacks
    loc_risk_map: Dict[str, Dict] = {}
    if not df_loc.empty:
        for _, r in df_loc.iterrows():
            d_name = str(r["location_group"])
            loc_risk_map[d_name] = {
                "avg_risk": _safe_float(r.get("average_risk_score")),
                "max_risk": _safe_float(r.get("maximum_risk_score")),
                "event_count": _safe_int(r.get("event_count")),
                "dominant_risk_category": str(r.get("dominant_risk_category", "LOW")),
            }

    # ── Path A: Dynamic Filtered Aggregation ─────────────────────────
    if has_filters:
        if df_ev.empty:
            return {
                "type": "FeatureCollection",
                "features": [],
                "total_districts": 0,
                "metric": metric or "risk",
                "message": "No valid geographic data available.",
                "response_time_ms": round((time.time() - t0) * 1000, 1),
            }

        df = df_ev.copy()

        # Validate risk_category
        valid_risk_cats = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
        if risk_category and risk_category.upper() not in valid_risk_cats:
            raise HTTPException(status_code=422, detail=f"risk_category must be one of {sorted(valid_risk_cats)}")

        if start_time:
            try:
                st = pd.to_datetime(start_time)
                df = df[df["complaint_timestamp"] >= st]
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid start_time format. Use ISO datetime.")

        if end_time:
            try:
                et = pd.to_datetime(end_time)
                df = df[df["complaint_timestamp"] <= et]
            except Exception:
                raise HTTPException(status_code=422, detail="Invalid end_time format. Use ISO datetime.")

        if crime_category:
            df = df[df["crime_category_group"].str.upper() == crime_category.upper()]

        if crime_type:
            df = df[df["crime_type"].str.upper() == crime_type.upper()]

        if risk_category:
            df = df[df["risk_category"] == risk_category.upper()]

        if min_risk_score is not None:
            df = df[df["risk_score"].fillna(0) >= min_risk_score]

        if max_risk_score is not None:
            df = df[df["risk_score"].fillna(0) <= max_risk_score]

        if hotspot_id is not None:
            df = df[df["cluster_id"] == hotspot_id]

        if hotspot_only:
            df = df[df["cluster_id"].notna() & (df["cluster_id"] >= 0)]

        if df.empty:
            return {
                "type": "FeatureCollection",
                "features": [],
                "total_districts": 0,
                "metric": metric or "risk",
                "message": "No geographic records match the selected filters.",
                "response_time_ms": round((time.time() - t0) * 1000, 1),
            }

        # Aggregate filtered events by district
        grouped = df.groupby("victim_district")
        features = []
        counts = grouped.size()
        max_count = max(counts.max(), 1)

        for district_name, group in grouped:
            coord = district_centroid.get(str(district_name))
            if not coord or not _is_valid_coord(coord["lat"], coord["lon"]):
                continue

            cnt = len(group)
            scores = group["risk_score"].dropna()
            fallback = loc_risk_map.get(str(district_name), {})

            if not scores.empty:
                avg_risk = round(float(scores.mean()), 2)
                max_risk = round(float(scores.max()), 2)
            else:
                avg_risk = fallback.get("avg_risk", 32.5)
                max_risk = fallback.get("max_risk", 50.0)

            # Category
            if avg_risk >= 80:
                cat = "CRITICAL"
            elif avg_risk >= 60:
                cat = "HIGH"
            elif avg_risk >= 40:
                cat = "MODERATE"
            else:
                cat = "LOW"

            # Weight calculation
            if metric and metric.lower() == "density":
                # Scaled between 0.15 and 1.0 based on relative complaint volume
                w = round(min(1.0, max(0.15, cnt / max_count)), 4)
            else:
                # Scaled between 0.15 and 1.0 based on average risk score
                w = round(min(1.0, max(0.15, float(avg_risk or 0) / 100.0)), 4)

            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [coord["lon"], coord["lat"]]},
                "properties": {
                    "district": str(district_name),
                    "event_count": cnt,
                    "average_risk_score": avg_risk,
                    "maximum_risk_score": max_risk,
                    "dominant_risk_category": cat,
                    "risk_category_computed": cat,
                    "heatmap_weight": w,
                    "metric": metric or "risk",
                    "disclaimer": DISCLAIMER,
                },
            })

        return {
            "type": "FeatureCollection",
            "features": features,
            "aggregation_method": f"filtered district aggregation ({metric or 'risk'})",
            "total_districts": len(features),
            "metric": metric or "risk",
            "response_time_ms": round((time.time() - t0) * 1000, 1),
        }

    # ── Path B: Default 40-District Baseline (Contract Compliance) ──
    if df_loc.empty:
        raise HTTPException(status_code=503, detail="Location risk data not available.")

    features = []
    for _, row in df_loc.iterrows():
        district = str(row["location_group"])
        coord = district_centroid.get(district)
        if coord is None or not _is_valid_coord(coord["lat"], coord["lon"]):
            continue

        avg_risk = _safe_float(row.get("average_risk_score"))
        max_risk = _safe_float(row.get("maximum_risk_score"))

        if avg_risk is None:
            cat = "UNKNOWN"
        elif avg_risk >= 80:
            cat = "CRITICAL"
        elif avg_risk >= 60:
            cat = "HIGH"
        elif avg_risk >= 40:
            cat = "MODERATE"
        else:
            cat = "LOW"

        # Normalized weight in [0.15, 1.0] for visible yet crisp rendering
        w = round(min(1.0, max(0.15, float(avg_risk or 0) / 100.0)), 4)

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [coord["lon"], coord["lat"]]},
            "properties": {
                "district": district,
                "event_count": _safe_int(row.get("event_count")),
                "average_risk_score": avg_risk,
                "maximum_risk_score": max_risk,
                "dominant_risk_category": str(row.get("dominant_risk_category", cat)),
                "risk_category_computed": cat,
                "heatmap_weight": w,
                "metric": "risk",
                "disclaimer": DISCLAIMER,
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "aggregation_method": "district-level mean risk score (Phase 9 location_risk_summary)",
        "total_districts": len(features),
        "metric": "risk",
        "response_time_ms": round((time.time() - t0) * 1000, 1),
    }


# ==============================================================================
# GET /gis/hotspots
# ==============================================================================
@router.get(
    "/hotspots",
    summary="Phase 14 DBSCAN Hotspot GeoJSON",
    description=(
        "Returns Phase 14 DBSCAN spatial hotspot centroids as GeoJSON FeatureCollection. "
        "Includes hotspot rank, event count, risk stats, and temporal range. "
        "DBSCAN hotspots are ANALYTICAL SPATIAL CLUSTERS — not proven criminal zones."
    ),
)
async def gis_hotspots(
    status_filter: Optional[str] = Query(
        None, description="LOW_ACTIVITY|MODERATE_ACTIVITY|HIGH_ACTIVITY|CRITICAL_ACTIVITY"
    ),
    min_event_count: Optional[int] = Query(None, ge=1),
    limit: int = Query(100, ge=1, le=200),
):
    t0 = time.time()
    gj = _get_geojson_hotspots()
    df_hs = _get_hotspot_summary()
    df_cs = _get_cluster_stats()
    df_temp = _get_temporal()
    df_rh = _load_risk_hotspot_summary()

    valid_statuses = {"LOW_ACTIVITY", "MODERATE_ACTIVITY", "HIGH_ACTIVITY", "CRITICAL_ACTIVITY"}
    if status_filter and status_filter.upper() not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"status_filter must be one of {sorted(valid_statuses)}")

    # Build enriched features
    # Merge cluster_stats dominant crime into hotspot summary
    crime_map: Dict[int, str] = {}
    if not df_cs.empty:
        for _, r in df_cs.iterrows():
            crime_map[int(r["cluster_id"])] = str(r.get("dominant_crime_type", ""))

    # Temporal peak info
    peak_map: Dict[int, Dict] = {}
    if not df_temp.empty:
        for _, r in df_temp.iterrows():
            peak_map[int(r["cluster_id"])] = {
                "peak_hour": _safe_int(r.get("peak_hour_of_day")),
                "peak_dow": _safe_int(r.get("peak_day_of_week")),
                "time_span_days": _safe_int(r.get("time_span_days")),
            }

    # Risk cross-tab priority class
    pclass_map: Dict[int, str] = {}
    if not df_rh.empty:
        for _, r in df_rh.iterrows():
            pclass_map[int(r["cluster_id"])] = str(r.get("priority_class", "DENSE_UNKNOWN"))

    features = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        cid = _safe_int(props.get("cluster_id"))
        hs_status = str(props.get("hotspot_status", ""))
        ec = _safe_int(props.get("event_count"))

        # Apply filters
        if status_filter and hs_status != status_filter.upper():
            continue
        if min_event_count is not None and (ec is None or ec < min_event_count):
            continue

        enriched_props = {
            "hotspot_id": cid,
            "hotspot_rank": _safe_int(props.get("hotspot_rank")),
            "event_count": ec,
            "hotspot_status": hs_status,
            "density_metric": _safe_float(props.get("density_metric")),
            "cluster_radius_km": _safe_float(props.get("cluster_radius_km")),
            "high_risk_count": _safe_int(props.get("high_risk_count")),
            "critical_risk_count": _safe_int(props.get("critical_risk_count")),
            "withdrawal_event_count": _safe_int(props.get("withdrawal_event_count")),
            "average_risk_score": _safe_float(props.get("average_risk_score")),
            "time_range_start": str(props.get("time_range_start", "")),
            "time_range_end": str(props.get("time_range_end", "")),
            "dominant_crime_type": crime_map.get(cid, ""),
            "priority_class": pclass_map.get(cid, ""),
            "peak_hour_of_day": peak_map.get(cid, {}).get("peak_hour"),
            "time_span_days": peak_map.get(cid, {}).get("time_span_days"),
            "disclaimer": DISCLAIMER,
        }
        features.append({
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": enriched_props,
        })

    features = features[:limit]

    return {
        "type": "FeatureCollection",
        "features": features,
        "total": len(features),
        "clustering_method": "DBSCAN (haversine, eps=0.5km, min_samples=3) — Phase 14",
        "interpretation": "Analytical spatial clusters of observed complaint events. Not proof of criminal activity.",
        "response_time_ms": round((time.time() - t0) * 1000, 1),
    }


# ==============================================================================
# GET /gis/hotspots/{hotspot_id}
# ==============================================================================
@router.get(
    "/hotspots/{hotspot_id}",
    summary="Single Hotspot Detail",
    description="Returns detailed analytical information for one DBSCAN hotspot cluster.",
)
async def gis_hotspot_detail(hotspot_id: str):
    t0 = time.time()
    df_hs = _get_hotspot_summary()
    df_cs = _get_cluster_stats()
    df_temp = _get_temporal()
    df_rh = _load_risk_hotspot_summary()
    df_w = _load_withdrawal_hotspots()

    if df_hs.empty:
        raise HTTPException(status_code=503, detail="Hotspot data not available.")

    parsed_id = None
    try:
        s = str(hotspot_id).strip().upper()
        if s.startswith("HS-"):
            s = s[3:]
        parsed_id = int(s)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Invalid hotspot ID format: '{hotspot_id}'.")

    row_hs = df_hs[df_hs["cluster_id"] == parsed_id]
    if row_hs.empty:
        raise HTTPException(status_code=404, detail=f"Hotspot {hotspot_id} not found.")
    hs = row_hs.iloc[0]

    row_cs = df_cs[df_cs["cluster_id"] == parsed_id].iloc[0] if not df_cs.empty and (df_cs["cluster_id"] == parsed_id).any() else None
    row_temp = df_temp[df_temp["cluster_id"] == parsed_id].iloc[0] if not df_temp.empty and (df_temp["cluster_id"] == parsed_id).any() else None
    row_rh = df_rh[df_rh["cluster_id"] == parsed_id].iloc[0] if not df_rh.empty and (df_rh["cluster_id"] == parsed_id).any() else None

    # Withdrawal hotspot entry
    w_info: Optional[Dict] = None
    if not df_w.empty and "cluster_id" in df_w.columns:
        row_w = df_w[df_w["cluster_id"] == parsed_id]
        if not row_w.empty:
            rw = row_w.iloc[0]
            w_info = {
                "withdrawal_event_count": _safe_int(rw.get("withdrawal_event_count")),
                "average_risk_score": _safe_float(rw.get("average_risk_score")),
                "high_risk_count": _safe_int(rw.get("high_risk_count")),
            }

    # Risk distribution
    risk_dist = None
    if row_rh is not None:
        risk_dist = {
            "low": _safe_int(row_rh.get("low_risk_count")),
            "moderate": _safe_int(row_rh.get("moderate_risk_count")),
            "high": _safe_int(row_rh.get("high_risk_count")),
            "critical": _safe_int(row_rh.get("critical_risk_count")),
            "priority_class": str(row_rh.get("priority_class", "")),
        }

    result = {
        "hotspot_id": hotspot_id,
        "hotspot_rank": _safe_int(hs.get("hotspot_rank")),
        "hotspot_status": str(hs.get("hotspot_status", "")),
        "event_count": _safe_int(hs.get("event_count")),
        "density_metric": _safe_float(hs.get("density_metric")),
        "centroid_latitude": _safe_float(hs.get("latitude_centroid")),
        "centroid_longitude": _safe_float(hs.get("longitude_centroid")),
        "cluster_radius_km": _safe_float(hs.get("cluster_radius_estimate_km")),
        "average_risk_score": _safe_float(hs.get("average_risk_score")),
        "maximum_risk_score": _safe_int(hs.get("maximum_risk_score")),
        "high_risk_count": _safe_int(hs.get("high_risk_count")),
        "critical_risk_count": _safe_int(hs.get("critical_risk_count")),
        "withdrawal_event_count": _safe_int(hs.get("withdrawal_event_count")),
        "time_range_start": str(hs.get("time_range_start", "")),
        "time_range_end": str(hs.get("time_range_end", "")),
        "dominant_crime_type": str(row_cs.get("dominant_crime_type", "")) if row_cs is not None else None,
        "temporal_info": {
            "peak_hour_of_day": _safe_int(row_temp.get("peak_hour_of_day")) if row_temp is not None else None,
            "peak_day_of_week": _safe_int(row_temp.get("peak_day_of_week")) if row_temp is not None else None,
            "time_span_days": _safe_int(row_temp.get("time_span_days")) if row_temp is not None else None,
            "events_last_30_days": _safe_int(row_temp.get("events_last_30_days")) if row_temp is not None else None,
        },
        "risk_distribution": risk_dist,
        "withdrawal_hotspot_info": w_info or {"note": "No withdrawal-specific cluster data for this hotspot."},
        "disclaimer": DISCLAIMER,
        "response_time_ms": round((time.time() - t0) * 1000, 1),
    }
    return result


# ==============================================================================
# GET /gis/filters
# ==============================================================================
@router.get(
    "/filters",
    summary="Available Filter Values",
    description="Returns distinct values available for dashboard filters.",
)
async def gis_filters():
    df = _get_events()
    if df.empty:
        return {"crime_types": [], "crime_categories": [], "risk_categories": [], "districts": [], "hotspot_ids": []}

    return {
        "crime_types": sorted(df["crime_type"].dropna().unique().tolist()),
        "crime_categories": sorted(df["crime_category_group"].dropna().unique().tolist()),
        "risk_categories": ["LOW", "MODERATE", "HIGH", "CRITICAL"],
        "districts": sorted(df["victim_district"].dropna().unique().tolist()),
        "hotspot_ids": sorted(df["cluster_id"].dropna().astype(int).unique().tolist()),
        "time_range": {
            "earliest": df["complaint_timestamp"].min().isoformat() if not df["complaint_timestamp"].dropna().empty else None,
            "latest": df["complaint_timestamp"].max().isoformat() if not df["complaint_timestamp"].dropna().empty else None,
        },
        "risk_score_range": {"min": 0, "max": 100},
    }


# ==============================================================================
# GET /gis/statistics
# ==============================================================================
@router.get(
    "/statistics",
    summary="Dashboard Chart Data",
    description="Returns aggregated statistics for dashboard charts.",
)
async def gis_statistics():
    t0 = time.time()
    df = _get_events()
    df_hs = _get_hotspot_summary()

    result: Dict[str, Any] = {}

    if not df.empty:
        # Risk category distribution
        rc = df["risk_category"].value_counts()
        result["risk_category_distribution"] = {
            "LOW": int(rc.get("LOW", 0)),
            "MODERATE": int(rc.get("MODERATE", 0)),
            "HIGH": int(rc.get("HIGH", 0)),
            "CRITICAL": int(rc.get("CRITICAL", 0)),
            "no_risk_data": int(df["risk_category"].isna().sum()),
        }

        # Crime category distribution
        result["crime_category_distribution"] = {
            str(k): int(v) for k, v in df["crime_category_group"].value_counts().items()
        }

        # Crime type distribution
        result["crime_type_distribution"] = {
            str(k): int(v) for k, v in df["crime_type"].value_counts().items()
        }

        # Hourly activity (clustered events)
        clustered = df[df["cluster_id"] >= 0]
        if not clustered.empty and "event_hour" in clustered.columns:
            hour_dist = clustered["event_hour"].value_counts().sort_index()
            result["hourly_activity_in_hotspots"] = {str(h): int(c) for h, c in hour_dist.items()}

        # Risk score histogram buckets
        risk_present = df[df["risk_score"].notna()]["risk_score"]
        if not risk_present.empty:
            bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            hist, _ = pd.cut(risk_present, bins=bins, retbins=False, include_lowest=True).value_counts(sort=False).align(
                pd.Series(0, index=pd.cut(risk_present, bins=bins, include_lowest=True).cat.categories)
            )
            result["risk_score_distribution"] = {str(k): int(v) for k, v in hist.items()}

        # District activity (top 10)
        result["top_districts_by_events"] = {
            str(k): int(v)
            for k, v in df["victim_district"].value_counts().head(10).items()
        }

    if not df_hs.empty:
        # Hotspot status distribution
        hs_status = df_hs["hotspot_status"].value_counts()
        result["hotspot_status_distribution"] = {str(k): int(v) for k, v in hs_status.items()}

        # Top 10 hotspots by event count
        top_hs = df_hs.nlargest(10, "event_count")
        result["top_hotspots"] = [
            {
                "cluster_id": _safe_int(r["cluster_id"]),
                "hotspot_rank": _safe_int(r["hotspot_rank"]),
                "event_count": _safe_int(r["event_count"]),
                "hotspot_status": str(r["hotspot_status"]),
                "average_risk_score": _safe_float(r.get("average_risk_score")),
                "latitude": _safe_float(r["latitude_centroid"]),
                "longitude": _safe_float(r["longitude_centroid"]),
            }
            for _, r in top_hs.iterrows()
        ]

    result["response_time_ms"] = round((time.time() - t0) * 1000, 1)
    return result


# ==============================================================================
# GET /gis/mule-pattern-accounts
# ==============================================================================
@router.get(
    "/mule-pattern-accounts",
    summary="Mule-Account-Pattern Indicators (Rule-Based Heuristic)",
    description=(
        "Returns beneficiary accounts flagged by a lightweight rule-based fan-in heuristic. "
        "EXPLICIT DISCLAIMER: Simple heuristic indicator only — NOT a graph neural network "
        "or validated mule detection system. Does not establish account involvement in fraud."
    ),
)
async def get_mule_pattern_accounts(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    flagged_only: bool = Query(True, description="Filter to accounts with mule_pattern_flag=True"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum pattern score"),
):
    df = _get_mule_patterns()
    if df.empty:
        df = _load_mule_pattern_accounts()

    if df.empty:
        return {
            "method": MULE_PATTERN_METHOD,
            "disclaimer": MULE_PATTERN_DISCLAIMER,
            "total": 0,
            "flagged_count": 0,
            "skip": skip,
            "limit": limit,
            "items": [],
        }

    filtered = df.copy()
    if flagged_only:
        if "mule_pattern_flag" in filtered.columns:
            filtered = filtered[filtered["mule_pattern_flag"].astype(str).str.lower() == "true"]

    if min_score is not None:
        if "mule_pattern_score" in filtered.columns:
            filtered = filtered[filtered["mule_pattern_score"] >= min_score]

    total_matching = len(filtered)
    total_flagged = (
        int((df["mule_pattern_flag"].astype(str).str.lower() == "true").sum())
        if "mule_pattern_flag" in df.columns
        else 0
    )

    paged = filtered.iloc[skip : skip + limit]

    items = []
    for _, r in paged.iterrows():
        items.append({
            "account_id": str(r.get("account_id", "")),
            "distinct_source_count_72h": _safe_int(r.get("distinct_source_count_72h")),
            "distinct_source_count_total": _safe_int(r.get("distinct_source_count_total")),
            "avg_incoming_gap_hours": _safe_float(r.get("avg_incoming_gap_hours")),
            "mule_pattern_score": _safe_int(r.get("mule_pattern_score")),
            "mule_pattern_flag": bool(str(r.get("mule_pattern_flag", "")).lower() == "true"),
        })

    return {
        "method": MULE_PATTERN_METHOD,
        "disclaimer": MULE_PATTERN_DISCLAIMER,
        "total": total_matching,
        "flagged_count": total_flagged,
        "skip": skip,
        "limit": limit,
        "items": items,
    }


# ==============================================================================
# GET /gis/predicted-locations (Phase 5)
# ==============================================================================
@router.get(
    "/predicted-locations",
    summary="Predicted High-Risk Cashout Locations & ATM Mapping",
    description=(
        "Returns GeoJSON FeatureCollection or structured JSON of forecasted high-risk withdrawal clusters "
        "cross-referenced with physical ATM coordinates (ATMs_Locations.csv). "
        "Enriched with physical ATM counts within 2.5 km and 5.0 km catchments, nearest ATM IDs, coordinates, "
        "and empirical ranking priority labels."
    ),
)
async def predicted_locations(
    min_risk_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum average risk score"),
    risk_category: Optional[str] = Query(None, description="Risk tier: LOW|MODERATE|HIGH|CRITICAL"),
    radius_km: float = Query(5.0, ge=0.5, le=50.0, description="Spatial ATM search radius in km (default 5.0 km)"),
    limit: int = Query(50, ge=1, le=100, description="Max clusters to return (default 50)"),
    top_k: Optional[int] = Query(None, ge=1, le=100, description="Top-K candidate locations (alias/override for limit)"),
    format: str = Query("geojson", description="Response format: 'geojson' (default) or 'json'"),
    prediction_id: Optional[str] = Query(None, description="Optional prediction reference ID"),
):
    t0 = time.time()
    effective_limit = top_k if top_k is not None else limit
    
    from src.spatial_cashout_service import (
        check_database_mode,
        SPATIAL_DISCLAIMER,
        vectorized_haversine,
        compute_ranking_score,
    )
    db_mode, _ = check_database_mode()
    pred_ref = prediction_id or f"PRED-GIS-{int(t0)}"

    df_cs = _get_cluster_stats().copy()
    if df_cs.empty:
        df_cs = _load_cluster_stats().copy()

    if df_cs.empty:
        if format.lower() == "json":
            return {
                "status": "empty_result",
                "prediction_id": pred_ref,
                "location_source": "historical_dbscan",
                "database_mode": db_mode,
                "total_locations": 0,
                "locations": [],
                "disclaimer": SPATIAL_DISCLAIMER,
                "response_time_ms": round((time.time() - t0) * 1000, 1),
            }
        return {
            "type": "FeatureCollection",
            "features": [],
            "total_predicted_locations": 0,
            "radius_km": radius_km,
            "disclaimer": DISCLAIMER,
            "response_time_ms": round((time.time() - t0) * 1000, 1),
        }

    # Map district names to clusters from clustered events
    df_ev = _get_events()
    cluster_district_map = {}
    if not df_ev.empty and "cluster_id" in df_ev.columns and "victim_district" in df_ev.columns:
        for cid, group in df_ev.groupby("cluster_id"):
            modes = group["victim_district"].dropna()
            if not modes.empty:
                cluster_district_map[cid] = modes.value_counts().index[0]

    # Load physical ATMs
    df_atms = _load_gis_atms()
    has_atms = not df_atms.empty and "latitude" in df_atms.columns and "longitude" in df_atms.columns
    if has_atms:
        atm_lats = df_atms["latitude"].to_numpy(dtype=float)
        atm_lons = df_atms["longitude"].to_numpy(dtype=float)

    features = []
    json_locations = []
    sort_col = "average_risk_score" if "average_risk_score" in df_cs.columns else "event_count"
    df_sorted = df_cs.sort_values(by=sort_col, ascending=False)
    rank_counter = 0

    for _, r in df_sorted.iterrows():
        cid = _safe_int(r.get("cluster_id"))
        if cid is None or cid < 0:
            continue

        lat = _safe_float(r.get("latitude_centroid"))
        lon = _safe_float(r.get("longitude_centroid"))
        if lat is None or lon is None or not _is_valid_coord(lat, lon):
            continue

        avg_risk = _safe_float(r.get("average_risk_score")) or 0.0
        max_risk = _safe_float(r.get("maximum_risk_score")) or avg_risk
        avg_prob = _safe_float(r.get("average_probability")) or round(avg_risk / 100.0, 4)
        event_cnt = _safe_int(r.get("event_count")) or 0
        crime_type = str(r.get("dominant_crime_type", "FINANCIAL_FRAUD"))
        district = cluster_district_map.get(cid, "Southern Region")

        # Categorize risk tier
        if avg_risk >= 75:
            cat = "CRITICAL"
        elif avg_risk >= 50:
            cat = "HIGH"
        elif avg_risk >= 30:
            cat = "MODERATE"
        else:
            cat = "LOW"

        # Apply filters
        if min_risk_score is not None and avg_risk < min_risk_score:
            continue
        if risk_category and cat != risk_category.upper():
            continue

        rank_counter += 1

        # Spatial ATM mapping & Catchments (2.5 km and radius_km / 5.0 km)
        atm_count_in_radius = 0
        atm_count_2_5km = 0
        nearest_atm_id = None
        nearest_atm_bank = None
        nearest_atm_dist = None
        nearest_atm_lat = None
        nearest_atm_lon = None
        nearby_atms_list = []

        if has_atms:
            dists = vectorized_haversine(lat, lon, atm_lats, atm_lons)
            mask = dists <= radius_km
            atm_count_in_radius = int(mask.sum())
            atm_count_2_5km = int((dists <= 2.5).sum())

            if len(dists) > 0:
                nearest_idx = int(np.argmin(dists))
                nearest_atm_dist = round(float(dists[nearest_idx]), 3)
                nearest_row = df_atms.iloc[nearest_idx]
                nearest_atm_id = str(nearest_row.get("atm_id", ""))
                nearest_atm_bank = str(nearest_row.get("bank_id", ""))
                nearest_atm_lat = round(float(nearest_row.get("latitude")), 6)
                nearest_atm_lon = round(float(nearest_row.get("longitude")), 6)

                # Top nearby ATMs
                sorted_indices = np.argsort(dists)[:5]
                for idx in sorted_indices:
                    d_val = float(dists[idx])
                    if d_val <= radius_km * 2:
                        atm_r = df_atms.iloc[int(idx)]
                        nearby_atms_list.append({
                            "atm_id": str(atm_r.get("atm_id", "")),
                            "bank_id": str(atm_r.get("bank_id", "")),
                            "latitude": round(float(atm_r.get("latitude")), 6),
                            "longitude": round(float(atm_r.get("longitude")), 6),
                            "distance_km": round(d_val, 3),
                            "is_24x7": bool(atm_r.get("is_24x7", 0) == 1),
                            "atm_type": str(atm_r.get("atm_type", "ATM")),
                        })

        # Calculate empirical ranking score
        rank_score, rank_label = compute_ranking_score(
            distance_to_complaint_km=None,
            district_matched=True,
            historical_event_count=event_cnt,
            cluster_risk_score=avg_risk,
            atm_density_5km=atm_count_in_radius,
        )

        if format.lower() == "json":
            json_locations.append({
                "rank": rank_counter,
                "cluster_id": f"cluster-{cid}",
                "cluster_id_num": cid,
                "district": district,
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "nearest_atm_id": nearest_atm_id,
                "nearest_atm_bank": nearest_atm_bank,
                "nearest_atm_latitude": nearest_atm_lat,
                "nearest_atm_longitude": nearest_atm_lon,
                "distance_km": nearest_atm_dist,
                "catchment_radius_km": radius_km,
                "catchment_2_5km_atm_count": atm_count_2_5km,
                "catchment_5_0km_atm_count": atm_count_in_radius,
                "historical_activity_count": event_cnt,
                "risk_score": int(round(avg_risk)),
                "risk_category": cat,
                "ranking_score": rank_score,
                "ranking_label": rank_label,
                "location_source": "historical_dbscan",
                "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
            })
        else:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lon, 6), round(lat, 6)],
                },
                "properties": {
                    "rank": rank_counter,
                    "hotspot_id": f"HS-{cid:02d}",
                    "cluster_id": cid,
                    "district": district,
                    "dominant_crime_type": crime_type,
                    "average_risk_score": round(avg_risk, 2),
                    "maximum_risk_score": round(max_risk, 2),
                    "risk_category": cat,
                    "predicted_probability": round(avg_prob, 4),
                    "ranking_score": rank_score,
                    "ranking_label": rank_label,
                    "event_count": event_cnt,
                    "withdrawal_events": _safe_int(r.get("withdrawal_event_count")),
                    "atm_count_in_radius": atm_count_in_radius,
                    "catchment_2_5km_atm_count": atm_count_2_5km,
                    "catchment_5_0km_atm_count": atm_count_in_radius,
                    "search_radius_km": radius_km,
                    "nearest_atm_id": nearest_atm_id,
                    "nearest_atm_bank": nearest_atm_bank,
                    "nearest_atm_latitude": nearest_atm_lat,
                    "nearest_atm_longitude": nearest_atm_lon,
                    "nearest_atm_distance_km": nearest_atm_dist,
                    "nearby_atms": nearby_atms_list,
                    "location_source": "historical_dbscan",
                    "database_mode": db_mode,
                    "disclaimer": DISCLAIMER,
                },
            }
            features.append(feature)

        if rank_counter >= effective_limit:
            break

    if format.lower() == "json":
        return {
            "status": "success" if json_locations else "empty_result",
            "prediction_id": pred_ref,
            "location_source": "historical_dbscan",
            "database_mode": db_mode,
            "total_locations": len(json_locations),
            "locations": json_locations,
            "disclaimer": SPATIAL_DISCLAIMER,
            "response_time_ms": round((time.time() - t0) * 1000, 1),
        }

    return {
        "type": "FeatureCollection",
        "features": features,
        "total_predicted_locations": len(features),
        "radius_km": radius_km,
        "disclaimer": DISCLAIMER,
        "response_time_ms": round((time.time() - t0) * 1000, 1),
    }

