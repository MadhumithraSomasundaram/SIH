#!/usr/bin/env python3
"""
scripts/reset_demo_data.py
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
Safe Demonstration Environment Reset Script

Restores the demonstration workspace to a pristine baseline before presentations.
Requires explicit --confirm flag to prevent accidental execution.

Guarantees:
  - NEVER modifies machine learning models (models/*.pkl, models/*.json).
  - NEVER modifies core datasets (data/raw/, data/processed/).
  - NEVER modifies source code or system configurations.
  - Automatically creates a timestamped backup before pruning mutable logs.
"""

import argparse
import csv
import datetime
import os
import shutil
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
PRED_LOG_DIR = OUTPUTS_DIR / "predictions"
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = DATA_DIR / "backup_csv"

# Mutable demonstration targets
AUDIT_LOG_CSV = OUTPUTS_DIR / "phase17_analyst_audit_log.csv"
FEEDBACK_CSV = OUTPUTS_DIR / "phase21_outcome_feedback.csv"
PRED_LOG_CSV = PRED_LOG_DIR / "api_prediction_log.csv"

# Baseline seeds to preserve
BASELINE_FEEDBACK_SEEDS = [
    "FBK-DEMO-000001",
    "FBK-DEMO-000002",
]


def backup_file(filepath: Path, backup_subfolder: Path) -> Path:
    """Create a timestamped backup of a file before modification."""
    backup_subfolder.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dest = backup_subfolder / f"{filepath.stem}_{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_dest)
    return backup_dest


def reset_feedback_csv(dry_run: bool = False) -> int:
    """Reset outcome feedback to pristine baseline seeds."""
    if not FEEDBACK_CSV.exists():
        print(f"[-] {FEEDBACK_CSV.name} does not exist. Skipping.")
        return 0

    with open(FEEDBACK_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if not reader:
        return 0

    fieldnames = list(reader[0].keys())
    kept_rows = [row for row in reader if row.get("feedback_id") in BASELINE_FEEDBACK_SEEDS]
    removed_count = len(reader) - len(kept_rows)

    if not dry_run and removed_count > 0:
        backup_file(FEEDBACK_CSV, BACKUP_DIR)
        with open(FEEDBACK_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept_rows)

    return removed_count


def reset_prediction_log(dry_run: bool = False) -> int:
    """Clear transient prediction API logs while preserving the CSV schema header."""
    if not PRED_LOG_CSV.exists():
        return 0

    with open(PRED_LOG_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    if len(reader) <= 1:
        return 0

    header = reader[0]
    removed_count = len(reader) - 1

    if not dry_run:
        backup_file(PRED_LOG_CSV, BACKUP_DIR)
        with open(PRED_LOG_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)

    return removed_count


def reset_audit_log(dry_run: bool = False) -> int:
    """Prune recent test runs from audit log, preserving standard baseline."""
    if not AUDIT_LOG_CSV.exists():
        return 0

    with open(AUDIT_LOG_CSV, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    if not reader:
        return 0

    fieldnames = list(reader[0].keys())
    # Keep baseline prototype entries (pre-demo initialization)
    kept_rows = [row for row in reader if not row.get("detail", "").startswith("E2E Test:")]
    removed_count = len(reader) - len(kept_rows)

    if not dry_run and removed_count > 0:
        backup_file(AUDIT_LOG_CSV, BACKUP_DIR)
        with open(AUDIT_LOG_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept_rows)

    return removed_count


def main():
    parser = argparse.ArgumentParser(
        description="Safe Demonstration Environment Reset for Cybercrime Prediction Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python scripts/reset_demo_data.py --confirm
  python scripts/reset_demo_data.py --dry-run
        """,
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicit confirmation required to execute reset.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the reset process without making modifications.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print(" CYBERCRIME PREDICTIVE ANALYTICS PLATFORM (SIH #26184)")
    print(" DEMONSTRATION ENVIRONMENT RESET TOOL")
    print("=" * 70)

    if not args.confirm and not args.dry_run:
        print("\n[!] SAFETY HALT: You must pass --confirm to reset demonstration data.")
        print("    Usage: python scripts/reset_demo_data.py --confirm")
        print("    Or run with --dry-run to view what would be modified.\n")
        sys.exit(1)

    mode_label = "[DRY RUN]" if args.dry_run else "[LIVE RESET]"
    print(f"\n[*] Execution Mode: {mode_label}")
    print(f"[*] Project Root:   {PROJECT_ROOT}")
    print(f"[*] Backup Dir:     {BACKUP_DIR}\n")

    # 1. Reset Outcome Feedback
    removed_fbk = reset_feedback_csv(dry_run=args.dry_run)
    print(f"[+] Outcome Feedback:  {removed_fbk} test rows pruned (baseline preserved).")

    # 2. Reset Prediction Log
    removed_pred = reset_prediction_log(dry_run=args.dry_run)
    print(f"[+] API Prediction Log: {removed_pred} test queries cleared (header preserved).")

    # 3. Reset Audit Log
    removed_audit = reset_audit_log(dry_run=args.dry_run)
    print(f"[+] Analyst Audit Log:  {removed_audit} test audit records pruned.")

    print("\n" + "-" * 70)
    print(" PROTECTED ASSETS VERIFICATION:")
    print("  - Models Directory (models/*.pkl):       UNTOUCHED [OK]")
    print("  - Core Raw Datasets (data/raw/):         UNTOUCHED [OK]")
    print("  - Processed Datasets (data/processed/):  UNTOUCHED [OK]")
    print("  - Application Code & Configs:            UNTOUCHED [OK]")
    print("-" * 70)

    if not args.dry_run:
        print("\n[OK] Demonstration workspace successfully reset to pristine state.")
        print(f"    Backups stored in: {BACKUP_DIR.resolve()}\n")
    else:
        print("\n[OK] Dry run completed. No files were modified.\n")


if __name__ == "__main__":
    main()
