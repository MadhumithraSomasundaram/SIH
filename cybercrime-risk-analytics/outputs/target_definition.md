# Target Definition Document — Problem Statement 26184
## Predictive Analytics Framework for Cybercrime Complaints

---

## 1. Target Name
**`future_withdrawal`**

## 2. Formal Operational Definition
$$\text{future\_withdrawal} = \begin{cases} 1 & \text{if a qualifying ATM cashout occurs in } (T_0, T_0 + 24\text{h}] \text{ at/near the relevant location} \\ 0 & \text{otherwise} \end{cases}$$

- **Meaning of `future_withdrawal = 1`:**  
  A cash withdrawal directly associated with the cybercrime incident occurs within the **next 24 hours** at an automated teller machine (ATM) located **within the same administrative district or within a 10 km spatial proximity radius** of the victim's reported locality.
- **Meaning of `future_withdrawal = 0`:**  
  No qualifying local cash withdrawal occurs during that 24-hour prediction window (e.g. no cashout occurred, the cashout occurred after > 24 hours, or the cash was extracted in a distant interstate mule network).

## 3. Location Matching Methodology
- **Primary Spatial Representation:** Geographic coordinates (`latitude`, `longitude`) combined with administrative jurisdiction (`victim_district`).
- **Distance Metric:** Haversine Great-Circle Distance on the Earth's sphere ($R = 6,371$ km).
- **Spatial Tolerance Threshold:** **10.0 kilometers** (or exact district match).
- **Reason for Selection:**  
  Empirical spatial analysis shows that 100% of local withdrawals in the same district occur within 5 to 10 km of the area centroid. Cashouts occurring beyond 25 km represent distant interstate mule cashouts (mean distance 383 km).

## 4. Time Window & Chronology Rules
- **Horizon Duration:** Strictly **24 hours** from complaint filing ($T_0 < T_w \le T_0 + 24.0\text{ hours}$).
- **Same-Timestamp Handling:** Events with $T_w \le T_0$ are strictly excluded to avoid simultaneous or retrospective bias.
- **Current Row Exclusion:** The complaint event itself is never treated as its own outcome.

## 5. Incomplete Observation Window Handling
- Field **`target_observation_complete`**:
  - `1`: The future 24-hour observation horizon is completely covered by the withdrawal registry.
  - `0`: Incomplete observation horizon.
- In our dataset, the withdrawal registry extends until **2026-09-02 22:18:33**, which is **46.38 hours beyond the latest complaint** (2026-08-31 23:55:41). Therefore, **100.0% of records (10,000/10,000)** have complete 24-hour future observability.

## 6. Target Distribution
- **Total Records:** 10,000
- **Positive Count (`future_withdrawal = 1`):** 1,027 (10.27%)
- **Negative Count (`future_withdrawal = 0`):** 8,973 (89.73%)
- **Class Ratio:** ~1:8.7 (Moderately imbalanced; realistic for proactive law enforcement intervention).

## 7. Known Limitations
- The target isolates local ATM cashouts; forecasting the specific interstate destination of distant mule cashouts (65.8% of cases) represents a separate multi-class destination routing problem.
