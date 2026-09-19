"""
Phase 5 Test Suite — Predicted High-Risk Locations & Physical ATM Mapping
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests:
1. Rejection of unauthenticated requests (HTTP 401)
2. Success with static dashboard API key (X-API-Key)
3. Success with Bearer JWT token (analyst / supervisor / bank analyst)
4. GeoJSON FeatureCollection structure and point geometry validation
5. Enrichment with physical ATM density counts and nearest ATM ID
6. Proximity radius filtering variation
7. Mandatory disclaimer verification
8. Zero sensitive credential or PII leakage
"""
import pytest
from starlette.testclient import TestClient
from api.main import app

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


class TestPredictedLocationsAPI:
    """Test GET /gis/predicted-locations endpoint and ATM cross-referencing."""

    def test_unauthenticated_request_rejected(self, client):
        """Must return 401 Unauthorized if no API key or JWT token is provided."""
        res = client.get("/gis/predicted-locations")
        assert res.status_code == 401

    def test_authenticated_via_api_key(self, client):
        """X-API-Key header grants access."""
        res = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert len(data["features"]) > 0

    def test_authenticated_via_jwt_token(self, client, analyst_token):
        """Bearer JWT token grants access."""
        res = client.get(
            "/gis/predicted-locations",
            headers={"Authorization": f"Bearer {analyst_token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0

    def test_geojson_feature_properties(self, client):
        """Validate GeoJSON schema and enriched ATM properties."""
        res = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()

        for feat in data["features"]:
            assert feat["type"] == "Feature"
            geom = feat["geometry"]
            assert geom["type"] == "Point"
            coords = geom["coordinates"]
            assert len(coords) == 2
            lon, lat = coords
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0

            props = feat["properties"]
            assert "hotspot_id" in props
            assert "cluster_id" in props
            assert "district" in props
            assert "average_risk_score" in props
            assert "risk_category" in props
            assert "predicted_probability" in props
            assert "atm_count_in_radius" in props
            assert "nearest_atm_id" in props
            assert "nearest_atm_distance_km" in props
            assert "disclaimer" in props
            assert isinstance(props["atm_count_in_radius"], int)
            assert props["atm_count_in_radius"] >= 0

    def test_radius_parameter_affects_atm_counts(self, client):
        """Larger radius must include at least as many or more ATMs than smaller radius."""
        res_small = client.get(
            "/gis/predicted-locations?radius_km=1.0",
            headers={"X-API-Key": API_KEY},
        )
        res_large = client.get(
            "/gis/predicted-locations?radius_km=10.0",
            headers={"X-API-Key": API_KEY},
        )
        assert res_small.status_code == 200
        assert res_large.status_code == 200

        data_small = res_small.json()
        data_large = res_large.json()

        assert len(data_small["features"]) > 0
        assert len(data_large["features"]) > 0

        # For the first hotspot, 10km count must be >= 1km count
        small_count = data_small["features"][0]["properties"]["atm_count_in_radius"]
        large_count = data_large["features"][0]["properties"]["atm_count_in_radius"]
        assert large_count >= small_count

    def test_mandatory_disclaimer_present(self, client):
        """Validate presence of required analytical disclaimer."""
        res = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        data = res.json()
        assert "disclaimer" in data
        assert "Analytical" in data["disclaimer"]

    def test_zero_pii_leakage(self, client):
        """Zero credentials, passwords, or PII exposed."""
        res = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        content = res.text.lower()
        prohibited = ["password", "cvv", "card_number", "aadhaar", "secret_key", "pin_number", "atm_pin", "user_otp"]
        for term in prohibited:
            assert term not in content, f"Sensitive term '{term}' found in response"
