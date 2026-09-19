# Phase 19 — 5-Minute SIH Live Demonstration Script
## Predictive Cybercrime Intelligence System
**Problem Statement ID:** 26184  
**Presenter Role:** Lead System Architect / Data Scientist  
**Target Duration:** Exactly 5 Minutes  
**Prerequisites Running:** `uvicorn api.main:app --port 8000`  

---

### [00:00 – 00:20] OPENING & SETUP
**Action**: Stand before screen. Have browser open at `http://localhost:8000/dashboard`.  
**Spoken Words**:  
> *"Respected judges, here we have our **Predictive Cybercrime Intelligence Dashboard** for Problem Statement 26184. In cyber financial fraud, criminals rapidly move stolen money across mule accounts, but their ultimate physical bottleneck is converting digital funds into cash at an ATM. Today, we demonstrate how our platform transforms raw complaint signals into predictive risk scores, explainable AI factors, spatial hotspots, and authorized human-in-the-loop investigation workflows."*

---

### [00:20 – 00:50] STEP 1 & 2: DASHBOARD & ANALYTICAL RISK MAP
**Action**: Point to Leaflet map container on the screen. Toggle the "Risk Intensity" layer.  
**Spoken Words**:  
> *"As you can see on the central display, our system renders an interactive spatio-temporal risk map. Rather than showing simple static pins of past complaints, the map reflects model-derived risk gradients across regional sectors. These signals are computed using 64 backward-looking temporal lags, rolling event frequencies, and spatial density grids—completely free of data leakage."*

---

### [00:50 – 01:25] STEP 3 & 4: SELECTING AN AREA & INSPECTING PREDICTIONS
**Action**: Click on Sector #14 (Andheri East corridor) or load the synthetic demo record `DEMO_CASE_003_HIGH`. Point to the prediction KPI panel.  
**Spoken Words**:  
> *"Let us select this elevated analytical sector. When a new complaint signal arrives, our pre-trained XGBoost model performs sub-second inference. Here are the exact outputs:  
> - **Predicted Withdrawal Probability**: **0.6319** (63.2%)  
> - **Calibrated Risk Score**: **63 / 100**  
> - **Operational Risk Tier**: **HIGH**  
> Notice that our risk score is mathematically deterministic: exactly round(probability × 100). This provides an intuitive scale for field officers without hiding the underlying probability."*

---

### [01:25 – 02:00] STEP 5: EXPLAINABLE AI VIA SHAP
**Action**: Click the **"Model Explanation"** button. The SHAP horizontal bar plot opens in a drawer or modal.  
**Spoken Words**:  
> *"A major limitation of traditional ML in policing is the 'black box' dilemma. Officers cannot act on an opaque number. By integrating SHAP TreeExplainer, we compute local Shapley values in real time without refitting.  
> Looking at the top risk contributors:  
> - The 24-hour localized complaint surge contributed **+0.182** toward the probability.  
> - The elevated transaction amount contributed **+0.141**.  
> We specifically state: 'these features contributed toward a higher model prediction'—we never make the unscientific claim that they 'caused' the crime."*

---

### [02:00 – 02:40] STEP 6: DBSCAN SPATIAL HOTSPOT CORRELATION
**Action**: Toggle the **"Hotspots"** layer on the map. Orange/red polygon cluster boundaries appear over ATM locations.  
**Spoken Words**:  
> *"Now, let us examine the spatial clustering. Notice this polygon overlay: this is a DBSCAN spatial hotspot cluster.  
> **Here is a critical architectural distinction**:  
> This hotspot is an unsupervised spatial cluster detected from historical cashout density using Haversine distance. It is completely separate from the XGBoost prediction. XGBoost gives us the predictive risk signal; DBSCAN gives us the physical corridor where ATMs congregate. Combining both produces an **Analytical Priority Corridor** where proactive patrol deterrence will be most effective."*

---

### [02:40 – 03:20] STEP 7: ALERT GENERATION & NON-PUNITIVE SAFEGUARDS
**Action**: Click on the **"Alerts"** panel. Highlight the generated alert banner: `ALT-20260916-014`.  
**Spoken Words**:  
> *"Because this incident exceeded our risk threshold of 60 and fell within an active hotspot, our alert engine generated an operational alert.  
> Notice the strict ethical safeguard here: **`human_review_required = True`**.  
> The system has no hooks to automatically freeze accounts, block transactions, or accuse anyone. It is strictly a decision-support tool alerting authorized analysts for human verification."*

---

### [03:20 – 04:00] STEP 8, 9 & 10: ANALYST INTERFACE & INVESTIGATION CREATION
**Action**: Switch tabs or navigate to `http://localhost:8000/analyst`. Log in as `demo_analyst`. Open the Alert Inbox, click **Acknowledge**, then click **Create Investigation**.  
**Spoken Words**:  
> *"Now we transition to the authorized law enforcement interface at `/analyst`. Here, an authenticated investigator reviews the alert queue.  
> The analyst clicks **'Acknowledge'**, shifting the lifecycle state from NEW to ACKNOWLEDGED.  
> Next, they click **'Create Investigation'**, creating case file `INV-2026-0042`. Our state machine strictly governs this pipeline—arbitrary status jumping is rejected by the backend."*

---

### [04:00 – 04:35] STEP 11 & 12: ADDING CASE NOTES & EVIDENCE REFERENCES
**Action**: Type a case note in the Notes box: *"Initiating beat patrol notice for Sector 14 ATM corridor."* Click **Add Note**. Click **Add Evidence Reference**, entering `NCRP-ACK-REF-2026-9912`.  
**Spoken Words**:  
> *"The officer appends an operational observation: 'Initiating beat patrol notice for Sector 14 ATM corridor.' This note is permanently stamped with the officer's ID and timestamp.  
> Next, the officer attaches an external evidence reference: `NCRP-ACK-REF-2026-9912`. In strict compliance with data privacy laws, we do not upload or store raw banking documents or citizen PII; we store standardized reference pointers for inter-agency coordination."*

---

### [04:35 – 05:00] STEP 13 & CONCLUSION: IMMUTABLE AUDIT TRAIL
**Action**: Click on the **"Audit Log"** tab. Scroll through the chronological audit entries showing LOGIN, ACKNOWLEDGE, CREATE_INVESTIGATION, ADD_NOTE, ADD_EVIDENCE.  
**Spoken Words**:  
> *"Finally, we navigate to the Audit Log. Every single query, status update, note, and evidence reference is logged into an immutable ledger with cryptographic timestamps and role attributions, ensuring complete legal accountability.  
> **In conclusion**: The system successfully moves from predictive analytics, to explainable spatial intelligence, and finally to human-reviewed operational action.  
> Thank you, and we welcome your questions!"*
