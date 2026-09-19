"""
Test Suite for Model Evaluation, Calibration, and Improvement (Phase 4 / PS ID 26184)
Cybercrime Predictive Analytics Framework

Covers Step 11 verification items:
 1. Model artifact loading
 2. Feature schema compatibility (86 features)
 3. Prediction output probability range [0.0, 1.0]
 4. Risk score calculation integer range [0, 100]
 5. Operational risk categories mapping
 6. SHAP tree explainability and non-zero attributions
 7. Chronological splitting monotonicity and zero overlap
 8. Leakage prevention (zero post-T0 features in X)
 9. Multi-threshold behavior and monotonic recall degradation
10. Calibration pipeline validity (Brier score reduction)
11. Missing feature imputation robustness
12. Model versioning and metadata fidelity
13. Dynamic complaint feature service V2 compatibility
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
import shap

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
PROC_DIR = BASE_DIR / "data" / "processed"


@pytest.fixture(scope="module")
def metadata():
    meta_path = MODELS_DIR / "metadata_v2_evaluation.json"
    assert meta_path.exists(), "metadata_v2_evaluation.json must exist"
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def feature_schema():
    schema_path = MODELS_DIR / "features_v2.json"
    assert schema_path.exists(), "features_v2.json must exist"
    with open(schema_path, "r", encoding="utf-8") as f:
        return list(json.load(f)["features"].keys())


@pytest.fixture(scope="module")
def base_model():
    model_path = MODELS_DIR / "xgboost_v2_model.pkl"
    assert model_path.exists(), "xgboost_v2_model.pkl must exist"
    return joblib.load(model_path)


@pytest.fixture(scope="module")
def calibrated_model():
    model_path = MODELS_DIR / "xgboost_v2_calibrated.pkl"
    assert model_path.exists(), "xgboost_v2_calibrated.pkl must exist"
    return joblib.load(model_path)


@pytest.fixture(scope="module")
def sample_test_data(feature_schema):
    test_df = pd.read_csv(PROC_DIR / "test_v2.csv")
    return test_df[feature_schema].iloc[:20].copy()


# ---------------------------------------------------------------------------
# 1. Model Artifact Loading
# ---------------------------------------------------------------------------
def test_01_model_loading(base_model, calibrated_model):
    assert base_model is not None
    assert calibrated_model is not None
    assert hasattr(base_model, "predict_proba")
    assert hasattr(calibrated_model, "predict_proba")


# ---------------------------------------------------------------------------
# 2. Feature Schema Compatibility
# ---------------------------------------------------------------------------
def test_02_feature_schema_compatibility(feature_schema, metadata):
    assert len(feature_schema) == 86
    assert metadata["feature_count"] == 86
    assert metadata["selected_features"] == feature_schema
    # Check for crucial transaction and account features
    expected_v2_feats = [
        "victim_account_type",
        "victim_account_age_days",
        "fraud_to_daily_amount_ratio",
        "case_prior_txn_count",
        "victim_outgoing_amount_24h",
        "victim_velocity_surge_ratio",
    ]
    for feat in expected_v2_feats:
        assert feat in feature_schema


# ---------------------------------------------------------------------------
# 3. Prediction Output Probability Range
# ---------------------------------------------------------------------------
def test_03_probability_range(calibrated_model, sample_test_data):
    probs = calibrated_model.predict_proba(sample_test_data)[:, 1]
    assert len(probs) == len(sample_test_data)
    assert np.all(probs >= 0.0)
    assert np.all(probs <= 1.0)
    assert not np.isnan(probs).any()
    assert not np.isinf(probs).any()


# ---------------------------------------------------------------------------
# 4. Risk Score Calculation
# ---------------------------------------------------------------------------
def test_04_risk_score_calculation(calibrated_model, sample_test_data):
    from src.predict import probability_to_risk_score
    probs = calibrated_model.predict_proba(sample_test_data)[:, 1]
    risk_scores = [probability_to_risk_score(p) for p in probs]
    for score in risk_scores:
        assert isinstance(score, int)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# 5. Operational Risk Categories Mapping
# ---------------------------------------------------------------------------
def test_05_risk_categories_mapping():
    from src.predict import assign_risk_category
    assert assign_risk_category(15) == "LOW"
    assert assign_risk_category(39) == "LOW"
    assert assign_risk_category(40) == "MODERATE"
    assert assign_risk_category(59) == "MODERATE"
    assert assign_risk_category(60) == "HIGH"
    assert assign_risk_category(79) == "HIGH"
    assert assign_risk_category(80) == "CRITICAL"
    assert assign_risk_category(100) == "CRITICAL"


# ---------------------------------------------------------------------------
# 6. SHAP Tree Explainability
# ---------------------------------------------------------------------------
def test_06_shap_explainability(base_model, sample_test_data):
    preprocessor = base_model.named_steps["preprocessor"]
    clf = base_model.named_steps["classifier"]
    
    X_trans = preprocessor.transform(sample_test_data.iloc[:3])
    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X_trans)
    
    assert shap_values.shape[0] == 3
    assert np.abs(shap_values).sum() > 0.0


# ---------------------------------------------------------------------------
# 7. Chronological Splitting Verification
# ---------------------------------------------------------------------------
def test_07_chronological_splitting():
    clean_df = pd.read_csv(PROC_DIR / "cleaned_cybercrime_data.csv")[["case_id", "complaint_timestamp"]]
    train_df = pd.read_csv(PROC_DIR / "train_v2.csv")[["case_id"]]
    val_df = pd.read_csv(PROC_DIR / "validation_v2.csv")[["case_id"]]
    test_df = pd.read_csv(PROC_DIR / "test_v2.csv")[["case_id"]]
    
    t_train = train_df.merge(clean_df, on="case_id")["complaint_timestamp"]
    t_val = val_df.merge(clean_df, on="case_id")["complaint_timestamp"]
    t_test = test_df.merge(clean_df, on="case_id")["complaint_timestamp"]
    
    # Train max must precede Validation min
    assert t_train.max() < t_val.min()
    # Validation max must precede Test min
    assert t_val.max() < t_test.min()


# ---------------------------------------------------------------------------
# 8. Leakage Prevention
# ---------------------------------------------------------------------------
def test_08_leakage_prevention(feature_schema):
    forbidden_leakage_features = [
        "future_withdrawal",
        "previous_event_count",
        "event_day",
        "event_month",
        "previous_activity_by_location",
        "location_total_previous_events",
        "previous_activity_by_district",
        "previous_activity_by_crime_category",
        "location_unique_crime_categories",
    ]
    for forbidden in forbidden_leakage_features:
        assert forbidden not in feature_schema, f"Leaked feature '{forbidden}' found in schema!"


# ---------------------------------------------------------------------------
# 9. Multi-Threshold Monotonic Behavior
# ---------------------------------------------------------------------------
def test_09_threshold_behavior(base_model, feature_schema):
    test_df = pd.read_csv(PROC_DIR / "test_v2.csv")
    y_test = test_df["future_withdrawal"].values
    probs = base_model.predict_proba(test_df[feature_schema])[:, 1]
    
    thresholds = [0.2, 0.4, 0.6, 0.8]
    recalls = []
    for th in thresholds:
        preds = (probs >= th).astype(int)
        tp = np.sum((preds == 1) & (y_test == 1))
        fn = np.sum((preds == 0) & (y_test == 1))
        recall = tp / (tp + fn)
        recalls.append(recall)
        
    # Recall must be non-increasing as threshold increases
    for i in range(len(recalls) - 1):
        assert recalls[i] >= recalls[i + 1]


# ---------------------------------------------------------------------------
# 10. Calibration Pipeline Validity
# ---------------------------------------------------------------------------
def test_10_calibration_validity(base_model, calibrated_model, feature_schema):
    from sklearn.metrics import brier_score_loss
    test_df = pd.read_csv(PROC_DIR / "test_v2.csv")
    y_test = test_df["future_withdrawal"].values
    X_test = test_df[feature_schema]
    
    raw_probs = base_model.predict_proba(X_test)[:, 1]
    cal_probs = calibrated_model.predict_proba(X_test)[:, 1]
    
    raw_brier = brier_score_loss(y_test, raw_probs)
    cal_brier = brier_score_loss(y_test, cal_probs)
    
    # Calibrated Brier score must be substantially lower (better calibrated)
    assert cal_brier < raw_brier
    assert cal_brier < 0.10


# ---------------------------------------------------------------------------
# 11. Missing Feature Imputation Robustness
# ---------------------------------------------------------------------------
def test_11_missing_value_handling(calibrated_model, sample_test_data):
    corrupted_data = sample_test_data.copy()
    # Introduce NaNs in both numerical and categorical columns
    corrupted_data.loc[0, "fraud_amount"] = np.nan
    corrupted_data.loc[0, "victim_account_age_days"] = np.nan
    corrupted_data.loc[0, "victim_account_type"] = np.nan
    corrupted_data.loc[1, "victim_outgoing_amount_24h"] = np.nan
    
    probs = calibrated_model.predict_proba(corrupted_data)[:, 1]
    assert not np.isnan(probs).any()
    assert 0.0 <= probs[0] <= 1.0


# ---------------------------------------------------------------------------
# 12. Model Versioning & Metadata Fidelity
# ---------------------------------------------------------------------------
def test_12_metadata_fidelity(metadata):
    assert metadata["problem_statement_id"] == "26184"
    assert "v2.1.0" in metadata["model_version"]
    assert metadata["target_definition"]["prediction_horizon"] == "24 hours"
    assert metadata["record_counts"]["training"] == 7000
    assert metadata["record_counts"]["validation"] == 1500
    assert metadata["record_counts"]["test"] == 1500
    assert "evaluation_metrics" in metadata


# ---------------------------------------------------------------------------
# 13. Dynamic Complaint Feature Service V2 Compatibility
# ---------------------------------------------------------------------------
def test_13_complaint_feature_service_v2(feature_schema):
    from src.complaint_feature_service import extract_features_from_complaint
    raw_complaint = {
        "complaint_timestamp": "2026-09-19T14:30:00Z",
        "fraud_amount": 85000.0,
        "complaint_category": "UPI_FRAUD",
        "state": "Karnataka",
        "district": "Bengaluru",
        "city": "Indiranagar",
        "latitude": 12.97,
        "longitude": 77.59,
        "sender_account_reference": "ACC000001",
    }
    extracted = extract_features_from_complaint(raw_complaint, expected_features=feature_schema)
    assert len(extracted) == len(feature_schema)
    for feat in feature_schema:
        assert feat in extracted
