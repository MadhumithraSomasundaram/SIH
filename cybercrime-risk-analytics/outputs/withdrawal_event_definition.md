# Withdrawal Event Definition Document
**Problem Statement ID 26184: Predictive Analytics Framework for Cybercrime Complaints**

---

## 1. Source Columns Used
- **Dataset:** `data/processed/cleaned_withdrawals.csv` (80,000 physical ATM cashout records)
- **Primary Linking Key:** `case_id` (links specific cybercrime complaint investigation to cashout transactions)
- **Temporal Marker:** `timestamp` (ISO-8601 exact timestamp of ATM cash dispensing)
- **Spatial Target Coordinates:** `latitude`, `longitude`, `district`, `area_id`, `atm_id`
- **Dispensed Magnitude:** `amount` (Cash amount dispensed in INR)

## 2. Values Interpreted as Withdrawal
- Every row in `cleaned_withdrawals.csv` represents a **verified physical cash withdrawal** executed at an automated teller machine (ATM).
- Of the 80,000 total withdrawal events:
  - **28,614 records (35.8%)** are verified ground-truth withdrawals directly linked to cybercrime complaint dockets via `case_id`.
  - **51,386 records (64.2%)** represent normal background banking cash withdrawals (unlinked to fraud).

## 3. Values Excluded
- Intermediate digital fund movements (`UPI`, `NEFT`, `IMPS`, `BANK_TRANSFER` in `Transactions.csv`) are excluded from target definition because Problem Statement 26184 specifically targets physical **cash withdrawal locations**.
- Post-investigation labels (`is_suspicious`) and simulation artifacts (`scenario`) are strictly excluded to maintain real-world operational realism.

## 4. Analytical Reasoning
- Cybercrime syndicates operate by rapidly layering stolen funds across digital accounts and finally liquidating them into untraceable physical currency at ATMs.
- The physical cashout event at the ATM represents the primary intervention opportunity for law enforcement to deploy proactive measures (e.g. CCTV monitoring, patrol alerts, automated cash-lockdown triggers).

## 5. Known Limitations
- Background withdrawals without `case_id` represent legitimate civilian activity and are not counted as fraud targets.
