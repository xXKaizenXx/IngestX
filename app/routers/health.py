from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlmodel import text

from app.core.database import engine
from app.services.queue import get_redis_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    return {"status": "ok"}


@router.get("/ready")
async def readiness():
    checks: dict[str, str] = {"api": "ok", "database": "unknown", "redis": "unknown"}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "error"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks, "detail": str(exc)},
        )

    try:
        get_redis_connection().ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = "error"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks, "detail": str(exc)},
        )

    return {"status": "ready", "checks": checks}
