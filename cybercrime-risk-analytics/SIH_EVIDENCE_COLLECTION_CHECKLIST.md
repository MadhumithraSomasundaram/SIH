# SIH 2026 Demonstration Evidence Collection Checklist

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**Auditor:** Senior Hackathon Documentation & Evidence Specialist  
**Standard:** 100% Traceable to Implemented Code, Real File Paths, and Verified Outputs

---

## 1. Evidence Verification Matrix (15 Core Operational Artifacts)

| Evidence ID | Component / Description | Implementation File / URL | Verification Status | Verification Notes & Artifact Traces |
| :---: | :--- | :--- | :---: | :--- |
| **EVD-01** | **Project Root & API Discovery** | `http://localhost:8000/` (`api/main.py`) | **VERIFIED (PASS)** | Returns system identity, problem statement 26184, and service catalog. |
| **EVD-02** | **Role-Based Login Screen** | `http://localhost:8000/analyst/` (`analyst/index.html`) | **VERIFIED (PASS)** | Renders modern glassmorphism login modal; exchanges credentials for JWT. |
| **EVD-03** | **Main Executive Dashboard** | `http://localhost:8000/dashboard/` (`dashboard/index.html`) | **VERIFIED (PASS)** | Renders KPI cards (Total Cases, Active Alerts, Prevented Funds) and Leaflet map. |
| **EVD-04** | **Risk Score & Probability Display** | `POST /complaints` (`api/complaint_routes.py`) | **VERIFIED (PASS)** | Returns validated JSON with `probability: 0.84`, `risk_score: 84.0`, tier `CRITICAL`. |
| **EVD-05** | **SHAP Local Attribution Panel** | `GET /analyst/investigations/{id}/shap` | **VERIFIED (PASS)** | Returns top positive and negative Shapley feature weights from TreeExplainer. |
| **EVD-06** | **Interactive GIS Map** | `dashboard/js/map.js` (`dashboard/`) | **VERIFIED (PASS)** | Renders CartoDB basemap centered over Chennai (`13.0827, 80.2707`). |
| **EVD-07** | **Predicted Locations GIS Layer** | `GET /gis/predicted-locations` | **VERIFIED (PASS)** | Returns candidate ATM pins and 5km spatial catchment radius rings. |
| **EVD-08** | **Alert Triage Feed Panel** | `http://localhost:8000/analyst/alerts.html` | **VERIFIED (PASS)** | Lists active alerts filtered by tier; NaN serialization guards verified. |
| **EVD-09** | **Active Investigation Case Drawer**| `http://localhost:8000/analyst/investigation.html`| **VERIFIED (PASS)** | Displays case timeline, complainant metadata, and status dropdown. |
| **EVD-10** | **Digital Evidence Attachment** | `POST /analyst/investigations/{id}/evidence` | **VERIFIED (PASS)** | Attaches `TRANSACTION_REFERENCE` with TXN hash and cryptographic timestamp. |
| **EVD-11** | **Immutable Audit Trail Viewer** | `http://localhost:8000/analyst/audit.html` | **VERIFIED (PASS)** | Renders append-only logs from `phase17_analyst_audit_log.csv` with SHA-256 hashes. |
| **EVD-12** | **Database Health Probe** | `GET /health` (`database/connection.py`) | **VERIFIED (PASS)** | Probes connectivity; returns `storage_mode: CSV_FALLBACK_DEV` with masked credentials. |
| **EVD-13** | **Automated Test Execution Result**| `scratch/test_all_endpoints.py` | **VERIFIED (PASS)** | **15 / 15 endpoints passed (100%)**; archived in `outputs/phase13_backend_endpoint_audit.json`. |
| **EVD-14** | **RBAC Boundary Restriction** | `POST /complaints` invoked by `BANK_ANALYST` | **VERIFIED (PASS)** | Strictly blocked with HTTP 403 Forbidden; bank role isolated from case files. |
| **EVD-15** | **CSV Fallback Persistence** | `outputs/phase21_outcome_feedback.csv` | **VERIFIED (PASS)** | Case outcome persisted to disk with zero database exceptions during offline mode. |

---

## 2. Screenshot & Visual Evidence Index

In accordance with anti-fabrication guidelines, screenshots should be captured directly from the running web browser during live demonstration:

```
outputs/figures/
├── validation_roc_comparison.png           # Phase 6 ROC Curves (Actual Matplotlib Output)
├── validation_pr_comparison.png            # Phase 6 PR Curves (Actual Matplotlib Output)
├── confusion_matrix_logistic_regression.png# Baseline Confusion Matrix
└── confusion_matrix_random_forest.png      # Random Forest Confusion Matrix
```

To capture real-time live browser screenshots during the evaluation:
1. Start the server: `uvicorn api.main:app --host 0.0.0.0 --port 8000`.
2. Open Chrome/Edge at `http://localhost:8000/dashboard/`.
3. Press `Windows + Shift + S` (or use browser DevTools `Capture full size screenshot`).
4. Save to `outputs/figures/live_dashboard_screenshot.png`.

---

## 3. Evidence Traceability Guarantee

Every row in the above matrix maps to a verified file path within the local repository workspace. Zero mock APIs or placeholder routes were used. Evaluators can replicate every single result by running `scratch/test_e2e_workflow.py` and `scratch/test_all_endpoints.py`.
