"""
Tests for Phase 7 — Temporal Forecasting & Recurrent Sequence (LSTM) Feasibility Assessment
Problem Statement ID: 26184
Cybercrime Predictive Analytics Framework
"""

import json
from pathlib import Path
import pytest

from src.evaluate_temporal_forecasting import (
    analyze_lead_time_distribution,
    analyze_sequence_sparsity,
    compare_architectures,
    generate_evaluation_report,
)


def test_lead_time_distribution_statistics():
    """Verify lead time distribution produces valid, physically sound metrics."""
    res = analyze_lead_time_distribution()
    assert res["total_linked_events"] > 0
    assert res["min_lead_time_hours"] >= 0.0, "Lead time cannot be negative (no lookahead leakage)"
    assert res["median_lead_time_hours"] > 0.0
    assert res["max_lead_time_hours"] <= 72.0
    assert res["p25_lead_time_hours"] <= res["median_lead_time_hours"] <= res["p75_lead_time_hours"]

    # Verify windows exist and sum to approximately 100%
    windows = res["actionable_windows"]
    total_pct = sum(w["percentage"] for w in windows.values())
    assert 99.0 <= total_pct <= 101.0, f"Percentages should sum to ~100%, got {total_pct}"


def test_sequence_sparsity_analysis():
    """Verify entity sequence length profiling captures single-event dominance."""
    res = analyze_sequence_sparsity()
    assert res["total_complaints"] > 0
    assert res["unique_entities"] > 0
    assert res["single_event_entity_percentage"] > 75.0, "Expected >75% single-event entities in complaint registries"
    assert res["mean_sequence_length"] < 2.0, "Mean sequence length in episodic complaints is typically ~1.1 to 1.3"
    assert "lstm_sparsity_penalty" in res
    assert "zero-padding" in res["lstm_sparsity_penalty"]


def test_architectural_comparison_dimensions():
    """Verify all 7 comparative dimensions are present and thoroughly justified."""
    res = compare_architectures()
    assert len(res["dimensions"]) == 7
    dim_titles = [d["dimension"] for d in res["dimensions"]]
    assert any("Data Topology" in t for t in dim_titles)
    assert any("Lead-Time" in t for t in dim_titles)
    assert any("Latency" in t for t in dim_titles)
    assert any("Explainability" in t for t in dim_titles)
    assert any("Regulatory" in t for t in dim_titles)
    assert "conclusion" in res


def test_report_generation_and_file_outputs(tmp_path):
    """Verify report generation generates valid markdown and JSON artifacts."""
    res = generate_evaluation_report()
    assert isinstance(res, dict)

    json_file = Path("outputs/temporal_forecasting_evaluation.json")
    md_file = Path("TEMPORAL_FORECASTING_EVALUATION.md")

    assert json_file.exists(), "JSON evaluation artifact must exist"
    assert md_file.exists(), "Markdown evaluation report must exist"

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["problem_statement_id"] == "26184"
        assert "lead_time_analysis" in data
        assert "sequence_sparsity_analysis" in data
        assert "architectural_comparison" in data

    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Phase 7: Temporal Forecasting" in content
        assert "Median Lead Time" in content
        assert "Single-Event Entities" in content
        assert "XGBoost" in content
        assert "LSTM" in content


def test_zero_credential_leakage_in_evaluation_output():
    """Verify no authentication secrets, tokens, or PII appear in the evaluation."""
    json_file = Path("outputs/temporal_forecasting_evaluation.json")
    md_file = Path("TEMPORAL_FORECASTING_EVALUATION.md")

    forbidden = ["password", "cvv", "card_number", "aadhaar", "secret_key", "pin_number", "atm_pin", "user_otp"]
    for path in [json_file, md_file]:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().lower()
            for token in forbidden:
                assert token not in text, f"Forbidden token '{token}' found in {path}"
