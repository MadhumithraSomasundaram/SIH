"""
Phase 12 — FastAPI Application
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Production-ready REST API wrapping the Phase 11 XGBoost inference pipeline.

Endpoints:
  GET  /                   — Service banner
  GET  /health             — Model health check
  GET  /model/info         — Safe model metadata
  POST /predict            — Single-record prediction
  POST /predict/batch      — Batch prediction (max 100 records)
  POST /explain            — Prediction + SHAP explanation

Usage:
  uvicorn api.main:app --reload

Swagger: http://127.0.0.1:8000/docs
ReDoc  : http://127.0.0.1:8000/redoc

STRICT PHASE BOUNDARY:
- No model retraining
- No preprocessing refitting
- No DBSCAN / GIS / frontend / alerts / live banking integration
- No stack traces or sensitive data in responses
"""

from __future__ import annotations

import csv
import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

# ---------------------------------------------------------------------------
# Path bootstrap — ensure project root is on sys.path so src.predict is importable
# ---------------------------------------------------------------------------
_API_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _API_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from api.dependencies import AppState, app_state, get_app_state, initialize_model_state
from api.auth import require_api_key
from api.error_handlers import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    value_error_handler,
)
from api.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    ExplainResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
    RootResponse,
    ShapContribution,
)

# Database integration (Phase 13)
import os
from sqlalchemy.orm import Session
from database.connection import get_db, check_database_health, SessionLocal
from database.crud import get_database_stats, create_prediction_result
from database.schemas import DatabaseHealthResponse, DatabaseStatsResponse, PredictionResultCreate

# Import Phase 11 inference functions
from src.predict import (
    assign_risk_category,
    explain_prediction,
    generate_interpretation,
    predict_new_records,
    predict_single_record,
    probability_to_risk_score,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("api.main")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTPUTS_DIR = _PROJECT_ROOT / "outputs"
PRED_LOG_DIR = OUTPUTS_DIR / "predictions"
for _d in [OUTPUTS_DIR, PRED_LOG_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

API_LOG_CSV = PRED_LOG_DIR / "api_prediction_log.csv"
API_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Prediction reference counter (thread-safe via GIL for single-worker dev use)
# ---------------------------------------------------------------------------
_pred_counter = 0


def _next_prediction_reference() -> str:
    """Generate a sequential, non-sensitive prediction reference."""
    global _pred_counter
    _pred_counter += 1
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"PRED-{today}-{_pred_counter:06d}"


# ---------------------------------------------------------------------------
# Lifespan — model loaded ONCE at startup, never per-request
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Model artifacts are loaded here and stored in the module-level app_state singleton.
    If loading fails the application refuses to start.
    """
    try:
        initialize_model_state()
        log.info("Lifespan startup: model artifacts ready.")
    except Exception as exc:
        log.critical("FATAL: Could not initialize model artifacts — %s", exc)
        raise  # Fail loudly — do NOT silently serve a broken API

    # Startup database connection & storage mode check
    try:
        db_health = check_database_health()
        if db_health.get("database") == "connected":
            log.info(
                "Lifespan startup: Database connected (storage_mode=%s, postgis=%s, host=%s)",
                db_health.get("storage_mode"),
                db_health.get("postgis"),
                db_health.get("database_host"),
            )
        else:
            log.warning(
                "Lifespan startup: Database unreachable; operating in fallback mode (storage_mode=%s). See DATABASE_SETUP.md.",
                db_health.get("storage_mode"),
            )
    except Exception as exc:
        log.warning("Lifespan startup: Database check encountered error: %s", exc)

    yield
    log.info("Lifespan shutdown: releasing resources.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Cybercrime Predictive Analytics API",
    description=(
        "REST API for predictive cybercrime withdrawal risk analysis.\n\n"
        "**Problem Statement ID 26184** — "
        "Development of a Predictive Analytics Framework for Cybercrime Complaints "
        "to Forecast Likely Cash Withdrawal Locations in Advance.\n\n"
        "---\n\n"
        "**Disclaimer:** This API provides predictive risk signals for **authorized analytical "
        "use only**. Predictions are **not proof of criminal activity** and require human "
        "review before any operational action.\n\n"
        "**Limitations:**\n"
        "- Model uses historical/anonymized data\n"
        "- Prediction horizon: 24 hours\n"
        "- Prediction quality depends on training data coverage\n"
        "- Model may experience temporal/geographic drift\n"
        "- Not a live banking or ATM integration system\n"
        "- No automatic law-enforcement action\n"
        "- All predictions require authorized human review\n"
    ),
    version=API_VERSION,
    contact={
        "name": "Cybercrime Analytics Team",
        "url": "http://127.0.0.1:8000/docs",
    },
    license_info={"name": "For authorized use only"},
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ---------------------------------------------------------------------------
# CORS — localhost only; wildcard with credentials is never used
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization", "X-API-Key"],
)


# ---------------------------------------------------------------------------
# Safe prediction logging (no sensitive fields)
# ---------------------------------------------------------------------------
def _log_prediction_to_csv(
    prediction_reference: str,
    endpoint: str,
    risk_score: int,
    risk_category: str,
    predicted_probability: float,
    model_version: str,
    latency_ms: float,
) -> None:
    """Append a single safe prediction log row to outputs/predictions/api_prediction_log.csv."""
    now_utc = datetime.now(timezone.utc).isoformat()
    row = {
        "prediction_timestamp": now_utc,
        "prediction_reference": prediction_reference,
        "endpoint": endpoint,
        "risk_score": risk_score,
        "risk_category": risk_category,
        "predicted_probability": round(predicted_probability, 6),
        "model_version": model_version,
        "latency_ms": round(latency_ms, 2),
    }
    write_header = not API_LOG_CSV.exists()
    with open(API_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Helper — convert PredictionRequest → dict for Phase 11 pipeline
# ---------------------------------------------------------------------------
def _request_to_dict(req: PredictionRequest) -> Dict[str, Any]:
    """
    Convert Pydantic request model to a plain dictionary.
    Excludes complaint_timestamp (context field, not a model feature) and None values
    are passed through — the preprocessor handles missing values via median imputation.
    """
    return req.model_dump(exclude={"complaint_timestamp"})


# ===========================================================================
# ENDPOINTS
# ===========================================================================

# ---------------------------------------------------------------------------
# GET /  — Service banner
# ---------------------------------------------------------------------------
@app.get(
    "/",
    response_model=RootResponse,
    summary="Service Banner",
    description="Returns a brief service identification banner.",
    tags=["Status"],
)
async def root():
    return RootResponse(
        service="Cybercrime Predictive Analytics API",
        status="running",
        version=API_VERSION,
        docs="http://127.0.0.1:8000/docs",
        disclaimer=(
            "Predictions are risk signals for authorized analytical use only. "
            "Not proof of criminal activity."
        ),
    )


# ---------------------------------------------------------------------------
# GET /health  — Health check
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Returns the health status of the API and whether the XGBoost model and "
        "preprocessing pipeline were loaded successfully at startup."
    ),
    tags=["Status"],
)
async def health(state: AppState = Depends(get_app_state)):
    is_healthy = state.model_loaded and state.pipeline_loaded
    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        model_loaded=state.model_loaded,
        prediction_pipeline_loaded=state.pipeline_loaded,
        model_version=state.model_version if is_healthy else None,
    )


# ---------------------------------------------------------------------------
# GET /model/info  — Safe model metadata
# ---------------------------------------------------------------------------
@app.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="Model Information",
    description=(
        "Returns safe model metadata. Never exposes training data, credentials, "
        "file paths, account numbers, or any personally identifiable information."
    ),
    tags=["Model"],
)
async def model_info(state: AppState = Depends(get_app_state)):
    if not state.model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. The service is unavailable.",
        )
    meta = state.metadata
    training_date = meta.get("generated_at", "")[:10] if meta.get("generated_at") else None

    return ModelInfoResponse(
        model_type="XGBoost Classifier (sklearn Pipeline)",
        model_version=state.model_version,
        prediction_target="future_withdrawal",
        prediction_horizon="24 hours",
        feature_count=len(state.feature_schema),
        risk_score_range="0–100",
        risk_categories=["LOW", "MODERATE", "HIGH", "CRITICAL"],
        training_date=training_date,
        limitations=[
            "Model uses historical/anonymized training data.",
            "Prediction horizon is 24 hours.",
            "Prediction quality depends on completeness and accuracy of input features.",
            "Model may experience temporal or geographic drift over time.",
            "Not connected to live banking, ATM, or government systems.",
            "No automatic law-enforcement actions are triggered.",
            "All predictions require authorized human review before operational use.",
            "Risk score is not proof of criminal activity.",
        ],
    )


# ---------------------------------------------------------------------------
# POST /predict  — Single-record prediction
# ---------------------------------------------------------------------------
@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Single-Record Prediction",
    description=(
        "Submit one cybercrime complaint record and receive:\n"
        "- `predicted_probability`: P(future_withdrawal = 1) in [0.0, 1.0]\n"
        "- `risk_score`: round(probability × 100) in [0, 100]\n"
        "- `risk_category`: LOW | MODERATE | HIGH | CRITICAL\n"
        "- `operational_interpretation`: Analyst guidance\n\n"
        "**Prohibited fields** (will cause HTTP 400/422):\n"
        "`future_withdrawal`, `withdrawal_timestamp`, `withdrawal_amount`, "
        "`withdrawal_status`, `target_*`, `is_linked_to_withdrawal`\n\n"
        "**Sensitive fields** (will cause HTTP 400/422):\n"
        "`card_number`, `pin`, `otp`, `cvv`, `password`"
    ),
    tags=["Prediction"],
)
async def predict_single(
    request: PredictionRequest,
    state: AppState = Depends(get_app_state),
    _auth: str = Depends(require_api_key),
):
    if not state.model_loaded or not state.pipeline_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not available. Please contact the system administrator.",
        )

    t_start = time.perf_counter()
    pred_ref = _next_prediction_reference()

    record_dict = _request_to_dict(request)

    try:
        result = predict_single_record(record_dict, state.pipeline, state.metadata)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        log.exception("Prediction failure for reference %s", pred_ref)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during prediction. Please contact the administrator.",
        )

    latency_ms = (time.perf_counter() - t_start) * 1000

    # Log safe fields only
    _log_prediction_to_csv(
        prediction_reference=pred_ref,
        endpoint="/predict",
        risk_score=result["risk_score"],
        risk_category=result["risk_category"],
        predicted_probability=result["probability"],
        model_version=state.model_version,
        latency_ms=latency_ms,
    )

    log.info(
        "POST /predict | ref=%s | score=%d | cat=%s | latency=%.1fms",
        pred_ref, result["risk_score"], result["risk_category"], latency_ms,
    )

    # Optionally store prediction in PostgreSQL + PostGIS (Phase 13)
    if os.getenv("ENABLE_PREDICTION_STORAGE", "true").lower() == "true":
        try:
            health_check = check_database_health()
            if health_check["status"] == "connected":
                db_item = PredictionResultCreate(
                    prediction_reference=pred_ref,
                    prediction_timestamp=datetime.now(timezone.utc),
                    predicted_probability=result["probability"],
                    risk_score=result["risk_score"],
                    risk_category=result["risk_category"],
                    operational_interpretation=result["operational_interpretation"],
                    model_version=state.model_version,
                    latitude=record_dict.get("latitude"),
                    longitude=record_dict.get("longitude"),
                    victim_district=record_dict.get("victim_district"),
                    crime_type=record_dict.get("crime_type"),
                )
                with SessionLocal() as db_session:
                    create_prediction_result(db_session, db_item)
        except Exception as db_err:
            log.debug("Database prediction storage skipped: %s", db_err)

    return PredictionResponse(
        prediction_reference=pred_ref,
        predicted_probability=round(result["probability"], 6),
        risk_score=result["risk_score"],
        risk_category=result["risk_category"],
        operational_interpretation=result["operational_interpretation"],
        model_version=state.model_version,
    )


# ---------------------------------------------------------------------------
# POST /predict/batch  — Batch prediction (max 100 records)
# ---------------------------------------------------------------------------
@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Prediction",
    description=(
        "Submit up to 100 cybercrime complaint records and receive predictions for all of them.\n\n"
        "- Input order is preserved in the response.\n"
        "- Preprocessing is not refitted.\n"
        "- Each record is independently validated.\n"
        "- Maximum batch size: 100 records.\n\n"
        "**Request body**: `{ \"records\": [{...}, {...}] }`"
    ),
    tags=["Prediction"],
)
async def predict_batch(
    batch_request: BatchPredictionRequest,
    state: AppState = Depends(get_app_state),
    _auth: str = Depends(require_api_key),
):
    if not state.model_loaded or not state.pipeline_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not available. Please contact the system administrator.",
        )

    t_start = time.perf_counter()
    records_dicts = [_request_to_dict(r) for r in batch_request.records]

    try:
        input_df = pd.DataFrame(records_dicts)
        result_df, _, _ = predict_new_records(input_df, state.pipeline, state.metadata)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        log.exception("Batch prediction failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during batch prediction.",
        )

    latency_ms = (time.perf_counter() - t_start) * 1000
    predictions = []
    batch_date = datetime.now(timezone.utc).strftime("%Y%m%d")

    for i, row in result_df.iterrows():
        global _pred_counter
        _pred_counter += 1
        pred_ref = f"PRED-{batch_date}-{_pred_counter:06d}"

        pred_resp = PredictionResponse(
            prediction_reference=pred_ref,
            predicted_probability=round(float(row["predicted_probability"]), 6),
            risk_score=int(row["risk_score"]),
            risk_category=str(row["risk_category"]),
            operational_interpretation=str(row["operational_interpretation"]),
            model_version=state.model_version,
        )
        predictions.append(pred_resp)

        _log_prediction_to_csv(
            prediction_reference=pred_ref,
            endpoint="/predict/batch",
            risk_score=int(row["risk_score"]),
            risk_category=str(row["risk_category"]),
            predicted_probability=float(row["predicted_probability"]),
            model_version=state.model_version,
            latency_ms=round(latency_ms / len(result_df), 2),
        )

    log.info(
        "POST /predict/batch | count=%d | latency=%.1fms",
        len(predictions), latency_ms,
    )

    return BatchPredictionResponse(
        count=len(predictions),
        predictions=predictions,
        model_version=state.model_version,
    )


# ---------------------------------------------------------------------------
# POST /explain  — Prediction + SHAP explanation
# ---------------------------------------------------------------------------
@app.post(
    "/explain",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
    summary="Prediction with SHAP Explanation",
    description=(
        "Submit one record and receive the prediction **plus** SHAP feature attribution.\n\n"
        "SHAP values indicate each feature's contribution to the model's output for **this specific "
        "record**. They represent **association**, not causation or proof of criminal activity.\n\n"
        "If SHAP computation fails, the prediction is still returned with `shap_available: false`."
    ),
    tags=["Explainability"],
)
async def explain(
    request: PredictionRequest,
    state: AppState = Depends(get_app_state),
    _auth: str = Depends(require_api_key),
):
    if not state.model_loaded or not state.pipeline_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not available. Please contact the system administrator.",
        )

    t_start = time.perf_counter()
    pred_ref = _next_prediction_reference()
    record_dict = _request_to_dict(request)

    # Run baseline prediction first (never fails due to SHAP)
    try:
        base_result = predict_single_record(record_dict, state.pipeline, state.metadata)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception:
        log.exception("Prediction failure in /explain for ref %s", pred_ref)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during prediction.",
        )

    # Run SHAP (graceful degradation — never blocks prediction)
    try:
        shap_result = explain_prediction(record_dict, state.pipeline, state.metadata)
        shap_ok = shap_result.get("status") == "SUCCESS"
    except Exception as exc:
        log.warning("SHAP explanation failed for ref %s: %s", pred_ref, exc)
        shap_result = {
            "status": f"SHAP unavailable: {str(exc)[:120]}",
            "top_positive_contributors": [],
            "top_negative_contributors": [],
        }
        shap_ok = False

    latency_ms = (time.perf_counter() - t_start) * 1000

    _log_prediction_to_csv(
        prediction_reference=pred_ref,
        endpoint="/explain",
        risk_score=base_result["risk_score"],
        risk_category=base_result["risk_category"],
        predicted_probability=base_result["probability"],
        model_version=state.model_version,
        latency_ms=latency_ms,
    )

    log.info(
        "POST /explain | ref=%s | score=%d | shap_ok=%s | latency=%.1fms",
        pred_ref, base_result["risk_score"], shap_ok, latency_ms,
    )

    # Build SHAP contribution objects
    def _to_contrib(entries: List[Dict]) -> List[ShapContribution]:
        return [
            ShapContribution(
                rank=e["rank"],
                feature=e["feature"],
                shap_value=round(e["shap_value"], 6),
                direction=e["direction"],
                # Phase 5: populate feature_value
                feature_value=e.get("feature_value"),
            )
            for e in entries
        ]

    return ExplainResponse(
        # ---- Legacy fields ----
        prediction_reference=pred_ref,
        predicted_probability=round(base_result["probability"], 6),
        risk_score=base_result["risk_score"],
        risk_category=base_result["risk_category"],
        operational_interpretation=base_result["operational_interpretation"],
        shap_available=shap_ok,
        shap_status=shap_result.get("status", "SHAP explanation unavailable"),
        top_positive_contributors=_to_contrib(shap_result.get("top_positive_contributors", [])),
        top_negative_contributors=_to_contrib(shap_result.get("top_negative_contributors", [])),
        # ---- Phase 5 enriched fields ----
        prediction_id=shap_result.get("prediction_id"),
        model_version=shap_result.get("model_version", state.model_version),
        prediction_timestamp=shap_result.get("prediction_timestamp"),
        risk_level=shap_result.get("risk_level", base_result["risk_category"]),
        explanation_available=shap_ok,
        explanation_limitations=shap_result.get("explanation_limitations"),
    )


# ---------------------------------------------------------------------------
# GET /database/health — Database & PostGIS health check (Phase 13)
# ---------------------------------------------------------------------------
@app.get(
    "/database/health",
    response_model=DatabaseHealthResponse,
    summary="Database & PostGIS Health Check",
    description="Returns database connection status, active storage mode, and PostGIS availability. Returns HTTP 503 if unavailable.",
    tags=["Database"],
)
async def database_health():
    health = check_database_health()
    resp_obj = DatabaseHealthResponse(
        status=health.get("status"),
        database=health["database"],
        storage_mode=health.get("storage_mode", "POSTGRESQL_POSTGIS" if health["database"] == "connected" else "CSV_FALLBACK_DEV"),
        database_host=health.get("database_host"),
        database_name=health.get("database_name"),
        postgis=health["postgis"],
        postgis_version=health.get("postgis_version"),
        error=health.get("error"),
        setup_instructions=health.get("setup_instructions"),
    )
    if health["status"] != "connected":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=resp_obj.model_dump(),
        )
    return resp_obj


# ---------------------------------------------------------------------------
# GET /database/stats — Database aggregate statistics (Phase 13)
# ---------------------------------------------------------------------------
@app.get(
    "/database/stats",
    response_model=DatabaseStatsResponse,
    summary="Database Aggregate Statistics",
    description="Returns aggregate event counts, spatial coverage, and timestamps. Never exposes raw rows.",
    tags=["Database"],
)
async def database_stats(db: Session = Depends(get_db)):
    health = check_database_health()
    if health["status"] != "connected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable. Verify PostgreSQL service is running and DATABASE_URL is configured.",
        )
    try:
        stats_data = get_database_stats(db)
        return DatabaseStatsResponse(**stats_data)
    except Exception as exc:
        log.warning("Error fetching database statistics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database statistics query failed.",
        )


# ---------------------------------------------------------------------------
# Phase 15 — GIS Dashboard Router
# ---------------------------------------------------------------------------
from api.gis_routes import router as gis_router

app.include_router(gis_router)

# ---------------------------------------------------------------------------
# Phase 16 — Alert & Notification System Router
# ---------------------------------------------------------------------------
from api.alert_routes import router as alert_router

app.include_router(alert_router)

# ---------------------------------------------------------------------------
# Phase 17 — Analyst Interface Router
# ---------------------------------------------------------------------------
from api.analyst_routes import router as analyst_router

app.include_router(analyst_router)
log.info("Phase 17 analyst router registered at /analyst")

# ---------------------------------------------------------------------------
# Phase 15 — Serve dashboard static files at /dashboard
# ---------------------------------------------------------------------------
_DASHBOARD_DIR = _PROJECT_ROOT / "dashboard"
if _DASHBOARD_DIR.exists():
    app.mount(
        "/dashboard",
        StaticFiles(directory=str(_DASHBOARD_DIR), html=True),
        name="dashboard",
    )
    log.info("Dashboard mounted at /dashboard  (dir=%s)", _DASHBOARD_DIR)
else:
    log.warning(
        "Dashboard directory not found at %s — run Phase 15 setup to create it.",
        _DASHBOARD_DIR,
    )

# ---------------------------------------------------------------------------
# Phase 17 — Serve analyst interface static files at /analyst
# ---------------------------------------------------------------------------
_ANALYST_DIR = _PROJECT_ROOT / "analyst"
if _ANALYST_DIR.exists():
    app.mount(
        "/analyst",
        StaticFiles(directory=str(_ANALYST_DIR), html=True),
        name="analyst",
    )
    log.info("Analyst interface mounted at /analyst  (dir=%s)", _ANALYST_DIR)
else:
    log.warning(
        "Analyst directory not found at %s — run Phase 17 setup to create it.",
        _ANALYST_DIR,
    )

# ---------------------------------------------------------------------------
# Secure Banking Interface Router & Static Files (/bank)
# ---------------------------------------------------------------------------
from api.bank_routes import router as bank_router

app.include_router(bank_router)
log.info("Secure Banking router registered at /bank")

_BANK_DIR = _PROJECT_ROOT / "bank"
if _BANK_DIR.exists():
    app.mount(
        "/bank",
        StaticFiles(directory=str(_BANK_DIR), html=True),
        name="bank",
    )
    log.info("Secure Banking interface mounted at /bank  (dir=%s)", _BANK_DIR)
else:
    log.warning(
        "Bank directory not found at %s — create it to serve the banking interface.",
        _BANK_DIR,
    )

# ---------------------------------------------------------------------------
# Dynamic Complaint Submission Router (/complaints)
# ---------------------------------------------------------------------------
from api.complaint_routes import router as complaint_router

app.include_router(complaint_router)
log.info("Dynamic Complaint Submission router registered at /complaints")

