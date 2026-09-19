"""
PostGIS Spatial Queries for Cybercrime Events
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from database.models import CybercrimeEvent
from database.schemas import validate_coordinates

logger = logging.getLogger("cybercrime_api.database.spatial")


def find_events_within_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Find cybercrime complaint events within a geographic radius in meters using PostGIS ST_DWithin.
    Uses geography casting so distance calculations are performed on the WGS 84 ellipsoid in meters.
    Coordinate order: ST_MakePoint(longitude, latitude).
    """
    validate_coordinates(latitude, longitude)
    if radius_meters <= 0:
        raise ValueError("radius_meters must be strictly positive")

    query = text("""
        SELECT 
            case_id,
            complaint_timestamp,
            crime_type,
            fraud_amount,
            victim_district,
            latitude,
            longitude,
            ST_Distance(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            ) AS distance_meters
        FROM cybercrime_events
        WHERE location IS NOT NULL
          AND ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius_meters
          )
        ORDER BY distance_meters ASC
        LIMIT :limit;
    """)

    result = db.execute(
        query,
        {
            "lat": float(latitude),
            "lon": float(longitude),
            "radius_meters": float(radius_meters),
            "limit": int(limit),
        }
    )

    rows = []
    for r in result.mappings():
        rows.append({
            "case_id": r["case_id"],
            "complaint_timestamp": r["complaint_timestamp"].isoformat() if r["complaint_timestamp"] else None,
            "crime_type": r["crime_type"],
            "fraud_amount": float(r["fraud_amount"]),
            "victim_district": r["victim_district"],
            "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
            "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
            "distance_meters": round(float(r["distance_meters"]), 2),
        })
    return rows


def count_events_within_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float
) -> int:
    """
    Count the number of cybercrime complaint events within a geographic radius in meters.
    """
    validate_coordinates(latitude, longitude)
    if radius_meters <= 0:
        raise ValueError("radius_meters must be strictly positive")

    query = text("""
        SELECT COUNT(*)
        FROM cybercrime_events
        WHERE location IS NOT NULL
          AND ST_DWithin(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius_meters
          );
    """)

    count = db.execute(
        query,
        {
            "lat": float(latitude),
            "lon": float(longitude),
            "radius_meters": float(radius_meters),
        }
    ).scalar()

    return int(count or 0)


def calculate_distance_meters(
    db: Session,
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate geodesic distance in meters between two coordinates using PostGIS ST_Distance.
    """
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)

    query = text("""
        SELECT ST_Distance(
            ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326)::geography,
            ST_SetSRID(ST_MakePoint(:lon2, :lat2), 4326)::geography
        );
    """)

    dist = db.execute(
        query,
        {
            "lat1": float(lat1),
            "lon1": float(lon1),
            "lat2": float(lat2),
            "lon2": float(lon2),
        }
    ).scalar()

    return float(dist or 0.0)


def find_events_in_bounding_box(
    db: Session,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve cybercrime complaint events inside a spatial bounding box using ST_MakeEnvelope.
    Envelope order: ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326).
    """
    validate_coordinates(min_lat, min_lon)
    validate_coordinates(max_lat, max_lon)

    query = text("""
        SELECT 
            case_id,
            complaint_timestamp,
            crime_type,
            fraud_amount,
            victim_district,
            latitude,
            longitude
        FROM cybercrime_events
        WHERE location IS NOT NULL
          AND location && ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
        ORDER BY complaint_timestamp DESC
        LIMIT :limit;
    """)

    result = db.execute(
        query,
        {
            "min_lat": float(min_lat),
            "max_lat": float(max_lat),
            "min_lon": float(min_lon),
            "max_lon": float(max_lon),
            "limit": int(limit),
        }
    )

    rows = []
    for r in result.mappings():
        rows.append({
            "case_id": r["case_id"],
            "complaint_timestamp": r["complaint_timestamp"].isoformat() if r["complaint_timestamp"] else None,
            "crime_type": r["crime_type"],
            "fraud_amount": float(r["fraud_amount"]),
            "victim_district": r["victim_district"],
            "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
            "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
        })
    return rows


def group_events_by_district(db: Session) -> List[Dict[str, Any]]:
    """
    Retrieve aggregate event counts and total fraud amount grouped by district.
    """
    query = text("""
        SELECT 
            COALESCE(victim_district, 'UNKNOWN') AS district,
            COUNT(*) AS event_count,
            ROUND(SUM(fraud_amount)::numeric, 2) AS total_fraud_amount,
            COUNT(location) AS events_with_location
        FROM cybercrime_events
        GROUP BY victim_district
        ORDER BY event_count DESC;
    """)

    result = db.execute(query)
    return [
        {
            "district": r["district"],
            "event_count": int(r["event_count"]),
            "total_fraud_amount": float(r["total_fraud_amount"] or 0.0),
            "events_with_location": int(r["events_with_location"]),
        }
        for r in result.mappings()
    ]


# ==============================================================================
# Phase 14 — Hotspot Queries
# These functions query the cybercrime_hotspots table created by Phase 14 DBSCAN.
# The table is populated by running: python src/hotspot_detection.py
# All queries return safe analytical aggregates — no raw complaint records.
# ==============================================================================

def get_hotspots(db: Session, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Return all DBSCAN spatial hotspots ordered by hotspot_rank ascending.
    Hotspots are analytical spatial clusters — not proven criminal locations.
    """
    query = text("""
        SELECT
            cluster_id,
            hotspot_rank,
            event_count,
            hotspot_status,
            density_metric,
            centroid_latitude,
            centroid_longitude,
            cluster_radius_km,
            high_risk_count,
            critical_risk_count,
            withdrawal_event_count,
            average_risk_score,
            time_range_start,
            time_range_end
        FROM cybercrime_hotspots
        ORDER BY hotspot_rank ASC
        LIMIT :limit
    """)
    try:
        result = db.execute(query, {"limit": int(limit)})
        return [dict(r._mapping) for r in result]
    except Exception as e:
        logger.warning(f"get_hotspots failed (table may not exist yet): {e}")
        return []


def get_hotspots_within_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Return hotspot centroids within a given radius (in meters) from a query point.
    Uses PostGIS ST_DWithin on the geography type for ellipsoidal accuracy.
    """
    validate_coordinates(latitude, longitude)
    if radius_meters <= 0:
        raise ValueError("radius_meters must be > 0")

    query = text("""
        SELECT
            cluster_id,
            hotspot_rank,
            event_count,
            hotspot_status,
            centroid_latitude,
            centroid_longitude,
            cluster_radius_km,
            average_risk_score,
            ST_Distance(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            ) AS distance_meters
        FROM cybercrime_hotspots
        WHERE ST_DWithin(
            location::geography,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radius_m
        )
        ORDER BY distance_meters ASC
        LIMIT :limit
    """)
    try:
        result = db.execute(query, {
            "lat": float(latitude),
            "lon": float(longitude),
            "radius_m": float(radius_meters),
            "limit": int(limit),
        })
        return [dict(r._mapping) for r in result]
    except Exception as e:
        logger.warning(f"get_hotspots_within_radius failed: {e}")
        return []


def get_high_priority_hotspots(
    db: Session,
    status_filter: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Return hotspots filtered by hotspot_status.

    Valid status values: LOW_ACTIVITY, MODERATE_ACTIVITY, HIGH_ACTIVITY, CRITICAL_ACTIVITY
    These are analytical categories — not official law-enforcement classifications.

    If status_filter is None, returns all hotspots with HIGH_ACTIVITY or CRITICAL_ACTIVITY.
    """
    allowed_statuses = {"LOW_ACTIVITY", "MODERATE_ACTIVITY", "HIGH_ACTIVITY", "CRITICAL_ACTIVITY"}
    if status_filter is not None and status_filter not in allowed_statuses:
        raise ValueError(f"status_filter must be one of {allowed_statuses}")

    if status_filter:
        query = text("""
            SELECT cluster_id, hotspot_rank, event_count, hotspot_status,
                   density_metric, centroid_latitude, centroid_longitude,
                   high_risk_count, critical_risk_count, withdrawal_event_count,
                   average_risk_score
            FROM cybercrime_hotspots
            WHERE hotspot_status = :status
            ORDER BY hotspot_rank ASC
            LIMIT :limit
        """)
        params: dict = {"status": status_filter, "limit": int(limit)}
    else:
        query = text("""
            SELECT cluster_id, hotspot_rank, event_count, hotspot_status,
                   density_metric, centroid_latitude, centroid_longitude,
                   high_risk_count, critical_risk_count, withdrawal_event_count,
                   average_risk_score
            FROM cybercrime_hotspots
            WHERE hotspot_status IN ('HIGH_ACTIVITY', 'CRITICAL_ACTIVITY')
            ORDER BY hotspot_rank ASC
            LIMIT :limit
        """)
        params = {"limit": int(limit)}

    try:
        result = db.execute(query, params)
        return [dict(r._mapping) for r in result]
    except Exception as e:
        logger.warning(f"get_high_priority_hotspots failed: {e}")
        return []


def get_hotspot_statistics(db: Session) -> Dict[str, Any]:
    """
    Return aggregate statistics across all DBSCAN hotspot clusters.
    """
    query = text("""
        SELECT
            COUNT(*)                       AS total_hotspots,
            SUM(event_count)               AS total_clustered_events,
            MAX(event_count)               AS largest_cluster_events,
            ROUND(AVG(event_count)::numeric, 1) AS avg_cluster_events,
            SUM(high_risk_count)           AS total_high_risk_events,
            SUM(critical_risk_count)       AS total_critical_risk_events,
            SUM(withdrawal_event_count)    AS total_withdrawal_events,
            COUNT(*) FILTER (WHERE hotspot_status = 'CRITICAL_ACTIVITY') AS critical_hotspots,
            COUNT(*) FILTER (WHERE hotspot_status = 'HIGH_ACTIVITY')     AS high_hotspots,
            COUNT(*) FILTER (WHERE hotspot_status = 'MODERATE_ACTIVITY') AS moderate_hotspots,
            COUNT(*) FILTER (WHERE hotspot_status = 'LOW_ACTIVITY')      AS low_hotspots
        FROM cybercrime_hotspots
    """)
    try:
        result = db.execute(query)
        row = result.mappings().fetchone()
        return dict(row) if row else {}
    except Exception as e:
        logger.warning(f"get_hotspot_statistics failed (table may not exist yet): {e}")
        return {"error": "cybercrime_hotspots table not available. Run: python src/hotspot_detection.py"}

def find_recent_events_by_timestamp(
    db: Session,
    since_timestamp: datetime,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve events occurring on or after a given timestamp, sorted newest first.
    """
    query = text("""
        SELECT 
            case_id,
            complaint_timestamp,
            crime_type,
            fraud_amount,
            victim_district,
            latitude,
            longitude
        FROM cybercrime_events
        WHERE complaint_timestamp >= :since
        ORDER BY complaint_timestamp DESC
        LIMIT :limit;
    """)

    result = db.execute(query, {"since": since_timestamp, "limit": int(limit)})
    return [
        {
            "case_id": r["case_id"],
            "complaint_timestamp": r["complaint_timestamp"].isoformat() if r["complaint_timestamp"] else None,
            "crime_type": r["crime_type"],
            "fraud_amount": float(r["fraud_amount"]),
            "victim_district": r["victim_district"],
            "latitude": float(r["latitude"]) if r["latitude"] is not None else None,
            "longitude": float(r["longitude"]) if r["longitude"] is not None else None,
        }
        for r in result.mappings()
    ]
