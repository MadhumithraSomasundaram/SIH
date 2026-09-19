# Phase 10 — Human-Readable Local SHAP Explanations

This document provides interpretable factor explanations for representative cybercrime complaints.

> **Operational Note:** Features represent statistical associations learned by the predictive model; they do NOT imply direct real-world causality or definitive proof of criminal activity.

---

### Record Reference: `record_0001` (Case ID: `CASE005933`)
- **Location Group / District:** Mangaluru
- **Crime Category Group:** INVESTMENT_SCAM
- **Predicted Withdrawal Probability:** 0.1065
- **Assigned Risk Score:** **11 / 100**
- **Operational Risk Category:** **LOW**

**Operational Assessment:**
The model estimates a **LOW** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- None of the top evaluated features pushed upward significantly.

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `victim district Mangaluru` (attribution = -0.5321)
- `previous activity by location` (attribution = -0.3350)
- `events in previous 30 days` (attribution = -0.2575)

---

### Record Reference: `record_0002` (Case ID: `CASE003187`)
- **Location Group / District:** Vellore
- **Crime Category Group:** INVESTMENT_SCAM
- **Predicted Withdrawal Probability:** 0.2465
- **Assigned Risk Score:** **25 / 100**
- **Operational Risk Category:** **LOW**

**Operational Assessment:**
The model estimates a **LOW** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `location previous 7d events` (attribution = +0.0837)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `previous activity by location` (attribution = -0.3188)
- `events in previous 30 days` (attribution = -0.1977)
- `victim area id AREA0040` (attribution = -0.1734)

---

### Record Reference: `record_0003` (Case ID: `CASE007883`)
- **Location Group / District:** Mangaluru
- **Crime Category Group:** INVESTMENT_SCAM
- **Predicted Withdrawal Probability:** 0.0949
- **Assigned Risk Score:** **9 / 100**
- **Operational Risk Category:** **LOW**

**Operational Assessment:**
The model estimates a **LOW** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- None of the top evaluated features pushed upward significantly.

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `victim district Mangaluru` (attribution = -0.5319)
- `previous activity by location` (attribution = -0.3304)
- `events in previous 30 days` (attribution = -0.2455)

---

### Record Reference: `record_0004` (Case ID: `CASE008891`)
- **Location Group / District:** Madurai
- **Crime Category Group:** PAYMENT_FRAUD
- **Predicted Withdrawal Probability:** 0.2339
- **Assigned Risk Score:** **23 / 100**
- **Operational Risk Category:** **LOW**

**Operational Assessment:**
The model estimates a **LOW** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `event minute` (attribution = +0.0482)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `previous activity by location` (attribution = -0.2795)
- `events in previous 30 days` (attribution = -0.1727)
- `previous activity by district` (attribution = -0.1585)

---

### Record Reference: `record_0005` (Case ID: `CASE003630`)
- **Location Group / District:** Erode
- **Crime Category Group:** PAYMENT_FRAUD
- **Predicted Withdrawal Probability:** 0.4871
- **Assigned Risk Score:** **49 / 100**
- **Operational Risk Category:** **MODERATE**

**Operational Assessment:**
The model estimates a **MODERATE** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `location previous 7d events` (attribution = +0.0766)
- `amount log1p` (attribution = +0.0703)
- `rolling crime event count 7d` (attribution = +0.0639)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `previous activity by crime category` (attribution = -0.1995)
- `events in previous 30 days` (attribution = -0.1879)
- `event day` (attribution = -0.0935)

---

### Record Reference: `record_0006` (Case ID: `CASE006660`)
- **Location Group / District:** Tirupati
- **Crime Category Group:** CREDENTIAL_THEFT
- **Predicted Withdrawal Probability:** 0.4969
- **Assigned Risk Score:** **50 / 100**
- **Operational Risk Category:** **MODERATE**

**Operational Assessment:**
The model estimates a **MODERATE** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `event hour` (attribution = +0.0486)
- `events in previous 1 day` (attribution = +0.0471)
- `rolling crime event count 7d` (attribution = +0.0457)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `previous activity by district` (attribution = -0.1433)
- `event day` (attribution = -0.1404)
- `previous activity by crime category` (attribution = -0.0798)

---

### Record Reference: `record_0007` (Case ID: `CASE008519`)
- **Location Group / District:** Ballari
- **Crime Category Group:** CREDENTIAL_THEFT
- **Predicted Withdrawal Probability:** 0.4514
- **Assigned Risk Score:** **45 / 100**
- **Operational Risk Category:** **MODERATE**

**Operational Assessment:**
The model estimates a **MODERATE** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `fraud amount` (attribution = +0.1338)
- `amount log1p` (attribution = +0.1045)
- `previous activity by location` (attribution = +0.0937)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `victim district Ballari` (attribution = -0.1994)
- `previous activity by crime category` (attribution = -0.1743)
- `events in previous 30 days` (attribution = -0.1345)

---

### Record Reference: `record_0008` (Case ID: `CASE005474`)
- **Location Group / District:** Tiruchirappalli
- **Crime Category Group:** CREDENTIAL_THEFT
- **Predicted Withdrawal Probability:** 0.6111
- **Assigned Risk Score:** **61 / 100**
- **Operational Risk Category:** **HIGH**

**Operational Assessment:**
The model estimates a **HIGH** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `victim area Woraiyur` (attribution = +0.3770)
- `previous activity by location` (attribution = +0.1259)
- `victim area id AREA0018` (attribution = +0.1129)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `events in previous 30 days` (attribution = -0.2019)
- `previous activity by crime category` (attribution = -0.1917)
- `rolling event count 1h` (attribution = -0.1106)

---

### Record Reference: `record_0009` (Case ID: `CASE007772`)
- **Location Group / District:** Tiruchirappalli
- **Crime Category Group:** PAYMENT_FRAUD
- **Predicted Withdrawal Probability:** 0.6319
- **Assigned Risk Score:** **63 / 100**
- **Operational Risk Category:** **HIGH**

**Operational Assessment:**
The model estimates a **HIGH** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `victim area Woraiyur` (attribution = +0.5327)
- `victim area id AREA0018` (attribution = +0.1129)
- `rolling event count 6h` (attribution = +0.0790)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `previous activity by crime category` (attribution = -0.1785)
- `events in previous 30 days` (attribution = -0.1472)
- `event day of week` (attribution = -0.0606)

---

### Record Reference: `record_0010` (Case ID: `CASE000291`)
- **Location Group / District:** Nellore
- **Crime Category Group:** SOCIAL_ENGINEERING
- **Predicted Withdrawal Probability:** 0.5980
- **Assigned Risk Score:** **60 / 100**
- **Operational Risk Category:** **HIGH**

**Operational Assessment:**
The model estimates a **HIGH** likelihood of a qualifying future cash withdrawal based on the observed incident pattern.

**Factors that increased the model's prediction (Pushed toward future withdrawal):**
- `event day` (attribution = +0.1289)
- `previous activity by location` (attribution = +0.1200)
- `amount log1p` (attribution = +0.0777)

**Factors that reduced the model's prediction (Pushed away from future withdrawal):**
- `previous activity by crime category` (attribution = -0.1796)
- `events in previous 30 days` (attribution = -0.0791)
- `previous activity by district` (attribution = -0.0353)

---
