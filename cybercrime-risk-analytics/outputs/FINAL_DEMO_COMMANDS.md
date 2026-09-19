# Final Master Demo Commands & Verification Guide
## Exact Working Commands for Smart India Hackathon Live Demonstration
### Problem Statement ID: 26184 — Cybercrime Predictive Analytics Framework

---

### 1. Instant 1-Click Demonstration Launcher (Recommended)

Double-click or run from PowerShell:
```powershell
scripts\run_demo.bat
```
**What this does automatically:**
1. Navigates to project root.
2. Verifies Python environment and dependencies.
3. Executes the 10-step system smoke test (`src/system_smoke_test.py`) in $<2.0\text{s}$.
4. Boots the FastAPI production ASGI server on `http://127.0.0.1:8000`.
5. Automatically opens default browser to Swagger documentation (`/docs`) and GIS Dashboard (`/dashboard`).

---

### 2. Manual Step-by-Step Command Sequence

#### Step A: Directory Anchoring
```powershell
cd /d d:\SIH\SIH_2026\cybercrime_prediction
```

#### Step B: Standalone Pre-Flight Smoke Test
Verify that the entire machine learning and alert pipeline is healthy:
```powershell
python src/system_smoke_test.py
```
*Expected Output: `SYSTEM SMOKE TEST COMPLETE: 10/10 STEPS PASSED` (Time: ~1.9s)*

#### Step C: Launch FastAPI ASGI Server
```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected Output: `Application startup complete. Uvicorn running on http://127.0.0.1:8000`*

#### Step D: Direct URL Access for Judges
- **Tactical GIS Command Dashboard:** [`http://127.0.0.1:8000/dashboard`](http://127.0.0.1:8000/dashboard)
- **Authorized Analyst Workspace:** [`http://127.0.0.1:8000/analyst`](http://127.0.0.1:8000/analyst)
- **Interactive REST API Documentation:** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)

---

### 3. Programmatic CLI Testing & Inference Commands

#### Test Inference with Pre-Loaded Demonstration Input:
```powershell
python src/predict.py --input data/new_prediction_input.csv
```
*Expected Output: Batch predictions on 5 records, drift diagnosis, and local SHAP explanation.*

#### Execute Full Automated Pytest Suite:
```powershell
pytest tests/ -v -m "not live_db" --ignore=tests/test_database.py
```
*Expected Output: `225 passed, 1 skipped in ~68s`*

#### Windows 1-Click Automated Test Runner:
```powershell
scripts\run_tests.bat
```

---

### 4. Direct API Curl / Webhook Verification

#### Health Liveness Check:
```powershell
curl -X GET http://127.0.0.1:8000/health
```

#### Model Information & Feature Schema:
```powershell
curl -X GET http://127.0.0.1:8000/model/info
```

#### Single Record Risk Inference:
```powershell
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d "{\"crime_type\":\"Online Financial Fraud\",\"fraud_amount\":75000.0,\"victim_district\":\"Trichy\",\"latitude\":10.7905,\"longitude\":78.7047}"
```

#### Retrieve DBSCAN Spatial Hotspots (GeoJSON):
```powershell
curl -X GET http://127.0.0.1:8000/gis/hotspots
```
