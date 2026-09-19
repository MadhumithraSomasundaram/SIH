# Phase 20: Pre-Demonstration Tactical Checklist
## Time-Phased Operational Verification (T-24h, T-1h, T-5m)
### Problem Statement ID: 26184 — Cybercrime Predictive Analytics Framework

---

### Phase 1: 24 Hours Before Judging (T-24h Readiness)

- [ ] **Code Freeze Absolute:** Confirm that no new code edits, model retraining, or dependency upgrades are performed.
- [ ] **Model Integrity Check:** Verify that `models/xgboost_cybercrime_model.pkl` exists, matches the expected file size (~1.2 MB), and loads cleanly via pickle.
- [ ] **Smoke Test Verification:** Run `python src/system_smoke_test.py` and confirm all 10/10 steps pass in $<0.30\text{ seconds}$.
- [ ] **Pytest Regression Run:** Execute `pytest tests/ -v -m "not live_db" --ignore=tests/test_database.py` and verify zero unexpected failures.
- [ ] **Batch Script Verification:** Double-click `scripts/run_demo.bat` and `scripts/run_tests.bat` to confirm smooth Windows command prompt execution.
- [ ] **Offline Data Verification:** Ensure `data/demo/demo_prediction_input.csv` and `outputs/phase15_hotspots.geojson` are present and readable.
- [ ] **Hardware & Charger Redundancy:** Confirm laptop charger, mouse, HDMI adapter, and backup USB drive containing full repository zip are packed.
- [ ] **Browser Pre-Caching:** Ensure Leaflet CSS/JS assets and OpenStreetMap tile layers are loaded once in Google Chrome and Microsoft Edge to populate local cache.

---

### Phase 2: 1 Hour Before Judging (T-1h Readiness)

- [ ] **Display & Resolution Setting:** Connect to the external projector/monitor. Set resolution to standard 1920x1080 (or adjust browser zoom to 80% if projecting at 1024x768).
- [ ] **Power Management:** Set Windows Power Plan to **"Best Performance"**; disable screen sleep, automatic lock, and screensaver timeouts.
- [ ] **Kill Background Processes:** Close heavy background software (Steam, Discord, Torrent clients, OneDrive sync, antivirus scans, large Docker daemons).
- [ ] **Port 8000 Verification:** Run `Get-NetTCPConnection -LocalPort 8000` in PowerShell to ensure port 8000 is completely free.
- [ ] **Browser Preparation:**
  - Tab 1: `http://127.0.0.1:8000/docs` (Swagger UI interactive API documentation).
  - Tab 2: `http://127.0.0.1:8000/dashboard` (Tactical GIS Analyst Dashboard).
  - Tab 3: `outputs/phase10_shap_summary.png` (Static high-resolution SHAP waterfall chart).
  - Tab 4: `outputs/phase20_technical_60_seconds.md` (Presenter's quick reference).
- [ ] **Terminal Layout:** Open two clean PowerShell / CMD windows:
  - Window 1: Ready to launch `scripts/run_demo.bat`.
  - Window 2: Parked at project root for live curl/smoke test queries.

---

### Phase 3: 5 Minutes Before Judges Arrive (T-5m Final Sanity)

- [ ] **Silence & Do Not Disturb:** Enable Windows "Focus Assist / Do Not Disturb". Mute system audio (unless using alert chime demo) and silence all mobile phones.
- [ ] **Local Network Check:** Confirm laptop is either on stable venue Wi-Fi or fully prepared to operate in offline vector cache mode.
- [ ] **Final Warm-Up Query:** Run a single dry test:
  ```powershell
  python -c "from src.predict import predict_single_record; print('Ready')"
  ```
- [ ] **Team Stationing & Speaking Roles:**
  - *Team Lead:* Stands at projector; delivers 60s pitch and handles operational/policy questions.
  - *ML Engineer:* Manages laptop; drives live API calls and explains XGBoost/SHAP metrics.
  - *Backend Architect:* Ready for database, spatial clustering, and performance throughput questions.
  - *Legal/Compliance Lead:* Ready for Section 65B/63, DPDP Act, and ethical human-in-the-loop governance inquiries.
- [ ] **Mindset & Body Language:** Stand tall, maintain eye contact with judges, embrace statistical honesty, and never get defensive when questioned on metrics.
