from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.core.middleware import SecurityHeadersMiddleware
from app.routers import health, ledger, system, webhooks, websocket

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.validate_for_runtime()
    logger.info(
        "starting_up",
        app=settings.app_name,
        environment=settings.environment,
    )
    if settings.environment == "development":
        init_db()
    yield
    logger.info("shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="High-throughput webhook ingestion & real-time ledger reconciliation",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(SecurityHeadersMiddleware)

    application.include_router(health.router)
    application.include_router(webhooks.router)
    application.include_router(websocket.router)
    application.include_router(ledger.router)
    application.include_router(system.router)

    return application


app = create_app()
