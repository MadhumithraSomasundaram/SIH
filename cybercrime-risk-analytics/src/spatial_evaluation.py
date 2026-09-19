"""
Spatial Evaluation Module
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Evaluates candidate cashout location predictions against actual historical cashout
ground truth (from Withdrawals.csv linked to qualifying fraud cases).

METRICS CALCULATED:
1. Top-1 Hit Rate: Actual cashout ATM matches Top-1 candidate ATM or falls in Top-1 catchment.
2. Top-3 Hit Rate: Actual cashout ATM matches one of Top-3 candidate ATMs or falls in their catchments.
3. Top-5 Hit Rate: Actual cashout ATM matches one of Top-5 candidate ATMs or falls in their catchments.
4. Accuracy within 2.5 km: Great-circle distance between Top-1 candidate and actual cashout <= 2.5 km.
5. Accuracy within 5.0 km: Great-circle distance between Top-1 candidate and actual cashout <= 5.0 km.
6. Average Distance Error: Mean distance (km) between predicted location and ground truth.
7. Median Distance Error: Median distance (km) between predicted location and ground truth.

RULES:
- Calculated ONLY when ground-truth withdrawal coordinates and timestamps are available.
- Zero fabrication of evaluation metrics.
- Enforces strict chronological boundaries to prevent temporal leakage.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.spatial_cashout_service import (
    haversine_distance,
    get_candidate_cashout_locations,
    is_valid_coordinate,
)

logger = logging.getLogger("cybercrime.spatial_evaluation")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"


def evaluate_spatial_predictions(
    sample_size: Optional[int] = 200,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Evaluates spatial cashout prediction performance against verified historical ground truth.
    
    Returns structured scorecard with measured hit rates, catchment accuracies,
    and distance errors.
    """
    tcd_path = DATA_DIR / "processed" / "targeted_cybercrime_data.csv"
    wd_path = DATA_DIR / "raw" / "Withdrawals.csv"

    if not tcd_path.exists() or not wd_path.exists():
        return {
            "status": "DATA_UNAVAILABLE",
            "message": "Required datasets (targeted_cybercrime_data.csv or Withdrawals.csv) not found.",
            "metrics_available": False,
        }

    # Load positive cases where a ground-truth cashout actually occurred (future_withdrawal == 1)
    df_cases = pd.read_csv(tcd_path)
    positives = df_cases[df_cases["future_withdrawal"] == 1].copy()
    if positives.empty:
        return {
            "status": "NO_POSITIVE_CASES",
            "message": "No cases with verified future cashout ground truth found.",
            "metrics_available": False,
        }

    # Load withdrawals and find qualifying cashout per case
    df_wd = pd.read_csv(wd_path)
    df_wd = df_wd[df_wd["case_id"].notna() & (df_wd["case_id"] != "")].copy()
    df_wd["timestamp"] = pd.to_datetime(df_wd["timestamp"], errors="coerce")
    positives["complaint_timestamp"] = pd.to_datetime(positives["complaint_timestamp"], errors="coerce")

    # Merge on case_id
    merged = positives.merge(df_wd, on="case_id", suffixes=("_case", "_wd"))
    
    # Filter strictly to cashout occurring within [T_0, T_0 + 24h]
    valid_window = (
        (merged["timestamp"] >= merged["complaint_timestamp"]) &
        (merged["timestamp"] <= merged["complaint_timestamp"] + pd.Timedelta(hours=24))
    )
    ground_truth = merged[valid_window].copy()

    # Drop duplicate cases, keeping the earliest qualifying cashout
    ground_truth = ground_truth.sort_values("timestamp").drop_duplicates(subset=["case_id"])

    if ground_truth.empty:
        return {
            "status": "NO_GROUND_TRUTH_MATCHES",
            "message": "No temporally qualifying cashouts found within 24-hour observation window.",
            "metrics_available": False,
        }

    if sample_size is not None and len(ground_truth) > sample_size:
        eval_sample = ground_truth.sample(n=sample_size, random_state=random_state)
    else:
        eval_sample = ground_truth

    top1_hits = 0
    top3_hits = 0
    top5_hits = 0
    acc_2_5km_count = 0
    acc_5_0km_count = 0
    distance_errors: List[float] = []

    eval_records = []

    for _, row in eval_sample.iterrows():
        c_district = row.get("victim_district")
        c_lat = row.get("latitude_case")
        c_lon = row.get("longitude_case")
        actual_lat = row.get("latitude_wd")
        actual_lon = row.get("longitude_wd")
        actual_atm_id = str(row.get("atm_id", ""))

        if not is_valid_coordinate(actual_lat, actual_lon):
            continue

        # Get Top-5 candidates based on complaint location
        candidates = get_candidate_cashout_locations(
            district=c_district,
            complaint_lat=c_lat,
            complaint_lon=c_lon,
            top_k=5,
        )

        if not candidates:
            continue

        top1 = candidates[0]
        # Distance error from Top-1 candidate centroid to actual cashout ATM
        d_top1 = haversine_distance(top1["latitude"], top1["longitude"], actual_lat, actual_lon)
        distance_errors.append(d_top1)

        if d_top1 <= 2.5:
            acc_2_5km_count += 1
        if d_top1 <= 5.0:
            acc_5_0km_count += 1

        # Check Top-K ATM matching or catchment inclusion (within candidate 5km catchment)
        candidate_atms = [c.get("nearest_atm_id") for c in candidates]
        
        # Check if actual ATM matches or falls within catchment radius
        def _in_candidate_catchment(cand: Dict[str, Any], a_lat: float, a_lon: float) -> bool:
            if cand.get("nearest_atm_id") == actual_atm_id:
                return True
            d = haversine_distance(cand["latitude"], cand["longitude"], a_lat, a_lon)
            return d <= 5.0

        if _in_candidate_catchment(candidates[0], actual_lat, actual_lon):
            top1_hits += 1
        if any(_in_candidate_catchment(c, actual_lat, actual_lon) for c in candidates[:3]):
            top3_hits += 1
        if any(_in_candidate_catchment(c, actual_lat, actual_lon) for c in candidates[:5]):
            top5_hits += 1

        eval_records.append({
            "case_id": row["case_id"],
            "district": c_district,
            "actual_atm_id": actual_atm_id,
            "predicted_top1_cluster": top1["cluster_id"],
            "predicted_top1_atm": top1.get("nearest_atm_id"),
            "distance_error_km": d_top1,
        })

    n_eval = len(distance_errors)
    if n_eval == 0:
        return {
            "status": "EVALUATION_FAILED",
            "message": "Zero valid coordinate pairs evaluated.",
            "metrics_available": False,
        }

    top1_hit_rate = round(top1_hits / n_eval, 4)
    top3_hit_rate = round(top3_hits / n_eval, 4)
    top5_hit_rate = round(top5_hits / n_eval, 4)
    acc_2_5km = round(acc_2_5km_count / n_eval, 4)
    acc_5_0km = round(acc_5_0km_count / n_eval, 4)
    avg_dist_err = round(float(np.mean(distance_errors)), 3)
    med_dist_err = round(float(np.median(distance_errors)), 3)

    scorecard = {
        "status": "SUCCESS",
        "evaluated_cases_count": n_eval,
        "sample_size_requested": sample_size,
        "metrics_available": True,
        "top_1_hit_rate": top1_hit_rate,
        "top_3_hit_rate": top3_hit_rate,
        "top_5_hit_rate": top5_hit_rate,
        "accuracy_within_2_5km": acc_2_5km,
        "accuracy_within_5_0km": acc_5_0km,
        "average_distance_error_km": avg_dist_err,
        "median_distance_error_km": med_dist_err,
        "evaluation_notes": (
            "Hit rate defined as qualifying ground-truth cashout ATM matching candidate nearest ATM "
            "or falling within candidate 5.0 km catchment radius. Distance error measured from top-1 "
            "predicted cluster centroid to ground-truth ATM coordinates."
        ),
    }

    # Save machine-readable evaluation output
    out_file = OUTPUTS_DIR / "spatial_evaluation_scorecard.json"
    try:
        import json
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=2)
        logger.info("Saved spatial evaluation scorecard to %s", out_file)
    except Exception as exc:
        logger.warning("Could not write spatial scorecard to file: %s", exc)

    return scorecard


if __name__ == "__main__":
    import pprint
    res = evaluate_spatial_predictions(sample_size=200)
    pprint.pprint(res)
