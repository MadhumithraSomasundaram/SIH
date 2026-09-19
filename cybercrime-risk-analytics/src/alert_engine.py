"""
Phase 16 — Alert Trigger Engine
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Generates actionable analytical alerts when model-derived risk or spatial
hotspot conditions meet documented thresholds.

STRICT BOUNDARIES:
- Analytical signals for authorized human review only
- No model retraining
- No automated punitive or financial actions
- No sensitive PII or credentials exposed
- No live banking or NCRP connections
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Path bootstrap
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from notifications.dispatcher import NotificationDispatcher
from database.connection import get_db, SessionLocal
from database.crud import (
    create_alert as db_create_alert,
    get_alerts as db_get_alerts,
    get_alert_statistics as db_get_alert_statistics,
    _LOCAL_ALERTS_CACHE,
)
from database.schemas import AlertCreate

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [alert_engine] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("alert_engine")

CONFIG_PATH = BASE_DIR / "config" / "alert_config.json"
OUTPUTS_DIR = BASE_DIR / "outputs"


# ==============================================================================
# 1. CONFIGURATION & DATA LOADERS
# ==============================================================================

def load_configuration(config_file: Optional[Path] = None) -> Dict[str, Any]:
    """Loads alert thresholds, cooldowns, and deduplication settings."""
    cfg_path = config_file or CONFIG_PATH
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("Could not parse %s: %s. Using safe defaults.", cfg_path, exc)

    return {
        "risk_thresholds": {"low": 0, "moderate": 40, "high": 60, "critical": 80},
        "hotspot_thresholds": {
            "critical_risk_score": 80,
            "elevated_risk_score": 60,
            "min_event_count_for_alert": 10,
            "withdrawal_event_threshold": 15,
        },
        "surge_detection": {
            "enabled": False,
            "unavailability_reason": "Activity surge alert unavailable because the current dataset does not provide sufficient temporal history.",
        },
        "cooldown_minutes": {"critical": 30, "high": 60, "moderate": 120, "low": 240},
        "rate_limiting": {"max_alerts_per_generation": 100},
        "enabled_alert_types": [
            "CRITICAL_RISK_LOCATION",
            "HIGH_RISK_LOCATION",
            "HOTSPOT_CRITICAL_RISK",
            "HOTSPOT_ELEVATED_RISK",
            "WITHDRAWAL_HOTSPOT",
        ],
        "human_review_required_severities": ["HIGH", "CRITICAL"],
    }


def load_risk_data() -> pd.DataFrame:
    """Loads validated prediction and risk score outputs from Phase 9 / Phase 11."""
    p9_file = OUTPUTS_DIR / "phase9_risk_scores.csv"
    if p9_file.exists():
        try:
            return pd.read_csv(p9_file)
        except Exception as exc:
            logger.warning("Failed to load Phase 9 risk scores: %s", exc)
    return pd.DataFrame()


def load_hotspot_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Loads Phase 14 DBSCAN analytical hotspot summaries:
    - hotspot_summary: cluster level density, counts, centroids
    - hotspot_risk: risk aggregation per cluster
    - withdrawal_hotspots: validated withdrawal counts
    """
    hs_file = OUTPUTS_DIR / "phase14_hotspot_summary.csv"
    hr_file = OUTPUTS_DIR / "phase14_hotspot_risk_summary.csv"
    wh_file = OUTPUTS_DIR / "phase14_withdrawal_hotspots.csv"

    df_hs = pd.read_csv(hs_file) if hs_file.exists() else pd.DataFrame()
    df_hr = pd.read_csv(hr_file) if hr_file.exists() else pd.DataFrame()
    df_wh = pd.read_csv(wh_file) if wh_file.exists() else pd.DataFrame()

    return df_hs, df_hr, df_wh


# ==============================================================================
# 2. VALIDATION & SEVERITY ASSIGNMENT
# ==============================================================================

def assign_alert_severity(risk_score: Any, thresholds: Optional[Dict[str, int]] = None) -> str:
    """
    Calibrates risk score [0, 100] to operational severity tier:
      0–39   : LOW
      40–59  : MODERATE
      60–79  : HIGH
      80–100 : CRITICAL
    """
    if thresholds is None:
        thresholds = {"critical": 80, "high": 60, "moderate": 40}

    if risk_score is None:
        return "LOW"

    try:
        score_val = float(risk_score)
        if math.isnan(score_val) or math.isinf(score_val):
            return "LOW"
    except (ValueError, TypeError):
        return "LOW"

    score = int(round(score_val))
    if score >= thresholds.get("critical", 80):
        return "CRITICAL"
    elif score >= thresholds.get("high", 60):
        return "HIGH"
    elif score >= thresholds.get("moderate", 40):
        return "MODERATE"
    else:
        return "LOW"


def validate_alert_inputs(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validates that candidate alert input contains required fields and valid ranges."""
    risk_score = record.get("risk_score")
    if risk_score is None:
        return False, "Missing risk_score"
    try:
        score_val = float(risk_score)
        if math.isnan(score_val) or math.isinf(score_val):
            return False, f"Risk score is NaN or Infinite: {risk_score}"
        if not (0.0 <= score_val <= 100.0):
            return False, f"Risk score {score_val} out of bounds [0, 100]"
    except (ValueError, TypeError):
        return False, f"Invalid risk_score type: {risk_score}"

    lat = record.get("latitude")
    lon = record.get("longitude")
    if lat is not None and lon is not None:
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            if math.isnan(lat_f) or math.isinf(lat_f) or math.isnan(lon_f) or math.isinf(lon_f):
                return False, "Coordinates contain NaN or Infinite values"
            if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
                return False, f"Coordinates out of bounds: lat={lat_f}, lon={lon_f}"
        except (ValueError, TypeError):
            return False, "Non-numeric coordinates"

    return True, None


# ==============================================================================
# 3. RULE EVALUATION FUNCTIONS
# ==============================================================================

def evaluate_risk_alert(
    row: Dict[str, Any],
    config: Dict[str, Any],
    alert_counter: int,
) -> Optional[Dict[str, Any]]:
    """
    Evaluates risk score for single complaint/prediction against thresholds.
    Triggers CRITICAL_RISK_LOCATION or HIGH_RISK_LOCATION.
    """
    score = int(row.get("risk_score", 0))
    thresholds = config.get("risk_thresholds", {"critical": 80, "high": 60, "moderate": 40})
    severity = assign_alert_severity(score, thresholds)

    if severity not in ("CRITICAL", "HIGH"):
        return None

    alert_type = "CRITICAL_RISK_LOCATION" if severity == "CRITICAL" else "HIGH_RISK_LOCATION"
    if alert_type not in config.get("enabled_alert_types", []):
        return None

    district = row.get("victim_district", "Unknown Area")
    category = row.get("crime_category_group") or row.get("crime_type") or "Cyber Fraud"
    prob = float(row.get("predicted_probability", score / 100.0))

    # Parse coordinates if present (e.g. location_grid '12.91_74.86')
    lat = row.get("latitude")
    lon = row.get("longitude")
    if (lat is None or lon is None) and "location_grid" in row and isinstance(row["location_grid"], str):
        parts = row["location_grid"].split("_")
        if len(parts) == 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
            except ValueError:
                pass

    alert_id = f"ALT-{alert_counter:06d}"
    return {
        "alert_id": alert_id,
        "alert_type": alert_type,
        "severity": severity,
        "status": "NEW",
        "prediction_reference": row.get("case_id") or row.get("prediction_reference"),
        "hotspot_id": None,
        "risk_score": score,
        "predicted_probability": round(prob, 4),
        "event_count": 1,
        "dominant_category": str(category),
        "time_window_start": row.get("complaint_timestamp"),
        "time_window_end": row.get("complaint_timestamp"),
        "operational_message": (
            f"{severity} predictive withdrawal probability ({score}%) detected in {district}. "
            f"Prioritize authorized human analytical review."
        ),
        "human_review_required": True,
        "model_version": row.get("model_version", "v1.0.0-xgb-calibrated"),
        "latitude": lat,
        "longitude": lon,
    }


def evaluate_hotspot_alert(
    hs_row: Dict[str, Any],
    hr_row: Optional[Dict[str, Any]],
    config: Dict[str, Any],
    alert_counter: int,
) -> Optional[Dict[str, Any]]:
    """
    Evaluates DBSCAN spatial cluster for elevated or critical risk.
    Triggers HOTSPOT_CRITICAL_RISK or HOTSPOT_ELEVATED_RISK.
    """
    raw_avg = hs_row.get("average_risk_score")
    avg_score = 0.0 if (pd.isna(raw_avg) or raw_avg is None) else float(raw_avg)
    raw_crit = hs_row.get("critical_risk_count")
    crit_count = 0 if (pd.isna(raw_crit) or raw_crit is None) else int(raw_crit)
    raw_high = hs_row.get("high_risk_count")
    high_count = 0 if (pd.isna(raw_high) or raw_high is None) else int(raw_high)
    cluster_id = str(hs_row.get("cluster_id"))
    raw_event_cnt = hs_row.get("event_count")
    event_count = 0 if (pd.isna(raw_event_cnt) or raw_event_cnt is None) else int(raw_event_cnt)

    if hr_row:
        hr_crit = hr_row.get("critical_risk_count")
        if not pd.isna(hr_crit) and hr_crit is not None:
            crit_count = max(crit_count, int(hr_crit))
        hr_high = hr_row.get("high_risk_count")
        if not pd.isna(hr_high) and hr_high is not None:
            high_count = max(high_count, int(hr_high))
        hr_avg = hr_row.get("average_risk_score")
        if not pd.isna(hr_avg) and hr_avg is not None:
            avg_score = max(avg_score, float(hr_avg))

    min_events = config.get("hotspot_thresholds", {}).get("min_event_count_for_alert", 10)
    if event_count < min_events:
        return None

    # Determine severity
    if avg_score >= 80 or crit_count > 0:
        severity = "CRITICAL"
        alert_type = "HOTSPOT_CRITICAL_RISK"
    elif avg_score >= 60 or high_count > 0:
        severity = "HIGH"
        alert_type = "HOTSPOT_ELEVATED_RISK"
    else:
        return None

    if alert_type not in config.get("enabled_alert_types", []):
        return None

    alert_id = f"ALT-{alert_counter:06d}"
    return {
        "alert_id": alert_id,
        "alert_type": alert_type,
        "severity": severity,
        "status": "NEW",
        "prediction_reference": None,
        "hotspot_id": f"HS-{cluster_id}",
        "risk_score": int(round(avg_score)),
        "predicted_probability": round(avg_score / 100.0, 4),
        "event_count": event_count,
        "dominant_category": "Clustered Incidents",
        "time_window_start": hs_row.get("time_range_start"),
        "time_window_end": hs_row.get("time_range_end"),
        "operational_message": (
            f"Analytical spatial cluster HS-{cluster_id} exhibits {severity.lower()} aggregate "
            f"predictive withdrawal risk (avg score {avg_score:.1f}, {event_count} events). "
            f"Authorized human review required."
        ),
        "human_review_required": True,
        "model_version": "v1.0.0-xgb-dbscan",
        "latitude": hs_row.get("latitude_centroid"),
        "longitude": hs_row.get("longitude_centroid"),
    }


def evaluate_withdrawal_alert(
    wh_row: Dict[str, Any],
    config: Dict[str, Any],
    alert_counter: int,
) -> Optional[Dict[str, Any]]:
    """
    Evaluates cluster for significant cash withdrawal volume.
    Triggers WITHDRAWAL_HOTSPOT.
    """
    raw_w = wh_row.get("withdrawal_event_count", 0)
    w_count = 0 if (pd.isna(raw_w) or raw_w is None) else int(raw_w)
    threshold = config.get("hotspot_thresholds", {}).get("withdrawal_event_threshold", 15)
    if w_count < threshold:
        return None

    if "WITHDRAWAL_HOTSPOT" not in config.get("enabled_alert_types", []):
        return None

    cluster_id = str(wh_row.get("cluster_id"))
    raw_score = wh_row.get("average_risk_score")
    if pd.isna(raw_score) or raw_score is None:
        avg_score = 65.0
    else:
        try:
            avg_score = float(raw_score)
            if pd.isna(avg_score):
                avg_score = 65.0
        except (ValueError, TypeError):
            avg_score = 65.0

    severity = "HIGH" if avg_score < 80 else "CRITICAL"

    alert_id = f"ALT-{alert_counter:06d}"
    return {
        "alert_id": alert_id,
        "alert_type": "WITHDRAWAL_HOTSPOT",
        "severity": severity,
        "status": "NEW",
        "prediction_reference": None,
        "hotspot_id": f"HS-{cluster_id}",
        "risk_score": int(round(avg_score)),
        "predicted_probability": round(avg_score / 100.0, 4),
        "event_count": w_count,
        "dominant_category": "Historical Cashout Pattern",
        "time_window_start": wh_row.get("time_range_start"),
        "time_window_end": wh_row.get("time_range_end"),
        "operational_message": (
            f"Analytical cluster HS-{cluster_id} contains {w_count} correlated cashout "
            f"withdrawal events. Authorized review recommended for preventive intelligence."
        ),
        "human_review_required": True,
        "model_version": "v1.0.0-xgb-dbscan",
        "latitude": wh_row.get("centroid_latitude"),
        "longitude": wh_row.get("centroid_longitude"),
    }


def evaluate_activity_surge(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Surge detection evaluation.
    Reports unavailability if dataset lacks longitudinal temporal baseline.
    """
    surge_cfg = config.get("surge_detection", {})
    if not surge_cfg.get("enabled", False):
        return {
            "status": "UNAVAILABLE",
            "available": False,
            "message": surge_cfg.get(
                "unavailability_reason",
                "Activity surge alert unavailable because the current dataset does not provide sufficient temporal history."
            ),
        }
    return {"status": "ACTIVE", "available": True, "message": "Surge detection operational."}


# ==============================================================================
# 4. DEDUPLICATION & COOLDOWN
# ==============================================================================

SEVERITY_WEIGHTS: Dict[str, int] = {
    "LOW": 1,
    "MODERATE": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


def _parse_alert_datetime(dt_val: Any) -> datetime:
    """Parses various datetime representations into a timezone-aware UTC datetime."""
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc)
        return dt_val.astimezone(timezone.utc)
    if isinstance(dt_val, str):
        try:
            cleaned = dt_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def make_dedup_key(alert: Dict[str, Any]) -> str:
    """Generates a collision-safe deduplication key using non-sensitive attributes."""
    atype = str(alert.get("alert_type"))
    loc = str(alert.get("hotspot_id") or alert.get("prediction_reference") or "global")
    sev = str(alert.get("severity", "LOW")).upper()
    return f"{atype}:{loc}:{sev}"


def deduplicate_alerts(
    candidate_alerts: List[Dict[str, Any]],
    existing_alerts: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Filters out duplicate alerts within active cooldown periods while allowing
    severity escalations (e.g. HIGH -> CRITICAL).
    Returns: (unique_alerts, duplicates_skipped, cooldown_skipped)
    """
    cooldowns = config.get("cooldown_minutes", {"critical": 30, "high": 60, "moderate": 120, "low": 240})
    now = datetime.now(timezone.utc)

    existing_exact_timestamps: Dict[str, datetime] = {}
    existing_entities: Dict[str, Tuple[datetime, int]] = {}

    for ex in existing_alerts:
        k = make_dedup_key(ex)
        ex_time = _parse_alert_datetime(ex.get("created_at"))
        ex_sev = str(ex.get("severity", "LOW")).upper()
        ex_rank = SEVERITY_WEIGHTS.get(ex_sev, 1)

        existing_exact_timestamps[k] = ex_time

        entity_k = f"{ex.get('alert_type')}:{ex.get('hotspot_id') or ex.get('prediction_reference') or 'global'}"
        if entity_k not in existing_entities or ex_time > existing_entities[entity_k][0]:
            existing_entities[entity_k] = (ex_time, ex_rank)

    unique_alerts: List[Dict[str, Any]] = []
    seen_in_batch = set()
    duplicates_skipped = 0
    cooldown_skipped = 0

    for cand in candidate_alerts:
        exact_k = make_dedup_key(cand)
        cand_sev = str(cand.get("severity", "LOW")).upper()
        cand_rank = SEVERITY_WEIGHTS.get(cand_sev, 1)
        cd_mins = cooldowns.get(cand_sev.lower(), 60)
        cand_time = _parse_alert_datetime(cand.get("created_at"))

        # 1. Intra-batch duplicate check
        if exact_k in seen_in_batch:
            duplicates_skipped += 1
            continue

        # 2. Cooldown check against entity history with escalation support
        entity_k = f"{cand.get('alert_type')}:{cand.get('hotspot_id') or cand.get('prediction_reference') or 'global'}"
        is_cooldown_suppressed = False

        if entity_k in existing_entities:
            prev_time, prev_rank = existing_entities[entity_k]
            delta_mins = (cand_time - prev_time).total_seconds() / 60.0

            # If severity escalated, bypass cooldown
            if cand_rank > prev_rank:
                is_cooldown_suppressed = False
            elif delta_mins < cd_mins:
                is_cooldown_suppressed = True

        if not is_cooldown_suppressed and exact_k in existing_exact_timestamps:
            prev_time = existing_exact_timestamps[exact_k]
            delta_mins = (cand_time - prev_time).total_seconds() / 60.0
            if delta_mins < cd_mins:
                is_cooldown_suppressed = True

        if is_cooldown_suppressed:
            cooldown_skipped += 1
            continue

        seen_in_batch.add(exact_k)
        existing_exact_timestamps[exact_k] = cand_time
        existing_entities[entity_k] = (cand_time, cand_rank)
        unique_alerts.append(cand)

    return unique_alerts, duplicates_skipped, cooldown_skipped


# ==============================================================================
# 5. CREATION, PERSISTENCE & DISPATCH
# ==============================================================================

def create_alert(
    alert_dict: Dict[str, Any],
    db_session: Optional[Any] = None,
    dispatcher: Optional[NotificationDispatcher] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Validates, stores in DB / memory, and dispatches notifications."""
    valid, err = validate_alert_inputs(alert_dict)
    if not valid:
        raise ValueError(f"Alert validation failed: {err}")

    # Build Pydantic model
    dto = AlertCreate(**alert_dict)
    persisted = db_create_alert(db_session, dto)

    # Dispatch notifications
    if dispatcher is not None:
        dispatcher.dispatch_alert(persisted, dry_run=dry_run)

    return persisted


def store_alert(alert: Dict[str, Any], db_session: Optional[Any] = None) -> Dict[str, Any]:
    """Helper alias for storing an alert."""
    return create_alert(alert, db_session=db_session, dry_run=True)


def generate_alert_summary(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates operational summary statistics for a set of alerts."""
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0}
    type_counts: Dict[str, int] = {}

    for a in alerts:
        sev = a.get("severity", "LOW")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
        t = a.get("alert_type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_generated": len(alerts),
        "critical_count": sev_counts["CRITICAL"],
        "high_count": sev_counts["HIGH"],
        "moderate_count": sev_counts["MODERATE"],
        "low_count": sev_counts["LOW"],
        "type_breakdown": type_counts,
        "disclaimer": "Model-derived analytical signals. Authorized human review required.",
    }


# ==============================================================================
# 6. MAIN ENGINE RUNNER
# ==============================================================================

def run_alert_generation(
    config: Optional[Dict[str, Any]] = None,
    db_session: Optional[Any] = None,
    dry_run: bool = True,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    End-to-end analytical alert generation workflow:
    1. Loads risk predictions & DBSCAN hotspots
    2. Evaluates risk, hotspot, and withdrawal rules
    3. Enforces rate limits and deduplication
    4. Persists unique alerts
    5. Dispatches notifications (dry run)
    """
    if config is None:
        config = load_configuration()

    df_risk = load_risk_data()
    df_hs, df_hr, df_wh = load_hotspot_data()

    dispatcher = NotificationDispatcher(
        log_enabled=config.get("notifications", {}).get("log", True),
        email_enabled=config.get("notifications", {}).get("email", False),
    )

    candidates: List[Dict[str, Any]] = []
    counter = len(_LOCAL_ALERTS_CACHE) + 1

    # A. Evaluate Risk Alerts (Phase 9 high/critical predictions)
    if not df_risk.empty:
        # Filter for high/critical records to inspect
        high_risk_df = df_risk[df_risk["risk_score"] >= config.get("risk_thresholds", {}).get("high", 60)]
        for _, row in high_risk_df.iterrows():
            alert = evaluate_risk_alert(row.to_dict(), config, counter)
            if alert:
                candidates.append(alert)
                counter += 1

    # B. Evaluate Hotspot Alerts (Phase 14 clusters)
    if not df_hs.empty:
        hr_lookup = {}
        if not df_hr.empty:
            for _, r in df_hr.iterrows():
                hr_lookup[r["cluster_id"]] = r.to_dict()

        for _, hs_row in df_hs.iterrows():
            cid = hs_row.get("cluster_id")
            hr_data = hr_lookup.get(cid)
            alert = evaluate_hotspot_alert(hs_row.to_dict(), hr_data, config, counter)
            if alert:
                candidates.append(alert)
                counter += 1

    # C. Evaluate Withdrawal Hotspot Alerts (Phase 14 withdrawal hotspots)
    if not df_wh.empty:
        for _, wh_row in df_wh.iterrows():
            alert = evaluate_withdrawal_alert(wh_row.to_dict(), config, counter)
            if alert:
                candidates.append(alert)
                counter += 1

    # D. Include synthetic demonstration scenarios if no critical records exist in slice
    has_critical = any(c.get("severity") == "CRITICAL" for c in candidates)
    if not has_critical and config.get("include_synthetic_demo_cases", True):
        # 1. Synthetic critical location alert
        crit_loc = {
            "risk_score": 91,
            "predicted_probability": 0.91,
            "case_id": "SYNTH_DEMO_CRIT_001",
            "victim_district": "Bengaluru Central",
            "crime_category_group": "INVESTMENT_SCAM",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "complaint_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "model_version": "v1.0.0-xgb-calibrated",
        }
        alert_crit_loc = evaluate_risk_alert(crit_loc, config, counter)
        if alert_crit_loc:
            candidates.append(alert_crit_loc)
            counter += 1

        # 2. Synthetic critical hotspot alert
        crit_hs = {
            "cluster_id": "99",
            "average_risk_score": 88.5,
            "critical_risk_count": 3,
            "high_risk_count": 5,
            "event_count": 48,
            "latitude_centroid": 13.0358,
            "longitude_centroid": 77.5970,
            "time_range_start": "2026-08-01 00:00:00",
            "time_range_end": "2026-08-31 23:59:59",
        }
        alert_crit_hs = evaluate_hotspot_alert(crit_hs, None, config, counter)
        if alert_crit_hs:
            candidates.append(alert_crit_hs)
            counter += 1

    # Rate limiting protection
    max_batch = config.get("rate_limiting", {}).get("max_alerts_per_generation", 100)
    candidates = candidates[:max_batch]

    # Deduplicate against existing alerts
    existing, _ = db_get_alerts(db_session, limit=500)
    unique_alerts, dup_skipped, cd_skipped = deduplicate_alerts(candidates, existing, config)

    # Persist and dispatch
    persisted_alerts: List[Dict[str, Any]] = []
    for alert_dict in unique_alerts:
        persisted = create_alert(
            alert_dict,
            db_session=db_session,
            dispatcher=dispatcher,
            dry_run=dry_run,
        )
        persisted_alerts.append(persisted)

    summary = generate_alert_summary(persisted_alerts)
    summary["duplicates_skipped"] = dup_skipped
    summary["cooldown_skipped"] = cd_skipped
    summary["dry_run"] = dry_run

    return persisted_alerts, summary


def main():
    """Command-line entry point to generate demonstration analytical alerts."""
    parser = argparse.ArgumentParser(description="Phase 16 — Cybercrime Analytical Alert Engine")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Execute in dry-run notification mode")
    parser.add_argument("--export-demo", action="store_true", default=True, help="Export demo alerts to outputs/")
    args = parser.parse_args()

    logger.info("Initializing Phase 16 Alert Engine...")
    cfg = load_configuration()

    session = None
    try:
        from database.connection import check_database_health
        health = check_database_health()
        if health.get("status") == "connected":
            session = SessionLocal()
        else:
            logger.info("Database offline. Utilizing high-performance local memory and file storage.")
    except Exception as exc:
        logger.warning("Database check failed, proceeding with local cache: %s", exc)

    try:
        alerts, summary = run_alert_generation(config=cfg, db_session=session, dry_run=args.dry_run)
        logger.info(
            "Generation complete! Total=%d | Critical=%d | High=%d | DuplicatesSkipped=%d",
            summary["total_generated"],
            summary["critical_count"],
            summary["high_count"],
            summary["duplicates_skipped"],
        )

        if args.export_demo and alerts:
            demo_csv = OUTPUTS_DIR / "phase16_demo_alerts.csv"
            df_demo = pd.DataFrame(alerts)
            df_demo["synthetic_demonstration"] = True
            df_demo.to_csv(demo_csv, index=False)
            logger.info("Exported %d demo alerts to %s", len(df_demo), demo_csv)

    finally:
        if session is not None:
            session.close()


if __name__ == "__main__":
    main()
