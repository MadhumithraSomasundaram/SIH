"""
Feature Engineering V2: Leakage-Free Transaction and Account Features
Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints

This script engineers leakage-free transaction and account features:
- Strictly bounded by T0 = complaint_timestamp.
- All future transactions (T_txn > T0) are filtered out before feature aggregation.
- Matches 100% of accounts via victim_account_id.
- Captures case-linked fraud transactions, rolling 24h/7d activity, fan-in/fan-out, baseline deviations.
"""

import json
import logging
import time
from pathlib import Path
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("feature_engineering_v2")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"


def load_raw_datasets():
    log.info("Loading raw datasets...")
    fc = pd.read_csv(RAW_DIR / "Fraud_Cases.csv")
    acc = pd.read_csv(RAW_DIR / "Accounts.csv")
    tx = pd.read_csv(RAW_DIR / "Transactions.csv")
    
    fc["complaint_dt"] = pd.to_datetime(fc["complaint_timestamp"])
    tx["txn_dt"] = pd.to_datetime(tx["timestamp"])
    
    log.info("Loaded: Fraud_Cases=%d, Accounts=%d, Transactions=%d", len(fc), len(acc), len(tx))
    return fc, acc, tx


def engineer_account_profile_features(fc, acc):
    log.info("Engineering account profile features...")
    acc_map = {
        "account_id": "victim_account_id",
        "account_type": "victim_account_type",
        "account_age_days": "victim_account_age_days",
        "baseline_daily_txn_count": "victim_baseline_daily_txns",
        "baseline_daily_amount": "victim_baseline_daily_amount",
        "baseline_daily_withdrawals": "victim_baseline_daily_withdrawals",
    }
    acc_sub = acc[list(acc_map.keys())].rename(columns=acc_map)
    df = fc.merge(acc_sub, on="victim_account_id", how="left")
    
    # Ratios and transformed metrics
    df["victim_account_age_years"] = (df["victim_account_age_days"] / 365.25).round(2)
    df["fraud_to_daily_amount_ratio"] = (
        df["fraud_amount"] / (df["victim_baseline_daily_amount"] + 1.0)
    ).round(4)
    df["fraud_amount_excess_over_baseline"] = np.maximum(
        0.0, df["fraud_amount"] - df["victim_baseline_daily_amount"]
    ).round(2)
    
    return df


def engineer_case_transaction_features(fc, tx):
    log.info("Engineering case-linked transaction features (strictly T_txn <= T0)...")
    tx_case = tx.dropna(subset=["case_id"])[
        ["case_id", "transaction_id", "txn_dt", "from_account", "to_account", "amount", "transaction_type"]
    ].merge(fc[["case_id", "complaint_dt"]], on="case_id", how="inner")
    
    # STRICT LEAKAGE PREVENTION: Drop any transaction occurring after complaint filing
    tx_prior = tx_case[tx_case["txn_dt"] <= tx_case["complaint_dt"]].copy()
    tx_prior["hours_prior"] = (
        tx_prior["complaint_dt"] - tx_prior["txn_dt"]
    ).dt.total_seconds() / 3600.0
    
    log.info(
        "Case-linked transactions: total=%d, prior=%d, future_excluded=%d",
        len(tx_case),
        len(tx_prior),
        len(tx_case) - len(tx_prior),
    )
    
    case_agg = tx_prior.groupby("case_id").agg(
        case_prior_txn_count=("transaction_id", "count"),
        case_prior_amount_sum=("amount", "sum"),
        case_prior_amount_max=("amount", "max"),
        case_prior_amount_avg=("amount", "mean"),
        case_prior_unique_beneficiaries=("to_account", "nunique"),
        case_prior_unique_channels=("transaction_type", "nunique"),
        case_hours_since_first_txn=("hours_prior", "max"),
        case_hours_since_last_txn=("hours_prior", "min"),
    ).reset_index()
    
    return case_agg


def engineer_victim_transaction_features(fc, tx):
    log.info("Engineering victim rolling & fan-in/fan-out features (strictly T_txn <= T0)...")
    tx_clean = tx[["transaction_id", "txn_dt", "from_account", "to_account", "amount"]].copy()
    
    # 1. Victim Outgoing (from_account == victim_account_id)
    m_out = tx_clean.merge(
        fc[["case_id", "victim_account_id", "complaint_dt"]],
        left_on="from_account",
        right_on="victim_account_id",
        how="inner",
    )
    m_out_prior = m_out[m_out["txn_dt"] <= m_out["complaint_dt"]].copy()
    m_out_prior["hours_prior"] = (
        m_out_prior["complaint_dt"] - m_out_prior["txn_dt"]
    ).dt.total_seconds() / 3600.0
    
    log.info(
        "Victim outgoing transactions: total=%d, prior=%d, future_excluded=%d",
        len(m_out),
        len(m_out_prior),
        len(m_out) - len(m_out_prior),
    )
    
    out_all = m_out_prior.groupby("case_id").agg(
        victim_outgoing_txns_all=("transaction_id", "count"),
        victim_outgoing_amount_all=("amount", "sum"),
        victim_outgoing_amount_avg=("amount", "mean"),
        victim_outgoing_amount_max=("amount", "max"),
        victim_fan_out_count=("to_account", "nunique"),
        victim_hours_since_last_outgoing=("hours_prior", "min"),
    ).reset_index()
    
    # 24h rolling
    m_out_24h = m_out_prior[m_out_prior["hours_prior"] <= 24.0]
    out_24h = m_out_24h.groupby("case_id").agg(
        victim_outgoing_txns_24h=("transaction_id", "count"),
        victim_outgoing_amount_24h=("amount", "sum"),
        victim_outgoing_recipients_24h=("to_account", "nunique"),
    ).reset_index()
    
    # 7d rolling
    m_out_7d = m_out_prior[m_out_prior["hours_prior"] <= 168.0]
    out_7d = m_out_7d.groupby("case_id").agg(
        victim_outgoing_txns_7d=("transaction_id", "count"),
        victim_outgoing_amount_7d=("amount", "sum"),
    ).reset_index()
    
    # 2. Victim Incoming (to_account == victim_account_id)
    m_in = tx_clean.merge(
        fc[["case_id", "victim_account_id", "complaint_dt"]],
        left_on="to_account",
        right_on="victim_account_id",
        how="inner",
    )
    m_in_prior = m_in[m_in["txn_dt"] <= m_in["complaint_dt"]].copy()
    m_in_prior["hours_prior"] = (
        m_in_prior["complaint_dt"] - m_in_prior["txn_dt"]
    ).dt.total_seconds() / 3600.0
    
    log.info(
        "Victim incoming transactions: total=%d, prior=%d, future_excluded=%d",
        len(m_in),
        len(m_in_prior),
        len(m_in) - len(m_in_prior),
    )
    
    in_all = m_in_prior.groupby("case_id").agg(
        victim_incoming_txns_all=("transaction_id", "count"),
        victim_incoming_amount_all=("amount", "sum"),
        victim_fan_in_count=("from_account", "nunique"),
        victim_hours_since_last_incoming=("hours_prior", "min"),
    ).reset_index()
    
    m_in_24h = m_in_prior[m_in_prior["hours_prior"] <= 24.0]
    in_24h = m_in_24h.groupby("case_id").agg(
        victim_incoming_txns_24h=("transaction_id", "count"),
        victim_incoming_amount_24h=("amount", "sum"),
    ).reset_index()
    
    # Combine victim rolling aggregations
    victim_tx_df = out_all.merge(out_24h, on="case_id", how="left")
    victim_tx_df = victim_tx_df.merge(out_7d, on="case_id", how="left")
    victim_tx_df = victim_tx_df.merge(in_all, on="case_id", how="left")
    victim_tx_df = victim_tx_df.merge(in_24h, on="case_id", how="left")
    
    return victim_tx_df


def build_feature_matrix_v2():
    t0 = time.time()
    fc, acc, tx = load_raw_datasets()
    
    # 1. Accounts profile
    df = engineer_account_profile_features(fc, acc)
    
    # 2. Case-linked transactions
    case_tx = engineer_case_transaction_features(fc, tx)
    df = df.merge(case_tx, on="case_id", how="left")
    
    # 3. Victim rolling transactions
    victim_tx = engineer_victim_transaction_features(fc, tx)
    df = df.merge(victim_tx, on="case_id", how="left")
    
    # Fill defaults for cases with zero prior transactions
    zero_fill_cols = [
        "case_prior_txn_count",
        "case_prior_amount_sum",
        "case_prior_amount_max",
        "case_prior_amount_avg",
        "case_prior_unique_beneficiaries",
        "case_prior_unique_channels",
        "victim_outgoing_txns_all",
        "victim_outgoing_amount_all",
        "victim_outgoing_amount_avg",
        "victim_outgoing_amount_max",
        "victim_fan_out_count",
        "victim_outgoing_txns_24h",
        "victim_outgoing_amount_24h",
        "victim_outgoing_recipients_24h",
        "victim_outgoing_txns_7d",
        "victim_outgoing_amount_7d",
        "victim_incoming_txns_all",
        "victim_incoming_amount_all",
        "victim_fan_in_count",
        "victim_incoming_txns_24h",
        "victim_incoming_amount_24h",
    ]
    for c in zero_fill_cols:
        df[c] = df[c].fillna(0)
    
    # Composite features
    df["victim_total_prior_volume"] = df["victim_outgoing_amount_all"] + df["victim_incoming_amount_all"]
    df["victim_net_prior_flow"] = df["victim_incoming_amount_all"] - df["victim_outgoing_amount_all"]
    df["victim_total_linked_accounts"] = df["victim_fan_in_count"] + df["victim_fan_out_count"]
    df["victim_velocity_surge_ratio"] = (
        df["victim_outgoing_txns_24h"] / (df["victim_baseline_daily_txns"] + 1.0)
    ).round(4)
    
    # Sentinel for inactive accounts: 9999.0 hours
    sentinel_cols = [
        "case_hours_since_first_txn",
        "case_hours_since_last_txn",
        "victim_hours_since_last_outgoing",
        "victim_hours_since_last_incoming",
    ]
    for c in sentinel_cols:
        df[c] = df[c].fillna(9999.0).round(2)
        
    df["victim_time_since_last_activity"] = np.minimum(
        df["victim_hours_since_last_outgoing"], df["victim_hours_since_last_incoming"]
    )
    
    elapsed = time.time() - t0
    log.info("Feature matrix v2 constructed successfully in %.2f seconds! Shape: %s", elapsed, df.shape)
    return df


if __name__ == "__main__":
    df = build_feature_matrix_v2()
    print("Engineered V2 Features Sample:")
    print(df[[
        "case_id", "victim_account_type", "victim_account_age_years",
        "case_prior_txn_count", "case_prior_amount_sum",
        "victim_outgoing_txns_24h", "victim_fan_out_count", "victim_fan_in_count",
        "victim_total_prior_volume", "victim_velocity_surge_ratio"
    ]].head())
