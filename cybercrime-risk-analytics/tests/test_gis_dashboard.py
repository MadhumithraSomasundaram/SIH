"""
Phase 15 — GIS Dashboard Tests
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests all /gis/* endpoints for:
- Correct response structure
- GeoJSON validity
- Privacy/PII field exclusion
- Input validation / error handling
- Coordinate bounds
- No future-data leakage

Usage:
    pytest tests/test_gis_dashboard.py -v
"""

import json
from pathlib import Path

import pandas as pd
import pytest

# FastAPI TestClient
from fastapi.testclient import TestClient

# Ensure project root is on path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import app

client = TestClient(
    app,
    raise_server_exceptions=False,
    headers={"X-API-Key": "sih26184-dashboard-prototype-key-2026"},
)

# ---------------------------------------------------------------------------
# Sensitive fields that MUST NOT appear in any response
# ---------------------------------------------------------------------------
SENSITIVE_FIELDS = {
    "account_number", "card_number", "cvv", "pin", "otp", "password",
    "phone", "email", "victim_phone", "victim_email",
    "aadhaar", "pan", "ifsc",
}

# Leakage fields — future-derived information must not enter the dashboard
LEAKAGE_FIELDS = {
    "future_withdrawal",  # ground truth label from training data
}


def _check_no_sensitive(obj, path="root"):
    """Recursively assert no sensitive field appears in a JSON response."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k.lower() not in SENSITIVE_FIELDS, (
                f"Sensitive field '{k}' found at path {path}.{k}"
            )
            _check_no_sensitive(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _check_no_sensitive(v, f"{path}[{i}]")


def _check_no_leakage(obj, path="root"):
    """Recursively assert no leakage field appears in a JSON response."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k.lower() not in LEAKAGE_FIELDS, (
                f"Leakage field '{k}' found at path {path}.{k}"
            )
            _check_no_leakage(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _check_no_leakage(v, f"{path}[{i}]")


def _valid_geojson_feature_collection(data):
    assert data.get("type") == "FeatureCollection", "type must be FeatureCollection"
    assert "features" in data, "Missing 'features' key"
    assert isinstance(data["features"], list), "features must be a list"


def _valid_coordinates(features):
    for i, feat in enumerate(features):
        geom = feat.get("geometry", {})
        assert geom.get("type") == "Point", f"Feature {i}: geometry must be Point"
        coords = geom.get("coordinates", [])
        assert len(coords) == 2, f"Feature {i}: coordinates must have 2 values"
        lon, lat = coords
        assert isinstance(lon, (int, float)) and not (lon != lon), f"Feature {i}: lon is NaN"
        assert isinstance(lat, (int, float)) and not (lat != lat), f"Feature {i}: lat is NaN"
        assert -180 <= lon <= 180, f"Feature {i}: longitude {lon} out of range"
        assert -90 <= lat <= 90, f"Feature {i}: latitude {lat} out of range"
        # Verify coordinates are within South India bounding box
        assert 74 <= lon <= 84, f"Feature {i}: longitude {lon} outside expected South India range"
        assert 8 <= lat <= 18, f"Feature {i}: latitude {lat} outside expected South India range"


# ==============================================================================
# 1. Health checks
# ==============================================================================

class TestHealthEndpoints:
    def test_api_root_ok(self):
        res = client.get("/")
        assert res.status_code == 200

    def test_model_health_ok(self):
        res = client.get("/health")
        assert res.status_code == 200


# ==============================================================================
# 2. GIS Summary
# ==============================================================================

class TestGISSummary:
    def test_summary_ok(self):
        res = client.get("/gis/summary")
        assert res.status_code == 200

    def test_summary_has_required_fields(self):
        res = client.get("/gis/summary")
        d = res.json()
        for field in ["total_analytical_records", "hotspot_count", "average_risk_score"]:
            assert field in d, f"Missing field: {field}"

    def test_summary_no_sensitive_fields(self):
        res = client.get("/gis/summary")
        _check_no_sensitive(res.json())

    def test_summary_no_leakage_fields(self):
        res = client.get("/gis/summary")
        _check_no_leakage(res.json())

    def test_summary_total_positive(self):
        res = client.get("/gis/summary")
        assert res.json()["total_analytical_records"] > 0

    def test_summary_hotspot_count_positive(self):
        res = client.get("/gis/summary")
        assert res.json()["hotspot_count"] > 0


# ==============================================================================
# 3. GIS Events
# ==============================================================================

class TestGISEvents:
    def test_events_ok(self):
        res = client.get("/gis/events?limit=10")
        assert res.status_code == 200

    def test_events_is_geojson(self):
        res = client.get("/gis/events?limit=10")
        _valid_geojson_feature_collection(res.json())

    def test_events_valid_coordinates(self):
        res = client.get("/gis/events?limit=50")
        _valid_coordinates(res.json()["features"])

    def test_events_no_sensitive_fields(self):
        res = client.get("/gis/events?limit=20")
        _check_no_sensitive(res.json())

    def test_events_no_leakage_fields(self):
        res = client.get("/gis/events?limit=20")
        _check_no_leakage(res.json())

    def test_events_risk_filter_high(self):
        res = client.get("/gis/events?risk_category=HIGH&limit=100")
        assert res.status_code == 200
        for feat in res.json()["features"]:
            rc = feat["properties"].get("risk_category")
            assert rc == "HIGH" or rc is None, f"Expected HIGH, got {rc}"

    def test_events_invalid_risk_category(self):
        res = client.get("/gis/events?risk_category=EXTREME")
        assert res.status_code == 422

    def test_events_invalid_start_time(self):
        res = client.get("/gis/events?start_time=notadate")
        assert res.status_code == 422

    def test_events_limit_respected(self):
        res = client.get("/gis/events?limit=5")
        data = res.json()
        assert len(data["features"]) <= 5

    def test_events_limit_too_large(self):
        res = client.get("/gis/events?limit=9999")
        # Should clamp or reject (limit max is 5000)
        assert res.status_code in (200, 422)

    def test_events_date_filter(self):
        res = client.get("/gis/events?start_time=2026-01-01&end_time=2026-03-31&limit=50")
        assert res.status_code == 200

    def test_events_risk_score_filter(self):
        res = client.get("/gis/events?min_risk_score=60&max_risk_score=100&limit=50")
        assert res.status_code == 200
        for feat in res.json()["features"]:
            score = feat["properties"].get("risk_score")
            if score is not None:
                assert score >= 60, f"Expected score >= 60, got {score}"


# ==============================================================================
# 4. GIS Risk Heatmap
# ==============================================================================

class TestGISHeatmap:
    def test_heatmap_ok(self):
        res = client.get("/gis/risk-heatmap")
        assert res.status_code == 200

    def test_heatmap_is_geojson(self):
        res = client.get("/gis/risk-heatmap")
        _valid_geojson_feature_collection(res.json())

    def test_heatmap_valid_coordinates(self):
        res = client.get("/gis/risk-heatmap")
        _valid_coordinates(res.json()["features"])

    def test_heatmap_no_sensitive_fields(self):
        res = client.get("/gis/risk-heatmap")
        _check_no_sensitive(res.json())

    def test_heatmap_weight_range(self):
        res = client.get("/gis/risk-heatmap")
        for feat in res.json()["features"]:
            w = feat["properties"].get("heatmap_weight")
            if w is not None:
                assert 0.0 <= w <= 1.0, f"heatmap_weight {w} out of [0,1]"

    def test_heatmap_has_40_districts(self):
        res = client.get("/gis/risk-heatmap")
        data = res.json()
        assert data["total_districts"] == 40


# ==============================================================================
# 5. GIS Hotspots
# ==============================================================================

class TestGISHotspots:
    def test_hotspots_ok(self):
        res = client.get("/gis/hotspots")
        assert res.status_code == 200

    def test_hotspots_is_geojson(self):
        res = client.get("/gis/hotspots")
        _valid_geojson_feature_collection(res.json())

    def test_hotspots_valid_coordinates(self):
        res = client.get("/gis/hotspots")
        _valid_coordinates(res.json()["features"])

    def test_hotspots_no_sensitive_fields(self):
        res = client.get("/gis/hotspots")
        _check_no_sensitive(res.json())

    def test_hotspots_no_leakage_fields(self):
        res = client.get("/gis/hotspots")
        _check_no_leakage(res.json())

    def test_hotspots_count_40(self):
        res = client.get("/gis/hotspots")
        assert res.json()["total"] == 40

    def test_hotspots_status_filter(self):
        res = client.get("/gis/hotspots?status_filter=HIGH_ACTIVITY")
        assert res.status_code == 200

    def test_hotspots_invalid_status_filter(self):
        res = client.get("/gis/hotspots?status_filter=CRIMINAL_ZONE")
        assert res.status_code == 422

    def test_hotspots_has_disclaimer(self):
        res = client.get("/gis/hotspots")
        for feat in res.json()["features"]:
            assert "disclaimer" in feat["properties"]


# ==============================================================================
# 6. Hotspot Detail
# ==============================================================================

class TestHotspotDetail:
    def test_hotspot_detail_ok(self):
        # Hotspot 23 is rank 1
        res = client.get("/gis/hotspots/23")
        assert res.status_code == 200

    def test_hotspot_detail_fields(self):
        res = client.get("/gis/hotspots/23")
        d = res.json()
        for field in ["hotspot_id", "hotspot_rank", "event_count", "centroid_latitude",
                      "centroid_longitude", "average_risk_score", "disclaimer"]:
            assert field in d, f"Missing field: {field}"

    def test_hotspot_detail_no_sensitive(self):
        res = client.get("/gis/hotspots/23")
        _check_no_sensitive(res.json())

    def test_hotspot_detail_invalid_id(self):
        res = client.get("/gis/hotspots/9999")
        assert res.status_code == 404

    def test_hotspot_detail_has_disclaimer(self):
        res = client.get("/gis/hotspots/23")
        d = res.json()
        assert "disclaimer" in d
        assert len(d["disclaimer"]) > 10


# ==============================================================================
# 7. Filters
# ==============================================================================

class TestGISFilters:
    def test_filters_ok(self):
        res = client.get("/gis/filters")
        assert res.status_code == 200

    def test_filters_has_crime_categories(self):
        res = client.get("/gis/filters")
        d = res.json()
        assert "crime_categories" in d
        assert len(d["crime_categories"]) > 0

    def test_filters_has_risk_categories(self):
        res = client.get("/gis/filters")
        d = res.json()
        assert set(d["risk_categories"]) == {"LOW", "MODERATE", "HIGH", "CRITICAL"}

    def test_filters_has_hotspot_ids(self):
        res = client.get("/gis/filters")
        d = res.json()
        assert len(d["hotspot_ids"]) == 40

    def test_filters_time_range_valid(self):
        res = client.get("/gis/filters")
        d = res.json()
        tr = d.get("time_range", {})
        assert tr.get("earliest") is not None
        assert tr.get("latest") is not None


# ==============================================================================
# 8. Statistics
# ==============================================================================

class TestGISStatistics:
    def test_statistics_ok(self):
        res = client.get("/gis/statistics")
        assert res.status_code == 200

    def test_statistics_has_risk_distribution(self):
        res = client.get("/gis/statistics")
        d = res.json()
        assert "risk_category_distribution" in d

    def test_statistics_no_sensitive_fields(self):
        res = client.get("/gis/statistics")
        _check_no_sensitive(res.json())

    def test_statistics_has_top_hotspots(self):
        res = client.get("/gis/statistics")
        d = res.json()
        assert "top_hotspots" in d
        assert len(d["top_hotspots"]) > 0


class TestGISAuthentication:
    def test_gis_summary_unauthenticated_returns_401(self):
        unauth = TestClient(app, raise_server_exceptions=False)
        res = unauth.get("/gis/summary")
        assert res.status_code == 401
        assert "Authentication required" in res.text

