"""Celery distributed task queue application initialization."""

from celery import Celery
from .config import settings
from .logging import logger

celery_app = Celery(
    "forest_fire_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["services.api.app.tasks.simulation_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max simulation limit
    imports=["services.api.app.tasks.simulation_tasks"]
)
celery_app.autodiscover_tasks(["services.api.app.tasks"])


import time
from typing import Optional

_cached_celery_status: Optional[str] = None
_cached_celery_time: float = 0.0


def check_celery_broker() -> str:
    """Check connectivity to Redis broker with fast socket pre-probe and caching."""
    global _cached_celery_status, _cached_celery_time
    now = time.time()
    if _cached_celery_status is not None and (now - _cached_celery_time) < 30.0:
        return _cached_celery_status

    import socket
    try:
        host = settings.REDIS_HOST if settings.REDIS_HOST not in ("redis", "") else "127.0.0.1"
        port = int(settings.REDIS_PORT or 6379)
        with socket.create_connection((host, port), timeout=0.1):
            pass
    except Exception:
        _cached_celery_status = "unreachable"
        _cached_celery_time = now
        return _cached_celery_status

    try:
        import redis
        client = redis.from_url(settings.REDIS_URL, socket_timeout=0.2)
        client.ping()
        _cached_celery_status = "connected"
    except Exception as e:
        logger.debug(f"Redis/Celery broker check failed: {e}")
        _cached_celery_status = "unreachable"

    _cached_celery_time = now
    return _cached_celery_status


