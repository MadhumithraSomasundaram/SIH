-- =============================================================================
-- Phase 13 — PostgreSQL + PostGIS Extension Setup
-- Problem Statement ID 26184: Cybercrime Predictive Analytics Framework
-- =============================================================================

-- Enable PostGIS spatial extension (requires superuser or database owner permissions)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify extension version
SELECT postgis_full_version();
