# Problem Statement & Solution Breakdown for SIH Evaluators

**Project:** Cybercrime Predictive Analytics Framework  
**Problem Statement ID:** 26184  
**Date:** 2026-09-19  
**Target Audience:** Smart India Hackathon Technical & Law Enforcement Jury

---

## 1. The Existing Cybercrime Challenge

Cyber-enabled financial fraud represents one of the fastest-growing categories of criminal activity worldwide. When citizens fall victim to phishing scams, identity theft, unauthorized UPI transfers, or investment frauds, the fraudulent proceeds are rapidly layered through chains of intermediary "mule accounts" before being converted into untraceable physical cash at automated teller machines (ATMs).

### 1.1 The Critical "Cashout Window" Gap
The fundamental vulnerability in traditional law enforcement workflows is the **temporal lag between complaint registration and operational action**:
- **Citizen Delay:** Victims often take between 1 to 4 hours to recognize fraud and register a complaint via the National Cyber Crime Reporting Portal (NCRP) or police helpline.
- **Inter-Agency Bureaucracy:** Once logged, obtaining bank transaction trails and tracing account hops through formal legal notices requires hours or days.
- **Mule Velocity:** Organized cyber syndicates deploy local "runners" who systematically withdraw funds at physical ATMs within **60 to 180 minutes** of the initial fraud.

By the time investigating officers receive actionable transaction statements, the illicit capital has already left the formal financial system.

---

## 2. Why Cybercrime Complaint Volume is Overwhelming

Modern law enforcement agencies receive tens of thousands of cybercrime complaints monthly. Traditional manual review faces severe structural bottlenecks:
1. **Low Signal-to-Noise Ratio:** Thousands of minor, non-actionable complaints dilute critical high-value syndicates.
2. **Cognitive Overload:** Human triage teams cannot manually calculate transaction velocity, cross-reference regional ATM networks, or detect recurring multi-district mule patterns in real time.
3. **Reactive Stance:** Triage officers are forced to operate purely reactively, investigating where funds *went yesterday* rather than where extractions are *occurring now*.

---

## 3. Why Early Cashout-Location Estimation Matters

The physical ATM is the single point of vulnerability for cyber syndicates. Unlike digital ledger transfers that execute in milliseconds across state lines, **physical cash withdrawal requires a physical perpetrator at a physical machine in the physical world**.

If law enforcement can forecast the likelihood and candidate physical corridors of an impending cashout within minutes of complaint intake:
- **Targeted Patrol Dispatch:** PCR (Police Control Room) patrol vans and beat officers can be directed to high-density ATM clusters along suspected exit corridors.
- **Branch & CCTV Alerts:** Bank branch security and CCTV monitoring rooms at candidate ATM locations can be alerted in advance.
- **Account Interdiction:** Emergency account freeze notices can be targeted at active extraction accounts before cashout limits are exhausted.

---

## 4. The Architectural Role of the Framework

Our framework introduces an integrated analytical workflow engineered specifically to support human decision-makers:

```
[Raw Citizen Complaint]
         ↓
[Predictive Analytics (XGBoost)]      → Forecasts: Will this case cash out within 24h?
         ↓
[Explainable AI (SHAP)]               → Explains: Why is this complaint high-risk?
         ↓
[Spatial Analysis (DBSCAN + GIS)]     → Estimates: Which physical ATM corridors are at risk?
         ↓
[Alert & Investigation Engine]        → Triage: Generates actionable alerts with cooldowns
         ↓
[Banking Liaison Desk]                → Interdicts: Issues emergency account freeze orders
```

### 4.1 Role of Predictive Analytics
The frozen XGBoost inference pipeline evaluates behavioral features (monetary amount, transaction time, cyclic hour, district history, velocity ratios) to output a calibrated cashout probability ($P \in [0, 1]$) and composite risk score ($0 - 100$). This filters out low-risk noise and highlights high-threat incidents in 14 milliseconds.

### 4.2 Role of Spatial Analysis
DBSCAN spatial clustering ($\varepsilon=500\text{m}, \text{MinPts}=3$) identifies recurring historical withdrawal nodes across 3,000 physical ATMs. Vectorized Haversine algorithms compute spatial distances, establishing 5km catchment corridors around candidate ATM nodes.

### 4.3 Role of Explainable AI (SHAP)
Field officers will not act on opaque "black-box" scores. Local SHAP attribution generates human-readable waterfall charts detailing the top drivers for each prediction (e.g. *"+32% risk due to high fraud amount," "+18% risk due to rapid account velocity"*), providing transparent justification for operational dispatch.

### 4.4 Role of Authorized Analysts & Human-in-the-Loop
The system is explicitly an **Intelligence Support System**, not an autonomous arrest bot. Every alert must be triaged, promoted, and approved by an authorized law enforcement analyst or supervisor before field action is taken.

---

## 5. What the System Explicitly Does NOT Guarantee

To maintain total scientific credibility before hackathon evaluators, our team emphasizes realistic boundaries:

1. **No Guaranteed Criminal Identification:** The platform predicts ATM withdrawal *locations* and *likelihoods*. It does not possess facial recognition or track specific individual suspects.
2. **No Guaranteed Monetary Recovery:** Rapid patrol dispatch maximizes the probability of interdiction, but cannot guarantee that cash has not already been dispensed.
3. **Estimated, Not Deterministic ATM Pinpoints:** The framework identifies candidate 5km spatial corridors and ranked ATM clusters; it does not claim to know the exact individual ATM machine with 100% certainty.
4. **Synthetic Data Sandbox:** The current iteration was validated using synthetic and anonymized complaint datasets to respect citizen privacy; production deployment requires integration with live state police CCTNS/NCRP networks.
5. **No Direct Real-Time Bank Integration:** The banking portal provides simulated inter-agency freeze workflows; production deployment requires formal API integration with NPCI and commercial core banking systems (CBS).
