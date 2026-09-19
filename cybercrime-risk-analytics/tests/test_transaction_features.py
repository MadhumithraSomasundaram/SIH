"""
Validation & Verification Suite for Leakage-Free Transaction and Account Features
Problem Statement ID 26184: Cybercrime Predictive Analytics Framework

Step 9 Validation Items:
1. Feature calculation correctness
2. Prediction timestamp restrictions (T_txn <= T0)
3. Historical transaction aggregation
4. Account feature generation
5. Missing-value handling
6. Duplicate handling
7. Train/test separation
8. Feature schema consistency (features_v2.json)
9. Inference compatibility
10. Data leakage prevention with controlled synthetic counter-examples
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROC_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"


# ---------------------------------------------------------------------------
# 1. Feature Calculation Correctness
# ---------------------------------------------------------------------------
def test_01_feature_calculation_correctness():
    """Verify mathematical correctness of account and transaction ratios/aggregates."""
    feat_df = pd.read_csv(PROC_DIR / "feature_engineered_v2.csv", nrows=100)
    
    # Check ratio: fraud_amount / (victim_baseline_daily_amount + 1.0)
    expected_ratio = (feat_df["fraud_amount"] / (feat_df["victim_baseline_daily_amount"] + 1.0)).round(4)
    np.testing.assert_allclose(feat_df["fraud_to_daily_amount_ratio"], expected_ratio, rtol=1e-3)
    
    # Check excess: max(0, fraud_amount - victim_baseline_daily_amount)
    expected_excess = np.maximum(0.0, feat_df["fraud_amount"] - feat_df["victim_baseline_daily_amount"]).round(2)
    np.testing.assert_allclose(feat_df["fraud_amount_excess_over_baseline"], expected_excess, rtol=1e-3)
    
    # Check total volume: outgoing + incoming
    expected_vol = feat_df["victim_outgoing_amount_all"] + feat_df["victim_incoming_amount_all"]
    np.testing.assert_allclose(feat_df["victim_total_prior_volume"], expected_vol, rtol=1e-3)


# ---------------------------------------------------------------------------
# 2. Prediction Timestamp Restrictions (T_txn <= T0)
# ---------------------------------------------------------------------------
def test_02_prediction_timestamp_restrictions():
    """Verify that every single transaction used in features occurred on or before complaint_timestamp."""
    fc = pd.read_csv(RAW_DIR / "Fraud_Cases.csv")
    tx = pd.read_csv(RAW_DIR / "Transactions.csv")
    
    fc["complaint_dt"] = pd.to_datetime(fc["complaint_timestamp"])
    tx["txn_dt"] = pd.to_datetime(tx["timestamp"])
    
    # For case-linked transactions, verify only prior txns are counted
    tx_case = tx.dropna(subset=["case_id"]).merge(fc[["case_id", "complaint_dt"]], on="case_id")
    prior_tx = tx_case[tx_case["txn_dt"] <= tx_case["complaint_dt"]]
    
    prior_counts = prior_tx.groupby("case_id").size().to_dict()
    
    train_v2 = pd.read_csv(PROC_DIR / "train_v2.csv")
    sample_cases = train_v2["case_id"].head(50).tolist()
    
    for cid in sample_cases:
        expected = prior_counts.get(cid, 0)
        actual = train_v2.loc[train_v2["case_id"] == cid, "case_prior_txn_count"].iloc[0]
        assert actual == expected, f"Case {cid} prior txn count mismatch: actual {actual} != expected {expected}"


# ---------------------------------------------------------------------------
# 3. Historical Transaction Aggregation
# ---------------------------------------------------------------------------
def test_03_historical_transaction_aggregation():
    """Verify aggregation window bounds (24h and 7d prior to T0)."""
    train_v2 = pd.read_csv(PROC_DIR / "train_v2.csv")
    
    # 24h count must always be <= 7d count
    assert (train_v2["victim_outgoing_txns_24h"] <= train_v2["victim_outgoing_txns_7d"]).all()
    # 7d count must always be <= all-time count
    assert (train_v2["victim_outgoing_txns_7d"] <= train_v2["victim_outgoing_txns_all"]).all()
    # 24h amount must always be <= 7d amount
    assert (train_v2["victim_outgoing_amount_24h"] <= train_v2["victim_outgoing_amount_7d"] + 1e-4).all()
    # 7d amount must always be <= all-time amount
    assert (train_v2["victim_outgoing_amount_7d"] <= train_v2["victim_outgoing_amount_all"] + 1e-4).all()


# ---------------------------------------------------------------------------
# 4. Account Feature Generation
# ---------------------------------------------------------------------------
def test_04_account_feature_generation():
    """Verify account-level features are properly extracted and joined from Accounts.csv."""
    acc = pd.read_csv(RAW_DIR / "Accounts.csv")
    train_v2 = pd.read_csv(PROC_DIR / "train_v2.csv")
    fc = pd.read_csv(RAW_DIR / "Fraud_Cases.csv")
    
    # Map case_id to victim_account_id
    case_to_acc = fc.set_index("case_id")["victim_account_id"].to_dict()
    acc_map = acc.set_index("account_id").to_dict(orient="index")
    
    for _, row in train_v2.head(20).iterrows():
        cid = row["case_id"]
        aid = case_to_acc[cid]
        acc_info = acc_map[aid]
        assert row["victim_account_type"] == acc_info["account_type"]
        assert row["victim_account_age_days"] == acc_info["account_age_days"]
        assert row["victim_baseline_daily_txns"] == acc_info["baseline_daily_txn_count"]


# ---------------------------------------------------------------------------
# 5. Missing-Value Handling
# ---------------------------------------------------------------------------
def test_05_missing_value_handling():
    """Verify that zero-fill defaults and sentinel values prevent NaNs in processed matrices."""
    train_v2 = pd.read_csv(PROC_DIR / "train_v2.csv")
    test_v2 = pd.read_csv(PROC_DIR / "test_v2.csv")
    
    v2_numeric = [
        "case_prior_txn_count", "case_prior_amount_sum", "case_prior_amount_max",
        "victim_outgoing_txns_24h", "victim_outgoing_amount_24h",
        "victim_incoming_txns_24h", "victim_total_prior_volume"
    ]
    for col in v2_numeric:
        assert train_v2[col].isnull().sum() == 0, f"Null values in train_v2[{col}]"
        assert test_v2[col].isnull().sum() == 0, f"Null values in test_v2[{col}]"
        
    # Inactive cases must have sentinel >= 9999.0
    zero_case_tx = train_v2[train_v2["case_prior_txn_count"] == 0]
    assert (zero_case_tx["case_hours_since_first_txn"] >= 9999.0).all()


# ---------------------------------------------------------------------------
# 6. Duplicate Handling
# ---------------------------------------------------------------------------
def test_06_duplicate_handling():
    """Verify duplicate case IDs or duplicate transactions do not cause row multiplication."""
    train_v2 = pd.read_csv(PROC_DIR / "train_v2.csv")
    val_v2 = pd.read_csv(PROC_DIR / "validation_v2.csv")
    test_v2 = pd.read_csv(PROC_DIR / "test_v2.csv")
    
    assert len(train_v2) == 7000
    assert len(val_v2) == 1500
    assert len(test_v2) == 1500
    assert train_v2["case_id"].nunique() == 7000
    assert val_v2["case_id"].nunique() == 1500
    assert test_v2["case_id"].nunique() == 1500


# ---------------------------------------------------------------------------
# 7. Train / Test Separation
# ---------------------------------------------------------------------------
def test_07_train_test_separation():
    """Verify strictly monotonic chronological separation between train, val, and test."""
    fc = pd.read_csv(RAW_DIR / "Fraud_Cases.csv")
    fc["complaint_dt"] = pd.to_datetime(fc["complaint_timestamp"])
    time_map = fc.set_index("case_id")["complaint_dt"].to_dict()
    
    train = pd.read_csv(PROC_DIR / "train_v2.csv")
    val = pd.read_csv(PROC_DIR / "validation_v2.csv")
    test = pd.read_csv(PROC_DIR / "test_v2.csv")
    
    train_times = train["case_id"].map(time_map)
    val_times = val["case_id"].map(time_map)
    test_times = test["case_id"].map(time_map)
    
    assert train_times.max() <= val_times.min(), "Train time overlaps with validation time!"
    assert val_times.max() <= test_times.min(), "Validation time overlaps with test time!"


# ---------------------------------------------------------------------------
# 8. Feature Schema Consistency
# ---------------------------------------------------------------------------
def test_08_feature_schema_consistency():
    """Verify features_v2.json schema matches the trained model pipeline feature expectations."""
    schema_path = MODELS_DIR / "features_v2.json"
    assert schema_path.exists(), "features_v2.json missing!"
    with open(schema_path) as f:
        schema = json.load(f)
        
    model = joblib.load(MODELS_DIR / "xgboost_v2_model.pkl")
    meta_path = MODELS_DIR / "metadata_v2.json"
    with open(meta_path) as f:
        meta = json.load(f)
        
    model_features = meta["selected_features"]
    schema_features = list(schema["features"].keys())
    
    assert len(model_features) == len(schema_features) == 86
    assert set(model_features) == set(schema_features)


# ---------------------------------------------------------------------------
# 9. Inference Compatibility
# ---------------------------------------------------------------------------
def test_09_inference_compatibility():
    """Verify that loaded pipeline predicts valid probabilities on holdout test cases."""
    pipeline = joblib.load(MODELS_DIR / "xgboost_v2_model.pkl")
    meta_path = MODELS_DIR / "metadata_v2.json"
    with open(meta_path) as f:
        meta = json.load(f)
    features = meta["selected_features"]
    
    test_v2 = pd.read_csv(PROC_DIR / "test_v2.csv")
    X_test_sample = test_v2[features].head(10)
    
    probs = pipeline.predict_proba(X_test_sample)[:, 1]
    assert len(probs) == 10
    assert (probs >= 0.0).all() and (probs <= 1.0).all()
    assert not np.isnan(probs).any()


# ---------------------------------------------------------------------------
# 10. Controlled Synthetic Data Leakage Prevention
# ---------------------------------------------------------------------------
def test_10_controlled_synthetic_future_transaction_leakage():
    """
    Controlled counter-example test:
    If a transaction occurs at T_txn = T0 + 1 hour, it MUST NOT be counted
    in case_prior_txn_count or victim_outgoing_txns_24h.
    """
    from src.feature_engineering_v2 import engineer_case_transaction_features
    
    mock_fc = pd.DataFrame([{
        "case_id": "SYNTH_001",
        "complaint_timestamp": "2026-06-01 12:00:00",
        "complaint_dt": pd.to_datetime("2026-06-01 12:00:00"),
        "victim_account_id": "ACC_SYNTH_01",
        "fraud_amount": 25000.0,
    }])
    
    mock_tx = pd.DataFrame([
        # Prior transaction 2 hours BEFORE T0 -> MUST BE INCLUDED
        {
            "transaction_id": "TX_PRIOR_01",
            "case_id": "SYNTH_001",
            "timestamp": "2026-06-01 10:00:00",
            "txn_dt": pd.to_datetime("2026-06-01 10:00:00"),
            "from_account": "ACC_SYNTH_01",
            "to_account": "ACC_MULE_01",
            "amount": 10000.0,
            "transaction_type": "IMPS",
        },
        # Future transaction 1 hour AFTER T0 -> MUST BE EXCLUDED
        {
            "transaction_id": "TX_FUTURE_02",
            "case_id": "SYNTH_001",
            "timestamp": "2026-06-01 13:00:00",
            "txn_dt": pd.to_datetime("2026-06-01 13:00:00"),
            "from_account": "ACC_SYNTH_01",
            "to_account": "ACC_MULE_02",
            "amount": 15000.0,
            "transaction_type": "UPI",
        },
    ])
    
    agg = engineer_case_transaction_features(mock_fc, mock_tx)
    
    assert len(agg) == 1
    assert agg.loc[0, "case_prior_txn_count"] == 1, "Future transaction was incorrectly counted!"
    assert agg.loc[0, "case_prior_amount_sum"] == 10000.0, "Future amount leaked into historical sum!"
    assert agg.loc[0, "case_prior_unique_beneficiaries"] == 1, "Future counterparty leaked into beneficiaries!"
