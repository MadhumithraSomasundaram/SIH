"""
Phase 7 Integration Test Suite — Dashboard Map Integration
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Verifies:
1. Backend GET /gis/predicted-locations endpoint response format and contract:
   - GeoJSON FeatureCollection format with Point geometries
   - Structured JSON format (format=json)
   - Parameter filtering: top_k, radius_km, min_risk_score
   - Non-causal disclaimer and risk ranking scores
   - Nearby physical ATM enrichment
2. Frontend integration & DOM integrity:
   - dashboard/index.html contains all required toggles, filters, legend elements, and status alerts
   - dashboard/css/dashboard.css contains necessary styling for pins, popups, and badges
   - dashboard/js/map.js correctly manages layer groups, coordinates, caching, and sanitization
   - analyst/js/investigation.js includes estimated corridor labeling and disclaimers
3. Security & Safety:
   - Authentication requirement (401 for unauthenticated requests)
   - Zero sensitive PII leakage
   - Coordinate boundary validation
"""
import os
import re
import pytest
from starlette.testclient import TestClient
from api.main import app

API_KEY = "sih26184-dashboard-prototype-key-2026"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


@pytest.fixture(scope="module")
def bank_token(client):
    res = client.post(
        "/bank/auth/login",
        json={"username": "demo_bank", "password": "BankDemo2026!"},
    )
    assert res.status_code == 200, f"Bank login failed: {res.text}"
    return res.json()["access_token"]


class TestPredictedLocationsAPIContract:
    """Verify backend API contract for frontend map consumption."""

    def test_unauthenticated_request_rejected(self, client):
        res = client.get("/gis/predicted-locations")
        assert res.status_code == 401

    def test_geojson_format_default(self, client):
        res = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()
        assert data.get("type") == "FeatureCollection"
        assert "features" in data
        features = data["features"]
        assert len(features) > 0

        for f in features:
            assert f["type"] == "Feature"
            coords = f["geometry"]["coordinates"]
            assert len(coords) == 2
            lon, lat = coords
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0

            props = f["properties"]
            assert "cluster_id" in props or "hotspot_id" in props
            assert "average_risk_score" in props
            assert "predicted_probability" in props
            assert "ranking_score" in props
            assert "ranking_label" in props
            assert "atm_count_in_radius" in props
            assert "disclaimer" in props
            assert any(k in props["disclaimer"].lower() for k in ["analytical", "estimate", "pattern", "guarantee"])

    def test_structured_json_format(self, client):
        res = client.get("/gis/predicted-locations?format=json", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") in ["success", "empty_result"]
        assert "prediction_id" in data
        assert "locations" in data
        assert "disclaimer" in data
        assert isinstance(data["locations"], list)
        assert len(data["locations"]) > 0

        loc = data["locations"][0]
        assert "rank" in loc
        assert "latitude" in loc
        assert "longitude" in loc
        assert "risk_score" in loc
        assert "ranking_score" in loc
        assert "catchment_5_0km_atm_count" in loc
        assert "nearest_atm_id" in loc

    def test_top_k_parameter(self, client):
        res3 = client.get("/gis/predicted-locations?top_k=3", headers={"X-API-Key": API_KEY})
        assert res3.status_code == 200
        features3 = res3.json()["features"]
        assert len(features3) <= 3

        res7 = client.get("/gis/predicted-locations?top_k=7", headers={"X-API-Key": API_KEY})
        assert res7.status_code == 200
        features7 = res7.json()["features"]
        assert len(features7) <= 7
        assert len(features7) >= len(features3)

    def test_min_risk_score_parameter(self, client):
        res_high = client.get("/gis/predicted-locations?min_risk_score=75.0", headers={"X-API-Key": API_KEY})
        assert res_high.status_code == 200
        for f in res_high.json()["features"]:
            score = f["properties"].get("average_risk_score") or 0.0
            assert score >= 75.0

    def test_radius_parameter_catchments(self, client):
        res = client.get("/gis/predicted-locations?radius_km=3.0", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()
        for f in data["features"]:
            props = f["properties"]
            assert "catchment_2_5km_atm_count" in props
            assert "catchment_5_0km_atm_count" in props
            assert props["catchment_5_0km_atm_count"] >= props["catchment_2_5km_atm_count"]

    def test_disclaimer_non_causal_clarity(self, client):
        res = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        data = res.json()
        top_feature = data["features"][0]
        disclaimer = top_feature["properties"]["disclaimer"]
        # Must clearly communicate non-causality or lack of guaranteed future withdrawal
        assert any(term in disclaimer.lower() for term in ["analytical", "estimate", "decision support", "pattern", "not forecast", "does not establish", "guarantee"])

    def test_zero_pii_leakage(self, client):
        res = client.get("/gis/predicted-locations", headers={"X-API-Key": API_KEY})
        assert res.status_code == 200
        text = res.text.lower()
        forbidden_terms = ["password", "token", "aadhar", "ssn", "cvv", "otp", "secret_key"]
        for term in forbidden_terms:
            assert term not in text, f"Sensitive term '{term}' leaked in predicted-locations response!"


class TestDashboardHTMLIntegrity:
    """Verify frontend HTML structure in dashboard/index.html."""

    @pytest.fixture(scope="class")
    def html_content(self):
        path = os.path.join(BASE_DIR, "dashboard", "index.html")
        assert os.path.isfile(path), f"File not found: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_layer_toggle_checkbox_exists(self, html_content):
        assert 'id="layer-predicted-locations"' in html_content
        # Must be unchecked by default
        assert 'id="layer-predicted-locations" checked' not in html_content

    def test_modern_toggle_exists(self, html_content):
        assert 'id="toggle-predicted-layer"' in html_content

    def test_dedicated_card_exists(self, html_content):
        assert 'id="card-predicted-options"' in html_content

    def test_filter_controls_exist(self, html_content):
        assert 'id="filter-corridor-risk"' in html_content
        assert 'id="filter-corridor-limit"' in html_content
        assert 'id="toggle-catchment-circles"' in html_content
        assert 'id="toggle-atm-markers"' in html_content

    def test_status_indicators_exist(self, html_content):
        assert 'id="corridor-status-badge"' in html_content
        assert 'id="corridor-loading"' in html_content
        assert 'id="corridor-empty"' in html_content
        assert 'id="corridor-error"' in html_content

    def test_map_legend_entries_exist(self, html_content):
        assert "Predicted Cashout Corridors" in html_content
        assert "Predicted Corridor" in html_content
        assert "Nearby ATM" in html_content

    def test_non_causal_notice_in_ui(self, html_content):
        # Notice box must be present explaining the predictive nature
        assert "predicted corridors are estimated risk areas based on historical patterns" in html_content
        assert "Not confirmed criminal or withdrawal locations" in html_content


class TestDashboardCSSIntegrity:
    """Verify CSS styling in dashboard/css/dashboard.css."""

    @pytest.fixture(scope="class")
    def css_content(self):
        path = os.path.join(BASE_DIR, "dashboard", "css", "dashboard.css")
        assert os.path.isfile(path), f"File not found: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_predicted_corridor_styles_exist(self, css_content):
        assert ".predicted-ind" in css_content
        assert ".predicted-pin" in css_content
        assert ".atm-pin" in css_content
        assert ".corridor-popup-wrap" in css_content
        assert ".corridor-popup-warning" in css_content


class TestDashboardJSIntegrity:
    """Verify JavaScript logic in dashboard/js/map.js."""

    @pytest.fixture(scope="class")
    def js_content(self):
        path = os.path.join(BASE_DIR, "dashboard", "js", "map.js")
        assert os.path.isfile(path), f"File not found: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_layer_groups_declared(self, js_content):
        assert "_predictedLayer" in js_content
        assert "_catchmentLayer" in js_content
        assert "_atmLayer" in js_content

    def test_methods_implemented(self, js_content):
        assert "loadPredictedLocations" in js_content
        assert "clearPredictedLayers" in js_content
        assert "renderPredictedLocations" in js_content

    def test_public_api_exposes_methods(self, js_content):
        assert "loadPredictedLocations," in js_content
        assert "clearPredictedLayers," in js_content
        assert "renderPredictedLocations," in js_content

    def test_session_caching_used(self, js_content):
        assert "_predictedDataCache" in js_content

    def test_coordinate_validation_present(self, js_content):
        assert "Number.isFinite" in js_content
        assert "lat < -90" in js_content or "lat > 90" in js_content

    def test_xss_sanitization_present(self, js_content):
        assert "function esc(" in js_content or "escapeHtml" in js_content or "replace(/&/g" in js_content


class TestAnalystDossierIntegrity:
    """Verify analyst intelligence brief labeling and disclaimers."""

    @pytest.fixture(scope="class")
    def analyst_js_content(self):
        path = os.path.join(BASE_DIR, "analyst", "js", "investigation.js")
        assert os.path.isfile(path), f"File not found: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_estimated_corridor_labeling(self, analyst_js_content):
        assert "Estimated High-Risk Cashout Corridor" in analyst_js_content
        assert "Analytical Notice:" in analyst_js_content
        assert "do NOT predict exact criminal whereabouts" in analyst_js_content
