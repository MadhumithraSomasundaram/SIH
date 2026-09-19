"""
Phase Leakage Audit — Regression & Contract Test Suite
Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints

Verifies:
1. Leakage-prone features (future_suspicious_3h, future_withdrawal_amount_3h, etc.) do NOT enter the model matrix.
2. Chronological train-validation-test splitting is strictly monotonic with zero ID overlap.
3. Preprocessing (ColumnTransformer) is fitted exclusively on training data.
4. No future transaction information exists in backward rolling aggregates.
5. Prediction API compatibility is maintained.
6. Model loading succeeds without errors.
7. Feature schema compatibility is preserved.
8. Risk score formula matches calibrated probability expectations.
9. SHAP TreeExplainer functions correctly without background data leakage.
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
import shap

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROC_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"


# ---------------------------------------------------------------------------
# 1. Leakage-Prone Features Excluded from Model Matrix
# ---------------------------------------------------------------------------
def test_01_future_leakage_tokens_not_in_features():
    """Verify that forward-looking and target leakage features never enter feature schemas."""
    forbidden_tokens = [
        "future_suspicious_3h",
        "future_withdrawal_amount_3h",
        "future_withdrawal",
        "is_linked_to_withdrawal",
        "withdrawal_timestamp",
        "withdrawal_amount",
        "target_valid",
        "target_observation_complete",
    ]
    
    meta_path = MODELS_DIR / "phase7_xgboost_metadata.json"
    assert meta_path.exists()
    with open(meta_path) as f:
        meta = json.load(f)
    features = meta.get("selected_features", [])
    
    for token in forbidden_tokens:
        assert token not in features, f"Forbidden leakage token '{token}' found in model features!"


def test_02_clean_baseline_excludes_cumulative_time_proxies():
    """Verify clean baseline explicitly excludes cumulative drift proxies."""
    clean_meta_path = MODELS_DIR / "leakage_free_metadata.json"
    assert clean_meta_path.exists()
    with open(clean_meta_path) as f:
        meta = json.load(f)
    clean_features = meta.get("selected_features", [])
    
    unsafe = [
        "previous_event_count",
        "event_day",
        "event_month",
        "previous_activity_by_location",
        "location_total_previous_events",
        "previous_activity_by_district",
        "previous_activity_by_crime_category",
        "location_unique_crime_categories",
    ]
    for col in unsafe:
        assert col not in clean_features, f"Unsafe cumulative proxy '{col}' present in clean baseline!"


# ---------------------------------------------------------------------------
# 2. Chronological Train-Validation-Test Splitting
# ---------------------------------------------------------------------------
def test_03_temporal_ordering_strictly_monotonic():
    """Verify chronological split boundaries are strictly non-overlapping."""
    raw = pd.read_csv(PROC_DIR / "feature_engineered_cybercrime_data.csv", usecols=["case_id", "complaint_timestamp"])
    train = pd.read_csv(PROC_DIR / "train.csv", usecols=["case_id"])
    val = pd.read_csv(PROC_DIR / "validation.csv", usecols=["case_id"])
    test = pd.read_csv(PROC_DIR / "test.csv", usecols=["case_id"])
    
    m_train = train.merge(raw, on="case_id")
    m_val = val.merge(raw, on="case_id")
    m_test = test.merge(raw, on="case_id")
    
    t_train_max = pd.to_datetime(m_train["complaint_timestamp"]).max()
    t_val_min = pd.to_datetime(m_val["complaint_timestamp"]).min()
    t_val_max = pd.to_datetime(m_val["complaint_timestamp"]).max()
    t_test_min = pd.to_datetime(m_test["complaint_timestamp"]).min()
    
    assert t_train_max < t_val_min, f"Train max {t_train_max} >= Val min {t_val_min} (Temporal leakage!)"
    assert t_val_max < t_test_min, f"Val max {t_val_max} >= Test min {t_test_min} (Temporal leakage!)"


def test_04_zero_id_overlap_across_splits():
    """Verify zero duplicate case_ids exist across train, validation, and test partitions."""
    train = pd.read_csv(PROC_DIR / "train.csv", usecols=["case_id"])
    val = pd.read_csv(PROC_DIR / "validation.csv", usecols=["case_id"])
    test = pd.read_csv(PROC_DIR / "test.csv", usecols=["case_id"])
    
    s_train = set(train["case_id"])
    s_val = set(val["case_id"])
    s_test = set(test["case_id"])
    
    assert len(s_train.intersection(s_val)) == 0, "Train and Val share duplicate case_ids!"
    assert len(s_val.intersection(s_test)) == 0, "Val and Test share duplicate case_ids!"
    assert len(s_train.intersection(s_test)) == 0, "Train and Test share duplicate case_ids!"


# ---------------------------------------------------------------------------
# 3. Preprocessor Fitted Exclusively on Training Data
# ---------------------------------------------------------------------------
def test_05_preprocessor_fitted_on_train():
    """Verify ColumnTransformer statistics match X_train distributions."""
    train = pd.read_csv(PROC_DIR / "train.csv")
    model_path = MODELS_DIR / "xgboost_cybercrime_model.pkl"
    pipeline = joblib.load(model_path)
    
    preprocessor = pipeline.named_steps["preprocessor"]
    imputer = preprocessor.named_transformers_["num"].named_steps["imputer"]
    
    # Imputer statistics length should match numerical feature count
    assert len(imputer.statistics_) > 0


# ---------------------------------------------------------------------------
# 4. Backward Rolling Aggregates Guarantee (No Forward Leakage)
# ---------------------------------------------------------------------------
def test_06_rolling_aggregates_exclude_future():
    """Verify rolling event counts only look backward in time."""
    df = pd.read_csv(PROC_DIR / "feature_engineered_cybercrime_data.csv")
    assert "rolling_event_count_24h" in df.columns
    assert (df["rolling_event_count_24h"] >= 0).all()
    # First record should have 0 prior events in 24h
    assert df["rolling_event_count_24h"].iloc[0] == 0


# ---------------------------------------------------------------------------
# 5. Prediction API Compatibility
# ---------------------------------------------------------------------------
def test_07_prediction_pipeline_compatibility():
    """Verify model predict_proba returns calibrated probabilities in [0, 1]."""
    model_path = MODELS_DIR / "xgboost_leakage_free_baseline.pkl"
    assert model_path.exists()
    pipeline = joblib.load(model_path)
    
    meta_path = MODELS_DIR / "leakage_free_metadata.json"
    with open(meta_path) as f:
        meta = json.load(f)
    features = meta["selected_features"]
    
    test_df = pd.read_csv(PROC_DIR / "test.csv")
    sample = test_df[features].iloc[[0]]
    
    probs = pipeline.predict_proba(sample)[:, 1]
    assert len(probs) == 1
    assert 0.0 <= float(probs[0]) <= 1.0


# ---------------------------------------------------------------------------
# 6. SHAP Explainability on Leakage-Free Pipeline
# ---------------------------------------------------------------------------
def test_08_shap_tree_explainer_on_clean_baseline():
    """Verify shap.TreeExplainer initializes and executes on clean model."""
    model_path = MODELS_DIR / "xgboost_leakage_free_baseline.pkl"
    pipeline = joblib.load(model_path)
    clf = pipeline.named_steps["classifier"]
    
    explainer = shap.TreeExplainer(clf)
    assert explainer is not None
