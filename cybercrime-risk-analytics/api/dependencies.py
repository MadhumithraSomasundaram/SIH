"""
Phase 12 — API Dependency Injection / Application State
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Loads the XGBoost model, preprocessor, feature schema, and metadata ONCE
at application startup. Exposes a singleton AppState that all endpoints share.

STRICT BOUNDARY:
- No retraining
- No preprocessor refitting
- Failure to load any critical artifact → application fails at startup (not silently)
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths (resolve relative to project root — two levels above this file)
# ---------------------------------------------------------------------------
_API_DIR = Path(__file__).resolve().parent
BASE_DIR = _API_DIR.parent
MODELS_DIR = BASE_DIR / "models"
PROC_DIR = BASE_DIR / "data" / "processed"


# ---------------------------------------------------------------------------
# Singleton application state
# ---------------------------------------------------------------------------
@dataclass
class AppState:
    """
    Holds all model artifacts loaded at startup.
    All fields are read-only after initialization.
    """
    pipeline: Any = None                    # sklearn Pipeline (preprocessor + XGBClassifier)
    preprocessor: Any = None               # TRAIN-fitted ColumnTransformer (frozen)
    metadata: Dict[str, Any] = field(default_factory=dict)
    feature_schema: List[str] = field(default_factory=list)
    model_version: str = "unknown"
    model_loaded: bool = False
    pipeline_loaded: bool = False
    load_error: Optional[str] = None


# Module-level singleton — populated by lifespan startup in main.py
app_state = AppState()


# ---------------------------------------------------------------------------
# Loader functions (called once during lifespan startup)
# ---------------------------------------------------------------------------
def _load_pipeline() -> Any:
    """Load the serialized sklearn Pipeline from disk."""
    model_path = MODELS_DIR / "xgboost_cybercrime_model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"XGBoost model artifact not found at '{model_path}'. "
            "Ensure Phase 7 training has been completed."
        )
    pipeline = joblib.load(model_path)
    log.info("Loaded XGBoost pipeline from %s", model_path)
    return pipeline


def _load_metadata() -> Dict[str, Any]:
    """Load training metadata JSON from disk."""
    meta_path = MODELS_DIR / "phase7_xgboost_metadata.json"
    if not meta_path.exists():
        log.warning("Metadata file not found at %s — using empty metadata.", meta_path)
        return {}
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    log.info("Loaded model metadata (%d keys)", len(meta))
    return meta


def _load_feature_schema(metadata: Dict[str, Any]) -> List[str]:
    """
    Returns the ordered list of 64 predictor feature names.
    Primary source: metadata['selected_features'].
    Fallback: train.csv column names (minus target & case_id).
    """
    features = metadata.get("selected_features", [])
    if features:
        log.info("Feature schema loaded from metadata (%d features).", len(features))
        return features

    # Fallback
    train_path = PROC_DIR / "train.csv"
    if train_path.exists():
        import pandas as pd
        tdf = pd.read_csv(train_path, nrows=2)
        features = [c for c in tdf.columns if c not in ("case_id", "future_withdrawal")]
        log.warning(
            "Feature schema loaded from train.csv fallback (%d features).", len(features)
        )
        return features

    raise RuntimeError(
        "Cannot determine feature schema: 'selected_features' missing from metadata "
        "and train.csv not found."
    )


def _derive_model_version(pipeline: Any, metadata: Dict[str, Any]) -> str:
    """Produce a deterministic version string from metadata + model params."""
    import hashlib
    gen_time = metadata.get("generated_at", "2026-09-15T00:00:00Z")
    try:
        clf = pipeline.named_steps["classifier"]
        params = str(clf.get_params())
    except Exception:
        params = "unknown"
    h = hashlib.sha256(f"{gen_time}_{params}".encode("utf-8")).hexdigest()[:8]
    return f"v1.0.0-xgb-{h}"


# ---------------------------------------------------------------------------
# Primary startup initializer — called from main.py lifespan
# ---------------------------------------------------------------------------
def initialize_model_state() -> None:
    """
    Load all artifacts into app_state singleton.
    Raises on critical failure so the application refuses to start with a broken model.
    """
    global app_state
    log.info("=" * 60)
    log.info("PHASE 12 — Initializing model artifacts at startup")
    log.info("=" * 60)

    try:
        pipeline = _load_pipeline()
        app_state.pipeline = pipeline
        app_state.model_loaded = True
    except Exception as exc:
        app_state.load_error = str(exc)
        log.error("CRITICAL: Failed to load XGBoost pipeline — %s", exc)
        raise  # Propagate so uvicorn startup fails loudly

    try:
        app_state.preprocessor = pipeline.named_steps["preprocessor"]
        app_state.pipeline_loaded = True
        log.info("Preprocessor (ColumnTransformer) extracted successfully.")
    except KeyError as exc:
        app_state.load_error = f"Pipeline missing 'preprocessor' step: {exc}"
        log.error(app_state.load_error)
        raise RuntimeError(app_state.load_error)

    try:
        app_state.metadata = _load_metadata()
        app_state.feature_schema = _load_feature_schema(app_state.metadata)
        app_state.model_version = _derive_model_version(pipeline, app_state.metadata)
        log.info(
            "Model version: %s | Features: %d",
            app_state.model_version,
            len(app_state.feature_schema),
        )
    except Exception as exc:
        app_state.load_error = str(exc)
        log.error("CRITICAL: Failed to load metadata/schema — %s", exc)
        raise

    log.info("=" * 60)
    log.info("Model artifacts loaded successfully. API is ready.")
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# FastAPI dependency — injected into endpoints
# ---------------------------------------------------------------------------
def get_app_state() -> AppState:
    """FastAPI dependency: returns the shared application state."""
    return app_state
