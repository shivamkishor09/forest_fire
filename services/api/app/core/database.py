"""Database connection and session factory configuration."""

from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from .config import settings
from .logging import logger

import time

Base = declarative_base()

# Configure engine (with short connect timeout so local dev without Postgres does not block)
try:
    connect_args = {}
    if "postgresql" in settings.DATABASE_URL:
        connect_args["connect_timeout"] = 1

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=False,
        connect_args=connect_args,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"Could not initialize database engine: {e}")
    engine = None
    SessionLocal = None


def get_db() -> Generator[Optional[Session], None, None]:
    """Dependency for yielding database session in API routes."""
    if SessionLocal is None or check_db_connection() != "connected":
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_cached_db_status: Optional[str] = None
_cached_db_time: float = 0.0


def check_db_connection() -> str:
    """Check connectivity to PostgreSQL database with fast socket pre-probe and caching."""
    global _cached_db_status, _cached_db_time
    now = time.time()
    if _cached_db_status is not None and (now - _cached_db_time) < 30.0:
        return _cached_db_status

    if engine is None:
        _cached_db_status = "not_configured"
        _cached_db_time = now
        return _cached_db_status

    import socket
    try:
        host = settings.POSTGRES_HOST if settings.POSTGRES_HOST not in ("postgres", "") else "127.0.0.1"
        port = int(settings.POSTGRES_PORT or 5432)
        with socket.create_connection((host, port), timeout=0.1):
            pass
    except Exception:
        _cached_db_status = "unreachable"
        _cached_db_time = now
        return _cached_db_status

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _cached_db_status = "connected"
    except Exception as e:
        logger.debug(f"Database health check failed: {e}")
        _cached_db_status = "unreachable"

    _cached_db_time = now
    return _cached_db_status


