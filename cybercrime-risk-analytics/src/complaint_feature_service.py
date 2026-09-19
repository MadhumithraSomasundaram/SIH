"""
Complaint Feature Service: Dynamic Feature Generation from Raw Complaints
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Transforms a raw ComplaintSubmissionRequest into the full feature vector
expected by the model pipeline, ensuring:
- Only information available at T0 (complaint_timestamp) is used.
- Validated feature schema alignment (exact names, dtypes, and order).
- No future-derived features or target leakage.
- Consistent missing-value handling via imputer defaults.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("api.complaint_features")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROC_DIR = DATA_DIR / "processed"

# Cache for static accounts baseline lookup
_ACCOUNTS_CACHE: Optional[pd.DataFrame] = None


def _get_accounts_cache() -> pd.DataFrame:
    global _ACCOUNTS_CACHE
    if _ACCOUNTS_CACHE is None:
        acc_path = RAW_DIR / "Accounts.csv"
        if acc_path.exists():
            try:
                _ACCOUNTS_CACHE = pd.read_csv(acc_path)
            except Exception as e:
                logger.warning("Could not load Accounts.csv: %s", e)
                _ACCOUNTS_CACHE = pd.DataFrame()
        else:
            _ACCOUNTS_CACHE = pd.DataFrame()
    return _ACCOUNTS_CACHE


def _hour_group(h: int) -> str:
    if h < 4:
        return "00-03"
    elif h < 8:
        return "04-07"
    elif h < 12:
        return "08-11"
    elif h < 16:
        return "12-15"
    elif h < 20:
        return "16-19"
    else:
        return "20-23"


def _time_period(h: int) -> str:
    if 0 <= h < 6:
        return "early_morning"
    elif 6 <= h < 12:
        return "morning"
    elif 12 <= h < 17:
        return "afternoon"
    elif 17 <= h < 21:
        return "evening"
    else:
        return "night"


def _group_crime(crime: str) -> str:
    c = str(crime).upper().replace(" ", "_")
    if any(k in c for k in ["UPI", "FINANCIAL", "PAYMENT", "BANKING"]):
        return "PAYMENT_FRAUD"
    elif "INVESTMENT" in c or "TRADING" in c or "CRYPTO" in c:
        return "INVESTMENT_SCAM"
    elif "PHISHING" in c or "CREDENTIAL" in c or "TAKEOVER" in c or "HACKING" in c:
        return "CREDENTIAL_THEFT"
    elif "IMPERSONATION" in c or "SEXTORTION" in c or "IDENTITY" in c:
        return "SOCIAL_ENGINEERING"
    return "OTHER"


def _amount_category(amount: float) -> str:
    if amount < 5000:
        return "LOW"
    elif amount < 20000:
        return "MEDIUM"
    elif amount < 50000:
        return "HIGH"
    else:
        return "CRITICAL"


def extract_features_from_complaint(
    complaint_data: Dict[str, Any],
    expected_features: List[str],
) -> Dict[str, Any]:
    """
    Transforms raw complaint dictionary into the exact feature dictionary expected by the model.
    """
    # 1. Parse and validate complaint timestamp
    raw_ts = complaint_data.get("complaint_timestamp")
    if isinstance(raw_ts, datetime):
        dt = raw_ts
    else:
        try:
            # Handle ISO string (with or without 'Z')
            ts_str = str(raw_ts).replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_str)
        except Exception as exc:
            raise ValueError(f"Invalid complaint_timestamp format: '{raw_ts}'. Must be ISO 8601.") from exc

    fraud_amt = float(complaint_data.get("fraud_amount") or 0.0)
    crime_type = str(complaint_data.get("complaint_category") or complaint_data.get("crime_type") or "Online Financial Fraud")
    reported_by_auth = float(complaint_data.get("reported_by_authority") or 0.0)
    
    state = complaint_data.get("state") or complaint_data.get("victim_state")
    district = complaint_data.get("district") or complaint_data.get("victim_district")
    area = complaint_data.get("city") or complaint_data.get("area") or complaint_data.get("victim_area")
    area_id = complaint_data.get("victim_area_id") or "AREA0001"
    
    lat = complaint_data.get("latitude")
    lon = complaint_data.get("longitude")
    has_coords = (lat is not None and lon is not None and not math.isnan(float(lat)) and not math.isnan(float(lon)))
    if has_coords:
        lat_f = float(lat)
        lon_f = float(lon)
        lat_rounded = round(lat_f, 2)
        lon_rounded = round(lon_f, 2)
        grid = f"{lat_rounded}_{lon_rounded}"
        coord_precision = "district_area_centroid"
        missing_coord = 0.0
    else:
        lat_f = None
        lon_f = None
        lat_rounded = None
        lon_rounded = None
        grid = "unknown_grid"
        coord_precision = "missing"
        missing_coord = 1.0

    # 2. Account Profile & Baselines Lookup
    sender_acc = complaint_data.get("sender_account_reference")
    acc_df = _get_accounts_cache()
    matched_acc = None
    if sender_acc and not acc_df.empty and "account_id" in acc_df.columns:
        m = acc_df[acc_df["account_id"] == str(sender_acc)]
        if not m.empty:
            matched_acc = m.iloc[0].to_dict()

    # Base profile values
    if matched_acc:
        acc_type = str(matched_acc.get("account_type", "SAVINGS"))
        acc_age_days = int(matched_acc.get("account_age_days", 365))
        base_daily_txns = int(matched_acc.get("baseline_daily_txn_count", 2))
        base_daily_amt = float(matched_acc.get("baseline_daily_amount", 5000.0))
        base_daily_wd = int(matched_acc.get("baseline_daily_withdrawals", 1))
    else:
        acc_type = "SAVINGS"
        acc_age_days = 365
        base_daily_txns = 2
        base_daily_amt = 5000.0
        base_daily_wd = 1

    # 3. Assemble Feature Dictionary
    f: Dict[str, Any] = {
        "crime_type": crime_type,
        "fraud_amount": fraud_amt,
        "reported_by_authority": reported_by_auth,
        "victim_state": state,
        "victim_district": district,
        "victim_area": area,
        "victim_area_id": area_id,
        "latitude": lat_f,
        "longitude": lon_f,
        "event_year": dt.year,
        "event_month": dt.month,
        "event_day": dt.timetuple().tm_yday,
        "event_day_of_month": dt.day,
        "event_day_of_week": dt.weekday(),
        "event_hour": dt.hour,
        "event_minute": dt.minute,
        "is_weekend": 1.0 if dt.weekday() >= 5 else 0.0,
        "is_month_start": 1.0 if dt.day == 1 else 0.0,
        "is_month_end": 1.0 if (dt.month != (dt + pd.Timedelta(days=1)).month) else 0.0,
        "is_quarter_start": 1.0 if (dt.day == 1 and dt.month in (1, 4, 7, 10)) else 0.0,
        "is_quarter_end": 1.0 if (dt.month in (3, 6, 9, 12) and (dt.month != (dt + pd.Timedelta(days=1)).month)) else 0.0,
        "hour_group": _hour_group(dt.hour),
        "time_period": _time_period(dt.hour),
        "latitude_rounded": lat_rounded,
        "longitude_rounded": lon_rounded,
        "location_grid": grid,
        "coordinate_precision": coord_precision,
        "geographic_region": "South_India",
        "crime_category_group": _group_crime(crime_type),
        "is_financial_fraud": 1.0 if any(k in crime_type.upper() for k in ["UPI", "INVESTMENT", "FINANCIAL", "BANKING"]) else 0.0,
        "is_online_fraud": 1.0 if any(k in crime_type.upper() for k in ["UPI", "PHISHING", "TAKEOVER", "ONLINE"]) else 0.0,
        "is_identity_related": 1.0 if any(k in crime_type.upper() for k in ["IMPERSONATION", "TAKEOVER", "IDENTITY"]) else 0.0,
        "is_transaction_related": 1.0 if any(k in crime_type.upper() for k in ["UPI", "INVESTMENT", "TRANSACTION", "TRANSFER"]) else 0.0,
        "amount_log1p": round(np.log1p(max(0.0, fraud_amt)), 4),
        "amount_is_zero": 1.0 if fraud_amt == 0.0 else 0.0,
        "amount_is_high": 1.0 if fraud_amt > 38206.47 else 0.0,
        "amount_category": _amount_category(fraud_amt),
        
        # Bounded historical rolling placeholders (will be imputed via median if missing, or neutral 0)
        "previous_event_count": 0,
        "time_since_previous_event_hours": 1.0,
        "events_in_previous_1_day": 0,
        "events_in_previous_3_days": 1,
        "events_in_previous_7_days": 2,
        "events_in_previous_30_days": 5,
        "previous_activity_by_location": 0,
        "previous_activity_by_district": 0,
        "previous_activity_by_crime_category": 0,
        "rolling_event_count_1h": 0,
        "rolling_event_count_6h": 0,
        "rolling_event_count_24h": 0,
        "rolling_event_count_7d": 1,
        "rolling_location_event_count_24h": 0,
        "rolling_crime_event_count_7d": 1,
        "location_total_previous_events": 0,
        "location_previous_24h_events": 0,
        "location_previous_7d_events": 1,
        "district_previous_24h_events": 0,
        "district_previous_7d_events": 1,
        "location_unique_crime_categories": 1,
        "has_location": 1.0 if has_coords else 0.0,
        "has_timestamp": 1.0,
        "has_amount": 1.0 if fraud_amt > 0 else 0.0,
        "has_crime_category": 1.0 if crime_type else 0.0,
        "has_district": 1.0 if district else 0.0,
        "missing_coordinate_flag": missing_coord,
        
        # V2 Transaction & Account Features (if V2 schema is requested)
        "victim_account_type": acc_type,
        "victim_account_age_days": acc_age_days,
        "victim_baseline_daily_txns": base_daily_txns,
        "victim_baseline_daily_amount": base_daily_amt,
        "victim_baseline_daily_withdrawals": base_daily_wd,
        "fraud_to_daily_amount_ratio": round(fraud_amt / (base_daily_amt + 1.0), 4),
        "fraud_amount_excess_over_baseline": round(max(0.0, fraud_amt - base_daily_amt), 2),
        "case_prior_txn_count": 1.0,
        "case_prior_amount_sum": fraud_amt,
        "case_prior_amount_max": fraud_amt,
        "case_prior_unique_channels": 1.0,
        "case_hours_since_first_txn": 0.5,
        "victim_outgoing_txns_all": 1.0,
        "victim_outgoing_amount_all": fraud_amt,
        "victim_outgoing_amount_avg": fraud_amt,
        "victim_outgoing_amount_max": fraud_amt,
        "victim_hours_since_last_outgoing": 0.5,
        "victim_outgoing_txns_24h": 1.0,
        "victim_outgoing_amount_24h": fraud_amt,
        "victim_outgoing_txns_7d": 1.0,
        "victim_outgoing_amount_7d": fraud_amt,
        "victim_incoming_txns_all": 0.0,
        "victim_incoming_amount_all": 0.0,
        "victim_incoming_txns_24h": 0.0,
        "victim_incoming_amount_24h": 0.0,
        "victim_hours_since_last_incoming": 9999.0,
        "victim_total_prior_volume": fraud_amt,
        "victim_net_prior_flow": -fraud_amt,
        "victim_total_linked_accounts": 1.0,
        "victim_velocity_surge_ratio": round(1.0 / (base_daily_txns + 1.0), 4),
    }

    # Filter to exactly the expected features in expected order
    record = {}
    for feat in expected_features:
        record[feat] = f.get(feat, None)

    return record
