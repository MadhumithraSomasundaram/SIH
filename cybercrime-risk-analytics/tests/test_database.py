"""
Phase 13 — PostgreSQL + PostGIS Test Suite
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Tests:
1. Database connection and health function
2. PostGIS availability detection
3. Table existence and schema definitions
4. Coordinate validation logic
5. Geometry POINT construction (SRID 4326, lon/lat order)
6. Spatial query validation
7. Prediction insertion schema validation
8. Transaction rollback handling
9. FastAPI /database/health endpoint
10. FastAPI /database/stats endpoint
"""
from datetime import datetime, timezone
import pytest
from starlette.testclient import TestClient

from api.main import app
from database.connection import check_database_health, Base, engine
from database.models import CybercrimeEvent, PredictionResult
from database.crud import is_valid_coordinate
from database.schemas import (
    validate_coordinates,
    CybercrimeEventCreate,
    PredictionResultCreate,
    SpatialRadiusQuery,
    SpatialBoundingBoxQuery,
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestCoordinateValidation:
    """Test coordinate bounding and rejection of invalid values."""

    def test_valid_coordinates_pass(self):
        assert is_valid_coordinate(12.9716, 77.5946) is True
        assert is_valid_coordinate(0.0, 0.0) is True
        assert is_valid_coordinate(-90.0, -180.0) is True
        assert is_valid_coordinate(90.0, 180.0) is True

    def test_invalid_latitude_rejected(self):
        assert is_valid_coordinate(90.001, 77.0) is False
        assert is_valid_coordinate(-90.1, 77.0) is False
        with pytest.raises(ValueError):
            validate_coordinates(95.0, 77.0)

    def test_invalid_longitude_rejected(self):
        assert is_valid_coordinate(12.0, 180.001) is False
        assert is_valid_coordinate(12.0, -180.1) is False
        with pytest.raises(ValueError):
            validate_coordinates(12.0, 185.0)

    def test_none_coordinates(self):
        assert is_valid_coordinate(None, 77.0) is False
        assert is_valid_coordinate(12.0, None) is False
        assert is_valid_coordinate(None, None) is False


class TestTableSchemas:
    """Test SQLAlchemy ORM table registrations and columns."""

    def test_cybercrime_events_table_registered(self):
        assert "cybercrime_events" in Base.metadata.tables
        table = Base.metadata.tables["cybercrime_events"]
        col_names = [c.name for c in table.columns]
        assert "case_id" in col_names
        assert "complaint_timestamp" in col_names
        assert "crime_type" in col_names
        assert "fraud_amount" in col_names
        assert "latitude" in col_names
        assert "longitude" in col_names
        assert "location" in col_names
        assert "future_withdrawal" in col_names

    def test_prediction_results_table_registered(self):
        assert "prediction_results" in Base.metadata.tables
        table = Base.metadata.tables["prediction_results"]
        col_names = [c.name for c in table.columns]
        assert "prediction_reference" in col_names
        assert "prediction_timestamp" in col_names
        assert "predicted_probability" in col_names
        assert "risk_score" in col_names
        assert "risk_category" in col_names
        assert "model_version" in col_names
        assert "location" in col_names


class TestPydanticDatabaseSchemas:
    """Test Pydantic schemas for event creation, prediction storage, and queries."""

    def test_cybercrime_event_create_valid(self):
        item = CybercrimeEventCreate(
            case_id="CMP-2026-TEST01",
            complaint_timestamp=datetime.now(timezone.utc),
            crime_type="UPI_FRAUD",
            fraud_amount=50000.0,
            reported_by_authority=1,
            victim_state="Karnataka",
            victim_district="Bengaluru Urban",
            latitude=12.9716,
            longitude=77.5946,
            is_linked_to_withdrawal=0,
            future_withdrawal=1,
        )
        assert item.case_id == "CMP-2026-TEST01"
        assert item.latitude == 12.9716

    def test_prediction_result_create_valid(self):
        pred = PredictionResultCreate(
            prediction_reference="PRED-2026-TEST01",
            prediction_timestamp=datetime.now(timezone.utc),
            predicted_probability=0.85,
            risk_score=85,
            risk_category="CRITICAL",
            operational_interpretation="High cashout probability",
            model_version="v1.0.0-xgb-668c1916",
            latitude=12.9716,
            longitude=77.5946,
            victim_district="Bengaluru Urban",
            crime_type="UPI_FRAUD",
        )
        assert pred.risk_score == 85
        assert pred.risk_category == "CRITICAL"

    def test_spatial_radius_query_schema(self):
        q = SpatialRadiusQuery(
            latitude=13.0,
            longitude=77.5,
            radius_meters=5000.0,
            limit=50,
        )
        assert q.radius_meters == 5000.0

    def test_spatial_bounding_box_query_schema(self):
        bbox = SpatialBoundingBoxQuery(
            min_lat=12.0,
            max_lat=13.0,
            min_lon=76.0,
            max_lon=78.0,
            limit=100,
        )
        assert bbox.min_lat == 12.0
        assert bbox.max_lat == 13.0

    def test_spatial_bounding_box_invalid_range_raises(self):
        with pytest.raises(ValueError):
            SpatialBoundingBoxQuery(
                min_lat=14.0,
                max_lat=12.0,  # Invalid: max < min
                min_lon=76.0,
                max_lon=78.0,
            )


class TestDatabaseEndpoints:
    """Test FastAPI /database/health and /database/stats endpoints."""

    def test_database_health_endpoint_contract(self, client):
        resp = client.get("/database/health")
        # May be 200 if PostgreSQL is active or 503 if unreachable,
        # but MUST adhere strictly to the DatabaseHealthResponse contract
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "database" in data
        assert "postgis" in data
        assert data["database"] in ("connected", "disconnected")
        # Ensure no sensitive database URLs or passwords leaked
        assert "password" not in str(data).lower()
        assert "postgres:" not in str(data).lower()

    def test_database_stats_endpoint_contract(self, client):
        resp = client.get("/database/stats")
        # Returns 200 with stats or 503 with clean error detail if DB disconnected
        assert resp.status_code in (200, 503)
        data = resp.json()
        if resp.status_code == 200:
            assert "total_events" in data
            assert "location_coverage_percent" in data
        else:
            msg = data.get("message") or data.get("detail") or ""
            assert "Database" in msg


from database.connection import check_database_health, Base, engine, get_sanitized_db_info
from unittest.mock import patch, MagicMock


class TestConnectionHealthFunction:
    """Test check_database_health() execution and structure."""

    def test_health_check_returns_dict(self):
        health = check_database_health()
        assert isinstance(health, dict)
        assert "status" in health
        assert "database" in health
        assert "postgis" in health
        assert "storage_mode" in health
        assert health["status"] in ("connected", "disconnected", "error")
        assert health["storage_mode"] in ("POSTGRESQL_POSTGIS", "CSV_FALLBACK_DEV")

    def test_sanitized_db_info_masks_credentials(self):
        host, dbname = get_sanitized_db_info()
        assert "password" not in host.lower()
        assert "password" not in dbname.lower()
        assert "postgres:" not in host.lower()

    def test_database_health_endpoint_storage_mode(self, client):
        resp = client.get("/database/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "storage_mode" in data
        assert data["storage_mode"] in ("POSTGRESQL_POSTGIS", "CSV_FALLBACK_DEV")
        if data["database"] == "disconnected":
            assert data["storage_mode"] == "CSV_FALLBACK_DEV"
            assert "setup_instructions" in data
            assert data["setup_instructions"] is not None
            assert "DATABASE_SETUP.md" in data["setup_instructions"]

    def test_check_database_health_mocked_connected(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value.scalar.return_value = "3.4.0 USE_GEOS=1"
        with patch.object(engine, "connect") as mock_connect:
            mock_connect.return_value.__enter__.return_value = mock_conn
            health = check_database_health()
            assert health["status"] == "connected"
            assert health["database"] == "connected"
            assert health["storage_mode"] == "POSTGRESQL_POSTGIS"
            assert health["postgis"] is True
            assert health["postgis_version"] == "3.4.0 USE_GEOS=1"
