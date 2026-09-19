"""
Phase 5 — Risk Scoring & SHAP Explainability Verification Suite
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

14 required verification scenarios:
 1.  Probability-to-risk-score formula: round(prob * 100)
 2.  All 9 boundary probabilities (0.00 -> 0 LOW ... 1.00 -> 100 CRITICAL)
 3.  Risk category tier boundaries (strict 4-tier map)
 4.  Out-of-bounds and NaN/Inf probability rejection / clipping
 5.  SHAP explanation succeeds on raw Pipeline model
 6.  SHAP explanation succeeds on CalibratedClassifierCV model (Phase 4)
 7.  SHAP mathematical consistency: shap values are finite and non-trivial
 8.  SHAP distinctness: different inputs -> different SHAP vectors
 9.  Enriched ExplainResponse fields present (prediction_id, model_version, etc.)
10.  feature_value populated in every SHAP contributor entry
11.  explanation_limitations non-causal disclaimer present and not empty
12.  Cross-function consistency: same record -> same probability, score, tier
     across probability_to_risk_score, assign_risk_category, predict_single_record
13.  Alert thresholds match config (CRITICAL >= 80, HIGH >= 60, MODERATE >= 40, LOW 0-39)
14.  Security: explanation output contains no forbidden credential tokens

IMPORTANT:
- Uses ONLY synthetic data records -- never real PII or operational data.
- Reads existing model artifacts and metadata; never retrain.
- Marked as skipped when model artifacts are unavailable (CI-safe).
"""

import json
import math
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
PROC_DIR = BASE_DIR / "data" / "processed"
CONFIG_PATH = BASE_DIR / "config" / "alert_config.json"

FORBIDDEN_TOKENS = [
    "card_number", "pin", "otp", "cvv", "password",
    "account_id", "bank_account", "ifsc",
]


def _build_synthetic_record(overrides=None):
    record = {
        "crime_type": "Online Financial Fraud",
        "fraud_amount": 15000.0,
        "reported_by_authority": 0.0,
        "victim_state": "Karnataka",
        "victim_district": "Bengaluru Urban",
        "victim_area": "Koramangala",
        "victim_area_id": "KA_BLR_KOR_001",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "event_year": 2026,
        "event_month": 8,
        "event_day": 200,
        "event_day_of_month": 19,
        "event_day_of_week": 2,
        "event_hour": 14,
        "event_minute": 30,
        "is_weekend": 0.0,
        "is_month_start": 0.0,
        "is_month_end": 0.0,
        "is_quarter_start": 0.0,
        "is_quarter_end": 0.0,
        "hour_group": "afternoon",
        "time_period": "business_hours",
        "latitude_rounded": 12.94,
        "longitude_rounded": 77.62,
        "location_grid": "12.94_77.62",
        "coordinate_precision": "high",
        "geographic_region": "South",
        "crime_category_group": "Financial Fraud",
        "is_financial_fraud": 1.0,
        "is_online_fraud": 1.0,
        "is_identity_related": 0.0,
        "is_transaction_related": 1.0,
        "amount_log1p": math.log1p(15000.0),
        "amount_is_zero": 0.0,
        "amount_is_high": 1.0,
        "amount_category": "high",
        "previous_event_count": 2.0,
        "time_since_previous_event_hours": 48.0,
        "events_in_previous_1_day": 1.0,
        "events_in_previous_3_days": 2.0,
        "events_in_previous_7_days": 3.0,
        "events_in_previous_30_days": 5.0,
        "previous_activity_by_location": 10.0,
        "previous_activity_by_district": 50.0,
        "previous_activity_by_crime_category": 25.0,
        "rolling_event_count_1h": 0.0,
        "rolling_event_count_6h": 1.0,
        "rolling_event_count_24h": 2.0,
        "rolling_event_count_7d": 5.0,
        "rolling_location_event_count_24h": 1.0,
        "rolling_crime_event_count_7d": 3.0,
        "location_total_previous_events": 20.0,
        "location_previous_24h_events": 1.0,
        "location_previous_7d_events": 5.0,
        "district_previous_24h_events": 10.0,
        "district_previous_7d_events": 35.0,
        "location_unique_crime_categories": 3.0,
        "has_location": 1.0,
        "has_timestamp": 1.0,
        "has_amount": 1.0,
        "has_crime_category": 1.0,
        "has_district": 1.0,
        "missing_coordinate_flag": 0.0,
    }
    if overrides:
        record.update(overrides)
    return record


# ---- Fixtures ----
@pytest.fixture(scope="module")
def raw_pipeline():
    model_path = MODELS_DIR / "xgboost_cybercrime_model.pkl"
    if not model_path.exists():
        pytest.skip("xgboost_cybercrime_model.pkl not found -- skipping.")
    import joblib
    return joblib.load(model_path)

@pytest.fixture(scope="module")
def calibrated_model():
    cal_path = MODELS_DIR / "xgboost_v2_calibrated.pkl"
    if not cal_path.exists():
        pytest.skip("xgboost_v2_calibrated.pkl not found -- skipping.")
    import joblib
    return joblib.load(cal_path)

@pytest.fixture(scope="module")
def metadata():
    meta_path = MODELS_DIR / "phase7_xgboost_metadata.json"
    if not meta_path.exists():
        pytest.skip("phase7_xgboost_metadata.json not found -- skipping.")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def metadata_v2():
    meta_path = MODELS_DIR / "metadata_v2_evaluation.json"
    if not meta_path.exists():
        pytest.skip("metadata_v2_evaluation.json not found -- skipping.")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def alert_config():
    if not CONFIG_PATH.exists():
        pytest.skip("alert_config.json not found -- skipping.")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def synthetic_record():
    return _build_synthetic_record()


# ---- SCENARIO 1: Formula ----
class TestRiskScoreFormula:
    def test_formula_basic(self):
        from src.generate_risk_score import probability_to_risk_score
        assert probability_to_risk_score(0.50) == 50
        assert probability_to_risk_score(0.75) == 75
        assert probability_to_risk_score(0.25) == 25

    def test_formula_vector_input(self):
        from src.generate_risk_score import probability_to_risk_score
        probs = np.array([0.0, 0.1, 0.5, 0.9, 1.0])
        scores = probability_to_risk_score(probs)
        expected = np.array([0, 10, 50, 90, 100])
        np.testing.assert_array_equal(scores, expected)

    def test_predict_py_formula_matches(self):
        from src.predict import probability_to_risk_score as f_pred
        from src.generate_risk_score import probability_to_risk_score as f_gen
        for p in [0.0, 0.15, 0.39, 0.40, 0.59, 0.60, 0.79, 0.80, 1.0]:
            assert f_pred(p) == f_gen(p), f"Formula mismatch at p={p}"


# ---- SCENARIO 2: Boundary probabilities ----
class TestBoundaryProbabilities:
    BOUNDARIES = [
        (0.00,  0, "LOW"),
        (0.10, 10, "LOW"),
        (0.39, 39, "LOW"),
        (0.40, 40, "MODERATE"),
        (0.59, 59, "MODERATE"),
        (0.60, 60, "HIGH"),
        (0.79, 79, "HIGH"),
        (0.80, 80, "CRITICAL"),
        (1.00, 100, "CRITICAL"),
    ]

    @pytest.mark.parametrize("prob,expected_score,expected_cat", BOUNDARIES)
    def test_boundary(self, prob, expected_score, expected_cat):
        from src.predict import probability_to_risk_score, assign_risk_category
        score = probability_to_risk_score(prob)
        cat = assign_risk_category(score)
        assert score == expected_score, f"Probability {prob} -> expected score {expected_score}, got {score}"
        assert cat == expected_cat, f"Score {score} -> expected category {expected_cat}, got {cat}"


# ---- SCENARIO 3: Risk category tiers ----
class TestRiskCategoryTiers:
    TIER_CASES = [
        (0, "LOW"), (20, "LOW"), (39, "LOW"),
        (40, "MODERATE"), (50, "MODERATE"), (59, "MODERATE"),
        (60, "HIGH"), (70, "HIGH"), (79, "HIGH"),
        (80, "CRITICAL"), (90, "CRITICAL"), (100, "CRITICAL"),
    ]

    @pytest.mark.parametrize("score,expected_cat", TIER_CASES)
    def test_category_from_score(self, score, expected_cat):
        from src.predict import assign_risk_category
        assert assign_risk_category(score) == expected_cat

    def test_no_unknown_category(self):
        from src.predict import assign_risk_category
        for score in range(0, 101):
            cat = assign_risk_category(score)
            assert cat in {"LOW", "MODERATE", "HIGH", "CRITICAL"}, f"Score {score} mapped to unexpected category '{cat}'"


# ---- SCENARIO 4: Edge cases ----
class TestProbabilityEdgeCases:
    def test_clip_below_zero(self):
        from src.predict import probability_to_risk_score
        assert probability_to_risk_score(-0.5) == 0

    def test_clip_above_one(self):
        from src.predict import probability_to_risk_score
        assert probability_to_risk_score(1.5) == 100

    def test_clip_vector_oob(self):
        from src.predict import probability_to_risk_score
        probs = np.array([-1.0, 0.5, 2.0])
        scores = probability_to_risk_score(probs)
        assert scores[0] == 0
        assert scores[1] == 50
        assert scores[2] == 100


# ---- SCENARIO 5: SHAP on raw Pipeline ----
class TestShapRawPipeline:
    def test_explain_returns_success_status(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        assert result["status"] == "SUCCESS", f"SHAP failed: {result.get('error_details', '')}"

    def test_positive_contributors_non_empty(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        assert len(result["top_positive_contributors"]) > 0

    def test_all_contributors_have_required_keys(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        required_keys = {"rank", "feature", "shap_value", "direction", "feature_value"}
        for entry in result["top_positive_contributors"] + result["top_negative_contributors"]:
            missing = required_keys - set(entry.keys())
            assert not missing, f"Contributor missing keys: {missing}"

    def test_direction_values_valid(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        valid_dirs = {"INCREASED_RISK", "DECREASED_RISK"}
        for entry in result["all_top_contributors"]:
            assert entry["direction"] in valid_dirs, f"Unexpected direction '{entry['direction']}'"



# ---- SCENARIO 6: SHAP on calibrated model ----
def _build_synthetic_v2_record():
    """
    Build a synthetic record with all 86 v2 features (anonymized).
    The v2 model requires 30 additional transaction/account features
    not present in the 64-feature v1 schema.
    """
    import math
    base = _build_synthetic_record()
    v2_extra = {
        "victim_account_type": "savings",
        "victim_account_age_days": 365.0,
        "victim_baseline_daily_txns": 5.0,
        "victim_baseline_daily_amount": 20000.0,
        "victim_baseline_daily_withdrawals": 2.0,
        "fraud_to_daily_amount_ratio": 0.75,
        "fraud_amount_excess_over_baseline": -5000.0,
        "case_prior_txn_count": 3.0,
        "case_prior_amount_sum": 45000.0,
        "case_prior_amount_max": 20000.0,
        "case_prior_unique_channels": 2.0,
        "case_hours_since_first_txn": 24.0,
        "victim_outgoing_txns_all": 100.0,
        "victim_outgoing_amount_all": 500000.0,
        "victim_outgoing_amount_avg": 5000.0,
        "victim_outgoing_amount_max": 50000.0,
        "victim_hours_since_last_outgoing": 12.0,
        "victim_outgoing_txns_24h": 2.0,
        "victim_outgoing_amount_24h": 10000.0,
        "victim_outgoing_txns_7d": 10.0,
        "victim_outgoing_amount_7d": 50000.0,
        "victim_incoming_txns_all": 80.0,
        "victim_incoming_amount_all": 400000.0,
        "victim_incoming_txns_24h": 1.0,
        "victim_incoming_amount_24h": 5000.0,
        "victim_hours_since_last_incoming": 36.0,
        "victim_total_prior_volume": 900000.0,
        "victim_net_prior_flow": 100000.0,
        "victim_total_linked_accounts": 3.0,
        "victim_velocity_surge_ratio": 1.5,
    }
    base.update(v2_extra)
    # Remove features not in v2 schema
    for k in ["event_month", "event_day", "previous_event_count",
              "previous_activity_by_location", "previous_activity_by_district",
              "previous_activity_by_crime_category", "location_total_previous_events",
              "location_unique_crime_categories"]:
        base.pop(k, None)
    return base


class TestShapCalibratedModel:
    def test_explain_calibrated_returns_success_or_skip(self, calibrated_model, metadata_v2):
        from src.predict import explain_prediction, load_feature_schema
        features = load_feature_schema(metadata_v2)
        if not features:
            pytest.skip("v2 feature schema unavailable.")
        synthetic_v2 = _build_synthetic_v2_record()
        result = explain_prediction(synthetic_v2, calibrated_model, metadata_v2)
        assert result["status"] == "SUCCESS", (
            f"SHAP failed on calibrated model: {result.get('error_details', '')}"
        )

    def test_calibrated_shap_contributors_non_empty(self, calibrated_model, metadata_v2):
        from src.predict import explain_prediction, load_feature_schema
        features = load_feature_schema(metadata_v2)
        if not features:
            pytest.skip("v2 feature schema unavailable.")
        synthetic_v2 = _build_synthetic_v2_record()
        result = explain_prediction(synthetic_v2, calibrated_model, metadata_v2)
        if result["status"] != "SUCCESS":
            pytest.skip(f"SHAP not available on calibrated model: {result.get('error_details', '')}")
        total = len(result["top_positive_contributors"]) + len(result["top_negative_contributors"])
        assert total > 0


# ---- SCENARIO 7: SHAP mathematical consistency ----
class TestShapMathematicalConsistency:
    def test_shap_values_are_finite(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        if result["status"] != "SUCCESS":
            pytest.skip("SHAP unavailable.")
        for entry in result["all_top_contributors"]:
            assert math.isfinite(entry["shap_value"]), f"Non-finite SHAP value for '{entry['feature']}'"

    def test_shap_values_non_trivial(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        if result["status"] != "SUCCESS":
            pytest.skip("SHAP unavailable.")
        total = sum(abs(e["shap_value"]) for e in result["all_top_contributors"])
        assert total > 0.0, "All SHAP values are zero"

    def test_shap_sum_nonzero_via_library(self, raw_pipeline, metadata, synthetic_record):
        import shap as shap_lib
        from src.predict import _extract_tree_estimator, _extract_preprocessor_for_shap, prepare_input, load_feature_schema
        expected_features = load_feature_schema(metadata)
        preprocessor = _extract_preprocessor_for_shap(raw_pipeline)
        tree_clf = _extract_tree_estimator(raw_pipeline)
        df = pd.DataFrame([synthetic_record])
        X_prep = prepare_input(df, expected_features)
        X_trans = preprocessor.transform(X_prep)
        explainer = shap_lib.TreeExplainer(tree_clf)
        shap_vals = explainer(X_trans)
        total = float(np.sum(np.abs(shap_vals.values[0])))
        assert total > 0.0


# ---- SCENARIO 8: SHAP distinctness ----
class TestShapDistinctness:
    def test_two_records_produce_different_shap(self, raw_pipeline, metadata):
        from src.predict import explain_prediction
        record_a = _build_synthetic_record({"fraud_amount": 5000.0, "rolling_event_count_24h": 0.0})
        record_b = _build_synthetic_record({"fraud_amount": 150000.0, "rolling_event_count_24h": 15.0, "previous_event_count": 20.0})
        res_a = explain_prediction(record_a, raw_pipeline, metadata)
        res_b = explain_prediction(record_b, raw_pipeline, metadata)
        if res_a["status"] != "SUCCESS" or res_b["status"] != "SUCCESS":
            pytest.skip("SHAP unavailable.")
        shap_a = {e["feature"]: e["shap_value"] for e in res_a["all_top_contributors"]}
        shap_b = {e["feature"]: e["shap_value"] for e in res_b["all_top_contributors"]}
        shared = set(shap_a.keys()) & set(shap_b.keys())
        assert any(shap_a[f] != shap_b[f] for f in shared), "Both records produced identical SHAP vectors"


# ---- SCENARIO 9: Enriched fields ----
class TestEnrichedExplainFields:
    REQUIRED_KEYS = ["prediction_id", "model_version", "prediction_timestamp", "risk_score", "risk_level", "explanation_available", "explanation_limitations"]

    def test_enriched_fields_present(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        for key in self.REQUIRED_KEYS:
            assert key in result, f"Phase 5 field '{key}' missing from explain_prediction output"

    def test_prediction_id_format(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        pid = result.get("prediction_id", "")
        assert isinstance(pid, str) and pid.startswith("EXPL-"), f"prediction_id should start with 'EXPL-', got: {pid!r}"

    def test_prediction_timestamp_iso_utc(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        from datetime import datetime
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        ts = result.get("prediction_timestamp", "")
        assert isinstance(ts, str) and len(ts) > 10
        try:
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"prediction_timestamp not ISO 8601: {ts!r}")

    def test_risk_level_matches_risk_category(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        if result["status"] == "SUCCESS":
            pred = result.get("prediction", {})
            assert result["risk_level"] == pred.get("risk_category")

    def test_explanation_available_bool(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        assert isinstance(result.get("explanation_available"), bool)
        if result["status"] == "SUCCESS":
            assert result["explanation_available"] is True
        else:
            assert result["explanation_available"] is False


# ---- SCENARIO 10: feature_value populated ----
class TestFeatureValuePopulated:
    def test_positive_contributors_have_feature_value(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        if result["status"] != "SUCCESS":
            pytest.skip("SHAP unavailable.")
        for entry in result["top_positive_contributors"]:
            assert "feature_value" in entry and entry["feature_value"] is not None, f"feature_value missing/None for '{entry['feature']}'"

    def test_negative_contributors_have_feature_value(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        if result["status"] != "SUCCESS":
            pytest.skip("SHAP unavailable.")
        for entry in result["top_negative_contributors"]:
            assert "feature_value" in entry and entry["feature_value"] is not None, f"feature_value missing/None for '{entry['feature']}'"


# ---- SCENARIO 11: Non-causal disclaimer ----
class TestExplanationLimitations:
    NON_CAUSAL_PHRASES = ["statistical", "do not imply", "not proof"]

    def test_disclaimer_present_and_non_empty(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        limitations = result.get("explanation_limitations", "")
        assert isinstance(limitations, str) and len(limitations) > 50

    def test_disclaimer_contains_non_causal_language(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        limitations = result.get("explanation_limitations", "").lower()
        found = [p for p in self.NON_CAUSAL_PHRASES if p in limitations]
        assert len(found) >= 2, f"Non-causal phrases found: {found}. Full: {limitations!r}"


# ---- SCENARIO 12: Cross-function consistency ----
class TestCrossFunctionConsistency:
    def test_score_matches_across_functions(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import predict_single_record, probability_to_risk_score, assign_risk_category
        single = predict_single_record(synthetic_record, raw_pipeline, metadata)
        score_direct = probability_to_risk_score(single["probability"])
        cat_direct = assign_risk_category(score_direct)
        assert score_direct == single["risk_score"]
        assert cat_direct == single["risk_category"]

    def test_explain_consistent_with_predict(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import predict_single_record, explain_prediction
        single = predict_single_record(synthetic_record, raw_pipeline, metadata)
        expl = explain_prediction(synthetic_record, raw_pipeline, metadata)
        if expl["status"] != "SUCCESS":
            pytest.skip("SHAP unavailable.")
        pred_in_expl = expl.get("prediction", {})
        assert abs(pred_in_expl.get("probability", -1) - single["probability"]) < 1e-5
        assert pred_in_expl.get("risk_score") == single["risk_score"]
        assert pred_in_expl.get("risk_category") == single["risk_category"]


# ---- SCENARIO 13: Alert thresholds ----
class TestAlertThresholdsMatchConfig:
    def test_critical_threshold_is_80(self, alert_config):
        assert alert_config["risk_thresholds"]["critical"] == 80

    def test_high_threshold_is_60(self, alert_config):
        assert alert_config["risk_thresholds"]["high"] == 60

    def test_moderate_threshold_is_40(self, alert_config):
        assert alert_config["risk_thresholds"]["moderate"] == 40

    def test_low_threshold_is_0(self, alert_config):
        assert alert_config["risk_thresholds"]["low"] == 0

    def test_config_thresholds_match_assign_risk_category(self, alert_config):
        from src.predict import assign_risk_category
        cfg = alert_config["risk_thresholds"]
        assert assign_risk_category(cfg["critical"]) == "CRITICAL"
        assert assign_risk_category(cfg["high"]) == "HIGH"
        assert assign_risk_category(cfg["moderate"]) == "MODERATE"
        assert assign_risk_category(cfg["low"]) == "LOW"

    def test_cooldown_critical_30_min(self, alert_config):
        assert alert_config["cooldown_minutes"]["critical"] == 30

    def test_cooldown_high_60_min(self, alert_config):
        assert alert_config["cooldown_minutes"]["high"] == 60


# ---- SCENARIO 14: Security ----
class TestExplanationSecurity:
    def test_no_forbidden_tokens_in_output(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        import json as json_mod
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        serialized = json_mod.dumps(result, default=str).lower()
        found = [t for t in FORBIDDEN_TOKENS if t in serialized]
        assert not found, f"Forbidden credential tokens found in output: {found}"

    def test_no_internal_paths_in_output(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        import json as json_mod
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        serialized = json_mod.dumps(result, default=str)
        suspicious = ["C:\\Users\\HP", "/home/", "/etc/passwd", ".env"]
        found = [p for p in suspicious if p in serialized]
        assert not found, f"Internal paths found in output: {found}"

    def test_feature_names_do_not_contain_pii_tokens(self, raw_pipeline, metadata, synthetic_record):
        from src.predict import explain_prediction
        result = explain_prediction(synthetic_record, raw_pipeline, metadata)
        if result["status"] != "SUCCESS":
            pytest.skip("SHAP unavailable.")
        all_features = [e["feature"] for e in result["all_top_contributors"]]
        for feat in all_features:
            for token in FORBIDDEN_TOKENS:
                assert token not in feat.lower(), f"Forbidden token '{token}' in SHAP feature: '{feat}'"
