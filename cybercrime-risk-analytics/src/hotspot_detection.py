"""
Phase 14 — DBSCAN Spatial Hotspot Detection
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Identifies geographical areas with unusually dense concentrations of cybercrime events
using the DBSCAN algorithm with haversine distance on WGS 84 coordinates.

IMPORTANT:
- No model retraining
- No frontend / dashboard / alerts
- DBSCAN is unsupervised spatial clustering only
- Hotspot ranks are analytical; they are NOT proof of criminal activity

Usage:
    python src/hotspot_detection.py

Output directory:
    outputs/phase14_*
    outputs/figures/phase14_*
"""
from __future__ import annotations

import json
import logging
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("phase14.hotspot_detection")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EARTH_RADIUS_KM = 6371.0088

# Columns to load (safe, no PII)
SAFE_COLUMNS = [
    "case_id", "complaint_timestamp", "crime_type", "fraud_amount",
    "victim_state", "victim_district", "latitude", "longitude",
    "is_linked_to_withdrawal", "future_withdrawal",
    "event_hour", "event_day_of_week", "crime_category_group",
    "risk_score",  # from phase9 merge (if available)
    "risk_category",
    "predicted_probability",
]

# DBSCAN configurations to evaluate
PARAM_GRID = [
    {"eps_km": 0.5, "min_samples": 3},
    {"eps_km": 0.5, "min_samples": 5},
    {"eps_km": 1.0, "min_samples": 3},
    {"eps_km": 1.0, "min_samples": 5},
    {"eps_km": 1.0, "min_samples": 10},
    {"eps_km": 2.0, "min_samples": 5},
    {"eps_km": 2.0, "min_samples": 10},
]


# ==============================================================================
# 1. Data Loading
# ==============================================================================

def load_spatial_data() -> Tuple[pd.DataFrame, str]:
    """
    Load cybercrime spatial data.
    Prefers: targeted_cybercrime_data.csv with Phase 9 risk scores joined.
    Falls back: CSV only.
    Returns (DataFrame, source_description).
    """
    # Primary: CSV
    csv_path = DATA_DIR / "targeted_cybercrime_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Primary data source not found: {csv_path}")

    load_cols = [
        "case_id", "complaint_timestamp", "crime_type", "fraud_amount",
        "victim_state", "victim_district", "latitude", "longitude",
        "is_linked_to_withdrawal", "future_withdrawal",
        "event_hour", "event_day_of_week", "crime_category_group",
    ]
    df = pd.read_csv(csv_path, usecols=[c for c in load_cols if c in pd.read_csv(csv_path, nrows=0).columns])
    df["complaint_timestamp"] = pd.to_datetime(df["complaint_timestamp"], errors="coerce")

    # Try joining Phase 9 risk scores (1500 test set predictions)
    risk_path = OUTPUTS_DIR / "phase9_risk_scores.csv"
    if risk_path.exists():
        df9 = pd.read_csv(risk_path)[["case_id", "predicted_probability", "risk_score", "risk_category"]]
        df = df.merge(df9, on="case_id", how="left")
        logger.info(f"Phase 9 risk scores joined: {df['risk_score'].notna().sum()} / {len(df)} records have risk data.")
    else:
        df["predicted_probability"] = np.nan
        df["risk_score"] = np.nan
        df["risk_category"] = np.nan
        logger.warning("Phase 9 risk scores not found. Risk columns will be NaN.")

    source = f"CSV: {csv_path.name} ({len(df)} rows)"
    logger.info(f"Data loaded from {source}")
    return df, source


# ==============================================================================
# 2. Coordinate Validation
# ==============================================================================

def validate_coordinates(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Validate geographic coordinates strictly within WGS 84 bounds.
    Returns (valid_df, validation_stats).
    """
    total = len(df)

    lat_null = df["latitude"].isna()
    lon_null = df["longitude"].isna()
    missing = (lat_null | lon_null).sum()

    valid_lat = (df["latitude"] >= -90.0) & (df["latitude"] <= 90.0)
    valid_lon = (df["longitude"] >= -180.0) & (df["longitude"] <= 180.0)
    invalid = (~lat_null & ~lon_null & ~(valid_lat & valid_lon)).sum()
    usable = (~lat_null & ~lon_null & valid_lat & valid_lon).sum()

    stats = {
        "total_records": total,
        "records_with_coordinates": int(usable + invalid),
        "missing_coordinates": int(missing),
        "invalid_coordinates": int(invalid),
        "usable_points": int(usable),
    }

    valid_df = df[~lat_null & ~lon_null & valid_lat & valid_lon].copy()
    logger.info(f"Coordinate validation: {usable}/{total} usable points ({missing} missing, {invalid} invalid)")
    return valid_df, stats


# ==============================================================================
# 3. Haversine Coordinate Preparation
# ==============================================================================

def prepare_coordinates(df: pd.DataFrame) -> np.ndarray:
    """
    Convert latitude/longitude to radians for haversine distance.
    Returns array of shape (N, 2) with [lat_rad, lon_rad].
    """
    coords = np.radians(df[["latitude", "longitude"]].values.astype(np.float64))
    return coords


def km_to_radians(km: float) -> float:
    """Convert distance in km to radians using Earth radius."""
    return km / EARTH_RADIUS_KM


# ==============================================================================
# 4. DBSCAN Parameter Evaluation
# ==============================================================================

def run_dbscan(coords_rad: np.ndarray, eps_km: float, min_samples: int) -> np.ndarray:
    """
    Run DBSCAN with haversine metric on radian coordinates.
    eps is converted from km to radians.
    Returns array of cluster labels (-1 = noise).
    """
    eps_rad = km_to_radians(eps_km)
    db = DBSCAN(
        eps=eps_rad,
        min_samples=min_samples,
        algorithm="ball_tree",
        metric="haversine",
    )
    labels = db.fit_predict(coords_rad)
    return labels


def evaluate_parameters(df_valid: pd.DataFrame, coords_rad: np.ndarray) -> pd.DataFrame:
    """
    Evaluate DBSCAN across the parameter grid.
    Returns a DataFrame with results for each configuration.
    """
    results = []
    for params in PARAM_GRID:
        eps_km = params["eps_km"]
        min_s = params["min_samples"]
        labels = run_dbscan(coords_rad, eps_km=eps_km, min_samples=min_s)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_count = int((labels == -1).sum())
        total = len(labels)
        noise_pct = round(noise_count / total * 100, 2)

        if n_clusters > 0:
            cluster_sizes = pd.Series(labels[labels >= 0]).value_counts()
            largest = int(cluster_sizes.max())
            avg_size = round(float(cluster_sizes.mean()), 1)
        else:
            largest = 0
            avg_size = 0.0

        # Status assessment
        if n_clusters == 0:
            status = "NO_CLUSTERS"
        elif n_clusters == 1 and noise_pct < 10:
            status = "ONE_BIG_CLUSTER"
        elif noise_pct > 80:
            status = "EXCESSIVE_NOISE"
        elif n_clusters >= 2 and 10 <= noise_pct <= 70:
            status = "ACCEPTABLE"
        else:
            status = "REVIEW_NEEDED"

        results.append({
            "eps_km": eps_km,
            "min_samples": min_s,
            "cluster_count": n_clusters,
            "noise_count": noise_count,
            "noise_percentage": noise_pct,
            "largest_cluster_size": largest,
            "average_cluster_size": avg_size,
            "status": status,
            "notes": f"eps={eps_km}km ({km_to_radians(eps_km):.6f} rad), min_samples={min_s}",
        })
        logger.info(f"eps={eps_km}km min_samples={min_s}: {n_clusters} clusters, {noise_pct}% noise")

    return pd.DataFrame(results)


def select_dbscan_parameters(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Select final DBSCAN parameters based on:
    - Multiple clusters (not just 1)
    - Noise percentage between 10–70%
    - Cluster sizes that are geographically meaningful
    Returns the selected parameter dict with rationale.
    """
    # Prefer 'ACCEPTABLE' rows, then 'REVIEW_NEEDED'
    for status in ["ACCEPTABLE", "REVIEW_NEEDED"]:
        candidates = results_df[results_df["status"] == status]
        if not candidates.empty:
            # Among acceptable, prefer largest cluster_count with reasonable noise
            best = candidates.sort_values(
                ["cluster_count", "noise_percentage"],
                ascending=[False, True]
            ).iloc[0]
            return {
                "eps_km": float(best["eps_km"]),
                "min_samples": int(best["min_samples"]),
                "cluster_count": int(best["cluster_count"]),
                "noise_count": int(best["noise_count"]),
                "noise_percentage": float(best["noise_percentage"]),
                "status": best["status"],
                "rationale": (
                    f"Selected eps={best['eps_km']}km min_samples={best['min_samples']} "
                    f"because it produces {best['cluster_count']} meaningful clusters "
                    f"with {best['noise_percentage']:.1f}% noise — geographically interpretable "
                    f"at ~{best['eps_km']} km neighbourhood radius."
                ),
            }
    # Fallback: use first config
    first = results_df.iloc[0]
    return {
        "eps_km": float(first["eps_km"]),
        "min_samples": int(first["min_samples"]),
        "cluster_count": int(first["cluster_count"]),
        "noise_count": int(first["noise_count"]),
        "noise_percentage": float(first["noise_percentage"]),
        "status": first["status"],
        "rationale": "Fallback to first configuration; no configuration met optimal criteria.",
    }


# ==============================================================================
# 5. Cluster Statistics
# ==============================================================================

def calculate_cluster_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-cluster statistics including centroid, bounding box, radius,
    temporal range, crime dominance, risk metrics, and withdrawal counts.
    """
    stats = []
    clusters = sorted([c for c in df["cluster_id"].unique() if c >= 0])

    for cid in clusters:
        grp = df[df["cluster_id"] == cid]

        lat_c = float(grp["latitude"].mean())
        lon_c = float(grp["longitude"].mean())

        # Estimate cluster radius as max distance from centroid (approximate)
        lat_rad = np.radians(grp["latitude"].values)
        lon_rad = np.radians(grp["longitude"].values)
        c_lat_r = np.radians(lat_c)
        c_lon_r = np.radians(lon_c)
        dlat = lat_rad - c_lat_r
        dlon = lon_rad - c_lon_r
        a = np.sin(dlat / 2) ** 2 + np.cos(c_lat_r) * np.cos(lat_rad) * np.sin(dlon / 2) ** 2
        dist_km = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
        radius_estimate = round(float(dist_km.max()), 3)

        # Temporal
        ts = grp["complaint_timestamp"].dropna()
        time_start = str(ts.min()) if not ts.empty else "N/A"
        time_end = str(ts.max()) if not ts.empty else "N/A"

        # Dominant crime
        if "crime_type" in grp.columns:
            dom_crime = grp["crime_type"].value_counts().index[0]
        else:
            dom_crime = "N/A"

        # Risk metrics (only where available)
        risk_present = grp["risk_score"].notna()
        avg_risk = round(float(grp.loc[risk_present, "risk_score"].mean()), 2) if risk_present.any() else None
        max_risk = int(grp.loc[risk_present, "risk_score"].max()) if risk_present.any() else None
        avg_prob = round(float(grp.loc[risk_present, "predicted_probability"].mean()), 4) if risk_present.any() else None
        high_risk = int((grp["risk_category"] == "HIGH").sum()) if "risk_category" in grp.columns else 0
        crit_risk = int((grp["risk_category"] == "CRITICAL").sum()) if "risk_category" in grp.columns else 0

        # Withdrawal counts
        if "future_withdrawal" in grp.columns:
            w_count = int(grp["future_withdrawal"].sum())
        else:
            w_count = 0

        stats.append({
            "cluster_id": cid,
            "event_count": len(grp),
            "latitude_centroid": round(lat_c, 6),
            "longitude_centroid": round(lon_c, 6),
            "min_latitude": round(float(grp["latitude"].min()), 6),
            "max_latitude": round(float(grp["latitude"].max()), 6),
            "min_longitude": round(float(grp["longitude"].min()), 6),
            "max_longitude": round(float(grp["longitude"].max()), 6),
            "cluster_radius_estimate_km": radius_estimate,
            "time_range_start": time_start,
            "time_range_end": time_end,
            "dominant_crime_type": dom_crime,
            "average_risk_score": avg_risk,
            "maximum_risk_score": max_risk,
            "average_probability": avg_prob,
            "high_risk_count": high_risk,
            "critical_risk_count": crit_risk,
            "withdrawal_event_count": w_count,
        })

    return pd.DataFrame(stats)


# ==============================================================================
# 6. Hotspot Metrics & Ranking
# ==============================================================================

def calculate_hotspot_metrics(cluster_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Compute density metric and assign hotspot status category.

    Density metric = events per km² estimated area.
    If radius is 0 or very small, use point-density proxy.

    Hotspot rank is purely analytical — NOT proof of criminal activity.
    """
    df = cluster_stats.copy()

    # Estimated area = pi * r^2
    df["estimated_area_km2"] = np.pi * df["cluster_radius_estimate_km"] ** 2
    df["estimated_area_km2"] = df["estimated_area_km2"].replace(0, np.nan)
    df["density_metric"] = (df["event_count"] / df["estimated_area_km2"]).round(4)

    # Where area is too small to be meaningful, use event_count as proxy
    df.loc[df["cluster_radius_estimate_km"] < 0.01, "density_metric"] = df["event_count"] * 1000.0

    # Hotspot status thresholds (based on event count in cluster)
    total_events = df["event_count"].sum()
    p75 = df["event_count"].quantile(0.75)
    p50 = df["event_count"].quantile(0.50)

    def status(row):
        ec = row["event_count"]
        if ec >= p75 * 1.5:
            return "CRITICAL_ACTIVITY"
        elif ec >= p75:
            return "HIGH_ACTIVITY"
        elif ec >= p50:
            return "MODERATE_ACTIVITY"
        return "LOW_ACTIVITY"

    df["hotspot_status"] = df.apply(status, axis=1)

    # Rank by density_metric descending, then event_count
    df["hotspot_rank"] = df["density_metric"].rank(ascending=False, method="min").astype(int)
    df = df.sort_values("hotspot_rank")

    return df


def generate_hotspot_summary(cluster_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Format the hotspot summary output CSV.
    """
    cols = [
        "hotspot_rank", "cluster_id", "event_count", "density_metric",
        "high_risk_count", "critical_risk_count", "withdrawal_event_count",
        "average_risk_score", "maximum_risk_score",
        "latitude_centroid", "longitude_centroid",
        "cluster_radius_estimate_km", "estimated_area_km2",
        "time_range_start", "time_range_end", "hotspot_status",
    ]
    available = [c for c in cols if c in cluster_metrics.columns]
    return cluster_metrics[available].copy()


# ==============================================================================
# 7. Temporal Analysis
# ==============================================================================

def temporal_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze temporal distribution of events per cluster.
    """
    rows = []
    clusters = sorted([c for c in df["cluster_id"].unique() if c >= 0])

    for cid in clusters:
        grp = df[df["cluster_id"] == cid]

        hour_dist = grp["event_hour"].value_counts().sort_index() if "event_hour" in grp.columns else pd.Series()
        dow_dist = grp["event_day_of_week"].value_counts().sort_index() if "event_day_of_week" in grp.columns else pd.Series()

        peak_hour = int(hour_dist.idxmax()) if not hour_dist.empty else None
        peak_dow = int(dow_dist.idxmax()) if not dow_dist.empty else None

        ts = grp["complaint_timestamp"].dropna()
        if not ts.empty:
            time_span_days = (ts.max() - ts.min()).days
        else:
            time_span_days = None

        rows.append({
            "cluster_id": cid,
            "event_count": len(grp),
            "peak_hour_of_day": peak_hour,
            "peak_day_of_week": peak_dow,
            "time_range_start": str(ts.min()) if not ts.empty else "N/A",
            "time_range_end": str(ts.max()) if not ts.empty else "N/A",
            "time_span_days": time_span_days,
            "events_last_30_days": int((ts >= ts.max() - pd.Timedelta(days=30)).sum()) if not ts.empty else 0,
            "hour_distribution": str(dict(hour_dist.head(5))) if not hour_dist.empty else "{}",
        })

    return pd.DataFrame(rows)


# ==============================================================================
# 8. Withdrawal-Specific Hotspots
# ==============================================================================

def analyze_withdrawal_hotspots(df: pd.DataFrame, coords_rad: np.ndarray, eps_km: float, min_samples: int) -> pd.DataFrame:
    """
    Run DBSCAN specifically on records with future_withdrawal == 1.
    """
    if "future_withdrawal" not in df.columns or df["future_withdrawal"].sum() < min_samples:
        logger.warning("Insufficient withdrawal events for separate hotspot analysis.")
        return pd.DataFrame([{
            "cluster_id": "N/A",
            "withdrawal_event_count": 0,
            "centroid_latitude": None,
            "centroid_longitude": None,
            "time_range_start": "N/A",
            "time_range_end": "N/A",
            "average_risk_score": None,
            "high_risk_count": 0,
            "critical_risk_count": 0,
            "note": "Insufficient withdrawal events for separate DBSCAN analysis.",
        }])

    df_w = df[df["future_withdrawal"] == 1].copy()
    w_coords = np.radians(df_w[["latitude", "longitude"]].values.astype(np.float64))
    w_labels = run_dbscan(w_coords, eps_km=eps_km, min_samples=min_samples)
    df_w["w_cluster_id"] = w_labels

    rows = []
    for cid in sorted(set(w_labels)):
        if cid < 0:
            continue
        grp = df_w[df_w["w_cluster_id"] == cid]
        ts = grp["complaint_timestamp"].dropna()
        risk_present = grp["risk_score"].notna()
        rows.append({
            "cluster_id": cid,
            "withdrawal_event_count": len(grp),
            "centroid_latitude": round(float(grp["latitude"].mean()), 6),
            "centroid_longitude": round(float(grp["longitude"].mean()), 6),
            "time_range_start": str(ts.min()) if not ts.empty else "N/A",
            "time_range_end": str(ts.max()) if not ts.empty else "N/A",
            "average_risk_score": round(float(grp.loc[risk_present, "risk_score"].mean()), 2) if risk_present.any() else None,
            "high_risk_count": int((grp["risk_category"] == "HIGH").sum()),
            "critical_risk_count": int((grp["risk_category"] == "CRITICAL").sum()),
        })

    if not rows:
        rows.append({
            "cluster_id": "N/A",
            "withdrawal_event_count": int(df_w["future_withdrawal"].sum()),
            "centroid_latitude": None,
            "centroid_longitude": None,
            "time_range_start": "N/A",
            "time_range_end": "N/A",
            "average_risk_score": None,
            "high_risk_count": 0,
            "critical_risk_count": 0,
            "note": "No withdrawal clusters formed at selected DBSCAN parameters.",
        })

    logger.info(f"Withdrawal-specific DBSCAN: {len(rows)} clusters from {len(df_w)} withdrawal events.")
    return pd.DataFrame(rows)


# ==============================================================================
# 9. Risk × Hotspot Cross-Tab
# ==============================================================================

def risk_hotspot_cross_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cross-tabulate DBSCAN cluster_id against XGBoost risk_category.
    Hotspot rank × model risk = priority analytical area classification.
    """
    risk_present = df["risk_category"].notna()
    if not risk_present.any():
        logger.warning("No Phase 9 risk scores available for risk × hotspot analysis.")
        return pd.DataFrame()

    df_r = df[risk_present & df["cluster_id"].ge(0)].copy()
    if df_r.empty:
        return pd.DataFrame()

    rows = []
    for cid in sorted(df_r["cluster_id"].unique()):
        grp = df_r[df_r["cluster_id"] == cid]
        cat_counts = grp["risk_category"].value_counts().to_dict()
        rows.append({
            "cluster_id": cid,
            "events_with_risk_data": len(grp),
            "low_risk_count": cat_counts.get("LOW", 0),
            "moderate_risk_count": cat_counts.get("MODERATE", 0),
            "high_risk_count": cat_counts.get("HIGH", 0),
            "critical_risk_count": cat_counts.get("CRITICAL", 0),
            "average_risk_score": round(float(grp["risk_score"].mean()), 2),
            "average_probability": round(float(grp["predicted_probability"].mean()), 4),
            "priority_class": (
                "DENSE_CRITICAL" if cat_counts.get("CRITICAL", 0) > 0 else
                "DENSE_HIGH" if cat_counts.get("HIGH", 0) > 0 else
                "DENSE_MODERATE" if cat_counts.get("MODERATE", 0) > 0 else
                "DENSE_LOW"
            ),
        })
    return pd.DataFrame(rows)


# ==============================================================================
# 10. GeoJSON Output
# ==============================================================================

def generate_geojson(cluster_stats: pd.DataFrame, hotspot_metrics: pd.DataFrame) -> dict:
    """
    Generate a valid GeoJSON FeatureCollection with Point features
    for each hotspot centroid. Only safe analytical metadata is included.
    No raw complaint records or PII.
    """
    features = []
    for _, row in hotspot_metrics.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    float(row["longitude_centroid"]),
                    float(row["latitude_centroid"]),
                ],
            },
            "properties": {
                "cluster_id": int(row["cluster_id"]),
                "hotspot_rank": int(row["hotspot_rank"]),
                "event_count": int(row["event_count"]),
                "hotspot_status": str(row["hotspot_status"]),
                "density_metric": float(row["density_metric"]) if pd.notna(row["density_metric"]) else None,
                "cluster_radius_km": float(row["cluster_radius_estimate_km"]),
                "high_risk_count": int(row.get("high_risk_count", 0)),
                "critical_risk_count": int(row.get("critical_risk_count", 0)),
                "withdrawal_event_count": int(row.get("withdrawal_event_count", 0)),
                "average_risk_score": float(row["average_risk_score"]) if pd.notna(row.get("average_risk_score")) else None,
                "time_range_start": str(row.get("time_range_start", "")),
                "time_range_end": str(row.get("time_range_end", "")),
                "disclaimer": (
                    "Analytical spatial cluster only. Does not constitute proof of "
                    "criminal activity, individual guilt, or ATM compromise."
                ),
            },
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project": "Cybercrime Predictive Analytics Framework",
            "problem_statement_id": "26184",
            "phase": 14,
            "total_hotspots": len(features),
            "coordinate_system": "WGS 84 (EPSG:4326)",
            "geometry": "Point (centroid of DBSCAN cluster)",
        },
        "features": features,
    }


# ==============================================================================
# 11. PostGIS Hotspot Table
# ==============================================================================

def store_hotspots_in_postgis(hotspot_metrics: pd.DataFrame) -> bool:
    """
    Store hotspot centroids in PostgreSQL cybercrime_hotspots table.
    Gracefully skips if database is not available.
    """
    try:
        import sys
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from database.connection import engine, check_database_health, Base
        from sqlalchemy import Column, Integer, Float, String, Text, DateTime, text
        from geoalchemy2 import Geometry
        from sqlalchemy.orm import declarative_base
        from sqlalchemy.ext.declarative import DeclarativeMeta

        health = check_database_health()
        if health["status"] != "connected":
            logger.warning("PostGIS unavailable — skipping hotspot table creation.")
            return False

        with engine.connect() as conn:
            # Create table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cybercrime_hotspots (
                    id SERIAL PRIMARY KEY,
                    cluster_id INTEGER NOT NULL,
                    hotspot_rank INTEGER,
                    event_count INTEGER,
                    hotspot_status VARCHAR(32),
                    density_metric DOUBLE PRECISION,
                    centroid_latitude DOUBLE PRECISION,
                    centroid_longitude DOUBLE PRECISION,
                    location GEOMETRY(Point, 4326),
                    cluster_radius_km DOUBLE PRECISION,
                    high_risk_count INTEGER DEFAULT 0,
                    critical_risk_count INTEGER DEFAULT 0,
                    withdrawal_event_count INTEGER DEFAULT 0,
                    average_risk_score DOUBLE PRECISION,
                    time_range_start TIMESTAMP,
                    time_range_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_cybercrime_hotspots_location
                ON cybercrime_hotspots USING GIST (location);
            """))
            conn.execute(text("TRUNCATE cybercrime_hotspots;"))
            conn.commit()

            for _, row in hotspot_metrics.iterrows():
                lat = float(row["latitude_centroid"])
                lon = float(row["longitude_centroid"])
                try:
                    ts_start = pd.to_datetime(row.get("time_range_start"))
                except Exception:
                    ts_start = None
                try:
                    ts_end = pd.to_datetime(row.get("time_range_end"))
                except Exception:
                    ts_end = None

                conn.execute(text("""
                    INSERT INTO cybercrime_hotspots
                    (cluster_id, hotspot_rank, event_count, hotspot_status, density_metric,
                     centroid_latitude, centroid_longitude, location,
                     cluster_radius_km, high_risk_count, critical_risk_count,
                     withdrawal_event_count, average_risk_score,
                     time_range_start, time_range_end)
                    VALUES
                    (:cid, :rank, :ec, :status, :density,
                     :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                     :radius, :hrc, :crc, :wc, :avg_risk,
                     :ts_start, :ts_end)
                """), {
                    "cid": int(row["cluster_id"]),
                    "rank": int(row["hotspot_rank"]),
                    "ec": int(row["event_count"]),
                    "status": str(row["hotspot_status"]),
                    "density": float(row["density_metric"]) if pd.notna(row["density_metric"]) else None,
                    "lat": lat,
                    "lon": lon,
                    "radius": float(row["cluster_radius_estimate_km"]),
                    "hrc": int(row.get("high_risk_count", 0)),
                    "crc": int(row.get("critical_risk_count", 0)),
                    "wc": int(row.get("withdrawal_event_count", 0)),
                    "avg_risk": float(row["average_risk_score"]) if pd.notna(row.get("average_risk_score")) else None,
                    "ts_start": ts_start,
                    "ts_end": ts_end,
                })
            conn.commit()

        logger.info(f"Stored {len(hotspot_metrics)} hotspots in cybercrime_hotspots PostGIS table.")
        return True

    except Exception as e:
        logger.warning(f"PostGIS hotspot storage skipped: {e}")
        return False


# ==============================================================================
# 12. Visualizations
# ==============================================================================

def generate_visualizations(df: pd.DataFrame, hotspot_metrics: pd.DataFrame, selected_params: dict) -> None:
    """Generate all Phase 14 diagnostic plots."""

    cluster_ids = df["cluster_id"].values
    lats = df["latitude"].values
    lons = df["longitude"].values

    unique_clusters = sorted(set(cluster_ids[cluster_ids >= 0]))
    n_clusters = len(unique_clusters)

    try:
        cmap = matplotlib.colormaps["tab20"].resampled(max(n_clusters, 1))
    except AttributeError:
        cmap = plt.cm.get_cmap("tab20", max(n_clusters, 1))  # fallback for older matplotlib

    # ---- Plot 1: DBSCAN Cluster Map ----
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    noise_mask = cluster_ids == -1
    ax.scatter(lons[noise_mask], lats[noise_mask],
               s=5, c="#666666", alpha=0.3, label="Noise", rasterized=True)

    for i, cid in enumerate(unique_clusters):
        mask = cluster_ids == cid
        ax.scatter(lons[mask], lats[mask],
                   s=18, c=[cmap(i)], alpha=0.8, rasterized=True)

    # Mark hotspot centroids
    if not hotspot_metrics.empty:
        ax.scatter(
            hotspot_metrics["longitude_centroid"],
            hotspot_metrics["latitude_centroid"],
            s=180, marker="*", c="white", edgecolors="#FFD700",
            linewidths=0.8, zorder=10, label="Hotspot Centroid"
        )

    ax.set_xlabel("Longitude", color="white")
    ax.set_ylabel("Latitude", color="white")
    ax.set_title(
        f"Phase 14 — DBSCAN Spatial Hotspot Detection\n"
        f"eps={selected_params['eps_km']}km  min_samples={selected_params['min_samples']}  "
        f"Clusters={n_clusters}  Noise={int(noise_mask.sum())}",
        color="white", fontsize=11,
    )
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555")
    noise_patch = mpatches.Patch(color="#666666", label=f"Noise ({int(noise_mask.sum())})")
    centroid_patch = mpatches.Patch(color="white", label="Hotspot centroid")
    ax.legend(handles=[noise_patch, centroid_patch], facecolor="#2e2e5e", labelcolor="white", loc="lower right")

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "phase14_dbscan_clusters.png", dpi=130, bbox_inches="tight")
    plt.close()
    logger.info("Saved phase14_dbscan_clusters.png")

    # ---- Plot 2: Cluster Size Distribution ----
    if not hotspot_metrics.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")
        bars = ax.bar(
            hotspot_metrics["cluster_id"].astype(str),
            hotspot_metrics["event_count"],
            color=cmap(np.linspace(0, 1, len(hotspot_metrics))),
            edgecolor="#333",
        )
        ax.set_xlabel("Cluster ID", color="white")
        ax.set_ylabel("Event Count", color="white")
        ax.set_title("Phase 14 — Cluster Size Distribution", color="white", fontsize=11)
        ax.tick_params(colors="white", axis="both")
        for spine in ax.spines.values():
            spine.set_edgecolor("#555")
        if len(hotspot_metrics) > 20:
            plt.xticks(rotation=90, fontsize=7)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "phase14_cluster_size_distribution.png", dpi=130, bbox_inches="tight")
        plt.close()
        logger.info("Saved phase14_cluster_size_distribution.png")

    # ---- Plot 3: Hotspot Risk Distribution ----
    risk_cols = [c for c in ["low_risk_count", "moderate_risk_count", "high_risk_count", "critical_risk_count"]
                 if c in df.columns or c.replace("_count", "").upper() in df.get("risk_category", pd.Series()).values]
    # Derive from clustered events
    if "risk_category" in df.columns and df["risk_category"].notna().any():
        df_risk = df[df["cluster_id"] >= 0].groupby(["cluster_id", "risk_category"]).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")
        colors = {"LOW": "#4CAF50", "MODERATE": "#FFC107", "HIGH": "#FF5722", "CRITICAL": "#9C27B0"}
        bottom = np.zeros(len(df_risk))
        for cat in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
            if cat in df_risk.columns:
                ax.bar(df_risk.index.astype(str), df_risk[cat],
                       bottom=bottom, label=cat, color=colors.get(cat, "grey"), edgecolor="#333")
                bottom += df_risk[cat].values
        ax.set_xlabel("Cluster ID", color="white")
        ax.set_ylabel("Event Count", color="white")
        ax.set_title("Phase 14 — Risk Category Distribution per Hotspot", color="white", fontsize=11)
        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#555")
        legend = ax.legend(title="Risk Category", facecolor="#2e2e5e", labelcolor="white")
        legend.get_title().set_color("white")
        if len(df_risk) > 20:
            plt.xticks(rotation=90, fontsize=7)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "phase14_hotspot_risk_distribution.png", dpi=130, bbox_inches="tight")
        plt.close()
        logger.info("Saved phase14_hotspot_risk_distribution.png")
    else:
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")
        ax.text(0.5, 0.5, "Phase 9 risk data available\nonly for 1,500 test records.\nMost clusters have no risk annotation.",
                ha="center", va="center", color="white", fontsize=12, transform=ax.transAxes)
        ax.set_title("Phase 14 — Hotspot Risk Distribution (Partial Data)", color="white")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "phase14_hotspot_risk_distribution.png", dpi=130, bbox_inches="tight")
        plt.close()
        logger.info("Saved phase14_hotspot_risk_distribution.png (partial data notice)")

    # ---- Plot 4: Temporal Hotspot Activity ----
    if "event_hour" in df.columns:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor("#1a1a2e")
        for axi in axes:
            axi.set_facecolor("#1a1a2e")

        # By hour
        hour_dist = df[df["cluster_id"] >= 0]["event_hour"].value_counts().sort_index()
        axes[0].bar(hour_dist.index, hour_dist.values, color="#00BCD4", edgecolor="#333")
        axes[0].set_xlabel("Hour of Day", color="white")
        axes[0].set_ylabel("Events in Clusters", color="white")
        axes[0].set_title("Hourly Activity in Hotspots", color="white")
        axes[0].tick_params(colors="white")
        for spine in axes[0].spines.values():
            spine.set_edgecolor("#555")

        # By day of week
        if "event_day_of_week" in df.columns:
            dow_dist = df[df["cluster_id"] >= 0]["event_day_of_week"].value_counts().sort_index()
            dow_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            axes[1].bar(
                [dow_labels[i] if i < len(dow_labels) else str(i) for i in dow_dist.index],
                dow_dist.values, color="#FF9800", edgecolor="#333"
            )
            axes[1].set_xlabel("Day of Week", color="white")
            axes[1].set_ylabel("Events in Clusters", color="white")
            axes[1].set_title("Day-of-Week Activity in Hotspots", color="white")
            axes[1].tick_params(colors="white")
            for spine in axes[1].spines.values():
                spine.set_edgecolor("#555")

        fig.suptitle("Phase 14 — Temporal Activity Distribution in Spatial Hotspots",
                     color="white", fontsize=12)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "phase14_hotspot_temporal_activity.png", dpi=130, bbox_inches="tight")
        plt.close()
        logger.info("Saved phase14_hotspot_temporal_activity.png")


# ==============================================================================
# 13. Validation
# ==============================================================================

def validate_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute unsupervised cluster validation metrics.
    """
    n_clusters = len(set(df["cluster_id"].unique()) - {-1})
    noise_count = int((df["cluster_id"] == -1).sum())
    total = len(df)
    noise_pct = round(noise_count / total * 100, 2)
    cluster_sizes = df[df["cluster_id"] >= 0]["cluster_id"].value_counts()
    largest_pct = round(float(cluster_sizes.max() / total * 100), 2) if not cluster_sizes.empty else 0.0
    median_size = round(float(cluster_sizes.median()), 1) if not cluster_sizes.empty else 0.0

    # Silhouette score only if ≥ 2 clusters and enough non-noise points
    sil_score = None
    coords_rad = np.radians(df[df["cluster_id"] >= 0][["latitude", "longitude"]].values)
    labels_non_noise = df[df["cluster_id"] >= 0]["cluster_id"].values

    if n_clusters >= 2 and len(coords_rad) >= 10:
        try:
            sil_score = round(float(silhouette_score(coords_rad, labels_non_noise, metric="haversine")), 4)
        except Exception as e:
            sil_score = None
            logger.warning(f"Silhouette score unavailable: {e}")

    return pd.DataFrame([{
        "cluster_count": n_clusters,
        "noise_count": noise_count,
        "noise_percentage": noise_pct,
        "largest_cluster_size": int(cluster_sizes.max()) if not cluster_sizes.empty else 0,
        "largest_cluster_percentage": largest_pct,
        "median_cluster_size": median_size,
        "silhouette_score": sil_score,
        "silhouette_note": (
            "Computed on non-noise points using haversine metric." if sil_score is not None
            else "Not computed — requires >= 2 clusters with sufficient samples."
        ),
    }])


def stability_check(df_valid: pd.DataFrame, coords_rad: np.ndarray,
                    eps_km: float, min_samples: int) -> pd.DataFrame:
    """
    Approximate stability by running DBSCAN on temporal halves.
    """
    rows = []
    df_sorted = df_valid.sort_values("complaint_timestamp").reset_index(drop=True)
    n = len(df_sorted)

    subsets = {
        "full_dataset": (0, n),
        "first_half": (0, n // 2),
        "second_half": (n // 2, n),
    }

    reference_labels = None
    reference_clusters = 0

    for subset_name, (start, end) in subsets.items():
        chunk = df_sorted.iloc[start:end]
        chunk_coords = np.radians(chunk[["latitude", "longitude"]].values.astype(np.float64))
        if len(chunk_coords) < min_samples:
            rows.append({"subset": subset_name, "cluster_count": 0, "noise_percentage": 100.0,
                         "major_cluster_overlap": "N/A", "status": "INSUFFICIENT_DATA",
                         "notes": f"Only {len(chunk_coords)} points — less than min_samples={min_samples}"})
            continue

        labels = run_dbscan(chunk_coords, eps_km=eps_km, min_samples=min_samples)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_pct = round(float((labels == -1).sum() / len(labels) * 100), 2)

        if subset_name == "full_dataset":
            reference_clusters = n_clusters
            overlap = "reference"
        else:
            delta = abs(n_clusters - reference_clusters)
            overlap = f"delta_clusters={delta}" if reference_clusters > 0 else "no_reference"

        status = "STABLE" if n_clusters > 0 and noise_pct < 80 else "UNSTABLE"
        rows.append({
            "subset": subset_name,
            "cluster_count": n_clusters,
            "noise_percentage": noise_pct,
            "major_cluster_overlap": overlap,
            "status": status,
            "notes": f"n={end - start} records, eps={eps_km}km, min_samples={min_samples}",
        })

    return pd.DataFrame(rows)


# ==============================================================================
# 14. Audit CSVs
# ==============================================================================

def leakage_audit() -> pd.DataFrame:
    rows = [
        {"field": "latitude", "source": "complaint_timestamp time", "status": "SAFE", "notes": "Observed incident coordinate; no future information"},
        {"field": "longitude", "source": "complaint_timestamp time", "status": "SAFE", "notes": "Observed incident coordinate; no future information"},
        {"field": "complaint_timestamp", "source": "incident record", "status": "SAFE", "notes": "Past event timestamp; no future leakage"},
        {"field": "crime_type", "source": "incident record", "status": "SAFE", "notes": "Observed at complaint filing time"},
        {"field": "victim_district", "source": "incident record", "status": "SAFE", "notes": "Administrative boundary; not derived from outcome"},
        {"field": "is_linked_to_withdrawal", "source": "historical flag", "status": "SAFE", "notes": "Historical association; not future target"},
        {"field": "future_withdrawal", "source": "Phase 4 ground truth", "status": "ANALYTICAL_USE_ONLY", "notes": "Used only to analyze cluster composition; DBSCAN runs on coordinates ONLY — not on future_withdrawal"},
        {"field": "risk_score", "source": "Phase 9 XGBoost output", "status": "SAFE", "notes": "Model output on held-out test set; DBSCAN does not use it as input"},
        {"field": "risk_category", "source": "Phase 9 XGBoost output", "status": "SAFE", "notes": "Analytical cross-tabulation only; not DBSCAN input"},
        {"field": "predicted_probability", "source": "Phase 9 XGBoost output", "status": "SAFE", "notes": "Cross-tabulation analysis only; not DBSCAN input"},
        {"field": "DBSCAN clustering basis", "source": "lat/lon radians only", "status": "CLEAN", "notes": "DBSCAN uses ONLY geographic coordinates. No risk labels or targets in distance matrix."},
    ]
    return pd.DataFrame(rows)


def sensitive_data_audit() -> pd.DataFrame:
    rows = [
        {"field": "victim_account_id_masked", "status": "EXCLUDED", "reason": "Bank account reference; excluded from all Phase 14 outputs"},
        {"field": "card_number", "status": "EXCLUDED", "reason": "PCI-DSS prohibited credential"},
        {"field": "pin", "status": "EXCLUDED", "reason": "Authentication credential"},
        {"field": "otp", "status": "EXCLUDED", "reason": "One-time passcode"},
        {"field": "cvv", "status": "EXCLUDED", "reason": "Card security code"},
        {"field": "password", "status": "EXCLUDED", "reason": "Authentication secret"},
        {"field": "fraud_amount", "status": "EXCLUDED_FROM_DBSCAN", "reason": "Financial amount not used as DBSCAN input"},
        {"field": "case_id", "status": "APPROVED", "reason": "Sanitized case reference for audit trail"},
        {"field": "latitude", "status": "APPROVED", "reason": "Required for spatial clustering; validated in bounds [-90,90]"},
        {"field": "longitude", "status": "APPROVED", "reason": "Required for spatial clustering; validated in bounds [-180,180]"},
        {"field": "cluster_id", "status": "APPROVED", "reason": "DBSCAN assignment; analytical only"},
        {"field": "victim_district", "status": "APPROVED", "reason": "Administrative aggregation; no individual identification"},
        {"field": "crime_type", "status": "APPROVED", "reason": "Crime category; aggregated across clusters"},
        {"field": "cluster centroids", "status": "APPROVED", "reason": "Geographic centroid of analytical spatial cluster"},
    ]
    return pd.DataFrame(rows)


# ==============================================================================
# 15. Report
# ==============================================================================

def generate_report(
    selected: dict,
    source: str,
    val_stats: dict,
    cluster_stats: pd.DataFrame,
    hotspot_metrics: pd.DataFrame,
    validation_df: pd.DataFrame,
    stability_df: pd.DataFrame,
    postgis_ok: bool,
) -> str:
    # Pre-compute all values to avoid backslash-in-f-string (Python < 3.12)
    n_clusters = int(selected["cluster_count"])
    noise = int(selected["noise_count"])
    noise_pct = float(selected["noise_percentage"])
    top_hotspot = hotspot_metrics.iloc[0] if not hotspot_metrics.empty else None
    sil = validation_df["silhouette_score"].iloc[0] if not validation_df.empty else None

    largest_cluster = int(cluster_stats["event_count"].max()) if not cluster_stats.empty else "N/A"
    median_cluster = round(float(cluster_stats["event_count"].median()), 1) if not cluster_stats.empty else "N/A"
    sil_str = str(sil) if sil is not None else "Not computed (requires >= 2 clusters)"
    sil_str2 = str(sil) if sil is not None else "Not computed"
    eps_rad = km_to_radians(selected["eps_km"])
    postgis_status = "CREATED" if postgis_ok else "SKIPPED - PostgreSQL offline"
    n_param_configs = len(PARAM_GRID)
    usable_pts = val_stats["usable_points"]
    total_recs = val_stats["total_records"]
    missing_coords = val_stats["missing_coordinates"]
    invalid_coords = val_stats["invalid_coordinates"]
    n_hotspots = len(hotspot_metrics)
    eps_km = selected["eps_km"]
    min_samp = selected["min_samples"]
    rationale = selected["rationale"]

    if top_hotspot is not None:
        top_hs_str = (
            f"**Top hotspot:** Cluster {int(top_hotspot['cluster_id'])} "
            f"— {int(top_hotspot['event_count'])} events at "
            f"({round(float(top_hotspot['latitude_centroid']), 4)}°N, "
            f"{round(float(top_hotspot['longitude_centroid']), 4)}°E)"
        )
    else:
        top_hs_str = "No hotspots formed."

    report = f"""# Phase 14 — DBSCAN Spatial Hotspot Detection
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Objective
Identify geographical areas with unusually dense concentrations of cybercrime-related complaints
using DBSCAN spatial clustering on WGS 84 geographic coordinates.

> **IMPORTANT INTERPRETATION:** DBSCAN identifies spatial concentrations of observed events.
> It does NOT prove criminal identity, criminal intent, future criminal activity, or causation.
> A hotspot is an analytical spatial cluster. Model risk score and hotspot rank are separate concepts.

---

## 2. Input Data
- **Source:** {source}
- **Total records:** {total_recs}
- **Usable geographic points:** {usable_pts}
- **Missing coordinates:** {missing_coords}
- **Invalid coordinates:** {invalid_coords}

---

## 3. Geographic Coverage
- **Latitude range:** 8.52 degrees N to 17.69 degrees N (South India)
- **Longitude range:** 74.50 degrees E to 83.22 degrees E
- **Geographic region:** South India (Kerala, Tamil Nadu, Andhra Pradesh, Karnataka)
- **Coordinate system:** WGS 84 (EPSG:4326)

---

## 4. Coordinate Validation
All {usable_pts} records passed WGS 84 bounds checking:
- Latitude within [-90.0, 90.0]: PASS
- Longitude within [-180.0, 180.0]: PASS

---

## 5. DBSCAN Method
scikit-learn DBSCAN with algorithm=ball_tree and metric=haversine.

---

## 6. Distance Metric — Haversine
Raw latitude/longitude degrees are not valid Euclidean distances.
The haversine great-circle formula is used instead.
Epsilon conversion: eps_radians = eps_km / Earth_radius_km = eps_km / {EARTH_RADIUS_KM}

---

## 7. Parameter Testing
{n_param_configs} configurations tested (see outputs/phase14_dbscan_parameter_results.csv):
- eps values: 0.5 km, 1.0 km, 2.0 km
- min_samples values: 3, 5, 10

---

## 8. Selected Parameters
- **eps:** {eps_km} km (= {eps_rad:.6f} radians)
- **min_samples:** {min_samp}
- **Rationale:** {rationale}

---

## 9. Cluster Results
- **Total clusters:** {n_clusters}
- **Noise points:** {noise} ({noise_pct:.1f}%)
- **Largest cluster:** {largest_cluster} events
- **Median cluster size:** {median_cluster} events
- **Silhouette score:** {sil_str}

---

## 10. Noise Analysis
- Noise = {noise} events not assigned to any spatial cluster at eps={eps_km} km.
- This is expected for dispersed singleton events.

---

## 11. Hotspot Statistics
- **Total analytical hotspots:** {n_hotspots}
- {top_hs_str}

---

## 12. Withdrawal Hotspots
Based on future_withdrawal == 1 sub-population.
See outputs/phase14_withdrawal_hotspots.csv.

---

## 13. Risk x Hotspot Analysis
See outputs/phase14_hotspot_risk_summary.csv.
Cross-tabulates cluster membership with Phase 9 XGBoost risk categories.
Note: Phase 9 predictions cover only the 1,500-record test split.

---

## 14. Temporal Analysis
See outputs/phase14_hotspot_temporal_summary.csv.

---

## 15. Validation
- Silhouette score (non-noise points, haversine): {sil_str2}

---

## 16. Stability
See outputs/phase14_cluster_stability.csv.

---

## 17. Security
All outputs exclude: account numbers, card numbers, PINs, OTPs, CVVs, passwords, phone/email PII.
See outputs/phase14_sensitive_data_audit.csv.

---

## 18. Leakage Audit
DBSCAN uses ONLY geographic coordinates (latitude/longitude) as input.
No risk scores, target labels, or future information enter the distance matrix.
See outputs/phase14_leakage_audit.csv.

---

## 19. Limitations
1. Hotspot clusters are descriptive — they reflect past event density, not future criminal certainty.
2. Phase 9 risk scores cover only 1,500 test records; 8,500 training records have no risk annotation.
3. Haversine DBSCAN does not correct for population density or complaint reporting rates.
4. Cluster stability depends on sufficient spatial density; sparse periods may yield few clusters.

---

## 20. Conclusion
Phase 14 successfully identified {n_clusters} spatial hotspot clusters from {usable_pts} validated
geographic complaint records. Hotspots are documented for authorized analytical use by human
investigators. All findings require human review and institutional authorization before any action.

---

## 21. Phase 15 Readiness
Phase 14 outputs available for Phase 15:
- outputs/phase14_hotspots_geojson.geojson — Map-ready spatial hotspot features
- outputs/phase14_hotspot_summary.csv — Ranked analytical hotspot catalog
- PostGIS table: cybercrime_hotspots (status: {postgis_status})
"""
    return report



# ==============================================================================
# 16. Main Orchestrator
# ==============================================================================

def main():
    logger.info("=" * 65)
    logger.info("Phase 14 — DBSCAN Spatial Hotspot Detection")
    logger.info("Problem Statement ID 26184")
    logger.info("=" * 65)

    t0 = datetime.now()

    # 1. Load data
    df_raw, source = load_spatial_data()

    # 2. Coordinate validation
    df_valid, val_stats = validate_coordinates(df_raw)

    # Save input profile
    pd.DataFrame([{
        "data_source": source,
        "total_rows": val_stats["total_records"],
        "usable_points": val_stats["usable_points"],
        "missing_coordinates": val_stats["missing_coordinates"],
        "invalid_coordinates": val_stats["invalid_coordinates"],
        "risk_score_coverage": int(df_valid["risk_score"].notna().sum()) if "risk_score" in df_valid.columns else 0,
        "latitude_min": round(float(df_valid["latitude"].min()), 4),
        "latitude_max": round(float(df_valid["latitude"].max()), 4),
        "longitude_min": round(float(df_valid["longitude"].min()), 4),
        "longitude_max": round(float(df_valid["longitude"].max()), 4),
        "timestamp_min": str(df_valid["complaint_timestamp"].min()),
        "timestamp_max": str(df_valid["complaint_timestamp"].max()),
    }]).to_csv(OUTPUTS_DIR / "phase14_input_profile.csv", index=False)
    logger.info("Saved phase14_input_profile.csv")

    pd.DataFrame([val_stats]).to_csv(OUTPUTS_DIR / "phase14_spatial_input_validation.csv", index=False)
    logger.info("Saved phase14_spatial_input_validation.csv")

    # 3. Haversine coordinates
    coords_rad = prepare_coordinates(df_valid)

    # 4. Parameter evaluation
    logger.info("Evaluating DBSCAN parameter grid...")
    param_results = evaluate_parameters(df_valid, coords_rad)
    param_results.to_csv(OUTPUTS_DIR / "phase14_dbscan_parameter_results.csv", index=False)
    logger.info("Saved phase14_dbscan_parameter_results.csv")

    # 5. Select parameters
    selected = select_dbscan_parameters(param_results)
    logger.info(f"Selected: eps={selected['eps_km']}km, min_samples={selected['min_samples']}")
    logger.info(f"Rationale: {selected['rationale']}")

    # 6. Final clustering
    final_labels = run_dbscan(coords_rad, eps_km=selected["eps_km"], min_samples=selected["min_samples"])
    df_valid = df_valid.copy()
    df_valid["cluster_id"] = final_labels

    # 7. Cluster statistics
    cluster_stats = calculate_cluster_statistics(df_valid)
    cluster_stats.to_csv(OUTPUTS_DIR / "phase14_cluster_statistics.csv", index=False)
    logger.info(f"Saved phase14_cluster_statistics.csv — {len(cluster_stats)} clusters")

    # 8. Hotspot metrics & ranking
    hotspot_metrics = calculate_hotspot_metrics(cluster_stats)
    hotspot_summary = generate_hotspot_summary(hotspot_metrics)
    hotspot_summary.to_csv(OUTPUTS_DIR / "phase14_hotspot_summary.csv", index=False)
    logger.info("Saved phase14_hotspot_summary.csv")

    # 9. Safe clustered events output
    safe_cols = [c for c in [
        "case_id", "complaint_timestamp", "crime_type", "victim_district",
        "latitude", "longitude", "cluster_id", "is_linked_to_withdrawal",
        "future_withdrawal", "risk_score", "risk_category", "event_hour",
        "event_day_of_week", "crime_category_group",
    ] if c in df_valid.columns]
    df_valid[safe_cols].to_csv(OUTPUTS_DIR / "phase14_clustered_events.csv", index=False)
    logger.info("Saved phase14_clustered_events.csv")

    # 10. Temporal analysis
    temp_df = temporal_analysis(df_valid)
    temp_df.to_csv(OUTPUTS_DIR / "phase14_hotspot_temporal_summary.csv", index=False)
    logger.info("Saved phase14_hotspot_temporal_summary.csv")

    # 11. Withdrawal-specific hotspots
    withdrawal_df = analyze_withdrawal_hotspots(
        df_valid, coords_rad, eps_km=selected["eps_km"], min_samples=selected["min_samples"]
    )
    withdrawal_df.to_csv(OUTPUTS_DIR / "phase14_withdrawal_hotspots.csv", index=False)
    logger.info("Saved phase14_withdrawal_hotspots.csv")

    # 12. Risk × hotspot
    risk_cross = risk_hotspot_cross_analysis(df_valid)
    if not risk_cross.empty:
        risk_cross.to_csv(OUTPUTS_DIR / "phase14_hotspot_risk_summary.csv", index=False)
        logger.info("Saved phase14_hotspot_risk_summary.csv")
    else:
        pd.DataFrame([{"note": "Phase 9 risk scores not available for cluster overlap analysis."}]).to_csv(
            OUTPUTS_DIR / "phase14_hotspot_risk_summary.csv", index=False
        )

    # 13. GeoJSON
    geojson_data = generate_geojson(cluster_stats, hotspot_metrics)
    with open(OUTPUTS_DIR / "phase14_hotspots_geojson.geojson", "w") as f:
        json.dump(geojson_data, f, indent=2, default=str)
    logger.info("Saved phase14_hotspots_geojson.geojson")

    # 14. PostGIS storage
    postgis_ok = store_hotspots_in_postgis(hotspot_metrics)

    # 15. Visualizations
    generate_visualizations(df_valid, hotspot_metrics, selected)

    # 16. Validation
    validation_df = validate_clusters(df_valid)
    validation_df.to_csv(OUTPUTS_DIR / "phase14_cluster_validation.csv", index=False)
    logger.info("Saved phase14_cluster_validation.csv")

    # 17. Stability
    stability_df = stability_check(df_valid, coords_rad, selected["eps_km"], selected["min_samples"])
    stability_df.to_csv(OUTPUTS_DIR / "phase14_cluster_stability.csv", index=False)
    logger.info("Saved phase14_cluster_stability.csv")

    # 18. Leakage & sensitivity audits
    leakage_audit().to_csv(OUTPUTS_DIR / "phase14_leakage_audit.csv", index=False)
    sensitive_data_audit().to_csv(OUTPUTS_DIR / "phase14_sensitive_data_audit.csv", index=False)
    logger.info("Saved phase14_leakage_audit.csv and phase14_sensitive_data_audit.csv")

    # 19. Report
    report_text = generate_report(
        selected, source, val_stats,
        cluster_stats, hotspot_metrics,
        validation_df, stability_df, postgis_ok,
    )
    report_path = OUTPUTS_DIR / "phase14_dbscan_report.md"
    report_path.write_text(report_text, encoding="utf-8")
    logger.info("Saved phase14_dbscan_report.md")

    runtime = (datetime.now() - t0).total_seconds()

    logger.info("=" * 65)
    logger.info("PHASE 14 SUMMARY")
    logger.info(f"  Input rows:          {val_stats['total_records']}")
    logger.info(f"  Usable coordinates:  {val_stats['usable_points']}")
    logger.info(f"  Selected eps:        {selected['eps_km']} km")
    logger.info(f"  Selected min_samples:{selected['min_samples']}")
    logger.info(f"  Clusters found:      {selected['cluster_count']}")
    logger.info(f"  Noise points:        {selected['noise_count']} ({selected['noise_percentage']}%)")
    logger.info(f"  PostGIS status:      {'STORED' if postgis_ok else 'SKIPPED (offline)'}")
    logger.info(f"  Runtime:             {runtime:.1f}s")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
