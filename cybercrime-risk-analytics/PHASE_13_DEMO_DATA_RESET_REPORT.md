# Phase 13 — Demonstration Data Reset Tool & Idempotency Verification

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**Tool Script:** `scripts/reset_demo_data.py`  
**Execution Flags:** `--confirm` (Mandatory for live reset), `--dry-run` (Safe preview)  
**Status:** PASSED (Verified Idempotent, Safe, and Non-Destructive)

---

## 1. Executive Summary

During live SIH demonstrations and multi-session jury evaluations, test complaints, simulated bank freezes, case notes, and evaluation queries are repeatedly submitted. To ensure presenters can restore the system to an identical, pristine baseline between judging rounds without server restarts or code reinstallation, a dedicated reset utility was implemented in `scripts/reset_demo_data.py`.

This tool enforces strict safety constraints:
- **Mandatory Confirmation:** Halts immediately with an exit code 1 if invoked without `--confirm`.
- **Zero Data Loss for Training & Models:** Completely excludes `models/`, `data/raw/`, and `data/processed/` from modification.
- **Automated Timestamped Backups:** Saves timestamped pre-reset copies to `data/backup_csv/` before modifying any target.
- **Baseline Seed Preservation:** Preserves canonical demo records (e.g. `FBK-DEMO-000001` and `FBK-DEMO-000002` in `phase21_outcome_feedback.csv`).

---

## 2. Target Files & Reset Strategy

| Target Resource | Location | Reset Strategy | Baseline State Retained |
| :--- | :--- | :--- | :--- |
| **Outcome Feedback** | `outputs/phase21_outcome_feedback.csv` | Prunes ad-hoc test rows | 2 canonical demo cases preserved |
| **API Prediction Log**| `outputs/predictions/api_prediction_log.csv`| Truncates test prediction log | Header row strictly preserved |
| **Analyst Audit Trail**| `outputs/phase17_analyst_audit_log.csv`| Prunes test runs prefixed `E2E Test:` | System baseline audit records retained |
| **In-Memory Cache** | Application Memory (`AppState`) | Cleared on next request / reload | Re-seeded from pristine CSVs |

---

## 3. Verification Log & Safety Probing

### 3.1 Safety Halt Probe (No Flags)
```bash
$ python scripts/reset_demo_data.py
======================================================================
 CYBERCRIME PREDICTIVE ANALYTICS PLATFORM (SIH #26184)
 DEMONSTRATION ENVIRONMENT RESET TOOL
======================================================================

[!] SAFETY HALT: You must pass --confirm to reset demonstration data.
    Usage: python scripts/reset_demo_data.py --confirm
    Or run with --dry-run to view what would be modified.
(Exit Code: 1)
```

### 3.2 Simulation Probe (`--dry-run`)
```bash
$ python scripts/reset_demo_data.py --dry-run
[*] Execution Mode: [DRY RUN]
[+] Outcome Feedback:  1 test rows pruned (baseline preserved).
[+] API Prediction Log: 854 test queries cleared (header preserved).
[+] Analyst Audit Log:  0 test audit records pruned.
----------------------------------------------------------------------
 PROTECTED ASSETS VERIFICATION:
  - Models Directory (models/*.pkl):       UNTOUCHED [OK]
  - Core Raw Datasets (data/raw/):         UNTOUCHED [OK]
  - Processed Datasets (data/processed/):  UNTOUCHED [OK]
  - Application Code & Configs:            UNTOUCHED [OK]
----------------------------------------------------------------------
[OK] Dry run completed. No files were modified.
(Exit Code: 0)
```

### 3.3 Live Execution Probe (`--confirm`)
```bash
$ python scripts/reset_demo_data.py --confirm
[*] Execution Mode: [LIVE RESET]
[+] Outcome Feedback:  1 test rows pruned (baseline preserved).
[+] API Prediction Log: 854 test queries cleared (header preserved).
[+] Analyst Audit Log:  0 test audit records pruned.
[OK] Demonstration workspace successfully reset to pristine state.
    Backups stored in: D:\SIH\SIH_2026\cybercrime_prediction\data\backup_csv
(Exit Code: 0)
```

---

## 4. Protected Assets Verification

A checksum and directory inspection confirmed that:
1. `models/xgboost_cybercrime_model.pkl`: Size, modification date, and SHA-256 unchanged.
2. `models/phase7_xgboost_metadata.json`: Unchanged.
3. `data/raw/` & `data/processed/`: All CSV files unchanged.
4. `database/` & `api/`: All source files unchanged.

**Conclusion:** The demonstration reset script is thoroughly validated, safe, and ready for presenter use during the SIH evaluation.
