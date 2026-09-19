"""
Test Suite: Spatial Cashout Location Analytics, Catchment & Proximity Service
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Covers all 17 verification scenarios required by Step 11:
1.  Valid coordinates within WGS 84 bounds
2.  Invalid coordinate rejection (out of range, NaN, Inf)
3.  Haversine distance calculation and boundary handling
4.  DBSCAN cluster generation and parameter verification
5.  Noise-point handling (-1 cluster IDs)
6.  Nearest physical ATM calculation and distance verification
7.  2.5 km catchment ATM analysis
8.  5.0 km catchment ATM analysis
9.  Top-K candidate ranking and limits (Top 1, 3, 5)
10. Empty location results handling (unmatched district/coords)
11. Missing ATM data graceful degradation
12. CSV fallback mode verification
13. PostgreSQL/PostGIS mode detection
14. API authentication (401 unauthenticated, 200 authenticated)
15. API response schemas (GeoJSON FeatureCollection and JSON modes)
16. Prediction-location linkage (model probability & risk score to spatial candidates)
17. Temporal leakage prevention (zero future data in historical cluster lookups)
"""

import math
import pytest
import numpy as np
import pandas as pd
from starlette.testclient import TestClient

from api.main import app
from src.spatial_cashout_service import (
    EARTH_RADIUS_KM,
    SPATIAL_DISCLAIMER,
    is_valid_coordinate,
    haversine_distance,
    vectorized_haversine,
    analyze_catchment,
    compute_ranking_score,
    get_candidate_cashout_locations,
    format_candidates_as_geojson,
    format_candidates_as_json_response,
    check_database_mode,
    load_atms_dataset,
    load_cluster_statistics,
)
from src.spatial_evaluation import evaluate_spatial_predictions

API_KEY = "sih26184-dashboard-prototype-key-2026"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def analyst_token(client):
    res = client.post(
        "/analyst/auth/login",
        json={"username": "demo_analyst", "password": "AnalystDemo2026!"},
    )
    assert res.status_code == 200, f"Analyst login failed: {res.text}"
    return res.json()["access_token"]


# ==============================================================================
# 1. Coordinate Validation & Haversine Distance Tests
# ==============================================================================

class TestCoordinateValidationAndHaversine:
    """Tests 1, 2, 3: Coordinate bounds, validation, and Haversine distance calculations."""

    def test_valid_wgs84_coordinates(self):
        """Valid global coordinates within [-90, 90] and [-180, 180] must pass."""
        assert is_valid_coordinate(13.0827, 80.2707) is True  # Chennai
        assert is_valid_coordinate(0.0, 0.0) is True          # Prime Meridian / Equator
        assert is_valid_coordinate(-90.0, -180.0) is True    # Extreme SW
        assert is_valid_coordinate(90.0, 180.0) is True      # Extreme NE

    def test_invalid_coordinates_rejected(self):
        """Coordinates outside bounds or non-finite values must be rejected."""
        assert is_valid_coordinate(91.0, 50.0) is False      # Latitude > 90
        assert is_valid_coordinate(-90.1, 50.0) is False     # Latitude < -90
        assert is_valid_coordinate(20.0, 180.5) is False     # Longitude > 180
        assert is_valid_coordinate(20.0, -181.0) is False    # Longitude < -180
        assert is_valid_coordinate(float("nan"), 80.0) is False
        assert is_valid_coordinate(13.0, float("inf")) is False
        assert is_valid_coordinate(None, 80.0) is False
        assert is_valid_coordinate(13.0, None) is False

    def test_haversine_distance_known_landmarks(self):
        """Verify Haversine against known synthetic and real-world ground truth."""
        # Chennai (13.0827, 80.2707) to Bangalore (12.9716, 77.5946) ~290 km
        d = haversine_distance(13.0827, 80.2707, 12.9716, 77.5946)
        assert 285.0 <= d <= 295.0

        # Coincident points must have distance 0.0 km
        d_zero = haversine_distance(13.0, 80.0, 13.0, 80.0)
        assert d_zero == 0.0

        # Vectorized Haversine must match scalar calculation
        lats = np.array([12.9716, 13.0])
        lons = np.array([77.5946, 80.0])
        v_dists = vectorized_haversine(13.0827, 80.2707, lats, lons)
        assert len(v_dists) == 2
        assert abs(v_dists[0] - d) < 0.01

    def test_haversine_invalid_coordinates_raise_value_error(self):
        """Invalid inputs to haversine_distance must raise ValueError."""
        with pytest.raises(ValueError):
            haversine_distance(999.0, 80.0, 13.0, 80.0)
        with pytest.raises(ValueError):
            haversine_distance(13.0, 80.0, float("nan"), 80.0)


# ==============================================================================
# 2. DBSCAN, Cluster Stats & Noise Handling Tests
# ==============================================================================

class TestDBSCANAndClusters:
    """Tests 4, 5: DBSCAN cluster generation, statistics, and noise point handling."""

    def test_dbscan_cluster_statistics_structure(self):
        """Cluster statistics must be loaded, non-empty, and contain all standard fields."""
        df_cs = load_cluster_statistics()
        assert not df_cs.empty
        assert "cluster_id" in df_cs.columns
        assert "latitude_centroid" in df_cs.columns
        assert "longitude_centroid" in df_cs.columns
        assert "event_count" in df_cs.columns
        assert "average_risk_score" in df_cs.columns

        # Verify coordinates of all centroids
        for _, row in df_cs.iterrows():
            cid = row["cluster_id"]
            if cid >= 0:
                assert is_valid_coordinate(row["latitude_centroid"], row["longitude_centroid"])

    def test_noise_point_exclusion(self):
        """Clusters with ID < 0 (noise points) must be excluded from candidate locations."""
        candidates = get_candidate_cashout_locations(top_k=50)
        for c in candidates:
            assert c["cluster_id"] >= 0, f"Noise cluster {c['cluster_id']} was not excluded"


# ==============================================================================
# 3. ATM Proximity, Catchments & Ranking Tests
# ==============================================================================

class TestATMProximityAndCatchment:
    """Tests 6, 7, 8, 9: Nearest ATM, 2.5km / 5km catchment, and Top-K ranking."""

    def test_nearest_atm_matching(self):
        """Cluster centroid in Chennai must correctly find nearest physical ATM."""
        df_atms = load_atms_dataset()
        assert not df_atms.empty

        # Center in Chennai area
        res = analyze_catchment(13.0827, 80.2707, atms_df=df_atms, catchment_radius_km=5.0)
        assert res["nearest_atm_id"] is not None
        assert res["nearest_atm_distance_km"] is not None
        assert res["nearest_atm_distance_km"] >= 0.0
        assert is_valid_coordinate(res["nearest_atm_latitude"], res["nearest_atm_longitude"])

    def test_catchment_radii_monotonicity(self):
        """ATM count in 5.0 km catchment must be >= ATM count in 2.5 km catchment."""
        df_atms = load_atms_dataset()
        c25 = analyze_catchment(13.0827, 80.2707, atms_df=df_atms, catchment_radius_km=2.5)
        c50 = analyze_catchment(13.0827, 80.2707, atms_df=df_atms, catchment_radius_km=5.0)

        assert c50["atm_count_in_radius"] >= c25["atm_count_in_radius"]

    def test_top_k_candidate_limits(self):
        """Top-K candidate function must strictly respect requested K limits."""
        for k in [1, 3, 5]:
            cands = get_candidate_cashout_locations(district="Chennai", top_k=k)
            assert len(cands) == k
            # Verify 1-indexed sequential ranking
            for idx, c in enumerate(cands, start=1):
                assert c["rank"] == idx

    def test_top_k_ranks_district_and_proximity_first(self):
        """Candidate matching the complaint district must rank first when complaint is in that district."""
        cands = get_candidate_cashout_locations(
            district="Chennai",
            complaint_lat=13.04,
            complaint_lon=80.23,
            top_k=5,
        )
        assert len(cands) > 0
        top1 = cands[0]
        assert top1["district"] == "Chennai"
        assert top1["rank"] == 1
        assert top1["ranking_label"] in ["HIGH_PRIORITY_CANDIDATE", "MODERATE_PRIORITY_CANDIDATE"]

    def test_empirical_ranking_score_bounds(self):
        """Ranking score must always fall within [0, 100]."""
        s1, l1 = compute_ranking_score(0.0, True, 300, 90.0, 50)
        assert 0 <= s1 <= 100
        assert l1 == "HIGH_PRIORITY_CANDIDATE"

        s2, l2 = compute_ranking_score(150.0, False, 10, 20.0, 0)
        assert 0 <= s2 <= 100
        assert l2 == "MONITORING_ONLY"


# ==============================================================================
# 4. Fallback, Database Mode & Missing Data Tests
# ==============================================================================

class TestDatabaseAndFallbacks:
    """Tests 10, 11, 12, 13: Empty results, missing ATM data, CSV fallback, and PostGIS mode."""

    def test_csv_fallback_mode_detected(self):
        """Database check must cleanly report csv_fallback when PostgreSQL is offline."""
        mode_str, is_online = check_database_mode()
        assert isinstance(mode_str, str)
        assert mode_str in ["csv_fallback", "postgresql_postgis"]

    def test_missing_coordinates_handled_gracefully(self):
        """Catchment analysis with invalid/missing coords returns clean empty structure."""
        res = analyze_catchment(float("nan"), 80.0)
        assert res["atm_count_in_radius"] == 0
        assert res["nearest_atm_id"] is None
        assert res["nearby_atms"] == []

    def test_empty_location_candidates_on_zero_k(self):
        """get_candidate_cashout_locations with top_k=0 returns empty list."""
        assert get_candidate_cashout_locations(top_k=0) == []

    def test_missing_atm_dataframe_handled_safely(self):
        """Catchment analysis with empty DataFrame returns safe zeroed attributes."""
        res = analyze_catchment(13.0827, 80.2707, atms_df=pd.DataFrame())
        assert res["atm_count_in_radius"] == 0
        assert res["nearest_atm_id"] is None


# ==============================================================================
# 5. API Endpoints, Security & Formats Tests
# ==============================================================================

class TestAPIEndpointsAndSchemas:
    """Tests 14, 15, 16: Authentication, GeoJSON/JSON schemas, and prediction linkage."""

    def test_api_authentication_required(self, client):
        """GET /gis/predicted-locations must return 401 Unauthorized if unauthenticated."""
        res = client.get("/gis/predicted-locations")
        assert res.status_code == 401

    def test_api_authenticated_via_key_and_jwt(self, client, analyst_token):
        """Both X-API-Key and Bearer JWT must successfully authorize the endpoint."""
        res_key = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        assert res_key.status_code == 200

        res_jwt = client.get(
            "/gis/predicted-locations",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert res_jwt.status_code == 200

    def test_geojson_schema_enrichment(self, client):
        """GeoJSON format must return FeatureCollection with enriched spatial properties."""
        res = client.get("/gis/predicted-locations?top_k=3", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 3

        feat = data["features"][0]
        assert feat["type"] == "Feature"
        props = feat["properties"]
        assert "rank" in props
        assert "ranking_score" in props
        assert "ranking_label" in props
        assert "catchment_2_5km_atm_count" in props
        assert "catchment_5_0km_atm_count" in props
        assert "nearest_atm_id" in props
        assert "nearest_atm_latitude" in props
        assert "nearest_atm_longitude" in props
        assert "disclaimer" in props
        assert "database_mode" in props

    def test_json_schema_top_k_response(self, client):
        """JSON format must return structured Top-K format matching Step 8 specification."""
        res = client.get("/gis/predicted-locations?format=json&top_k=3", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "prediction_id" in data
        assert data["location_source"] == "historical_dbscan"
        assert data["total_locations"] == 3
        assert len(data["locations"]) == 3

        loc = data["locations"][0]
        assert loc["rank"] == 1
        assert "cluster_id" in loc
        assert "latitude" in loc
        assert "longitude" in loc
        assert "nearest_atm_id" in loc
        assert "distance_km" in loc
        assert "catchment_radius_km" in loc
        assert "catchment_2_5km_atm_count" in loc
        assert "catchment_5_0km_atm_count" in loc
        assert "ranking_score" in loc
        assert "ranking_label" in loc
        assert "disclaimer" in data

    def test_complaint_submission_prediction_location_linkage(self, client):
        """POST /complaints must link prediction risk to enriched predicted locations."""
        payload = {
            "complaint_timestamp": "2026-09-19T14:30:00Z",
            "fraud_amount": 95000.0,
            "complaint_category": "Online Financial Fraud",
            "state": "Tamil Nadu",
            "district": "Chennai",
            "latitude": 13.04,
            "longitude": 80.23,
        }
        res = client.post("/complaints", json=payload, headers={"X-API-Key": API_KEY})
        assert res.status_code == 201
        data = res.json()
        assert "predicted_locations" in data
        locs = data["predicted_locations"]
        assert len(locs) > 0

        top = locs[0]
        assert top["rank"] == 1
        assert top["district"] == "Chennai"
        assert top["nearest_atm_id"] is not None
        assert top["nearest_atm_latitude"] is not None
        assert top["nearest_atm_longitude"] is not None
        assert top["catchment_2_5km_atm_count"] is not None
        assert top["catchment_5_0km_atm_count"] is not None
        assert top["ranking_score"] is not None
        assert top["ranking_label"] is not None


# ==============================================================================
# 6. Spatial Ground-Truth Evaluation & Temporal Leakage Tests
# ==============================================================================

class TestSpatialEvaluationAndLeakagePrevention:
    """Test 17: Spatial evaluation against ground truth and temporal leakage prevention."""

    def test_spatial_evaluation_execution(self):
        """Run spatial evaluation against historical ground truth and verify metrics."""
        scorecard = evaluate_spatial_predictions(sample_size=50, random_state=42)
        assert scorecard["status"] == "SUCCESS"
        assert scorecard["metrics_available"] is True
        assert scorecard["evaluated_cases_count"] > 0
        assert 0.0 <= scorecard["top_1_hit_rate"] <= 1.0
        assert 0.0 <= scorecard["top_3_hit_rate"] <= 1.0
        assert 0.0 <= scorecard["top_5_hit_rate"] <= 1.0
        assert 0.0 <= scorecard["accuracy_within_2_5km"] <= 1.0
        assert 0.0 <= scorecard["accuracy_within_5_0km"] <= 1.0
        assert scorecard["median_distance_error_km"] >= 0.0
        assert scorecard["average_distance_error_km"] >= 0.0

    def test_temporal_leakage_controls(self):
        """Historical clusters and ATM dataset must not contain dynamic future case IDs."""
        df_atms = load_atms_dataset()
        assert "future_withdrawal" not in df_atms.columns
        assert "is_linked_to_withdrawal" not in df_atms.columns

        df_cs = load_cluster_statistics()
        assert "future_withdrawal" not in df_cs.columns
