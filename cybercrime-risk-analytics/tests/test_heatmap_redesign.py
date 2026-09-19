"""
Professional GIS Heatmap Redesign Test Suite
Problem Statement ID: 26184 — Cybercrime Predictive Analytics Framework

Validates:
1. Default 40-district baseline preservation (contract compliance)
2. Density metric vs risk metric parameter handling
3. Dynamic temporal filtering (start_time, end_time)
4. Category filtering (crime_category, risk_category)
5. Empty filter scenario handling (clean FeatureCollection, message)
6. Coordinate bounds (-90 to 90, -180 to 180, non-zero)
7. Privacy: zero PII or sensitive account details
8. Methodological disclaimer present in properties
9. Response performance (<200ms)
"""

import time
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(
        app,
        headers={"X-API-Key": "sih26184-dashboard-prototype-key-2026"},
    ) as c:
        yield c


class TestHeatmapRedesign:
    def test_default_heatmap_contract(self, client):
        """Ensure default GET /gis/risk-heatmap returns exactly 40 districts."""
        res = client.get("/gis/risk-heatmap")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert data["total_districts"] == 40
        assert len(data["features"]) == 40
        assert data["metric"] == "risk"

    def test_density_metric_option(self, client):
        """Ensure metric=density returns valid weights and aggregation."""
        res = client.get("/gis/risk-heatmap?metric=density")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert data["metric"] == "density"
        for feat in data["features"]:
            w = feat["properties"].get("heatmap_weight")
            assert 0.0 <= w <= 1.0

    def test_risk_category_filtering(self, client):
        """Ensure risk_category query parameter updates heatmap data."""
        res = client.get("/gis/risk-heatmap?risk_category=HIGH")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        for feat in data["features"]:
            assert feat["properties"]["heatmap_weight"] >= 0.0

    def test_crime_category_filtering(self, client):
        """Ensure crime_category filtering returns subset."""
        res = client.get("/gis/risk-heatmap?crime_category=PAYMENT_FRAUD")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0

    def test_date_range_filtering(self, client):
        """Ensure temporal filters are respected."""
        res = client.get("/gis/risk-heatmap?start_time=2026-01-01&end_time=2026-01-31")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0

    def test_empty_filter_results_handled_gracefully(self, client):
        """Ensure non-matching filters return empty FeatureCollection with helpful message."""
        res = client.get("/gis/risk-heatmap?crime_category=NONEXISTENT_CATEGORY_9999")
        assert res.status_code == 200
        data = res.json()
        assert data["type"] == "FeatureCollection"
        assert data["total_districts"] == 0
        assert len(data["features"]) == 0
        assert "No geographic records match the selected filters." in data["message"]

    def test_coordinate_validity(self, client):
        """Ensure all returned coordinates are within valid geographic bounds and non-zero."""
        res = client.get("/gis/risk-heatmap")
        assert res.status_code == 200
        for feat in res.json()["features"]:
            coords = feat["geometry"]["coordinates"]
            assert len(coords) == 2
            lon, lat = coords
            assert -90.0 <= lat <= 90.0
            assert -180.0 <= lon <= 180.0
            assert not (lat == 0.0 and lon == 0.0)

    def test_no_pii_or_sensitive_leakage(self, client):
        """Ensure no sensitive banking or personal fields exist in heatmap features."""
        res = client.get("/gis/risk-heatmap")
        assert res.status_code == 200
        forbidden = {"account_number", "card_number", "cvv", "pin", "otp", "password", "phone", "email"}
        for feat in res.json()["features"]:
            props = feat.get("properties", {})
            for key in props:
                assert key.lower() not in forbidden, f"Forbidden field '{key}' leaked!"

    def test_disclaimer_present(self, client):
        """Ensure ethical/methodological disclaimer is included in properties."""
        res = client.get("/gis/risk-heatmap")
        assert res.status_code == 200
        for feat in res.json()["features"]:
            assert "disclaimer" in feat["properties"]
            assert "Analytical signal only" in feat["properties"]["disclaimer"]

    def test_performance_under_200ms(self, client):
        """Verify endpoint responds quickly."""
        t0 = time.time()
        res = client.get("/gis/risk-heatmap")
        elapsed_ms = (time.time() - t0) * 1000
        assert res.status_code == 200
        assert elapsed_ms < 200, f"Heatmap endpoint took {elapsed_ms}ms, expected <200ms"
