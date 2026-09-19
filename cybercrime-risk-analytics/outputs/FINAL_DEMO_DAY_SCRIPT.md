# Final Demo Day Presentation Script: 5-Minute Live Walkthrough
## Timed, Actionable Demonstration Script for SIH Judges
### Problem Statement ID: 26184 — Cybercrime Predictive Analytics Framework

---

### Overview & Timing Strategy

| Time Window | Segment | Primary Objective | Speaker |
|---|---|---|---|
| **0:00 – 0:30** | Problem Introduction | Establish the "Golden Window" & ATM cash-out choke point | Team Lead |
| **0:30 – 1:00** | Incoming Event Ingestion | Show complaint telemetry & privacy-preserving schema | ML Engineer |
| **1:00 – 1:45** | AI Risk Prediction | Execute inference in $<30\text{ms}$ & show calibrated probability | ML Engineer |
| **1:45 – 2:15** | Risk Score & SHAP | Show risk tier & court-admissible SHAP attribution | ML Engineer |
| **2:15 – 3:00** | GIS Map & DBSCAN | Distinguish XGBoost predictive risk from DBSCAN spatial clusters | Backend Lead |
| **3:00 – 3:45** | Alert Generation | Show alert severity & mandatory human review flag | Team Lead |
| **3:45 – 4:30** | Analyst Investigation | Demonstrate case state machine & SHA-256 audit log | Backend Lead |
| **4:30 – 5:00** | Impact, Ethics & Limitations | Emphasize non-punitive governance, FOSS, & cost efficiency | Team Lead |

---

### Segment 1: Problem Introduction (0:00 – 0:30)

- **WHAT I CLICK:** Presenter stands beside the display screen showing the title slide or dashboard homepage (`http://127.0.0.1:8000/dashboard`).
- **WHAT I SAY:**
  > *"Respected Judges, digital banking fraud in India is bleeding thousands of crores out of ordinary citizens. But digital fraud faces a physical bottleneck: cyber syndicates must convert stolen digital ledger balances into untraceable physical paper cash at ATMs before victim debit cards or transit accounts are frozen.
  > Today, police receive 1930 complaints hours after the fact and have no way to predict which of the thousands of ATMs across a city are being targeted. We built an authorized decision-support framework that bridges this gap in under 30 milliseconds."*
- **WHAT THE JUDGE SHOULD SEE:** The clean, dark-mode Tactical Command Dashboard loaded with active GIS layers and alert status indicators.
- **BACKUP IF IT FAILS:** If the browser tab is closed or lagging, switch immediately to pre-opened `dashboard/index.html` or display Slide 1 of the offline presentation deck (`outputs/phase19_final_presentation.md`).

---

### Segment 2: Incoming Complaint / Event (0:30 – 1:00)

- **WHAT I CLICK:** Click the **"Load Demo Complaint"** button (or open `DEMO_CASE_003_HIGH` in the Swagger UI at `http://127.0.0.1:8000/docs`).
- **WHAT I SAY:**
  > *"Here is an incoming complaint reported to the cyber helpline. Notice the critical telemetry: a victim lost ₹75,000 via unauthorized IMPS transfer, followed by 4 rapid debit attempts within 30 minutes in the Woraiyur sector of Trichy.
  > Notice also what is NOT here: no Aadhaar numbers, no unmasked phone numbers, and no banking passwords. In strict accordance with the Digital Personal Data Protection Act, 2023, the data is anonymized and stripped of citizen PII before processing."*
- **WHAT THE JUDGE SHOULD SEE:** A modal window displaying the validated JSON payload with fields `case_id: DEMO_CASE_003_HIGH`, `fraud_amount: 75000`, `velocity_30m: 4`, and `crime_type: Online Banking Fraud`.
- **BACKUP IF IT FAILS:** Show the pre-compiled CSV row directly from `data/demo/demo_prediction_input.csv` or view the terminal output of `python src/system_smoke_test.py`.

---

### Segment 3: AI Risk Prediction (1:00 – 1:45)

- **WHAT I CLICK:** Click the **"Execute Prediction"** button.
- **WHAT I SAY:**
  > *"When we dispatch this payload, our asynchronous FastAPI pipeline validates the 64 engineered features in 1.2 milliseconds and sends them through our frozen XGBoost model.
  > In just 1.8 milliseconds of CPU compute—totaling 29 milliseconds end-to-end—the model computes the predicted withdrawal probability: 0.6319, or 63.2%."*
- **WHAT THE JUDGE SHOULD SEE:** An instantaneous green status badge displaying `Status: 200 OK | Latency: 29ms | Predicted Probability: 0.6319`.
- **BACKUP IF IT FAILS:** Execute the quick CLI command in the open PowerShell window:
  `python -c "from src.predict import predict_single_record; print(predict_single_record({'fraud_amount': 75000}))"` which returns the exact pre-calculated score in $<0.2\text{s}$.

---

### Segment 4: Risk Score & SHAP Explainability (1:45 – 2:15)

- **WHAT I CLICK:** Click the **"SHAP Explainability"** tab to open the waterfall attribution plot.
- **WHAT I SAY:**
  > *"The raw probability maps deterministically to a calibrated Risk Score of 63 out of 100, categorizing this case as HIGH priority.
  > Crucially, our system is never a black box. Using SHAP TreeExplainer, we provide exact local feature attributions. 
  > These features contributed toward the model's prediction: the local historical complaint density in Woraiyur contributed +53 percentage points, and the rapid rolling 6-hour event velocity contributed +7.9 percentage points.
  > We never say 'this feature caused the crime.' We provide an objective, court-admissible explanation under Section 65B of the Evidence Act and Section 63 BSA."*
- **WHAT THE JUDGE SHOULD SEE:** The Risk Gauge pointing to `63 (HIGH)` alongside the SHAP bar chart showing positive contributions from `victim_area_Woraiyur` and `rolling_event_count_6h`.
- **BACKUP IF IT FAILS:** Open pre-rendered high-resolution image `outputs/phase10_shap_summary.png` directly in Windows Photo Viewer.

---

### Segment 5: GIS Map & DBSCAN Hotspot Clustering (2:15 – 3:00)

- **WHAT I CLICK:** Click **"Correlate Spatial Clusters"** on the dashboard. The Leaflet map pans smoothly to coordinates `(10.7905, 78.7047)`.
- **WHAT I SAY:**
  > *"Now observe our spatial intelligence layer. It is vital to distinguish our two algorithms:  
  > 1. XGBoost provides the **Predictive Risk Signal** based on transaction behavioral kinematics.  
  > 2. DBSCAN provides **Spatial Density Clustering**, grouping historical coordinates within 500 meters and discarding isolated outliers as noise.  
  > Look at Urban Cluster #14 on the map: it encloses 6 commercial bank ATMs and 2 CSP kiosks along the market road. By combining XGBoost with DBSCAN, we define a precise 500-meter patrol corridor, turning an impossible needle-in-a-haystack search into an actionable patrol perimeter."*
- **WHAT THE JUDGE SHOULD SEE:** A responsive Leaflet map showing the red incident marker enclosed within a translucent blue 500-meter polygon (Urban Cluster #14) with nearby bank ATM pins clearly highlighted.
- **BACKUP IF IT FAILS:** If internet tiles fail to load, point to the SVG polygon boundaries: *"Notice that our spatial polygons render offline from local GeoJSON vector files (`phase15_hotspots.geojson`) with full geodetic precision."*

---

### Segment 6: Alert Generation (3:00 – 3:45)

- **WHAT I CLICK:** Click the **"Alert Notifications"** drawer in the upper right navigation bar.
- **WHAT I SAY:**
  > *"Because this incident crosses our operational threshold of 50, an analytical alert is immediately triggered: Alert ALT-2026-0815-003 with severity HIGH_RISK_LOCATION.
  > Notice the prominent banner: 'Human Review Required: True | Automated Freezing: Prohibited'.
  > Our system enforces strict constitutional due process under Article 21. It never automatically halts bank switches or orders autonomous police actions. It acts as an intelligence advisor to the duty cyber analyst."*
- **WHAT THE JUDGE SHOULD SEE:** A high-contrast alert card displaying Alert ID, timestamp, Severity (`HIGH`), Risk Score (`63`), and the prominent Human Review requirement flag.
- **BACKUP IF IT FAILS:** View the pre-compiled alert log in `outputs/phase16_alert_validation.csv`.

---

### Segment 7: Analyst Investigation & Audit Trail (3:45 – 4:30)

- **WHAT I CLICK:** Click **"Open in Analyst Portal"** $\to$ click **"Claim Investigation"** $\to$ switch status to `UNDER_INVESTIGATION` $\to$ click **"Audit Trail"**.
- **WHAT I SAY:**
  > *"Here in the Authorized Analyst Workspace, an assigned officer claims the case. The officer enters investigative notes, generates an emergency Section 91 CrPC advisory to the bank nodal desk, and alerts mobile beat units.
  > Look at the Audit Trail tab: every action—from the initial API scoring to the analyst's note—is sealed with an immutable SHA-256 cryptographic hash and millisecond UTC timestamp. The database prohibits UPDATE and DELETE queries on audit tables, guaranteeing tamper-proof chain of custody for prosecution."*
- **WHAT THE JUDGE SHOULD SEE:** The investigation case dossier showing updated status `UNDER_INVESTIGATION`, case notes, attached SHA-256 evidence hashes, and the corresponding append-only row in the Audit Log table.
- **BACKUP IF IT FAILS:** Show the test database verification table in `outputs/phase18_analyst_validation.csv` or terminal output of Step 9 and 10 from `system_smoke_test.py`.

---

### Segment 8: Impact, Ethics & Limitations (4:30 – 5:00)

- **WHAT I CLICK:** Return to the primary overview screen.
- **WHAT I SAY:**
  > *"To conclude: our system is 100% Free and Open-Source, requiring zero expensive GPU hardware or recurring cloud fees. It runs completely air-gapped on standard state police servers.
  > We present completely honest, locked Phase 8 test metrics: 86.93% Accuracy, 96.73% Specificity, and 0.1029 PR-AUC—representing a 3.2x lift over random guessing under real-world 10% class imbalance.
  > We don't claim to predict crime with a crystal ball. We provide authorized law enforcement with the operational clarity to protect ordinary citizens before their life savings disappear into paper cash. Thank you, and we are ready for your questions."*
- **WHAT THE JUDGE SHOULD SEE:** Summary scorecard slide displaying architecture metrics, 100% test pass rate, and team contact details.
- **BACKUP IF IT FAILS:** Deliver the spoken conclusion with confident posture and point judges to the physical laminated 2-page executive summary handout.
