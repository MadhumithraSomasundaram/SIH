"""
CSV Dataset Backup Utility
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Safely creates timestamped or standardized backups of all primary CSV datasets in data/backup_csv/
with SHA-256 checksums and row count audits to guarantee zero data loss.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backup_csv")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROC_DIR = DATA_DIR / "processed"
BACKUP_DIR = DATA_DIR / "backup_csv"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def backup_all_csv_datasets() -> Dict[str, Any]:
    """Backs up raw and processed CSV datasets and generates an audit log."""
    targets = [
        (RAW_DIR / "Fraud_Cases.csv", "raw_fraud_cases.csv"),
        (RAW_DIR / "Transactions.csv", "raw_transactions.csv"),
        (RAW_DIR / "Accounts.csv", "raw_accounts.csv"),
        (RAW_DIR / "Withdrawals.csv", "raw_withdrawals.csv"),
        (RAW_DIR / "ATMs_Locations.csv", "raw_atms_locations.csv"),
        (PROC_DIR / "targeted_cybercrime_data.csv", "proc_targeted_cybercrime_data.csv"),
        (PROC_DIR / "train.csv", "proc_train.csv"),
        (PROC_DIR / "validation.csv", "proc_validation.csv"),
        (PROC_DIR / "test.csv", "proc_test.csv"),
    ]

    backup_manifest: List[Dict[str, Any]] = []

    for src_path, dest_name in targets:
        if not src_path.exists():
            logger.warning("Target CSV not found, skipping: %s", src_path)
            continue

        dest_path = BACKUP_DIR / dest_name
        shutil.copy2(src_path, dest_path)

        src_hash = calculate_sha256(src_path)
        dest_hash = calculate_sha256(dest_path)
        assert src_hash == dest_hash, f"Backup checksum mismatch for {dest_name}!"

        # Row count
        try:
            df = pd.read_csv(src_path)
            row_count = len(df)
            col_count = len(df.columns)
        except Exception:
            row_count = -1
            col_count = -1

        entry = {
            "source_path": str(src_path.relative_to(BASE_DIR)),
            "backup_path": str(dest_path.relative_to(BASE_DIR)),
            "file_size_bytes": dest_path.stat().st_size,
            "row_count": row_count,
            "col_count": col_count,
            "sha256": dest_hash,
            "status": "VERIFIED_MATCH",
        }
        backup_manifest.append(entry)
        logger.info("Backed up %s -> %s (%d rows, %d bytes)", src_path.name, dest_name, row_count, dest_path.stat().st_size)

    manifest_file = OUTPUTS_DIR / "phase11_csv_backup_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump({"backup_count": len(backup_manifest), "files": backup_manifest}, f, indent=2)

    logger.info("Backup manifest saved to %s", manifest_file)
    return {"status": "SUCCESS", "backup_count": len(backup_manifest), "manifest": backup_manifest}


if __name__ == "__main__":
    res = backup_all_csv_datasets()
    print(f"Backup completed: {res['backup_count']} files verified.")
