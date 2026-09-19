"""
Database Connection and Session Management
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)
"""
import logging
import os
from pathlib import Path
from typing import Generator, Dict, Any, Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("cybercrime_api.database")

# Load environment variables from .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Read DATABASE_URL or discrete connection parameters from environment
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
elif DB_USER or DB_HOST or DB_NAME:
    user = DB_USER or "postgres"
    pwd = f":{DB_PASSWORD}" if DB_PASSWORD else ""
    host = DB_HOST or "localhost"
    port = DB_PORT or "5432"
    dbname = DB_NAME or "cybercrime_prediction"
    DATABASE_URL = f"postgresql+psycopg://{user}{pwd}@{host}:{port}/{dbname}"
else:
    DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/cybercrime_prediction"

# Connection pool settings
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "2"))

# Check if SQLite is being used for testing or fallback
is_sqlite = DATABASE_URL.startswith("sqlite")

engine_args: Dict[str, Any] = {
    "echo": False,
    "future": True,
}

if not is_sqlite:
    engine_args.update({
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_timeout": POOL_TIMEOUT,
        "pool_recycle": POOL_RECYCLE,
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": DB_CONNECT_TIMEOUT},
    })

try:
    engine = create_engine(DATABASE_URL, **engine_args)
except Exception as e:
    logger.error(f"Failed to initialize SQLAlchemy engine: {e}")
    # Fallback to in-memory SQLite if engine creation fails outright
    engine = create_engine("sqlite:///:memory:", echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_sanitized_db_info() -> tuple[str, str]:
    """Extract host and database name safely without exposing credentials."""
    try:
        from sqlalchemy.engine.url import make_url
        url = make_url(DATABASE_URL)
        host_str = url.host or "localhost"
        if url.port:
            host_str = f"{host_str}:{url.port}"
        return host_str, url.database or "cybercrime_prediction"
    except Exception:
        return "localhost:5432", "cybercrime_prediction"


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI request-scoped database session dependency.
    Safely opens, yields, and closes session on completion or error.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction rolled back due to error: {e}")
        raise
    finally:
        db.close()


def check_database_health() -> Dict[str, Any]:
    """
    Check connectivity to the database and verify PostGIS extension status.
    Never exposes passwords, connection strings, or internal paths.
    Returns storage_mode ('POSTGRESQL_POSTGIS' or 'CSV_FALLBACK_DEV')
    and actionable setup instructions when disconnected.
    """
    safe_host, safe_dbname = get_sanitized_db_info()
    try:
        with engine.connect() as conn:
            # 1. Test basic connectivity
            conn.execute(text("SELECT 1"))
            
            # 2. Check PostGIS extension
            postgis_installed = False
            postgis_version = None
            try:
                res = conn.execute(text("SELECT PostGIS_Version()")).scalar()
                if res:
                    postgis_installed = True
                    postgis_version = str(res)
            except Exception:
                # Check pg_extension table if function call fails
                try:
                    ext_res = conn.execute(
                        text("SELECT extname, extversion FROM pg_extension WHERE extname = 'postgis'")
                    ).fetchone()
                    if ext_res:
                        postgis_installed = True
                        postgis_version = str(ext_res[1])
                except Exception:
                    postgis_installed = False

            return {
                "status": "connected",
                "database": "connected",
                "storage_mode": "POSTGRESQL_POSTGIS",
                "database_host": safe_host,
                "database_name": safe_dbname,
                "postgis": postgis_installed,
                "postgis_version": postgis_version,
                "error": None,
                "setup_instructions": None,
            }
    except SQLAlchemyError as exc:
        logger.warning(f"Database health check failed: {type(exc).__name__}")
        return {
            "status": "disconnected",
            "database": "disconnected",
            "storage_mode": "CSV_FALLBACK_DEV",
            "database_host": safe_host,
            "database_name": safe_dbname,
            "postgis": False,
            "postgis_version": None,
            "error": "Database connection unavailable. System operating in CSV_FALLBACK_DEV mode.",
            "setup_instructions": "To enable primary PostgreSQL+PostGIS storage, start PostgreSQL service and refer to DATABASE_SETUP.md.",
        }
    except Exception as exc:
        logger.warning(f"Unexpected error during database health check: {type(exc).__name__}")
        return {
            "status": "error",
            "database": "error",
            "storage_mode": "CSV_FALLBACK_DEV",
            "database_host": safe_host,
            "database_name": safe_dbname,
            "postgis": False,
            "postgis_version": None,
            "error": "Unexpected database error.",
            "setup_instructions": "Verify database service and connection parameters. See DATABASE_SETUP.md.",
        }
