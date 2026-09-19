"""
Train Leakage-Free Baseline XGBoost Model
Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints

This script creates and trains a strictly leakage-free baseline model:
1. Excludes confirmed non-stationary cumulative time proxies and forward-looking features.
2. Fits the ColumnTransformer preprocessor strictly on the training partition.
3. Preserves the frozen ground truth target: future_withdrawal (24h cashout event).
4. Evaluates on chronological validation and holdout test partitions.
5. Saves the updated model artifact, feature schema, and metadata for full reproducibility.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("leakage_free_baseline")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROC_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Confirmed non-stationary cumulative time proxies & drift features to exclude
EXCLUDED_LEAKAGE_FEATURES = [
    "previous_event_count",                # Monotonic row index (0-9999), 0 overlap between train and test
    "event_day",                           # Day of year (1-243), monotonic seasonal drift
    "event_month",                         # Calendar month (1-8), non-stationary time proxy
    "previous_activity_by_location",       # Cumulative unbounded count since Jan 1
    "location_total_previous_events",      # Exact duplicate of previous_activity_by_location
    "previous_activity_by_district",       # Cumulative unbounded district count
    "previous_activity_by_crime_category", # Cumulative unbounded category count
    "location_unique_crime_categories",    # Cumulative unbounded unique crime count
]


def load_datasets():
    train = pd.read_csv(PROC_DIR / "train.csv")
    val = pd.read_csv(PROC_DIR / "validation.csv")
    test = pd.read_csv(PROC_DIR / "test.csv")
    log.info("Loaded datasets: Train=%d, Val=%d, Test=%d", len(train), len(val), len(test))
    return train, val, test


def select_leakage_free_features(train_df):
    target = "future_withdrawal"
    id_cols = ["case_id", target]
    
    all_features = [c for c in train_df.columns if c not in id_cols]
    clean_features = [c for c in all_features if c not in EXCLUDED_LEAKAGE_FEATURES]
    
    log.info(
        "Initial features: %d | Excluded leakage/drift features: %d | Retained clean features: %d",
        len(all_features),
        len(EXCLUDED_LEAKAGE_FEATURES),
        len(clean_features),
    )
    return clean_features


def build_preprocessor(X_train):
    num_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X_train.select_dtypes(include=["object", "string"]).columns.tolist()
    
    log.info("Feature types: %d numerical, %d categorical", len(num_cols), len(cat_cols))
    
    num_pipe = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    
    preprocessor = ColumnTransformer([
        ("num", num_pipe, num_cols),
        ("cat", cat_pipe, cat_cols),
    ], remainder="drop")
    
    return preprocessor, num_cols, cat_cols


def train_and_evaluate():
    train, val, test = load_datasets()
    clean_features = select_leakage_free_features(train)
    
    X_train = train[clean_features]
    y_train = train["future_withdrawal"]
    
    X_val = val[clean_features]
    y_val = val["future_withdrawal"]
    
    X_test = test[clean_features]
    y_test = test["future_withdrawal"]
    
    preprocessor, num_cols, cat_cols = build_preprocessor(X_train)
    
    # Class imbalance weight calculated strictly on training set
    pos_count = int((y_train == 1).sum())
    neg_count = int((y_train == 0).sum())
    scale_pos_weight = neg_count / pos_count
    log.info("Training class distribution: Pos=%d (%.2f%%), Neg=%d | scale_pos_weight=%.4f",
             pos_count, (pos_count / len(y_train)) * 100, neg_count, scale_pos_weight)
    
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
    log.info("Leakage-free baseline trained in %.3f seconds", train_time)
    
    # Evaluate Validation
    val_probs = pipeline.predict_proba(X_val)[:, 1]
    val_preds = (val_probs >= 0.5).astype(int)
    val_metrics = {
        "dataset": "validation",
        "accuracy": round(float(accuracy_score(y_val, val_preds)), 4),
        "precision": round(float(precision_score(y_val, val_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_val, val_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_val, val_preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_val, val_probs)), 4),
        "pr_auc": round(float(average_precision_score(y_val, val_probs)), 4),
        "brier_score": round(float(brier_score_loss(y_val, val_probs)), 4),
    }
    
    # Evaluate Holdout Test
    test_probs = pipeline.predict_proba(X_test)[:, 1]
    test_preds = (test_probs >= 0.5).astype(int)
    cm = confusion_matrix(y_test, test_preds)
    test_metrics = {
        "dataset": "test",
        "accuracy": round(float(accuracy_score(y_test, test_preds)), 4),
        "precision": round(float(precision_score(y_test, test_preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, test_preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, test_preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, test_probs)), 4),
        "pr_auc": round(float(average_precision_score(y_test, test_probs)), 4),
        "brier_score": round(float(brier_score_loss(y_test, test_probs)), 4),
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1]),
    }
    
    log.info("Validation Metrics: %s", val_metrics)
    log.info("Test Metrics: %s", test_metrics)
    
    # Save Model Artifact
    model_out = MODELS_DIR / "xgboost_leakage_free_baseline.pkl"
    joblib.dump(pipeline, model_out)
    log.info("Saved clean baseline model to %s", model_out)
    
    # Save Feature Catalog
    feat_rows = []
    for f in clean_features:
        feat_rows.append({
            "feature": f,
            "category": "Numerical" if f in num_cols else "Categorical",
            "leakage_status": "PASS (Leakage-Free)",
            "availability": "Available at complaint intake T0",
        })
    pd.DataFrame(feat_rows).to_csv(OUTPUTS_DIR / "leakage_free_selected_features.csv", index=False)
    
    # Save Metrics CSV
    metrics_df = pd.DataFrame([val_metrics, test_metrics])
    metrics_df.to_csv(OUTPUTS_DIR / "leakage_free_evaluation_metrics.csv", index=False)
    
    # Save Metadata JSON
    metadata = {
        "model_type": "XGBoost Classifier (sklearn Pipeline)",
        "model_version": "v1.1.0-xgb-leakage-free",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "random_state": 42,
        "selected_features": clean_features,
        "feature_count": len(clean_features),
        "numerical_features": num_cols,
        "categorical_features": cat_cols,
        "excluded_features": EXCLUDED_LEAKAGE_FEATURES,
        "training_time_seconds": train_time,
        "class_balance_scale_pos_weight": round(scale_pos_weight, 4),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "target_variable": "future_withdrawal",
        "prediction_horizon": "24 hours",
    }
    with open(MODELS_DIR / "leakage_free_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    log.info("Saved metadata to %s", MODELS_DIR / "leakage_free_metadata.json")
    
    return pipeline, metadata, test_metrics


if __name__ == "__main__":
    train_and_evaluate()
