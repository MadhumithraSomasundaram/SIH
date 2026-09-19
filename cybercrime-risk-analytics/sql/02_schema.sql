-- =============================================================================
-- Phase 13 — PostgreSQL + PostGIS Table Schema
-- Problem Statement ID 26184: Cybercrime Predictive Analytics Framework
-- =============================================================================

-- Table 1: Core Cybercrime Complaint Events
CREATE TABLE IF NOT EXISTS cybercrime_events (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(64) UNIQUE NOT NULL,
    complaint_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    crime_type VARCHAR(64) NOT NULL,
    fraud_amount DOUBLE PRECISION NOT NULL,
    reported_by_authority INTEGER DEFAULT 0,
    victim_state VARCHAR(64),
    victim_district VARCHAR(64),
    victim_area VARCHAR(128),
    victim_area_id VARCHAR(64),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOMETRY(Point, 4326),
    is_linked_to_withdrawal INTEGER DEFAULT 0,
    future_withdrawal INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);

-- Table 2: Model Inference & Operational Predictions
CREATE TABLE IF NOT EXISTS prediction_results (
    id SERIAL PRIMARY KEY,
    prediction_reference VARCHAR(64) NOT NULL,
    prediction_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    predicted_probability DOUBLE PRECISION NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_category VARCHAR(32) NOT NULL,
    operational_interpretation TEXT,
    model_version VARCHAR(64) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOMETRY(Point, 4326),
    victim_district VARCHAR(64),
    crime_type VARCHAR(64),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
);
