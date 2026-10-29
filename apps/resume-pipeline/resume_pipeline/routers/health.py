"""Health (RG-004).

The one route that does not require the service token, because a liveness probe that needs a
credential is a probe that reports "unhealthy" the day the credential rotates.

It reports `degraded`, not a 5xx, when Postgres is unreachable: the process is up and answering,
and a supervisor that restarts on a 500 would restart it pointlessly while the database is the
thing that is down.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

import structlog
from fastapi import APIRouter

from resume_pipeline.db import connection
from resume_pipeline.schemas.common import HealthStatus

router = APIRouter(tags=["health"])

log = structlog.get_logger(__name__)

FALLBACK_VERSION = "0.1.0"


def service_version() -> str:
    try:
        return package_version("resume-pipeline")
    except PackageNotFoundError:
        return FALLBACK_VERSION


async def database_state() -> str:
    try:
        async with connection() as conn:
            await conn.fetchval("select 1")
        return "ok"
    except Exception:
        # The reason is logged, never returned: a connection error message carries the DSN.
        log.warning("health.db_unreachable")
        return "degraded"


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    db = await database_state()
    return HealthStatus(status="ok" if db == "ok" else "degraded", version=service_version(), db=db)
