"""
Spatial Cashout Location Analytics Service
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

This service bridges model predictions (future withdrawal likelihood) with spatial
analysis (candidate physical cashout regions based on historical DBSCAN clusters
and physical ATM proximity).

CORE PRINCIPLES:
1. ML prediction = future withdrawal likelihood [0.0, 1.0].
2. Spatial analysis = potential cashout regions based on historical spatial clusters and physical ATMs.
3. Historical cluster matching is NOT direct coordinate forecasting.
4. Catchment areas (2.5 km, 5.0 km) represent spatial analysis regions, not certainty.
5. All calculations handle missing coordinates, zero-division, and boundaries gracefully.
6. Operates in PostgreSQL/PostGIS mode when available; gracefully falls back to CSV structures.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger("cybercrime.spatial_cashout_service")

# Standard Earth Mean Radius (WGS 84 / IUGG recommended)
EARTH_RADIUS_KM: float = 6371.0088

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

SPATIAL_DISCLAIMER: str = (
    "Candidate cashout locations represent historical DBSCAN hotspot clusters and physical ATM proximity "
    "patterns for authorized analytical review. Not proof of criminal activity. Does not guarantee exact "
    "physical coordinates or future ATM withdrawals."
)

# In-memory caches for rapid spatial cross-referencing
_CACHED_ATMS: Optional[pd.DataFrame] = None
_CACHED_CLUSTER_STATS: Optional[pd.DataFrame] = None
_CACHED_DISTRICT_MAP: Optional[Dict[int, str]] = None


# ==============================================================================
# 1. Coordinate Validation & Haversine Distance
# ==============================================================================

def is_valid_coordinate(lat: Optional[float], lon: Optional[float]) -> bool:
    """
    Validate that latitude and longitude are valid, finite numbers
    within standard WGS 84 geographic coordinate reference system limits.
    """
    if lat is None or lon is None:
        return False
    try:
        f_lat, f_lon = float(lat), float(lon)
        if math.isnan(f_lat) or math.isnan(f_lon) or math.isinf(f_lat) or math.isinf(f_lon):
            return False
        return -90.0 <= f_lat <= 90.0 and -180.0 <= f_lon <= 180.0
    except (TypeError, ValueError):
        return False


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two points on Earth using Haversine formula.

    Input order: (lat1, lon1, lat2, lon2)
    Units: Decimal degrees in, kilometers out.
    Boundary handling: Clips angular arguments to [-1.0, 1.0] to prevent domain errors.
    """
    if not is_valid_coordinate(lat1, lon1) or not is_valid_coordinate(lat2, lon2):
        raise ValueError(
            f"Invalid coordinate inputs: ({lat1}, {lon1}) -> ({lat2}, {lon2}). "
            "Coordinates must be finite floats within [-90, 90] and [-180, 180]."
        )

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    a_clamped = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a_clamped), math.sqrt(1.0 - a_clamped))

    return round(EARTH_RADIUS_KM * c, 3)


def vectorized_haversine(
    lat: float,
    lon: float,
    lats_arr: np.ndarray,
    lons_arr: np.ndarray,
) -> np.ndarray:
    """
    Fast vectorized Haversine distance from a single point to an array of points.
    Returns distances in kilometers.
    """
    phi1 = np.radians(lat)
    phi2 = np.radians(lats_arr)
    dphi = phi2 - phi1
    dlambda = np.radians(lons_arr) - np.radians(lon)

    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return np.round(EARTH_RADIUS_KM * c, 3)


# ==============================================================================
# 2. Data Loading & Fallback Management
# ==============================================================================

def check_database_mode() -> Tuple[str, bool]:
    """
    Check if PostgreSQL / PostGIS database is active or if CSV fallback is engaged.
    """
    try:
        from database.crud import is_db_available
        if is_db_available():
            return "postgresql_postgis", True
    except Exception:
        pass
    return "csv_fallback", False


def load_atms_dataset(reload: bool = False) -> pd.DataFrame:
    """
    Load physical ATM locations from data/raw/ATMs_Locations.csv.
    """
    global _CACHED_ATMS
    if _CACHED_ATMS is not None and not reload:
        return _CACHED_ATMS

    atm_csv = DATA_DIR / "raw" / "ATMs_Locations.csv"
    if not atm_csv.exists():
        logger.warning("ATMs_Locations.csv not found at %s. Returning empty DataFrame.", atm_csv)
        _CACHED_ATMS = pd.DataFrame()
        return _CACHED_ATMS

    try:
        df = pd.read_csv(atm_csv)
        # Verify mandatory geographic columns
        req_cols = ["atm_id", "latitude", "longitude"]
        if not all(col in df.columns for col in req_cols):
            logger.error("ATMs_Locations.csv missing required columns: %s", req_cols)
            _CACHED_ATMS = pd.DataFrame()
            return _CACHED_ATMS

        # Filter to valid coordinates only
        valid_mask = df["latitude"].notna() & df["longitude"].notna()
        df_valid = df[valid_mask].copy()
        df_valid["latitude"] = df_valid["latitude"].astype(float)
        df_valid["longitude"] = df_valid["longitude"].astype(float)
        
        # Verify ranges
        in_range = (
            (df_valid["latitude"] >= -90.0) & (df_valid["latitude"] <= 90.0) &
            (df_valid["longitude"] >= -180.0) & (df_valid["longitude"] <= 180.0)
        )
        df_valid = df_valid[in_range]
        _CACHED_ATMS = df_valid
        return _CACHED_ATMS
    except Exception as exc:
        logger.error("Failed loading ATMs_Locations.csv: %s", exc)
        _CACHED_ATMS = pd.DataFrame()
        return _CACHED_ATMS


def load_cluster_statistics(reload: bool = False) -> pd.DataFrame:
    """
    Load precomputed DBSCAN spatial cluster statistics.
    """
    global _CACHED_CLUSTER_STATS
    if _CACHED_CLUSTER_STATS is not None and not reload:
        return _CACHED_CLUSTER_STATS

    cs_csv = OUTPUTS_DIR / "phase14_cluster_statistics.csv"
    if not cs_csv.exists():
        logger.warning("phase14_cluster_statistics.csv not found at %s.", cs_csv)
        _CACHED_CLUSTER_STATS = pd.DataFrame()
        return _CACHED_CLUSTER_STATS

    try:
        df = pd.read_csv(cs_csv)
        _CACHED_CLUSTER_STATS = df
        return _CACHED_CLUSTER_STATS
    except Exception as exc:
        logger.error("Failed loading phase14_cluster_statistics.csv: %s", exc)
        _CACHED_CLUSTER_STATS = pd.DataFrame()
        return _CACHED_CLUSTER_STATS


def load_cluster_district_map(reload: bool = False) -> Dict[int, str]:
    """
    Map cluster IDs to primary district names using clustered events.
    """
    global _CACHED_DISTRICT_MAP
    if _CACHED_DISTRICT_MAP is not None and not reload:
        return _CACHED_DISTRICT_MAP

    dist_map: Dict[int, str] = {}
    events_csv = OUTPUTS_DIR / "phase14_clustered_events.csv"
    if events_csv.exists():
        try:
            df = pd.read_csv(events_csv, usecols=["cluster_id", "victim_district"])
            df = df.dropna(subset=["cluster_id", "victim_district"])
            for cid, grp in df.groupby("cluster_id"):
                cid_int = int(cid)
                if cid_int >= 0:
                    dist_map[cid_int] = grp["victim_district"].value_counts().index[0]
        except Exception as exc:
            logger.warning("Could not map clusters from clustered events: %s", exc)

    # Fallback to Areas_Master if needed
    if not dist_map:
        areas_csv = DATA_DIR / "raw" / "Areas_Master.csv"
        if areas_csv.exists():
            try:
                df_areas = pd.read_csv(areas_csv)
                if "district" in df_areas.columns:
                    unique_districts = df_areas["district"].unique()
                    for idx, d_name in enumerate(unique_districts):
                        dist_map[idx] = str(d_name)
            except Exception:
                pass

    _CACHED_DISTRICT_MAP = dist_map
    return _CACHED_DISTRICT_MAP


# ==============================================================================
# 3. Catchment & Nearest ATM Calculations
# ==============================================================================

def analyze_catchment(
    lat: float,
    lon: float,
    atms_df: Optional[pd.DataFrame] = None,
    catchment_radius_km: float = 5.0,
) -> Dict[str, Any]:
    """
    Performs catchment analysis around a geographic coordinate (e.g. cluster centroid).
    Calculates:
    - Total ATMs within the specified radius
    - Nearest physical ATM ID, bank, and exact distance
    - Top nearby ATMs with attributes
    """
    if atms_df is None:
        atms_df = load_atms_dataset()

    if atms_df.empty or not is_valid_coordinate(lat, lon):
        return {
            "catchment_radius_km": catchment_radius_km,
            "atm_count_in_radius": 0,
            "nearest_atm_id": None,
            "nearest_atm_bank": None,
            "nearest_atm_distance_km": None,
            "nearest_atm_latitude": None,
            "nearest_atm_longitude": None,
            "nearby_atms": [],
        }

    atm_lats = atms_df["latitude"].to_numpy(dtype=float)
    atm_lons = atms_df["longitude"].to_numpy(dtype=float)

    distances = vectorized_haversine(lat, lon, atm_lats, atm_lons)
    within_radius_mask = distances <= catchment_radius_km
    atm_count = int(within_radius_mask.sum())

    nearest_atm_id = None
    nearest_atm_bank = None
    nearest_dist = None
    nearest_atm_lat = None
    nearest_atm_lon = None
    nearby_atms = []

    if len(distances) > 0:
        nearest_idx = int(np.argmin(distances))
        nearest_dist = round(float(distances[nearest_idx]), 3)
        nearest_row = atms_df.iloc[nearest_idx]
        nearest_atm_id = str(nearest_row.get("atm_id", ""))
        nearest_atm_bank = str(nearest_row.get("bank_id", ""))
        nearest_atm_lat = round(float(nearest_row.get("latitude")), 6)
        nearest_atm_lon = round(float(nearest_row.get("longitude")), 6)

        # Sort top 5 within 2x catchment radius for situational awareness
        sorted_indices = np.argsort(distances)[:5]
        for idx in sorted_indices:
            d_val = float(distances[idx])
            if d_val <= catchment_radius_km * 2:
                r = atms_df.iloc[int(idx)]
                nearby_atms.append({
                    "atm_id": str(r.get("atm_id", "")),
                    "bank_id": str(r.get("bank_id", "")),
                    "latitude": round(float(r.get("latitude")), 6),
                    "longitude": round(float(r.get("longitude")), 6),
                    "distance_km": round(d_val, 3),
                    "is_24x7": bool(r.get("is_24x7", 0) == 1),
                    "atm_type": str(r.get("atm_type", "ATM")),
                })

    return {
        "catchment_radius_km": catchment_radius_km,
        "atm_count_in_radius": atm_count,
        "nearest_atm_id": nearest_atm_id,
        "nearest_atm_bank": nearest_atm_bank,
        "nearest_atm_distance_km": nearest_dist,
        "nearest_atm_latitude": nearest_atm_lat,
        "nearest_atm_longitude": nearest_atm_lon,
        "nearby_atms": nearby_atms,
    }


# ==============================================================================
# 4. Top-K Candidate Generation & Ranking
# ==============================================================================

def compute_ranking_score(
    distance_to_complaint_km: Optional[float],
    district_matched: bool,
    historical_event_count: int,
    cluster_risk_score: float,
    atm_density_5km: int,
) -> Tuple[int, str]:
    """
    Computes an empirical heuristic ranking score [0, 100] and priority tier.

    FORMULA:
    - Distance factor (0.45 weight): Proximity to complaint location (or district match proxy)
    - Risk factor (0.30 weight): Historical cluster average risk score
    - Density factor (0.25 weight): Available ATM cashout infrastructure (5 km count)

    NOTE: This is an operational prioritization heuristic, NOT a validated probability.
    """
    # 1. Distance Component (45 points max)
    if distance_to_complaint_km is not None:
        # 0 km -> 1.0, 50 km -> 0.0
        dist_factor = max(0.0, 1.0 - (distance_to_complaint_km / 50.0))
    elif district_matched:
        dist_factor = 0.85
    else:
        dist_factor = 0.20
    score_dist = dist_factor * 45.0

    # 2. Historical Risk Component (30 points max)
    risk_factor = min(1.0, max(0.0, cluster_risk_score / 100.0))
    score_risk = risk_factor * 30.0

    # 3. Density & Infrastructure Component (25 points max)
    # Assume 20 ATMs in 5 km represents saturated infrastructure
    density_factor = min(1.0, atm_density_5km / 20.0)
    score_density = density_factor * 25.0

    total_score = int(round(score_dist + score_risk + score_density))
    total_score = max(0, min(100, total_score))

    # Priority tier label
    if total_score >= 70:
        label = "HIGH_PRIORITY_CANDIDATE"
    elif total_score >= 40:
        label = "MODERATE_PRIORITY_CANDIDATE"
    else:
        label = "MONITORING_ONLY"

    return total_score, label


def get_candidate_cashout_locations(
    district: Optional[str] = None,
    complaint_lat: Optional[float] = None,
    complaint_lon: Optional[float] = None,
    prediction_time: Optional[str] = None,
    model_risk_score: Optional[int] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Identifies and ranks Top-K candidate cashout locations based on:
    1. Historical DBSCAN hotspot cluster centroids
    2. Proximity to complaint incident location or district concordance
    3. Physical ATM density (2.5 km and 5.0 km catchments)
    4. Nearest physical ATM identification

    Returns structured candidates with zero fabricated data.
    """
    if top_k <= 0:
        return []

    top_k = min(50, top_k)
    df_cs = load_cluster_statistics()
    if df_cs.empty:
        logger.warning("No cluster statistics available. Returning empty candidates.")
        return []

    df_atms = load_atms_dataset()
    dist_map = load_cluster_district_map()
    has_coords = is_valid_coordinate(complaint_lat, complaint_lon)

    t_stamp = prediction_time or datetime.now(timezone.utc).isoformat()
    db_mode, _ = check_database_mode()

    candidates = []

    for _, row in df_cs.iterrows():
        try:
            cid = int(row["cluster_id"])
            c_lat = float(row["latitude_centroid"])
            c_lon = float(row["longitude_centroid"])
        except (ValueError, TypeError, KeyError):
            continue

        if not is_valid_coordinate(c_lat, c_lon):
            continue

        c_district = dist_map.get(cid, "Regional Center")
        avg_risk = float(row.get("average_risk_score", 50.0))
        event_count = int(row.get("event_count", 0))

        # Determine risk category tier
        if avg_risk >= 80:
            cat = "CRITICAL"
        elif avg_risk >= 60:
            cat = "HIGH"
        elif avg_risk >= 40:
            cat = "MODERATE"
        else:
            cat = "LOW"

        # Haversine distance from complaint to cluster
        dist_to_comp: Optional[float] = None
        if has_coords:
            dist_to_comp = haversine_distance(complaint_lat, complaint_lon, c_lat, c_lon)

        district_matched = bool(
            district and c_district and str(district).strip().lower() == str(c_district).strip().lower()
        )

        # Catchment analysis at 2.5 km and 5.0 km
        catchment_2_5 = analyze_catchment(c_lat, c_lon, df_atms, catchment_radius_km=2.5)
        catchment_5_0 = analyze_catchment(c_lat, c_lon, df_atms, catchment_radius_km=5.0)

        atm_2_5_count = catchment_2_5["atm_count_in_radius"]
        atm_5_0_count = catchment_5_0["atm_count_in_radius"]
        nearest_atm_id = catchment_5_0["nearest_atm_id"]
        nearest_atm_bank = catchment_5_0["nearest_atm_bank"]
        nearest_atm_dist = catchment_5_0["nearest_atm_distance_km"]
        nearest_atm_lat = catchment_5_0["nearest_atm_latitude"]
        nearest_atm_lon = catchment_5_0["nearest_atm_longitude"]

        # Compute empirical ranking score
        ranking_score, ranking_label = compute_ranking_score(
            distance_to_complaint_km=dist_to_comp,
            district_matched=district_matched,
            historical_event_count=event_count,
            cluster_risk_score=avg_risk,
            atm_density_5km=atm_5_0_count,
        )

        candidates.append({
            "cluster_id": cid,
            "district": c_district,
            "latitude": round(c_lat, 6),
            "longitude": round(c_lon, 6),
            "distance_to_complaint_km": dist_to_comp,
            "nearest_atm_id": nearest_atm_id,
            "nearest_atm_bank": nearest_atm_bank,
            "nearest_atm_distance_km": nearest_atm_dist,
            "nearest_atm_latitude": nearest_atm_lat,
            "nearest_atm_longitude": nearest_atm_lon,
            "catchment_2_5km_atm_count": atm_2_5_count,
            "catchment_5_0km_atm_count": atm_5_0_count,
            "historical_event_count": event_count,
            "risk_score": int(round(avg_risk)),
            "risk_category": cat,
            "ranking_score": ranking_score,
            "ranking_label": ranking_label,
            "district_matched": district_matched,
            "location_source": "historical_dbscan",
            "prediction_timestamp": t_stamp,
            "database_mode": db_mode,
        })

    # Sort ordering:
    # 1. District concordance (exact match first)
    # 2. Distance to complaint (if coordinates available)
    # 3. Ranking score descending
    def _rank_key(item: Dict[str, Any]) -> Tuple[int, float, int]:
        match_tier = 0 if item["district_matched"] else 1
        d_val = item["distance_to_complaint_km"] if item["distance_to_complaint_km"] is not None else 9999.0
        r_val = -item["ranking_score"]
        return (match_tier, d_val, r_val)

    candidates.sort(key=_rank_key)

    # Assign 1-indexed ranks to Top-K
    top_results = []
    for idx, c in enumerate(candidates[:top_k], start=1):
        c_copy = dict(c)
        c_copy["rank"] = idx
        top_results.append(c_copy)

    return top_results


# ==============================================================================
# 5. GeoJSON and Structured Response Formatters
# ==============================================================================

def format_candidates_as_geojson(
    candidates: List[Dict[str, Any]],
    search_radius_km: float = 5.0,
) -> Dict[str, Any]:
    """
    Format candidates into a standard GeoJSON FeatureCollection with rich analytical properties.
    Maintains 100% backward compatibility for existing GIS map frontends.
    """
    features = []
    for c in candidates:
        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [c["longitude"], c["latitude"]],
            },
            "properties": {
                "rank": c["rank"],
                "hotspot_id": f"HS-{c['cluster_id']:02d}",
                "cluster_id": c["cluster_id"],
                "district": c["district"],
                "average_risk_score": c["risk_score"],
                "risk_category": c["risk_category"],
                "predicted_probability": round(c["risk_score"] / 100.0, 4),
                "ranking_score": c["ranking_score"],
                "ranking_label": c["ranking_label"],
                "atm_count_in_radius": c["catchment_5_0km_atm_count"],
                "catchment_2_5km_atm_count": c["catchment_2_5km_atm_count"],
                "catchment_5_0km_atm_count": c["catchment_5_0km_atm_count"],
                "nearest_atm_id": c["nearest_atm_id"],
                "nearest_atm_bank": c["nearest_atm_bank"],
                "nearest_atm_distance_km": c["nearest_atm_distance_km"],
                "nearest_atm_latitude": c["nearest_atm_latitude"],
                "nearest_atm_longitude": c["nearest_atm_longitude"],
                "distance_to_complaint_km": c["distance_to_complaint_km"],
                "historical_event_count": c["historical_event_count"],
                "location_source": c["location_source"],
                "disclaimer": SPATIAL_DISCLAIMER,
            },
        }
        features.append(feat)

    return {
        "type": "FeatureCollection",
        "features": features,
        "total_predicted_locations": len(features),
        "radius_km": search_radius_km,
        "disclaimer": SPATIAL_DISCLAIMER,
    }


def format_candidates_as_json_response(
    candidates: List[Dict[str, Any]],
    prediction_id: str,
    status: str = "success",
) -> Dict[str, Any]:
    """
    Format candidates into the structured Top-K JSON response specified in Step 8:
    {
      "status": "success",
      "prediction_id": "PRED-...",
      "location_source": "historical_dbscan",
      "database_mode": "csv_fallback",
      "locations": [ ... ],
      "disclaimer": "..."
    }
    """
    loc_items = []
    for c in candidates:
        loc_items.append({
            "rank": c["rank"],
            "cluster_id": f"cluster-{c['cluster_id']}",
            "cluster_id_num": c["cluster_id"],
            "district": c["district"],
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "nearest_atm_id": c["nearest_atm_id"],
            "nearest_atm_bank": c["nearest_atm_bank"],
            "nearest_atm_latitude": c["nearest_atm_latitude"],
            "nearest_atm_longitude": c["nearest_atm_longitude"],
            "distance_km": c["nearest_atm_distance_km"],
            "distance_to_complaint_km": c["distance_to_complaint_km"],
            "catchment_radius_km": 5.0,
            "catchment_2_5km_atm_count": c["catchment_2_5km_atm_count"],
            "catchment_5_0km_atm_count": c["catchment_5_0km_atm_count"],
            "historical_activity_count": c["historical_event_count"],
            "risk_score": c["risk_score"],
            "risk_category": c["risk_category"],
            "ranking_score": c["ranking_score"],
            "ranking_label": c["ranking_label"],
            "location_source": c["location_source"],
            "prediction_timestamp": c["prediction_timestamp"],
        })

    db_mode, _ = check_database_mode()
    return {
        "status": status,
        "prediction_id": prediction_id,
        "location_source": "historical_dbscan",
        "database_mode": db_mode,
        "total_locations": len(loc_items),
        "locations": loc_items,
        "disclaimer": SPATIAL_DISCLAIMER,
    }
