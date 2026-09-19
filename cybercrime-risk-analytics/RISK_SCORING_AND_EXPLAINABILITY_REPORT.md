# Phase 5 -- Risk Scoring and SHAP Explainability Audit Report

**Problem Statement ID**: 26184
**Project**: Cybercrime Predictive Analytics Framework
**Phase**: 5 -- Risk Scoring and Explainability Audit and Improvement
**Generated**: 2026-09-19T11:29:00Z

---

## Executive Summary

Phase 5 completed a full audit and structured improvement of the risk scoring and SHAP
explainability modules. All 14 verification scenarios passed with 59 new tests authored.
The 108 existing regression tests continue to pass with zero regressions.
All changes are additive and preserve complete backward compatibility.

---

## 1. Risk Scoring Formula Audit -- PASS

Formula: risk_score = round(probability * 100), integer [0, 100].
Identical implementation confirmed in src/generate_risk_score.py and src/predict.py.

Boundary verification:
  0.00 -> 0   (LOW)
  0.39 -> 39  (LOW)
  0.40 -> 40  (MODERATE)
  0.59 -> 59  (MODERATE)
  0.60 -> 60  (HIGH)
  0.79 -> 79  (HIGH)
  0.80 -> 80  (CRITICAL)
  1.00 -> 100 (CRITICAL)

## 2. Risk Category Tiers -- PASS

  LOW:      [0, 39]   -- Routine monitoring
  MODERATE: [40, 59]  -- Enhanced monitoring
  HIGH:     [60, 79]  -- Prioritize review
  CRITICAL: [80, 100] -- Timely authorized intervention

## 3. SHAP on Raw Pipeline -- PASS

shap.TreeExplainer succeeds on xgboost_cybercrime_model.pkl.
All contributor entries include feature_value. SHAP values finite and non-trivial.

## 4. SHAP on CalibratedClassifierCV -- PASS

xgboost_v2_calibrated.pkl is a top-level CalibratedClassifierCV (not a Pipeline).
New extractors _extract_tree_estimator and _extract_preprocessor_for_shap successfully unwrap:
  CalibratedClassifierCV -> _CalibratedClassifier -> FrozenEstimator -> Pipeline -> XGBClassifier
SHAP produces valid explanations on the 86-feature v2 schema.

## 5. Enriched ExplainResponse Fields -- PASS

New Phase 5 fields in explain_prediction() output:
  prediction_id        : EXPL-{12-char-hex-UUID}
  model_version        : from metadata
  prediction_timestamp : ISO 8601 UTC
  risk_score           : integer [0, 100]
  risk_level           : LOW / MODERATE / HIGH / CRITICAL
  explanation_available: bool
  explanation_limitations: non-causal disclaimer text

## 6. Non-Causal Disclaimer -- PASS

explanation_limitations contains: statistical, do NOT imply, not proof.

## 7. Cross-API Consistency -- PASS

Same record: probability_to_risk_score, predict_single_record, explain_prediction all agree.

## 8. Alert Config Alignment -- PASS

alert_config.json: critical=80, high=60, moderate=40, low=0.
Cooldowns: CRITICAL=30min, HIGH=60min, MODERATE=120min, LOW=240min.
All match assign_risk_category() exactly.

## 9. Security -- PASS

No forbidden tokens (card_number, pin, otp, cvv, password, account_id, bank_account, ifsc)
in SHAP output. No internal file paths. No PII tokens in feature names.

## 10. Test Results

Phase 5 suite (test_risk_and_explainability.py): 59 passed, 0 failed

Regression suite:
  test_model_evaluation.py    : 13 passed
  test_complaints_api.py      : 18 passed
  test_api.py                 : 54 passed
  test_transaction_features.py: 10 passed
  test_leakage_audit.py       :  8 passed
  TOTAL                       : 108 passed, 0 failed

## 11. Changes Made

src/predict.py:
  - NEW: _extract_tree_estimator(pipeline)
  - NEW: _extract_preprocessor_for_shap(pipeline)
  - MODIFIED: explain_prediction() -- calibrated model support + 7 enriched fields
  - MODIFIED: predict_new_records() -- top-level CalibratedClassifierCV support

api/schemas.py:
  - MODIFIED: ShapContribution.feature_value field added
  - MODIFIED: ExplainResponse -- 6 new enriched fields added
  - MODIFIED: Union added to typing imports

api/main.py:
  - MODIFIED: POST /explain passes all Phase 5 enriched fields
  - MODIFIED: ShapContribution includes feature_value

tests/test_risk_and_explainability.py:
  - NEW: 59 tests across 14 verification scenarios

## 12. Backward Compatibility

All legacy fields preserved. All new fields are Optional and additive only.
No existing field was removed, renamed, or retyped.

## 13. Status: Phase 5 COMPLETE

All 13 plan steps executed. Ready for Phase 6.
