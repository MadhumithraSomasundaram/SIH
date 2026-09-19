# Phase 18 — Smart India Hackathon (SIH) Final Demo Checklist
## Cybercrime Predictive Analytics Framework for Forecasting Likely Cash Withdrawal Locations
**Problem Statement ID:** 26184  
**Project Category:** Law Enforcement & Cybercrime Analytics  
**Deployment Target:** Decision-Support Analyst System  

---

## 1. Pre-Demonstration Verification (Before Taking the Stage)

Ensure the local environment is operational:

- [x] **Python Environment Active**: Python 3.11+ virtual environment verified with all dependencies (`requirements.txt`).
- [x] **Dependencies Verified**: All 24 core packages installed and verified (`outputs/phase18_dependency_report.csv`).
- [x] **Model Artifact Present**: `models/xgboost_cybercrime_model.pkl` and `models/phase7_xgboost_metadata.json` intact.
- [x] **Model Loads Successfully**: Verified via `python -c "import joblib; m = joblib.load('models/xgboost_cybercrime_model.pkl')"`
- [ ] **Database Connection Check**: Note that PostgreSQL/PostGIS is marked *NOT CONFIGURED* if running without external service; confirm system is operating on file/memory fallback.
- [x] **FastAPI Server Ready**: Server starts cleanly via `uvicorn api.main:app --port 8000`.
- [x] **Dashboard Assets Ready**: Web interface accessible at `http://localhost:8000/dashboard` and `http://localhost:8000/analyst`.
- [x] **Demo Dataset Verified**: `data/demo/demo_prediction_input.csv` verified with LOW, MODERATE, and HIGH risk examples.
- [x] **Demo Prediction Output Ready**: `outputs/demo/demo_prediction_results.csv` generated.
- [x] **Smoke Test Passes**: `python src/system_smoke_test.py` completes 10/10 steps in `< 1.0 second`.
- [x] **Unit & Integration Tests Pass**: `pytest tests/test_end_to_end.py -q` yields 21 passed, 1 skipped (0 failed).

---

## 2. Live Demonstration Flow (During SIH Presentation)

Follow this structured chronological narrative:

- [x] **1. Introduce Problem Statement**:
  - State Problem ID 26184: Forecasting likely cash withdrawal locations in advance of cyber fraud cash-outs to enable proactive policing.
  - Explain the critical operational gap: Traditional response is purely reactive (funds are withdrawn before first responders are notified).
- [x] **2. Present Synthetic / Anonymized Data Pipeline**:
  - Show `data/raw/` and `data/processed/` structure.
  - Emphasize strict data hygiene, anonymization, and zero PII leakage.
- [x] **3. Demonstrate Predictive ML Inference**:
  - Execute `python src/predict.py --input data/demo/demo_prediction_input.csv`.
  - Highlight the predicted probability: $P(\text{future\_withdrawal} = 1)$.
- [x] **4. Show Calibrated Risk Scoring & Categorization**:
  - Show risk score calculation: $\text{risk\_score} = \text{round}(P \times 100)$.
  - Show risk tiering: LOW (11), MODERATE (49), HIGH (63).
- [x] **5. Demonstrate Explainable AI (SHAP Local Attribution)**:
  - Highlight top contributing factors (e.g., `rolling_event_count_24h`, `fraud_amount`, district activity).
  - Emphasize to judges: "Law enforcement officers are never presented with a black box."
- [x] **6. Showcase Spatial Hotspot Clustering (DBSCAN)**:
  - Open `outputs/phase14_hotspot_summary.csv` or GIS map.
  - Explain how 40 density-based clusters prioritize physical ATM corridors without manual grid definitions.
- [x] **7. Demonstrate Interactive GIS Dashboard**:
  - Open `http://localhost:8000/dashboard`.
  - Filter by risk level, examine cluster boundaries, inspect ATM density overlays.
- [x] **8. Demonstrate Alert Generation & Notification Engine**:
  - Show how HIGH risk triggers an alert with priority flag.
  - Point out `human_review_required = True`.
- [x] **9. Demonstrate Authorized Analyst Workspace**:
  - Open `http://localhost:8000/analyst`.
  - Show alert triage, case investigation creation, and note logging.
- [x] **10. Demonstrate Immutable Audit Trail**:
  - View audit ledger showing non-repudiable logs of all officer actions, timestamps, and role attributions.

---

## 3. Post-Demo Briefing & Regulatory Alignment (Addressing Judges' Questions)

When questioned on ethics, model limitations, and real-world deployment:

- [x] **Acknowledge Class Imbalance & Real Metrics**:
  - Be completely honest about Phase 8 test metrics: test PR-AUC = 0.1029, ROC-AUC = 0.4760, Precision = 0.0638.
  - Explain that extreme class imbalance (~10% positive rate) makes PR-AUC the authentic metric rather than misleading raw accuracy.
- [x] **Clarify Risk Score Range Limitation**:
  - Explicitly acknowledge: "The trained model naturally produces scores up to 63 on test data; CRITICAL scores (≥80) are not naturally produced under the current threshold, which we document as an honest operational boundary."
- [x] **Reiterate Ethical & Operational Boundaries**:
  - "The system is an analytical decision-support tool for patrol and beat allocation."
  - "The system never labels any individual as a criminal."
  - "No automated account freezes, transaction blocking, or punitive actions exist in this software."
- [x] **Highlight Data Privacy & Regulatory Compliance**:
  - Zero sensitive banking credentials (PAN, PIN, CVV, OTP) or national IDs (Aadhaar) are processed.
- [x] **Outline Roadmap for Live Production Deployment**:
  - Authorized real-time API feeds from NCRP / I4C.
  - Direct integration with core banking switch telemetry under RBI / NPCI compliance frameworks.
  - Continuous model drift monitoring and periodic re-calibration.
