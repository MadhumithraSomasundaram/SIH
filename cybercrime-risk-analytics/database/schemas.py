"""
Pydantic Schemas for Database Operations and Spatial Queries
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ==============================================================================
# Coordinate Validation Helper
# ==============================================================================

def validate_coordinates(lat: Optional[float], lon: Optional[float]) -> None:
    """Validate latitude and longitude against standard geographic bounds."""
    if lat is not None:
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude {lat} out of range [-90.0, 90.0]")
    if lon is not None:
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude {lon} out of range [-180.0, 180.0]")


# ==============================================================================
# Cybercrime Event Schemas
# ==============================================================================

class CybercrimeEventBase(BaseModel):
    case_id: str = Field(..., max_length=64, description="Unique case identifier")
    complaint_timestamp: datetime = Field(..., description="Timestamp of incident")
    crime_type: str = Field(..., max_length=64, description="Crime category")
    fraud_amount: float = Field(..., ge=0.0, description="Financial loss in INR")
    reported_by_authority: int = Field(0, ge=0, le=1, description="1 if filed by authority, else 0")
    victim_state: Optional[str] = Field(None, max_length=64)
    victim_district: Optional[str] = Field(None, max_length=64)
    victim_area: Optional[str] = Field(None, max_length=128)
    victim_area_id: Optional[str] = Field(None, max_length=64)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    is_linked_to_withdrawal: int = Field(0, ge=0, le=1)
    future_withdrawal: Optional[int] = Field(None, ge=0, le=1)


class CybercrimeEventCreate(CybercrimeEventBase):
    pass


class CybercrimeEventRead(CybercrimeEventBase):
    id: int
    created_at: datetime
    has_geometry: bool = Field(False, description="True if PostGIS POINT was generated")

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Prediction Storage Schemas
# ==============================================================================

class PredictionResultCreate(BaseModel):
    prediction_reference: str = Field(..., max_length=64)
    prediction_timestamp: datetime
    predicted_probability: float = Field(..., ge=0.0, le=1.0)
    risk_score: int = Field(..., ge=0, le=100)
    risk_category: str = Field(..., max_length=32)
    operational_interpretation: Optional[str] = None
    model_version: str = Field(..., max_length=64)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    victim_district: Optional[str] = Field(None, max_length=64)
    crime_type: Optional[str] = Field(None, max_length=64)


class PredictionResultRead(BaseModel):
    id: int
    prediction_reference: str
    prediction_timestamp: datetime
    predicted_probability: float
    risk_score: int
    risk_category: str
    operational_interpretation: Optional[str]
    model_version: str
    latitude: Optional[float]
    longitude: Optional[float]
    victim_district: Optional[str]
    crime_type: Optional[str]
    created_at: datetime
    has_geometry: bool = False

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Spatial Query Request Schemas
# ==============================================================================

class SpatialRadiusQuery(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Center point latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Center point longitude")
    radius_meters: float = Field(..., gt=0.0, le=500000.0, description="Search radius in meters (max 500km)")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")


class SpatialBoundingBoxQuery(BaseModel):
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)
    limit: int = Field(100, ge=1, le=1000)

    @field_validator("max_lat")
    @classmethod
    def lat_order(cls, v: float, info):
        if "min_lat" in info.data and v < info.data["min_lat"]:
            raise ValueError("max_lat must be greater than or equal to min_lat")
        return v

    @field_validator("max_lon")
    @classmethod
    def lon_order(cls, v: float, info):
        if "min_lon" in info.data and v < info.data["min_lon"]:
            raise ValueError("max_lon must be greater than or equal to min_lon")
        return v


# ==============================================================================
# Database Health & Stats Schemas
# ==============================================================================

class DatabaseHealthResponse(BaseModel):
    status: Optional[str] = Field(None, description="'connected', 'disconnected', or 'error'")
    database: str = Field(..., description="'connected' or 'disconnected'")
    storage_mode: str = Field(
        "POSTGRESQL_POSTGIS",
        description="Active storage mode: 'POSTGRESQL_POSTGIS' or 'CSV_FALLBACK_DEV'",
    )
    database_host: Optional[str] = Field(None, description="Sanitized database host (no credentials)")
    database_name: Optional[str] = Field(None, description="Database name")
    postgis: bool = Field(..., description="True if PostGIS extension is available")
    postgis_version: Optional[str] = None
    error: Optional[str] = None
    setup_instructions: Optional[str] = Field(
        None,
        description="Guidance on connecting PostgreSQL/PostGIS or running in fallback mode",
    )


class DatabaseStatsResponse(BaseModel):
    total_events: int
    events_with_location: int
    location_coverage_percent: float
    total_predictions: int
    latest_event_timestamp: Optional[str] = None
    earliest_event_timestamp: Optional[str] = None
    districts_count: int
    crime_types_count: int


# ==============================================================================
# Phase 16 — Alert & Notification Schemas
# ==============================================================================

class AlertBase(BaseModel):
    alert_id: str = Field(..., max_length=64, description="Unique analytical alert identifier")
    alert_type: str = Field(..., max_length=64, description="Alert category type")
    severity: str = Field(..., max_length=32, description="LOW, MODERATE, HIGH, CRITICAL")
    status: str = Field("NEW", max_length=32, description="NEW, ACKNOWLEDGED, IN_REVIEW, RESOLVED, DISMISSED")
    prediction_reference: Optional[str] = None
    hotspot_id: Optional[str] = None
    risk_score: Optional[int] = Field(None, ge=0, le=100)
    predicted_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    event_count: Optional[int] = None
    dominant_category: Optional[str] = None
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    operational_message: str = "Analytical alert for authorized review."
    human_review_required: bool = True
    model_version: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class AlertCreate(AlertBase):
    created_at: Optional[datetime] = None


class AlertRead(AlertBase):
    id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    disclaimer: str = "Analytical alert — authorized human review required. Does not establish criminal activity."

    model_config = ConfigDict(from_attributes=True)


class AlertStatusUpdate(BaseModel):
    actor_type: str = Field("AUTHORIZED_USER", max_length=32)
    notes: Optional[str] = Field(None, description="Analyst rationale or review notes")


class AlertStatisticsResponse(BaseModel):
    total_alerts: int
    new_alerts: int
    critical_alerts: int
    high_alerts: int
    acknowledged_alerts: int
    in_review_alerts: int
    resolved_alerts: int
    dismissed_alerts: int
    alerts_by_type: dict = Field(default_factory=dict)


class AlertGenerationSummary(BaseModel):
    generated: int
    critical: int
    high: int
    moderate: int
    duplicates_skipped: int
    cooldown_skipped: int
    disclaimer: str = "Analytical signals generated for authorized review. No automated punitive actions performed."


class AuditLogRead(BaseModel):
    id: Optional[int] = None
    alert_id: str
    action: str
    previous_status: Optional[str]
    new_status: str
    timestamp: datetime
    actor_type: str
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)
