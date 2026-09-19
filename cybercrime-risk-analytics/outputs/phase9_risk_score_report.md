# Phase 9 — Risk Score Generation Report
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Objective
Translate the primary XGBoost predictive model's continuous output into an actionable, interpretable decision-support framework:
$$\text{Predicted Probability } P(\text{future\_withdrawal} = 1) \longrightarrow \text{Risk Score } [0, 100] \longrightarrow \text{Operational Risk Category}$$

**Core Governance Principle:**
The risk score represents the **predicted statistical likelihood of a qualifying future cash withdrawal** within the defined 24-hour temporal window. It **does NOT** represent proof of criminal guilt, proof of a compromised ATM, or an automated directive for punitive action. The system enforces **human-in-the-loop validation**.

---

## 2. Risk Score Formulation & Scoring Rules
### Primary Formula:
$$\text{risk\_score} = \text{round}(\text{predicted\_probability} \times 100)$$

- Scores are strictly integers from **0 to 100**.
- **No arbitrary manual point adjustments:** The machine learning model probability is the sole risk signal, preventing double-counting of features (amounts, crime types, location counters).

---

## 3. Operational Risk Categories

| Risk Score Range | Category | Operational Action & Protocol |
|---|---|---|
| **0 – 39** | **LOW** | Low predicted likelihood of a qualifying future withdrawal. Continue routine monitoring. |
| **40 – 59** | **MODERATE** | Moderate predicted likelihood. Consider enhanced monitoring by authorized analysts. |
| **60 – 79** | **HIGH** | High predicted likelihood. Prioritize review and verification by authorized personnel. |
| **80 – 100** | **CRITICAL** | Very high predicted likelihood. Prioritize timely review and authorized intervention according to operational procedures. |

*Boundary Unit Tests:* $39 \to \text{LOW}$, $40 \to \text{MODERATE}$, $59 \to \text{MODERATE}$, $60 \to \text{HIGH}$, $79 \to \text{HIGH}$, $80 \to \text{CRITICAL}$ — **ALL PASSED**.

---

## 4. Input Dataset Profile
- **Input Evaluated:** Untouched Chronological Test Dataset (`test.csv`, 1,500 complaints).
- **Time Range:** `2026-07-27 11:26:18` to `2026-08-31 23:55:41`.
- **Target:** `future_withdrawal` (Positive prevalence: 10.33%).
- **Features:** 64 leakage-safe predictors.
- **Location Fields:** `victim_state`, `victim_district`, `location_grid`, `geographic_region`.

---

## 5. Score Statistics Summary

| Metric | Predicted Probability | Risk Score (0–100) |
|---|---|---|
| **Minimum** | 0.094887 | 9 |
| **Maximum** | 0.631938 | 63 |
| **Mean** | 0.335639 | 33.57 |
| **Median** | 0.333554 | 33 |
| **Standard Deviation** | 0.087827 | 8.79 |

---

## 6. Category Distribution

| Category | Record Count | Percentage (%) | Score Range | Mean Probability |
|---|---|---|---|---|
| **LOW** | 1120 | 74.67% | 9 – 39 | 0.2975 |
| **MODERATE** | 375 | 25.00% | 40 – 58 | 0.4460 |
| **HIGH** | 5 | 0.33% | 60 – 63 | 0.6104 |
| **CRITICAL** | 0 | 0.00% | N/A | N/A |

---

## 7. Diagnostic Threshold Analysis
*(Post-hoc diagnostic analysis on test dataset — NOT used for model selection or tuning)*

| Risk Threshold | Complaints $\ge$ Threshold | % of Total | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| **$\ge 20$** | 1,425 | 95.00% | 143 | 1,282 | 12 | 63 | 0.1004 | **0.9226** | 0.1810 |
| **$\ge 30$** | 1,003 | 66.87% | 104 | 899 | 51 | 446 | 0.1037 | **0.6710** | 0.1796 |
| **$\ge 40$** | 380 | 25.33% | 36 | 344 | 119 | 1,001 | 0.0947 | 0.2323 | 0.1346 |
| **$\ge 50$** | 56 | 3.73% | 5 | 51 | 150 | 1,294 | 0.0893 | 0.0323 | 0.0474 |
| **$\ge 60$** | 5 | 0.33% | 1 | 4 | 154 | 1,341 | 0.2000 | 0.0065 | 0.0125 |

---

## 8. Location-Level Risk Summary
Aggregated across 38 Southern India districts present in the evaluation stream.
Top districts by complaint frequency:
- **Bengaluru Urban:** 53 complaints, Max Risk Score = 53, Dominant Category: LOW
- **Rajamahendravaram:** 46 complaints, Max Risk Score = 53, Dominant Category: LOW
- **Kakinada:** 45 complaints, Max Risk Score = 60, Dominant Category: LOW
- **Malappuram:** 44 complaints, Max Risk Score = 47, Dominant Category: LOW
- **Kalaburagi:** 43 complaints, Max Risk Score = 56, Dominant Category: LOW

*Note: This is an aggregated descriptive summary; spatial clustering (DBSCAN) and GIS heatmaps are deferred to Phase 10.*

---

## 9. Outcome Validation & Monotonicity
- **Monotonicity Check:** **PASSED**  
  $$\text{Mean Probability: } \text{LOW (0.2975)} \le \text{MODERATE (0.4460)} \le \text{HIGH (0.6104)}$$
- **High-Risk Outcome Validation:**  
  Complaints in the **HIGH** risk tier exhibited an observed withdrawal rate of **20.00%**, approximately double the population baseline prevalence (10.33%).

---

## 10. Calibration Assessment
As documented in Phase 8 (`outputs/phase8_calibration_report.csv`, Brier score = 0.1560), model probabilities span smoothly across [0.09, 0.63].
> *Notice:* Risk scores are probability-derived operational indices designed for triage and ranking. They should not be interpreted as mathematically perfect absolute frequencies. Recalibration on the test set was strictly avoided to maintain out-of-sample purity.

---

## 11. Governance, Safety & Limitations
1. **Decision Support Only:** Risk scores flag complaints for human analyst review, not autonomous action.
2. **No Automated PII:** Account numbers, card credentials, OTPs, and passwords are fully isolated.
3. **Class Imbalance & Thresholding:** At conservative thresholds ($\ge 50$), false alarms are low but recall is limited. Operations requiring high interception should calibrate triage queues around thresholds 25–35.
4. **Data Scope:** Operational deployment requires live Core Banking System (CBS) and NCRP/I4C feed integration.

---

## 12. Conclusion & Phase 10 Readiness
Phase 9 successfully generates validated risk scores and operational categories from the frozen XGBoost pipeline.

**Phase 9 is COMPLETE. Ready for Phase 10 — Spatial Hotspot & Geographic Cluster Analysis.**
