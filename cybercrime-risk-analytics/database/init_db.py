"""
Database Initialization Script — PostgreSQL + PostGIS Schema & Indexes
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
Usage:
    python database/init_db.py
"""
import sys
import logging
from sqlalchemy import text
from database.connection import engine, Base, check_database_health
import database.models  # Ensure models are registered on Base
import database.investigation_models  # Ensure Phase 11/17 models are registered on Base


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_db")


def initialize_database() -> bool:
    """
    Initialize PostgreSQL database:
    1. Test connection
    2. Check / Enable PostGIS extension
    3. Create all tables defined in Base.metadata
    4. Create spatial GIST indexes and B-Tree indexes
    """
    logger.info("=" * 60)
    logger.info("Initializing Cybercrime Predictive Analytics Database")
    logger.info("=" * 60)

    # 1. Check database connectivity
    health = check_database_health()
    if health["status"] != "connected":
        logger.error("FATAL: Cannot connect to database server.")
        logger.error(f"Details: {health.get('error')}")
        logger.error("Please ensure PostgreSQL is running and DATABASE_URL is set in .env")
        return False

    logger.info("Database connection: SUCCESS (PostgreSQL reachable)")

    # 2. Check / Create PostGIS extension
    with engine.connect() as conn:
        logger.info("Checking PostGIS extension...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
            logger.info(f"PostGIS extension active: version {postgis_ver}")
        except Exception as e:
            logger.warning(f"Could not enable PostGIS extension via SQL: {e}")
            logger.warning("Ensure the database user has superuser privileges or PostGIS is pre-installed.")

    # 3. Create Tables via SQLAlchemy metadata
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base tables created successfully:")
        for tbl in Base.metadata.tables.keys():
            logger.info(f"  - {tbl}")
    except Exception as e:
        logger.error(f"Failed to create tables via SQLAlchemy: {e}")
        return False

    # 4. Create explicitly named PostGIS GIST and B-tree indexes
    logger.info("Applying additional SQL indexes...")
    index_sqls = [
        "CREATE INDEX IF NOT EXISTS idx_cybercrime_events_location ON cybercrime_events USING GIST (location);",
        "CREATE INDEX IF NOT EXISTS idx_cybercrime_events_timestamp ON cybercrime_events (complaint_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_cybercrime_events_crime_type ON cybercrime_events (crime_type);",
        "CREATE INDEX IF NOT EXISTS idx_cybercrime_events_district ON cybercrime_events (victim_district);",
        "CREATE INDEX IF NOT EXISTS idx_prediction_results_location ON prediction_results USING GIST (location);",
        "CREATE INDEX IF NOT EXISTS idx_prediction_results_timestamp ON prediction_results (prediction_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_prediction_results_category ON prediction_results (risk_category);",
    ]

    with engine.connect() as conn:
        for sql in index_sqls:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                # Some databases (e.g. SQLite without SpatiaLite) won't support GIST
                logger.warning(f"Index execution notice for [{sql.split()[4] if len(sql.split()) > 4 else sql}]: {e}")

    logger.info("=" * 60)
    logger.info("Database Initialization COMPLETE")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    success = initialize_database()
    if not success:
        sys.exit(1)
