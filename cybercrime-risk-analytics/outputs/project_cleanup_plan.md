# Cybercrime Risk Analytics: Project Cleanup Plan

## 1. Backup Status
- **Git Status:** The project is NOT a Git repository.
- **Backup Archive:** A full backup has been successfully created at `d:\SIH\SIH_2026\cybercrime_prediction_backup.zip`.

## 2. File Categories & Discovery
A complete scan of the 500 files in the project has been performed. The exhaustive inventory is available at `outputs/project_cleanup_inventory.csv`.

### Files Safe to Remove (Category E: Generated Cache)
- `__pycache__` directories and `.pyc` files (e.g., `api/__pycache__/*`, `database/__pycache__/*`, `src/__pycache__/*`, `tests/__pycache__/*`).
- `.pytest_cache` directories and contents.
- Temporary files like `.DS_Store` or `Thumbs.db` (if any are found).

### Files that Must be Preserved (Category A: Required and Used)
- All trained model artifacts (`models/*.json`, `models/*.pkl`, `models/*.joblib`).
- Preprocessors, feature schemas, and SHAP outputs.
- Database configurations and PostgreSQL migration files.
- Datasets (`data/*`) ensuring synthetic demo datasets remain intact.
- Source code (`api/`, `database/`, `src/`, `dashboard/`, `analyst/`).
- Test files (`tests/*.py`).
- Important documentation and configuration files (`README.md`, `requirements.txt`, `.env.example`).

### Files Requiring Manual Review (Category H: Unknown)
- Temporary experimental scripts or unused notebooks.
- Obsolete implementations that may conflict with the current intended architecture (none confirmed yet; to be verified during cleanup execution).

## 3. Duplicate Files
- No structural duplicate application components were found during the initial scan. Exact hashing can be used for deep validation if requested.

## 4. Execution Plan
1. Delete all `__pycache__` directories and `.pyc` files.
2. Delete the `.pytest_cache` directory.
3. Remove `generate_inventory.py` (the temporary script created to generate the CSV).
4. Verify the system startup and run the test suites (`test_end_to_end.py`, `test_dashboard_polish.py`, etc.) to ensure zero breakage.
5. Create the final cleanup report (`outputs/final_cleanup_report.md`).
