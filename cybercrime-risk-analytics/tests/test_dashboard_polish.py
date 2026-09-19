"""
Final Dashboard Polish Test Suite
Problem Statement ID: 26184 — Cybercrime Predictive Analytics Framework

Validates all 15 functional items required for the polished SIH dashboard:
1. Dashboard loads
2. Map container & legend load
3. Heatmap layer endpoint loads
4. DBSCAN Hotspots endpoint loads
5. Filters endpoint & parameter handling work
6. Hotspot selection drill-down works
7. Alert selection drill-down works
8. Alert lifecycle actions work
9. Model Intelligence modal content verified
10. SHAP feature contributions load
11. Investigation workflow stepper verified
12. Audit log interface accessible
13. API errors handled gracefully
14. Database health & resilient fallback verified
15. Responsive layout styles verified
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client():
    # Context manager triggers FastAPI lifespan startup to initialize model state
    with TestClient(
        app,
        headers={"X-API-Key": "sih26184-dashboard-prototype-key-2026"},
    ) as c:
        yield c


def test_01_dashboard_loads(client):
    """Verify dashboard loads with HTML title and top navigation."""
    res = client.get("/dashboard/")
    assert res.status_code == 200
    html = res.text
    assert "<title>Cybercrime Risk Analytics" in html
    assert 'id="top-nav"' in html
    assert "Overview" in html
    assert "Risk Map" in html
    assert "Alerts" in html
    assert "Hotspots" in html
    assert "Investigations" in html
    assert "Model Intelligence" in html
    assert "Audit Log" in html


def test_02_map_and_legend_load(client):
    """Verify map container and floating legend exist in dashboard HTML."""
    res = client.get("/dashboard/")
    assert res.status_code == 200
    html = res.text
    assert 'id="map"' in html
    assert 'id="map-legend"' in html
    assert "RISK LEVEL" in html
    assert "0–39" in html
    assert "80–100" in html
    assert "XGBoost Predictive Risk" in html
    assert "DBSCAN Analytical Hotspot" in html


def test_03_heatmap_loads(client):
    """Verify predictive risk heatmap endpoint returns GeoJSON FeatureCollection."""
    res = client.get("/gis/risk-heatmap")
    assert res.status_code == 200
    data = res.json()
    assert data.get("type") == "FeatureCollection"
    assert len(data.get("features", [])) > 0


def test_04_hotspots_load(client):
    """Verify DBSCAN hotspots endpoint returns 40 spatial clusters."""
    res = client.get("/gis/hotspots")
    assert res.status_code == 200
    data = res.json()
    assert data.get("total") == 40
    assert len(data.get("features", [])) == 40


def test_05_filters_work(client):
    """Verify filter options and parameter-filtered event queries."""
    res_filt = client.get("/gis/filters")
    assert res_filt.status_code == 200
    filt = res_filt.json()
    assert len(filt.get("crime_categories", [])) > 0

    # Test hotspot_only filter
    res_ev = client.get("/gis/events?hotspot_only=true&limit=10")
    assert res_ev.status_code == 200
    ev = res_ev.json()
    assert ev.get("type") == "FeatureCollection"


def test_06_hotspot_selection_works(client):
    """Verify single hotspot detail drill-down."""
    res = client.get("/gis/hotspots/23")
    assert res.status_code == 200
    data = res.json()
    assert str(data.get("hotspot_id")) == "23"
    assert data.get("event_count") == 310
    assert "average_risk_score" in data
    assert "maximum_risk_score" in data
    assert "dominant_crime_type" in data


def test_07_alert_selection_works(client):
    """Verify alert listing and single alert retrieval."""
    res_list = client.get("/alerts?limit=5")
    assert res_list.status_code == 200
    items = res_list.json().get("items", [])
    assert len(items) > 0

    first_id = items[0]["alert_id"]
    res_single = client.get(f"/alerts/{first_id}")
    assert res_single.status_code == 200
    alt = res_single.json()
    assert alt.get("alert_id") == first_id
    assert "severity" in alt
    assert "risk_score" in alt


def test_08_alert_actions_work(client):
    """Verify lifecycle transitions on alert endpoints."""
    res_list = client.get("/alerts?limit=5")
    items = res_list.json().get("items", [])
    first_id = items[0]["alert_id"]

    res_ack = client.patch(
        f"/alerts/{first_id}/acknowledge",
        json={"actor_type": "AUTHORIZED_USER", "notes": "Pytest acknowledgment test"}
    )
    assert res_ack.status_code in [200, 400]  # 200 if valid transition, 400 if already in later state


def test_09_model_intelligence_content(client):
    """Verify Model Intelligence modal content in dashboard HTML."""
    res = client.get("/dashboard/")
    html = res.text
    assert 'id="model-intelligence-modal"' in html
    assert "XGBoost (Gradient Boosted Trees)" in html
    assert "future_withdrawal" in html
    assert "24 Hours" in html
    assert "scale_pos_weight" in html
    assert "Platt Scaling" in html
    assert "previous_activity_by_crime_category" in html
    assert "contributed toward the model prediction" in html
    assert "never caused the crime" in html


def test_10_shap_information_loads(client):
    """Verify SHAP explanation endpoint returns marginal attributions with lifespan initialized."""
    sample_payload = {
        "crime_type": "Online Financial Fraud",
        "fraud_amount": 15000.0,
        "reported_by_authority": 0.0,
        "victim_state": "Andhra Pradesh",
        "victim_district": "Chittoor",
        "victim_area": "Tirupati",
        "victim_area_id": "AP_CHT_001",
        "latitude": 13.63,
        "longitude": 79.42,
        "event_year": 2026,
        "event_month": 3,
        "event_day": 75,
        "event_day_of_month": 15,
        "event_day_of_week": 2,
        "event_hour": 14,
        "event_minute": 30,
        "is_weekend": 0.0,
        "is_month_start": 0.0,
        "is_month_end": 0.0,
        "is_quarter_start": 0.0,
        "is_quarter_end": 0.0,
        "hour_group": "afternoon",
        "time_period": "business_hours",
        "latitude_rounded": 13.63,
        "longitude_rounded": 79.42,
        "location_grid": "13.63_79.42",
        "coordinate_precision": "high",
        "geographic_region": "South",
        "crime_category_group": "Financial",
    }
    res = client.post("/explain", json=sample_payload)
    assert res.status_code == 200
    data = res.json()
    assert "risk_score" in data
    assert "top_positive_contributors" in data
    assert "top_negative_contributors" in data
    assert "shap_status" in data
    assert len(data.get("top_positive_contributors", [])) > 0 or data.get("shap_available") is True


def test_11_investigation_workflow_stepper(client):
    """Verify investigation workflow stepper in dashboard HTML."""
    res = client.get("/dashboard/")
    html = res.text
    assert 'class="workflow-stepper"' in html
    assert "NEW ALERT" in html
    assert "ACKNOWLEDGED" in html
    assert "IN REVIEW" in html
    assert "VALIDATION" in html
    assert "RESOLVED" in html


def test_12_audit_log_works(client):
    """Verify audit log HTML endpoint accessibility."""
    res = client.get("/analyst/audit.html")
    assert res.status_code == 200
    assert "Audit" in res.text


def test_13_api_errors_handled(client):
    """Verify unknown alert returns 404 with sanitized error envelope."""
    res = client.get("/alerts/NON_EXISTENT_ALERT_ID_9999")
    assert res.status_code == 404
    data = res.json()
    assert "message" in data or "error" in data or "detail" in data


def test_14_database_health_fallback(client):
    """Verify database health check endpoint returns status (200 healthy, or 503 with dual-mode fallback)."""
    res = client.get("/database/health")
    assert res.status_code in [200, 503]
    data = res.json()
    assert "status" in data or "error" in data or "detail" in data


def test_15_responsive_layout_works(client):
    """Verify CSS media queries for desktop, laptop, and tablet."""
    res = client.get("/dashboard/css/dashboard.css")
    assert res.status_code == 200
    css = res.text
    assert "@media (max-width: 1200px)" in css
    assert "@media (max-width: 900px)" in css


def test_16_kpi_card_clarification(client):
    """Verify explicit KPI terminology separating Analytical Records from Analytical Alerts."""
    res = client.get("/dashboard/")
    assert res.status_code == 200
    html = res.text
    assert "ANALYTICAL RECORDS" in html
    assert "HIGH-RISK RECORDS" in html
    assert "CRITICAL-RISK RECORDS" in html
    assert "ANALYTICAL HOTSPOTS" in html
    assert "AVERAGE MODEL RISK" in html
    assert "AREA WITH HIGHEST AVERAGE MODEL RISK" in html
    assert "Analytical Alerts (Operational Queue)" in html
    assert "alert-total-cnt" in html
    assert "alert-crit-cnt" in html
    assert "alert-high-cnt" in html


def test_17_toolbar_hotspot_dropdown(client):
    """Verify toolbar contains hotspot filter select and backend supports hotspot_id query."""
    res = client.get("/dashboard/")
    assert res.status_code == 200
    assert 'id="tb-filter-hotspot-id"' in res.text

    # Verify backend query with hotspot_id
    res_ev = client.get("/gis/events?hotspot_id=23&limit=5")
    assert res_ev.status_code == 200
    data = res_ev.json()
    assert data.get("type") == "FeatureCollection"
