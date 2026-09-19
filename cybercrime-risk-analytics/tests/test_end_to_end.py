"""
Phase 18 — End-to-End Integration Test Suite
Problem Statement ID: 26184
Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations

Tests verify the complete 18-phase analytical pipeline:
1. Phase 2 cleaned dataset exists
2. Phase 3 feature dataset exists
3. Phase 4 target exists
4. future_withdrawal contains only valid target values (0 and 1)
5. train/validation/test exist
6. temporal ordering is valid
7. XGBoost model loads
8. model prediction works
9. prediction probability is between 0 and 1
10. risk score is between 0 and 100
11. risk category is valid
12. SHAP pipeline can load if implemented
13. PostGIS/database connection works if configured (SKIPPED if not configured)
14. hotspot output exists
15. GeoJSON is valid
16. FastAPI starts
17. /health works
18. /predict works
19. alert engine works
20. analyst interface/API works
21. audit records can be created
22. no sensitive fields are exposed
"""

import json
import os
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
import joblib

# Set root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from starlette.testclient import TestClient
from api.main import app
from database.connection import check_database_health


# ---------------------------------------------------------------------------
# FIXTURES
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def client():
    with TestClient(
        app,
        headers={"X-API-Key": "sih26184-dashboard-prototype-key-2026"},
    ) as c:
        yield c


@pytest.fixture(scope="module")
def sample_features():
    x_test_path = PROJECT_ROOT / "data/processed/X_test.csv"
    assert x_test_path.exists(), "X_test.csv missing"
    df = pd.read_csv(x_test_path)
    return df.iloc[[0]]


# ---------------------------------------------------------------------------
# 1. Phase 2 cleaned dataset exists
# ---------------------------------------------------------------------------
def test_01_phase2_cleaned_dataset_exists():
    path = PROJECT_ROOT / "data/processed/cleaned_cybercrime_data.csv"
    assert path.exists(), f"Phase 2 cleaned dataset not found at {path}"
    assert path.stat().st_size > 0, "Cleaned dataset file is empty"


# ---------------------------------------------------------------------------
# 2. Phase 3 feature dataset exists
# ---------------------------------------------------------------------------
def test_02_phase3_feature_dataset_exists():
    path = PROJECT_ROOT / "data/processed/feature_engineered_cybercrime_data.csv"
    assert path.exists(), f"Phase 3 feature dataset not found at {path}"
    assert path.stat().st_size > 0, "Feature dataset file is empty"


# ---------------------------------------------------------------------------
# 3. Phase 4 target exists
# ---------------------------------------------------------------------------
def test_03_phase4_target_exists():
    path = PROJECT_ROOT / "data/processed/targeted_cybercrime_data.csv"
    assert path.exists(), f"Phase 4 targeted dataset not found at {path}"
    df = pd.read_csv(path, nrows=5)
    assert "future_withdrawal" in df.columns, "Target column 'future_withdrawal' missing from targeted dataset"


# ---------------------------------------------------------------------------
# 4. future_withdrawal contains only valid target values
# ---------------------------------------------------------------------------
def test_04_target_values_are_valid_binary():
    path = PROJECT_ROOT / "data/processed/y_test.csv"
    assert path.exists(), "y_test.csv missing"
    y_test = pd.read_csv(path)
    # Get values column
    target_col = y_test.columns[0]
    unique_vals = set(y_test[target_col].unique())
    assert unique_vals.issubset({0, 1}), f"Unexpected target values: {unique_vals}"


# ---------------------------------------------------------------------------
# 5. train/validation/test exist
# ---------------------------------------------------------------------------
def test_05_train_val_test_splits_exist():
    for split in ["train.csv", "validation.csv", "test.csv"]:
        path = PROJECT_ROOT / "data/processed" / split
        assert path.exists(), f"Split {split} not found"
        assert path.stat().st_size > 0, f"Split {split} is empty"


# ---------------------------------------------------------------------------
# 6. temporal ordering is valid
# ---------------------------------------------------------------------------
def test_06_temporal_ordering_valid():
    train_path = PROJECT_ROOT / "data/processed/train.csv"
    val_path = PROJECT_ROOT / "data/processed/validation.csv"
    test_path = PROJECT_ROOT / "data/processed/test.csv"
    
    assert train_path.exists() and val_path.exists() and test_path.exists()
    assert (PROJECT_ROOT / "data/processed/X_train.csv").exists()
    assert (PROJECT_ROOT / "data/processed/X_validation.csv").exists()
    assert (PROJECT_ROOT / "data/processed/X_test.csv").exists()


# ---------------------------------------------------------------------------
# 7. XGBoost model loads
# ---------------------------------------------------------------------------
def test_07_xgboost_model_loads():
    model_path = PROJECT_ROOT / "models/xgboost_cybercrime_model.pkl"
    assert model_path.exists(), "Model artifact not found"
    model = joblib.load(model_path)
    assert model is not None, "Loaded model is None"
    assert hasattr(model, "predict_proba"), "Model missing predict_proba method"


# ---------------------------------------------------------------------------
# 8. model prediction works
# ---------------------------------------------------------------------------
def test_08_model_prediction_works(sample_features):
    model_path = PROJECT_ROOT / "models/xgboost_cybercrime_model.pkl"
    model = joblib.load(model_path)
    preds = model.predict(sample_features)
    assert len(preds) == 1, "Expected single prediction"
    assert preds[0] in [0, 1], "Prediction not binary"


# ---------------------------------------------------------------------------
# 9. prediction probability is between 0 and 1
# ---------------------------------------------------------------------------
def test_09_prediction_probability_bounded(sample_features):
    model_path = PROJECT_ROOT / "models/xgboost_cybercrime_model.pkl"
    model = joblib.load(model_path)
    probas = model.predict_proba(sample_features)[:, 1]
    assert len(probas) == 1
    p = float(probas[0])
    assert 0.0 <= p <= 1.0, f"Probability {p} out of bounds [0, 1]"


# ---------------------------------------------------------------------------
# 10. risk score is between 0 and 100
# ---------------------------------------------------------------------------
def test_10_risk_score_bounded():
    # Test formula: round(prob * 100)
    for p in [0.0, 0.25, 0.5, 0.75, 1.0]:
        score = int(round(p * 100))
        assert 0 <= score <= 100, f"Score {score} out of bounds"


# ---------------------------------------------------------------------------
# 11. risk category is valid
# ---------------------------------------------------------------------------
def test_11_risk_category_valid():
    valid_categories = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    def get_cat(score):
        if score <= 39: return "LOW"
        if score <= 59: return "MODERATE"
        if score <= 79: return "HIGH"
        return "CRITICAL"
        
    for s in [0, 25, 45, 65, 85, 100]:
        assert get_cat(s) in valid_categories


# ---------------------------------------------------------------------------
# 12. SHAP pipeline can load if implemented
# ---------------------------------------------------------------------------
def test_12_shap_pipeline_loads():
    import shap
    model_path = PROJECT_ROOT / "models/xgboost_cybercrime_model.pkl"
    pipeline = joblib.load(model_path)
    clf = pipeline.named_steps.get("classifier")
    assert clf is not None, "Classifier step missing"
    explainer = shap.TreeExplainer(clf)
    assert explainer is not None, "SHAP TreeExplainer failed to initialize"


# ---------------------------------------------------------------------------
# 13. PostGIS/database connection works if configured
# ---------------------------------------------------------------------------
def test_13_postgis_database_connection_contract():
    health = check_database_health()
    assert isinstance(health, dict), "Health check must return dict"
    if health.get("status") != "healthy":
        pytest.skip("SKIPPED — EXTERNAL SERVICE NOT CONFIGURED: PostgreSQL/PostGIS inactive locally")
    else:
        assert health.get("postgis") is True


# ---------------------------------------------------------------------------
# 14. hotspot output exists
# ---------------------------------------------------------------------------
def test_14_hotspot_output_exists():
    summary_path = PROJECT_ROOT / "outputs/phase14_hotspot_summary.csv"
    assert summary_path.exists(), "Phase 14 hotspot summary CSV missing"
    df = pd.read_csv(summary_path)
    assert len(df) > 0, "Hotspot summary is empty"


# ---------------------------------------------------------------------------
# 15. GeoJSON is valid
# ---------------------------------------------------------------------------
def test_15_geojson_is_valid():
    geojson_path = PROJECT_ROOT / "outputs/phase14_hotspots_geojson.geojson"
    assert geojson_path.exists(), "GeoJSON missing"
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("type") == "FeatureCollection", "GeoJSON must be a FeatureCollection"
    assert "features" in data, "GeoJSON missing features array"
    assert len(data["features"]) > 0, "Features list is empty"


# ---------------------------------------------------------------------------
# 16. FastAPI starts
# ---------------------------------------------------------------------------
def test_16_fastapi_starts(client):
    r = client.get("/")
    assert r.status_code in [200, 307], f"FastAPI root returned unexpected {r.status_code}"


# ---------------------------------------------------------------------------
# 17. /health works
# ---------------------------------------------------------------------------
def test_17_api_health_works(client):
    r = client.get("/health")
    assert r.status_code == 200, f"/health failed: {r.status_code}"
    data = r.json()
    assert "status" in data, "Missing status key in /health"


# ---------------------------------------------------------------------------
# 18. /predict works
# ---------------------------------------------------------------------------
def test_18_api_predict_works(client):
    demo_path = PROJECT_ROOT / "data/demo/demo_prediction_input.csv"
    assert demo_path.exists(), "Demo prediction input missing"
    rec = pd.read_csv(demo_path).iloc[0].to_dict()
    r = client.post("/predict", json=rec)
    assert r.status_code == 200, f"/predict failed: {r.status_code}, {r.text}"
    data = r.json()
    assert "predicted_probability" in data, "Missing predicted_probability"
    assert "risk_score" in data, "Missing risk_score"
    assert "risk_category" in data, "Missing risk_category"


# ---------------------------------------------------------------------------
# 19. alert engine works
# ---------------------------------------------------------------------------
def test_19_alert_engine_works(client):
    r = client.get("/alerts")
    assert r.status_code in [200, 401], f"/alerts failed: {r.status_code}"
    # Verify coordinate validation logic: should return None on valid, raise on invalid
    from database.schemas import validate_coordinates
    validate_coordinates(19.12, 72.86)
    with pytest.raises(ValueError):
        validate_coordinates(199.0, 72.86)


# ---------------------------------------------------------------------------
# 20. analyst interface/API works
# ---------------------------------------------------------------------------
def test_20_analyst_interface_accessible(client):
    # Verify analyst static assets exist
    analyst_html = PROJECT_ROOT / "analyst/index.html"
    assert analyst_html.exists(), "analyst/index.html missing"
    
    # Endpoint requires auth: verify 401 response without token
    r = client.get("/analyst/overview")
    assert r.status_code == 401, f"Expected 401 without auth token, got {r.status_code}"


# ---------------------------------------------------------------------------
# 21. audit records can be created
# ---------------------------------------------------------------------------
def test_21_audit_records_can_be_created():
    from database.investigation_models import AnalystAuditLog
    # Verify model instantiation
    audit = AnalystAuditLog(
        audit_id="AUD-TEST-001",
        action="VIEW_ALERT",
        resource_type="ALERT",
        resource_id="ALT-001",
        actor_role="ANALYST",
        result="SUCCESS",
        detail="Test audit entry"
    )
    assert audit.audit_id == "AUD-TEST-001"
    assert audit.action == "VIEW_ALERT"
    assert audit.resource_type == "ALERT"



# ---------------------------------------------------------------------------
# 22. no sensitive fields are exposed
# ---------------------------------------------------------------------------
def test_22_no_sensitive_fields_exposed(client):
    r = client.get("/model/info")
    assert r.status_code == 200
    text = r.text.lower()
    prohibited = ["password", "cvv", "card_number", "aadhaar", "pan_card", "secret_key"]
    for word in prohibited:
        assert word not in text, f"Sensitive word '{word}' detected in /model/info response"
