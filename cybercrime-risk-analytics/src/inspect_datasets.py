"""
Dataset Inspection and Data Leakage Audit - Step 1
Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"


def main():
    print("=" * 60)
    print("STEP 1: INSPECTION OF DATASETS")
    print("=" * 60)

    # 1. Fraud Cases
    fc = pd.read_csv(RAW_DIR / "Fraud_Cases.csv")
    fc["complaint_dt"] = pd.to_datetime(fc["complaint_timestamp"])
    print("\n1. Fraud_Cases.csv:")
    print(f"   Shape: {fc.shape}")
    print(f"   Unique case_id: {fc['case_id'].nunique()}")
    print(f"   Unique victim_account_id: {fc['victim_account_id'].nunique()}")
    print(f"   Date Range: {fc['complaint_dt'].min()} to {fc['complaint_dt'].max()}")
    print(f"   Missing Values: {dict(fc.isnull().sum())}")
    print(f"   Fraud Amount Stats: min={fc['fraud_amount'].min()}, mean={fc['fraud_amount'].mean():.2f}, max={fc['fraud_amount'].max()}")

    # 2. Accounts
    acc = pd.read_csv(RAW_DIR / "Accounts.csv")
    print("\n2. Accounts.csv:")
    print(f"   Shape: {acc.shape}")
    print(f"   Unique account_id: {acc['account_id'].nunique()}")
    print(f"   Missing Values: {dict(acc.isnull().sum())}")
    # Match between fraud cases and accounts
    victim_match = fc["victim_account_id"].isin(acc["account_id"]).sum()
    print(f"   Victim accounts matching Accounts.csv: {victim_match} / {len(fc)} ({victim_match / len(fc) * 100:.1f}%)")

    # 3. Transactions
    tx = pd.read_csv(RAW_DIR / "Transactions.csv")
    tx["txn_dt"] = pd.to_datetime(tx["timestamp"])
    print("\n3. Transactions.csv:")
    print(f"   Shape: {tx.shape}")
    print(f"   Unique transaction_id: {tx['transaction_id'].nunique()}")
    print(f"   Non-null case_id: {tx['case_id'].notnull().sum()} ({tx['case_id'].notnull().mean() * 100:.2f}%)")
    print(f"   Date Range: {tx['txn_dt'].min()} to {tx['txn_dt'].max()}")
    print(f"   Unique from_account: {tx['from_account'].nunique()}")
    print(f"   Unique to_account: {tx['to_account'].nunique()}")
    print(f"   Missing Values: {dict(tx.isnull().sum())}")

    # 4. ATMs & Areas
    atms = pd.read_csv(RAW_DIR / "ATMs_Locations.csv")
    areas = pd.read_csv(RAW_DIR / "Areas_Master.csv")
    print("\n4. ATMs & Areas Master:")
    print(f"   ATMs Shape: {atms.shape} | Unique atm_id: {atms['atm_id'].nunique()}")
    print(f"   Areas Shape: {areas.shape} | Unique area_id: {areas['area_id'].nunique()}")

    # 5. Withdrawals
    wd = pd.read_csv(RAW_DIR / "Withdrawals.csv")
    wd["wd_dt"] = pd.to_datetime(wd["timestamp"])
    print("\n5. Withdrawals.csv:")
    print(f"   Shape: {wd.shape}")
    print(f"   Unique withdrawal_id: {wd['withdrawal_id'].nunique()}")
    print(f"   Non-null case_id: {wd['case_id'].notnull().sum()} ({wd['case_id'].notnull().mean() * 100:.2f}%)")
    print(f"   Date Range: {wd['wd_dt'].min()} to {wd['wd_dt'].max()}")

    # 6. Existing Train (64-features)
    train = pd.read_csv(PROC_DIR / "train.csv")
    print("\n6. train.csv (Current ML Dataset):")
    print(f"   Shape: {train.shape}")
    print(f"   Target distribution: {dict(train['future_withdrawal'].value_counts())}")
    pos = train['future_withdrawal'].sum()
    print(f"   Positive class rate: {pos / len(train) * 100:.2f}%")

    print("\n" + "=" * 60)
    print("STEP 2: PREDICTION TIMESTAMP & TEMPORAL ALIGNMENT")
    print("=" * 60)
    # Direct case_id transactions
    tx_case = tx.dropna(subset=["case_id"]).merge(
        fc[["case_id", "complaint_dt"]], on="case_id", how="inner"
    )
    tx_case["delta_hours"] = (tx_case["txn_dt"] - tx_case["complaint_dt"]).dt.total_seconds() / 3600.0

    prior_case_tx = tx_case[tx_case["delta_hours"] <= 0]
    future_case_tx = tx_case[tx_case["delta_hours"] > 0]
    print(f"Transactions explicitly tagged with case_id: {len(tx_case)}")
    print(f"  - Prior to or at complaint filing (delta <= 0h): {len(prior_case_tx)} (LEAKAGE-FREE)")
    print(f"  - Occurred after complaint filing (delta > 0h): {len(future_case_tx)} (FUTURE / LEAKAGE IF USED)")

    # Victim Outgoing Transactions (from_account == victim_account_id)
    # Exclude case_id from tx to avoid merge conflicts
    tx_sub = tx[["transaction_id", "timestamp", "txn_dt", "from_account", "to_account", "amount", "transaction_type"]]
    m_out = tx_sub.merge(
        fc[["case_id", "victim_account_id", "complaint_dt"]],
        left_on="from_account",
        right_on="victim_account_id",
        how="inner",
    )
    m_out["hours_before_complaint"] = (m_out["complaint_dt"] - m_out["txn_dt"]).dt.total_seconds() / 3600.0

    prior_out = m_out[m_out["hours_before_complaint"] >= 0]
    future_out = m_out[m_out["hours_before_complaint"] < 0]
    print(f"\nAll transactions from victim account (from_account == victim_account_id): {len(m_out)}")
    print(f"  - Prior to complaint filing (hours_before >= 0): {len(prior_out)} (LEAKAGE-FREE)")
    print(f"  - Within 24h prior: {len(prior_out[prior_out['hours_before_complaint'] <= 24])}")
    print(f"  - Within 7 days (168h) prior: {len(prior_out[prior_out['hours_before_complaint'] <= 168])}")
    print(f"  - Future transactions after complaint: {len(future_out)} (EXCLUDED)")

    # Victim Incoming Transactions (to_account == victim_account_id)
    m_in = tx_sub.merge(
        fc[["case_id", "victim_account_id", "complaint_dt"]],
        left_on="to_account",
        right_on="victim_account_id",
        how="inner",
    )
    m_in["hours_before_complaint"] = (m_in["complaint_dt"] - m_in["txn_dt"]).dt.total_seconds() / 3600.0
    prior_in = m_in[m_in["hours_before_complaint"] >= 0]
    future_in = m_in[m_in["hours_before_complaint"] < 0]
    print(f"\nAll incoming transactions to victim account (to_account == victim_account_id): {len(m_in)}")
    print(f"  - Prior to complaint filing (hours_before >= 0): {len(prior_in)} (LEAKAGE-FREE)")
    print(f"  - Within 24h prior: {len(prior_in[prior_in['hours_before_complaint'] <= 24])}")
    print(f"  - Within 7 days prior: {len(prior_in[prior_in['hours_before_complaint'] <= 168])}")
    print(f"  - Future transactions after complaint: {len(future_in)} (EXCLUDED)")


if __name__ == "__main__":
    main()
