"""
Phase Mule Pattern Detection — Rule-Based Heuristic Fan-In Indicator
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

STRICT SCOPE & ARCHITECTURAL BOUNDARY:
--------------------------------------
This module implements a lightweight, rule-based heuristic indicator based on
transaction fan-in patterns (multiple distinct senders to a single beneficiary within
a 72-hour rolling window).

EXPLICIT DISCLAIMER & LIMITATIONS:
- This is a SIMPLE HEURISTIC, NOT a graph neural network, GNN, or true multi-hop mule
  network mapping.
- It does NOT import or use graph libraries (networkx, igraph).
- It does NOT modify or retrain the XGBoost prediction model or its feature pipeline.
- It does NOT establish account involvement in fraud or definitive legal culpability.
- Multi-hop graph-based tracing is a planned future capability, not implemented here.
- Outputs are analytical pattern indicators for authorized human review only.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROC_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [mule_pattern_detection] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("mule_pattern_detection")

# Heuristic Constants & Compliance Metadata
HEURISTIC_METHOD = "rule_based_heuristic_fan_in_pattern"
HEURISTIC_DISCLAIMER = (
    "Simplified heuristic indicator only — not a validated mule detection system. "
    "Does not establish account involvement in fraud. "
    "Multi-hop graph-based tracing is a planned future capability, not implemented here."
)


def compute_mule_pattern_indicators(
    transactions_path: Path,
    window_hours: float = 72.0,
    score_threshold: int = 70,
) -> pd.DataFrame:
    """
    Compute rule-based heuristic fan-in indicators for beneficiary accounts.

    Algorithm:
    1. Reads cleaned transactions (pre-cleaned by data_cleaning.py).
    2. Groups transactions by beneficiary account (`to_account` / `to_account_masked`).
    3. For each account:
       - Calculates max distinct source accounts (`from_account`) in any rolling
         time window of duration `window_hours` (default: 72 hours).
       - Calculates total distinct source accounts over full history.
       - Calculates average time gap (in hours) between consecutive incoming transactions.
    4. Scales `distinct_source_count_72h` to a 0-100 `mule_pattern_score`.
    5. Flags accounts with score >= score_threshold (default: 70) as `mule_pattern_flag: true`.
    """
    if not transactions_path.exists():
        raise FileNotFoundError(f"Cleaned transactions file not found at: {transactions_path}")

    logger.info("Loading cleaned transactions from: %s", transactions_path)
    t0 = time.time()

    # Determine columns to load
    sample_df = pd.read_csv(transactions_path, nrows=5)
    to_col = "to_account_masked" if "to_account_masked" in sample_df.columns else "to_account"
    from_col = "from_account_masked" if "from_account_masked" in sample_df.columns else "from_account"
    time_col = "timestamp"

    if to_col not in sample_df.columns or from_col not in sample_df.columns or time_col not in sample_df.columns:
        raise ValueError(
            f"Missing required columns in transactions data. "
            f"Expected '{to_col}', '{from_col}', '{time_col}'. Found: {list(sample_df.columns)}"
        )

    df = pd.read_csv(transactions_path, usecols=[to_col, from_col, time_col])
    logger.info("Loaded %d transaction rows in %.2fs", len(df), time.time() - t0)

    # Parse timestamps and sort
    t_sort_start = time.time()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values([to_col, time_col]).reset_index(drop=True)
    logger.info("Sorted transactions by account and timestamp in %.2fs", time.time() - t_sort_start)

    # Convert timestamp to unix seconds for vectorised window math
    ts_seconds = (df[time_col].astype("int64") // 10**9).values
    accounts = df[to_col].values
    sources = df[from_col].values

    window_secs = int(window_hours * 3600)
    n_rows = len(df)

    records: List[Tuple[str, int, int, float]] = []
    t_comp_start = time.time()

    i = 0
    while i < n_rows:
        curr_acc = accounts[i]
        j = i
        while j < n_rows and accounts[j] == curr_acc:
            j += 1

        # Slice [i:j] represents all incoming transactions for curr_acc
        acc_sources = sources[i:j]
        acc_ts = ts_seconds[i:j]
        m = j - i

        total_distinct = len(set(acc_sources))

        if m <= 1:
            max_72h = 1
            avg_gap_hours = 0.0
        else:
            max_72h = 1
            # Sliding window over transactions for this account
            for left in range(m):
                t_left = acc_ts[left]
                window_sources = set()
                for right in range(left, m):
                    if acc_ts[right] - t_left <= window_secs:
                        window_sources.add(acc_sources[right])
                    else:
                        break
                if len(window_sources) > max_72h:
                    max_72h = len(window_sources)

            # Average gap between consecutive incoming transactions (hours)
            gaps = (acc_ts[1:] - acc_ts[:-1]) / 3600.0
            avg_gap_hours = round(float(np.mean(gaps)), 2)

        records.append((str(curr_acc), int(max_72h), int(total_distinct), float(avg_gap_hours)))
        i = j

    res_df = pd.DataFrame(
        records,
        columns=[
            "account_id",
            "distinct_source_count_72h",
            "distinct_source_count_total",
            "avg_incoming_gap_hours",
        ],
    )
    logger.info("Aggregated %d unique beneficiary accounts in %.2fs", len(res_df), time.time() - t_comp_start)

    # 4. Score normalization (0-100 integer)
    min_count = res_df["distinct_source_count_72h"].min()
    max_count = res_df["distinct_source_count_72h"].max()

    if max_count > min_count:
        norm_scores = np.round(
            ((res_df["distinct_source_count_72h"] - min_count) / (max_count - min_count)) * 100.0
        ).astype(int)
    else:
        norm_scores = np.zeros(len(res_df), dtype=int)

    res_df["mule_pattern_score"] = np.clip(norm_scores, 0, 100)

    # 5. Flag accounts above configurable threshold
    res_df["mule_pattern_flag"] = res_df["mule_pattern_score"] >= score_threshold

    # 6. Add compliance / method metadata columns
    res_df["method"] = HEURISTIC_METHOD
    res_df["disclaimer"] = HEURISTIC_DISCLAIMER

    # Sort descending by score, then 72h count
    res_df = res_df.sort_values(
        ["mule_pattern_score", "distinct_source_count_72h", "avg_incoming_gap_hours"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return res_df


def run_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    window_hours: float = 72.0,
    score_threshold: int = 70,
) -> Path:
    """Execute mule pattern detection pipeline and save CSV output."""
    if input_path is None:
        input_path = PROC_DIR / "cleaned_transactions.csv"
    if output_path is None:
        output_path = OUTPUTS_DIR / "phase_mule_pattern_accounts.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    results_df = compute_mule_pattern_indicators(
        transactions_path=input_path,
        window_hours=window_hours,
        score_threshold=score_threshold,
    )

    results_df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Saved mule pattern accounts to: %s", output_path)

    total_accs = len(results_df)
    flagged_accs = int(results_df["mule_pattern_flag"].sum())
    flagged_pct = (flagged_accs / total_accs * 100.0) if total_accs > 0 else 0.0

    logger.info(
        "Summary: %d total accounts evaluated, %d flagged with elevated fan-in indicator (%.2f%%)",
        total_accs,
        flagged_accs,
        flagged_pct,
    )
    logger.info("Method: %s", HEURISTIC_METHOD)
    logger.info("Disclaimer: %s", HEURISTIC_DISCLAIMER)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Lightweight rule-based heuristic indicator for fan-in transaction patterns."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROC_DIR / "cleaned_transactions.csv",
        help="Path to cleaned transactions CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUTS_DIR / "phase_mule_pattern_accounts.csv",
        help="Destination path for output CSV",
    )
    parser.add_argument(
        "--window-hours",
        type=float,
        default=72.0,
        help="Rolling time window in hours for fan-in count (default: 72.0)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=70,
        help="Score threshold (0-100) above which accounts are flagged (default: 70)",
    )

    args = parser.parse_args()
    run_pipeline(
        input_path=args.input,
        output_path=args.output,
        window_hours=args.window_hours,
        score_threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
