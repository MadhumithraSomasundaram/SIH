-- =============================================================================
-- Phase 13 — PostgreSQL + PostGIS Indexes
-- Problem Statement ID 26184: Cybercrime Predictive Analytics Framework
-- =============================================================================

-- 1. Spatial GIST Index on cybercrime_events location geometry
CREATE INDEX IF NOT EXISTS idx_cybercrime_events_location 
ON cybercrime_events 
USING GIST (location);

-- 2. B-Tree Indexes on cybercrime_events query filters
CREATE INDEX IF NOT EXISTS idx_cybercrime_events_timestamp 
ON cybercrime_events (complaint_timestamp);

CREATE INDEX IF NOT EXISTS idx_cybercrime_events_crime_type 
ON cybercrime_events (crime_type);

CREATE INDEX IF NOT EXISTS idx_cybercrime_events_district 
ON cybercrime_events (victim_district);

CREATE INDEX IF NOT EXISTS idx_cybercrime_events_composite 
ON cybercrime_events (victim_district, complaint_timestamp);

-- 3. Spatial GIST Index on prediction_results location geometry
CREATE INDEX IF NOT EXISTS idx_prediction_results_location 
ON prediction_results 
USING GIST (location);

-- 4. B-Tree Indexes on prediction_results operational queries
CREATE INDEX IF NOT EXISTS idx_prediction_results_reference 
ON prediction_results (prediction_reference);

CREATE INDEX IF NOT EXISTS idx_prediction_results_timestamp 
ON prediction_results (prediction_timestamp);

CREATE INDEX IF NOT EXISTS idx_prediction_results_category 
ON prediction_results (risk_category);

CREATE INDEX IF NOT EXISTS idx_prediction_results_district_score 
ON prediction_results (victim_district, risk_score);
