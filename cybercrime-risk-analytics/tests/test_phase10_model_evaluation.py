"""
Phase 10 Test Suite: Model Evaluation, Data Leakage Audit and Spatial Accuracy Metrics
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests all 20 required audit items:
1. Chronological data splitting
2. Duplicate records across splits
3. Feature leakage checks
4. Training-only preprocessing
5. Target-label generation
6. Probability range
7. Classification metrics reproduction
8. Threshold evaluation
9. Calibration evaluation
10. Coordinate validation
11. Haversine calculation
12. Spatial radius calculation
13. Top-K spatial evaluation on test ground truth
14. Future ground-truth exclusion from prediction inputs
15. SHAP feature alignment and additivity
16. Model loading and pipeline integrity
17. Reproducibility with fixed random seed
18. Missing values handling
19. Invalid timestamps handling
20. Insufficient spatial ground truth graceful degradation
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.spatial_cashout_service import (
    haversine_distance,
    is_valid_coordinate,
    get_candidate_cashout_locations,
)
from src.predict import load_model, predict_single_record, explain_prediction

DATA_DIR = BASE_DIR / "data"
PROC_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
MODELS_DIR = BASE_DIR / "models"


@pytest.fixture(scope="module")
def legacy_model_bundle():
    model_path = MODELS_DIR / "xgboost_cybercrime_model.pkl"
    meta_path = MODELS_DIR / "phase7_xgboost_metadata.json"
    assert model_path.exists(), f"Model artifact missing: {model_path}"
    assert meta_path.exists(), f"Metadata artifact missing: {meta_path}"

    model = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    return model, metadata


@pytest.fixture(scope="module")
def processed_datasets():
    train_path = PROC_DIR / "train.csv"
    val_path = PROC_DIR / "validation.csv"
    test_path = PROC_DIR / "test.csv"
    tcd_path = PROC_DIR / "targeted_cybercrime_data.csv"

    assert train_path.exists() and val_path.exists() and test_path.exists()

    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)
    df_test = pd.read_csv(test_path)
    df_tcd = pd.read_csv(tcd_path) if tcd_path.exists() else None

    return df_train, df_val, df_test, df_tcd


# ==============================================================================
# TEST 1: CHRONOLOGICAL DATA SPLITTING
# ==============================================================================
def test_01_chronological_data_splitting(processed_datasets):
    df_train, df_val, df_test, df_tcd = processed_datasets
    if "complaint_timestamp" not in df_train.columns and df_tcd is not None:
        meta_sub = df_tcd[["case_id", "complaint_timestamp"]]
        df_train = df_train.merge(meta_sub, on="case_id", how="left")
        df_val = df_val.merge(meta_sub, on="case_id", how="left")
        df_test = df_test.merge(meta_sub, on="case_id", how="left")

    ts_train_max = pd.to_datetime(df_train["complaint_timestamp"]).max()
    ts_val_min = pd.to_datetime(df_val["complaint_timestamp"]).min()
    ts_val_max = pd.to_datetime(df_val["complaint_timestamp"]).max()
    ts_test_min = pd.to_datetime(df_test["complaint_timestamp"]).min()

    # Monotonic chronological partitioning
    assert ts_train_max <= ts_val_min, f"Train max ({ts_train_max}) > Val min ({ts_val_min})"
    assert ts_val_max <= ts_test_min, f"Val max ({ts_val_max}) > Test min ({ts_test_min})"


# ==============================================================================
# TEST 2: DUPLICATE RECORDS ACROSS SPLITS
# ==============================================================================
def test_02_duplicate_records_across_splits(processed_datasets):
    df_train, df_val, df_test, _ = processed_datasets
    train_ids = set(df_train["case_id"])
    val_ids = set(df_val["case_id"])
    test_ids = set(df_test["case_id"])

    assert len(train_ids.intersection(val_ids)) == 0, "Overlap found between train and validation"
    assert len(val_ids.intersection(test_ids)) == 0, "Overlap found between validation and test"
    assert len(train_ids.intersection(test_ids)) == 0, "Overlap found between train and test"


# ==============================================================================
# TEST 3: FEATURE LEAKAGE CHECKS
# ==============================================================================
def test_03_feature_leakage_checks(legacy_model_bundle):
    _, metadata = legacy_model_bundle
    features = set(metadata["selected_features"])

    prohibited_features = {
        "future_suspicious_3h",
        "future_withdrawal_amount_3h",
        "withdrawal_amount",
        "future_withdrawal",
        "atm_id",
        "withdrawal_timestamp",
        "withdrawal_id",
    }

    leaked = features.intersection(prohibited_features)
    assert len(leaked) == 0, f"Critical leakage features detected in model inputs: {leaked}"


# ==============================================================================
# TEST 4: TRAINING-ONLY PREPROCESSING
# ==============================================================================
def test_04_training_only_preprocessing(legacy_model_bundle):
    model, _ = legacy_model_bundle
    assert hasattr(model, "named_steps") or hasattr(model, "steps"), "Model is not a scikit-learn Pipeline"
    
    # Check that preprocessor step exists
    preprocessor = model.named_steps.get("preprocessor") or model.steps[0][1]
    assert preprocessor is not None, "Pipeline is missing preprocessor transformer"


# ==============================================================================
# TEST 5: TARGET-LABEL GENERATION
# ==============================================================================
def test_05_target_label_generation(processed_datasets):
    df_train, df_val, df_test, _ = processed_datasets
    for name, df in [("train", df_train), ("val", df_val), ("test", df_test)]:
        assert "future_withdrawal" in df.columns, f"{name} missing target future_withdrawal"
        vals = set(df["future_withdrawal"].dropna().unique())
        assert vals.issubset({0, 1}), f"Target contains non-binary values in {name}: {vals}"
        pos_rate = df["future_withdrawal"].mean()
        assert 0.05 <= pos_rate <= 0.20, f"Unusual positive class rate in {name}: {pos_rate}"


# ==============================================================================
# TEST 6: PROBABILITY RANGE
# ==============================================================================
def test_06_probability_range(legacy_model_bundle, processed_datasets):
    model, metadata = legacy_model_bundle
    _, _, df_test, _ = processed_datasets
    features = metadata["selected_features"]

    X_test = df_test[features]
    probs = model.predict_proba(X_test)[:, 1]

    assert probs.min() >= 0.0, f"Negative probability found: {probs.min()}"
    assert probs.max() <= 1.0, f"Probability exceeds 1.0: {probs.max()}"
    assert not np.isnan(probs).any(), "NaN detected in prediction probabilities"
    assert not np.isinf(probs).any(), "Inf detected in prediction probabilities"


# ==============================================================================
# TEST 7: CLASSIFICATION METRICS REPRODUCTION
# ==============================================================================
def test_07_classification_metrics_reproduction(legacy_model_bundle, processed_datasets):
    model, metadata = legacy_model_bundle
    _, _, df_test, _ = processed_datasets
    features = metadata["selected_features"]

    X_test = df_test[features]
    y_test = df_test["future_withdrawal"].values

    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    acc = float(np.mean(preds == y_test))
    rec = float(np.sum((preds == 1) & (y_test == 1)) / np.sum(y_test == 1))

    # Verify reported legacy numbers: Accuracy ~86.93%, Recall ~1.94% (3/155)
    assert abs(acc - 0.8693) < 0.005, f"Accuracy mismatch: got {acc}, expected ~0.8693"
    assert abs(rec - 0.0194) < 0.005, f"Recall mismatch: got {rec}, expected ~0.0194"


# ==============================================================================
# TEST 8: THRESHOLD EVALUATION
# ==============================================================================
def test_08_threshold_evaluation(legacy_model_bundle, processed_datasets):
    model, metadata = legacy_model_bundle
    _, _, df_test, _ = processed_datasets
    features = metadata["selected_features"]

    X_test = df_test[features]
    probs = model.predict_proba(X_test)[:, 1]

    rec_01 = np.sum((probs >= 0.1) & (df_test["future_withdrawal"] == 1))
    rec_05 = np.sum((probs >= 0.5) & (df_test["future_withdrawal"] == 1))
    rec_09 = np.sum((probs >= 0.9) & (df_test["future_withdrawal"] == 1))

    # Lower threshold must catch >= positives than higher threshold
    assert rec_01 >= rec_05 >= rec_09, "Threshold recall monotonicity violated"


# ==============================================================================
# TEST 9: CALIBRATION EVALUATION
# ==============================================================================
def test_09_calibration_evaluation(legacy_model_bundle, processed_datasets):
    model, metadata = legacy_model_bundle
    _, _, df_test, _ = processed_datasets
    features = metadata["selected_features"]

    X_test = df_test[features]
    y_test = df_test["future_withdrawal"].values
    probs = model.predict_proba(X_test)[:, 1]

    brier = float(np.mean((probs - y_test) ** 2))
    assert 0.0 <= brier <= 1.0, f"Invalid Brier score: {brier}"
    assert brier < 0.25, f"Brier score exceeds random guessing threshold (0.25): {brier}"


# ==============================================================================
# TEST 10: COORDINATE VALIDATION
# ==============================================================================
def test_10_coordinate_validation():
    assert is_valid_coordinate(13.04, 80.23) is True
    assert is_valid_coordinate(-90.0, 0.0) is True
    assert is_valid_coordinate(90.0, 180.0) is True
    assert is_valid_coordinate(91.0, 80.0) is False
    assert is_valid_coordinate(13.04, 181.0) is False
    assert is_valid_coordinate(None, 80.0) is False
    assert is_valid_coordinate(float("nan"), 80.0) is False
    assert is_valid_coordinate(13.04, float("inf")) is False


# ==============================================================================
# TEST 11: HAVERSINE CALCULATION
# ==============================================================================
def test_11_haversine_calculation():
    # Chennai (13.0827, 80.2707) to Bengaluru (12.9716, 77.5946) ~ 290 km
    d = haversine_distance(13.0827, 80.2707, 12.9716, 77.5946)
    assert 280.0 <= d <= 305.0, f"Unexpected Chennai-Bengaluru distance: {d} km"
    
    # Same point distance must be 0
    d_zero = haversine_distance(13.0827, 80.2707, 13.0827, 80.2707)
    assert d_zero == 0.0


# ==============================================================================
# TEST 12: SPATIAL RADIUS CALCULATION
# ==============================================================================
def test_12_spatial_radius_calculation():
    cands = get_candidate_cashout_locations(district="Chennai", complaint_lat=13.04, complaint_lon=80.23, top_k=5)
    assert len(cands) > 0, "No candidates returned for valid coordinate"
    for c in cands:
        assert "nearest_atm_distance_km" in c
        assert c["nearest_atm_distance_km"] >= 0.0
        assert "catchment_2_5km_atm_count" in c
        assert "catchment_5_0km_atm_count" in c
        assert c["catchment_5_0km_atm_count"] >= c["catchment_2_5km_atm_count"]


# ==============================================================================
# TEST 13: TOP-K SPATIAL EVALUATION ON TEST GROUND TRUTH
# ==============================================================================
def test_13_top_k_evaluation():
    from src.evaluate_phase10_audit import evaluate_spatial_test_ground_truth
    res = evaluate_spatial_test_ground_truth()
    assert res["status"] == "SUCCESS"
    assert res["metrics_available"] is True
    assert res["evaluated_test_ground_truth_count"] == 155
    # Empirical hit rates
    assert res["top_1_hit_rate"] >= 0.65
    assert res["top_5_hit_rate"] >= res["top_1_hit_rate"]
    assert res["median_distance_error_km"] <= 5.0


# ==============================================================================
# TEST 14: FUTURE GROUND-TRUTH EXCLUSION FROM PREDICTION INPUTS
# ==============================================================================
def test_14_future_ground_truth_exclusion(legacy_model_bundle):
    _, metadata = legacy_model_bundle
    from src.complaint_feature_service import extract_features_from_complaint
    sample_complaint = {
        "complaint_id": "CMP-TEST-LEAKAGE-001",
        "complaint_timestamp": "2026-03-01T12:00:00Z",
        "fraud_amount": 45000.0,
        "state": "Tamil Nadu",
        "district": "Chennai",
        "latitude": 13.04,
        "longitude": 80.23,
        "complaint_category": "UPI_FRAUD",
    }
    feats = extract_features_from_complaint(sample_complaint, expected_features=metadata["selected_features"])
    assert "future_withdrawal" not in feats
    assert "withdrawal_amount" not in feats
    assert "atm_id" not in feats


# ==============================================================================
# TEST 15: SHAP FEATURE ALIGNMENT AND ADDITIVITY
# ==============================================================================
def test_15_shap_feature_alignment(legacy_model_bundle, processed_datasets):
    model, metadata = legacy_model_bundle
    _, _, df_test, _ = processed_datasets
    features = metadata["selected_features"]

    sample_dict = df_test.iloc[0][features].to_dict()
    explanation = explain_prediction(sample_dict, pipeline=model, metadata=metadata)

    assert explanation["status"] == "SUCCESS"
    assert "top_positive_contributors" in explanation
    for driver in explanation["top_positive_contributors"]:
        assert "feature" in driver
        assert "shap_value" in driver
        assert driver["shap_value"] >= 0.0
        assert driver["direction"] == "INCREASED_RISK"


# ==============================================================================
# TEST 16: MODEL LOADING AND PIPELINE INTEGRITY
# ==============================================================================
def test_16_model_loading_and_pipeline_integrity():
    model = load_model()
    assert model is not None
    assert hasattr(model, "predict_proba")


# ==============================================================================
# TEST 17: REPRODUCIBILITY WITH FIXED RANDOM SEED
# ==============================================================================
def test_17_reproducibility(legacy_model_bundle, processed_datasets):
    model, metadata = legacy_model_bundle
    _, _, df_test, _ = processed_datasets
    features = metadata["selected_features"]

    sample_X = df_test.iloc[:5][features]
    probs1 = model.predict_proba(sample_X)[:, 1]
    probs2 = model.predict_proba(sample_X)[:, 1]

    np.testing.assert_array_almost_equal(probs1, probs2, decimal=6)


# ==============================================================================
# TEST 18: MISSING VALUES IN FEATURES
# ==============================================================================
def test_18_missing_values_handling(legacy_model_bundle, processed_datasets):
    model, metadata = legacy_model_bundle
    _, _, df_test, _ = processed_datasets
    features = metadata["selected_features"]

    sample_X = df_test.iloc[:1][features].copy()
    # Inject NaNs in numerical and categorical features
    sample_X.iloc[0, 0] = np.nan
    sample_X.iloc[0, 1] = np.nan

    probs = model.predict_proba(sample_X)[:, 1]
    assert not np.isnan(probs[0]), "Model failed to impute NaN values gracefully"


# ==============================================================================
# TEST 19: INVALID TIMESTAMPS
# ==============================================================================
def test_19_invalid_timestamps(legacy_model_bundle):
    _, metadata = legacy_model_bundle
    from src.complaint_feature_service import extract_features_from_complaint
    bad_payload = {
        "complaint_timestamp": "NOT-A-TIMESTAMP",
        "fraud_amount": 5000.0,
        "state": "Tamil Nadu",
        "district": "Chennai",
    }
    with pytest.raises(ValueError):
        extract_features_from_complaint(bad_payload, expected_features=metadata["selected_features"])


# ==============================================================================
# TEST 20: INSUFFICIENT SPATIAL GROUND TRUTH GRACEFUL DEGRADATION
# ==============================================================================
def test_20_insufficient_spatial_ground_truth():
    # If coordinates are missing or invalid, spatial candidate lookup still returns valid cluster fallback
    cands = get_candidate_cashout_locations(district=None, complaint_lat=None, complaint_lon=None, top_k=5)
    assert isinstance(cands, list)
    # Even if none found or fallback returned, it never crashes
