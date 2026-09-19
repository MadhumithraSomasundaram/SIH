"""
Train Leakage-Free V2 XGBoost Model with Transaction & Account Features
Problem Statement ID 26184: Cybercrime Predictive Analytics Framework

This script trains and validates the Phase 2 Leakage-Free Model:
1. Integrates validated historical transaction and account features strictly bounded by T0 (complaint_timestamp).
2. Excludes confirmed non-stationary cumulative time proxies and forward-looking features.
3. Fits the preprocessor strictly on the training partition.
4. Evaluates on chronological validation and holdout test partitions.
5. Saves models, versioned schemas (features_v2.json), and comprehensive metadata.
"""

import json
import logging
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.feature_engineering_v2 import build_feature_matrix_v2
from src.train_leakage_free_baseline import select_leakage_free_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("train_v2_model")

PROC_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

V2_TRANSACTION_ACCOUNT_FEATURES = [
    # Account Profile Features (Accounts.csv)
    "victim_account_type",
    "victim_account_age_days",
    "victim_baseline_daily_txns",
    "victim_baseline_daily_amount",
    "victim_baseline_daily_withdrawals",
    "fraud_to_daily_amount_ratio",
    "fraud_amount_excess_over_baseline",
    # Case-Linked Prior Fraud Transactions (Transactions.csv, T_txn <= T0)
    "case_prior_txn_count",
    "case_prior_amount_sum",
    "case_prior_amount_max",
    "case_prior_unique_channels",
    "case_hours_since_first_txn",
    # Victim Account Rolling & Velocity (Transactions.csv, T_txn <= T0)
    "victim_outgoing_txns_all",
    "victim_outgoing_amount_all",
    "victim_outgoing_amount_avg",
    "victim_outgoing_amount_max",
    "victim_hours_since_last_outgoing",
    "victim_outgoing_txns_24h",
    "victim_outgoing_amount_24h",
    "victim_outgoing_txns_7d",
    "victim_outgoing_amount_7d",
    # Victim Incoming Flow & Fan-In (Transactions.csv, T_txn <= T0)
    "victim_incoming_txns_all",
    "victim_incoming_amount_all",
    "victim_incoming_txns_24h",
    "victim_incoming_amount_24h",
    "victim_hours_since_last_incoming",
    # Composites & Graph Indicators
    "victim_total_prior_volume",
    "victim_net_prior_flow",
    "victim_total_linked_accounts",
    "victim_velocity_surge_ratio",
]


def generate_and_save_feature_schema(all_features, num_cols, cat_cols):
    log.info("Generating versioned feature schema: features_v2.json...")
    schema = {
        "schema_version": "2.0.0",
        "description": "Leakage-free feature schema for Cybercrime Predictive Analytics Framework (PS ID 26184)",
        "prediction_timestamp_anchor": "T0 = complaint_timestamp",
        "total_features": len(all_features),
        "numerical_feature_count": len(num_cols),
        "categorical_feature_count": len(cat_cols),
        "features": {},
    }

    for f in all_features:
        f_type = "categorical" if f in cat_cols else "numerical"
        
        # Determine metadata based on feature category
        if f.startswith("victim_account_") or f.startswith("victim_baseline_"):
            source = "Accounts.csv"
            calc = "Lookup via victim_account_id from static customer profile"
            window = "At prediction time T0"
            leakage = "PASS (Leakage-Free: Pre-existing account demographic/baseline)"
            impute = "most_frequent" if f_type == "categorical" else "median"
        elif f in ["fraud_to_daily_amount_ratio", "fraud_amount_excess_over_baseline"]:
            source = "Fraud_Cases.csv + Accounts.csv"
            calc = "Mathematical ratio/excess of complaint fraud_amount vs baseline_daily_amount"
            window = "Available at complaint intake T0"
            leakage = "PASS (Leakage-Free: Evaluated at T0)"
            impute = "median"
        elif f.startswith("case_prior_") or f.startswith("case_hours_"):
            source = "Transactions.csv"
            calc = "Aggregation of transactions tagged with case_id where timestamp <= T0"
            window = "(-inf, T0]"
            leakage = "PASS (Leakage-Free: Post-complaint transactions strictly excluded)"
            impute = "0 for counts/sums, 9999.0 sentinel for elapsed hours"
        elif f.startswith("victim_outgoing_") or f.startswith("victim_hours_since_last_outgoing"):
            source = "Transactions.csv"
            calc = "Aggregation of transactions where from_account == victim_account_id and timestamp <= T0"
            window = "24h prior, 7d prior, or all-time prior (-inf, T0]"
            leakage = "PASS (Leakage-Free: Post-complaint activity strictly excluded)"
            impute = "0 for counts/sums, median for rates"
        elif f.startswith("victim_incoming_") or f.startswith("victim_hours_since_last_incoming"):
            source = "Transactions.csv"
            calc = "Aggregation of transactions where to_account == victim_account_id and timestamp <= T0"
            window = "24h prior or all-time prior (-inf, T0]"
            leakage = "PASS (Leakage-Free: Post-complaint activity strictly excluded)"
            impute = "0 for counts/sums"
        elif f in ["victim_total_prior_volume", "victim_net_prior_flow", "victim_total_linked_accounts", "victim_velocity_surge_ratio"]:
            source = "Transactions.csv + Accounts.csv"
            calc = "Composite interaction of leakage-free historical inflows, outflows, and baselines"
            window = "(-inf, T0]"
            leakage = "PASS (Leakage-Free: Functions purely of historical quantities)"
            impute = "0 or median"
        else:
            source = "Fraud_Cases.csv (Processed)"
            calc = "Base geographical, temporal (calendar cycle), or intake attribute"
            window = "At complaint intake T0"
            leakage = "PASS (Leakage-Free: Excludes non-stationary cumulative counters)"
            impute = "most_frequent" if f_type == "categorical" else "median"

        schema["features"][f] = {
            "data_type": f_type,
            "source_dataset": source,
            "calculation_method": calc,
            "time_window": window,
            "leakage_status": leakage,
            "missing_value_policy": impute,
        }

    out_file = MODELS_DIR / "features_v2.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    log.info("Saved feature schema to %s", out_file)
    return schema


def main():
    log.info("Starting Phase 2 Model Retraining with V2 Leakage-Free Features...")
    
    # 1. Build V2 feature matrix
    v2_matrix = build_feature_matrix_v2()
    
    # Save full feature-engineered dataset v2
    full_fc = pd.read_csv(PROC_DIR / "cleaned_cybercrime_data.csv")
    full_v2 = full_fc.merge(v2_matrix[["case_id"] + V2_TRANSACTION_ACCOUNT_FEATURES], on="case_id", how="left")
    full_v2.to_csv(PROC_DIR / "feature_engineered_v2.csv", index=False)
    log.info("Saved feature_engineered_v2.csv with shape %s", full_v2.shape)

    # 2. Load chronological train/val/test splits
    train = pd.read_csv(PROC_DIR / "train.csv")
    val = pd.read_csv(PROC_DIR / "validation.csv")
    test = pd.read_csv(PROC_DIR / "test.csv")
    
    base_clean = select_leakage_free_features(train)
    all_features = base_clean + V2_TRANSACTION_ACCOUNT_FEATURES
    
    train_v2 = train.merge(v2_matrix[["case_id"] + V2_TRANSACTION_ACCOUNT_FEATURES], on="case_id", how="left")
    val_v2 = val.merge(v2_matrix[["case_id"] + V2_TRANSACTION_ACCOUNT_FEATURES], on="case_id", how="left")
    test_v2 = test.merge(v2_matrix[["case_id"] + V2_TRANSACTION_ACCOUNT_FEATURES], on="case_id", how="left")
    
    train_v2.to_csv(PROC_DIR / "train_v2.csv", index=False)
    val_v2.to_csv(PROC_DIR / "validation_v2.csv", index=False)
    test_v2.to_csv(PROC_DIR / "test_v2.csv", index=False)
    log.info("Saved train_v2.csv, validation_v2.csv, test_v2.csv")

    X_train = train_v2[all_features]
    y_train = train_v2["future_withdrawal"]
    X_val = val_v2[all_features]
    y_val = val_v2["future_withdrawal"]
    X_test = test_v2[all_features]
    y_test = test_v2["future_withdrawal"]

    num_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X_train.select_dtypes(include=["object", "string"]).columns.tolist()
    log.info("Total features: %d (Numerical: %d, Categorical: %d)", len(all_features), len(num_cols), len(cat_cols))

    # Generate versioned schema
    generate_and_save_feature_schema(all_features, num_cols, cat_cols)

    # Build Preprocessor fit strictly on training set
    num_pipe = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("num", num_pipe, num_cols),
        ("cat", cat_pipe, cat_cols),
    ], remainder="drop")

    pos_count = int((y_train == 1).sum())
    neg_count = int((y_train == 0).sum())
    scale_pos_weight = neg_count / pos_count
    log.info("Training distribution: Pos=%d, Neg=%d, scale_pos_weight=%.4f", pos_count, neg_count, scale_pos_weight)

    clf = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="logloss",
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", clf),
    ])

    t0 = time.time()
    pipeline.fit(X_train, y_train)
    train_time = round(time.time() - t0, 3)
    log.info("Model trained in %.3f seconds", train_time)

    # Evaluation
    val_probs = pipeline.predict_proba(X_val)[:, 1]
    val_preds = (val_probs >= 0.5).astype(int)
    val_cm = confusion_matrix(y_val, val_preds)
    val_metrics = {
        "dataset": "validation",
        "accuracy": round(float(accuracy_score(y_val, val_preds)), 4),
        "precision": round(float(precision_score(y_val, val_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_val, val_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_val, val_preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_val, val_probs)), 4),
        "pr_auc": round(float(average_precision_score(y_val, val_probs)), 4),
        "brier_score": round(float(brier_score_loss(y_val, val_probs)), 4),
        "tn": int(val_cm[0, 0]),
        "fp": int(val_cm[0, 1]),
        "fn": int(val_cm[1, 0]),
        "tp": int(val_cm[1, 1]),
    }

    test_probs = pipeline.predict_proba(X_test)[:, 1]
    test_preds = (test_probs >= 0.5).astype(int)
    test_cm = confusion_matrix(y_test, test_preds)
    test_metrics = {
        "dataset": "test",
        "accuracy": round(float(accuracy_score(y_test, test_preds)), 4),
        "precision": round(float(precision_score(y_test, test_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, test_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, test_preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, test_probs)), 4),
        "pr_auc": round(float(average_precision_score(y_test, test_probs)), 4),
        "brier_score": round(float(brier_score_loss(y_test, test_probs)), 4),
        "tn": int(test_cm[0, 0]),
        "fp": int(test_cm[0, 1]),
        "fn": int(test_cm[1, 0]),
        "tp": int(test_cm[1, 1]),
    }

    log.info("Validation Metrics: %s", val_metrics)
    log.info("Test Metrics: %s", test_metrics)

    # Save Model Artifact
    model_out = MODELS_DIR / "xgboost_v2_model.pkl"
    joblib.dump(pipeline, model_out)
    log.info("Saved V2 model to %s", model_out)

    # Save Feature Catalog CSV
    feat_rows = []
    for f in all_features:
        feat_rows.append({
            "feature": f,
            "category": "Numerical" if f in num_cols else "Categorical",
            "source": "Transactions / Accounts" if f in V2_TRANSACTION_ACCOUNT_FEATURES else "Intake / Base",
            "leakage_status": "PASS (Leakage-Free)",
            "availability": "Available at complaint intake T0",
        })
    pd.DataFrame(feat_rows).to_csv(OUTPUTS_DIR / "selected_features_v2.csv", index=False)

    # Save Metrics CSV
    metrics_df = pd.DataFrame([val_metrics, test_metrics])
    metrics_df.to_csv(OUTPUTS_DIR / "evaluation_metrics_v2.csv", index=False)

    # Save Metadata JSON
    metadata = {
        "model_type": "XGBoost Classifier Pipeline (V2 Feature Engineering)",
        "model_version": "v2.0.0-xgb-transaction-account-features",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "random_state": 42,
        "feature_count_total": len(all_features),
        "feature_count_base_clean": len(base_clean),
        "feature_count_v2_new": len(V2_TRANSACTION_ACCOUNT_FEATURES),
        "selected_features": all_features,
        "numerical_features": num_cols,
        "categorical_features": cat_cols,
        "training_time_seconds": train_time,
        "class_balance_scale_pos_weight": round(scale_pos_weight, 4),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "target_variable": "future_withdrawal",
        "prediction_horizon": "24 hours",
    }
    with open(MODELS_DIR / "metadata_v2.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info("Saved metadata to %s", MODELS_DIR / "metadata_v2.json")

    return pipeline, metadata, test_metrics


if __name__ == "__main__":
    main()
