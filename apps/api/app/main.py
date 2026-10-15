"""
FastAPI Application Entry Point
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.credential_sanitizer import CredentialSanitizer
from app.core.db import AsyncSessionLocal
from app.core.logging import logger
from app.modules.agents.agents_routes import router as agents_router
from app.modules.agents.agents_services import AgentService
from app.modules.evaluation.evaluation_routes import router as evaluation_router
from app.modules.execution.execution_routes import execution_router
from app.modules.metadata.metadata_routes import router as metadata_router
from app.modules.migration_plans.migration_plans_routes import router as migration_plans_router
from app.modules.observability.health_service import SystemHealthService
from app.modules.observability.observability_routes import router as observability_router
from app.modules.sources.sources_routes import router as sources_router
from app.modules.users.users_routes import router as users_router

# Import all domain models to ensure SQLAlchemy mappers are registered
import app.modules.agents.agents_models  # noqa: F401
import app.modules.evaluation.evaluation_models  # noqa: F401
import app.modules.execution.execution_models  # noqa: F401
import app.modules.metadata.metadata_models  # noqa: F401
import app.modules.observability.observability_models  # noqa: F401
import app.modules.sources.sources_models  # noqa: F401
import app.modules.migration_plans.migration_plans_models  # noqa: F401
import app.modules.users.users_models  # noqa: F401



async def stale_agent_watchdog():
    """Background periodic loop that detects timed-out agents and recovers orphaned migration jobs."""
    while True:
        try:
            await asyncio.sleep(20)
            async with AsyncSessionLocal() as session:
                try:
                    await AgentService.check_stale_agents_and_jobs(
                        session, stale_threshold_seconds=60
                    )
                except Exception as exc:
                    logger.warning(f"Error in stale agent watchdog run: {exc}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Unexpected error in stale watchdog loop: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern application lifespan context manager managing background tasks & cleanup."""
    logger.info(f"Starting {settings.PROJECT_NAME} in environment: {settings.ENVIRONMENT}")
    try:
        from app.core.db import engine, Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized and verified.")
    except Exception as exc:
        logger.warning(f"Startup table verification note: {exc}")

    watchdog_task = asyncio.create_task(stale_agent_watchdog())
    try:
        yield
    finally:
        watchdog_task.cancel()
        try:
            await watchdog_task
        except asyncio.CancelledError:
            pass
        try:
            from app.core.redis_client import close_redis_client
            await close_redis_client()
        except Exception as exc:
            logger.warning(f"Error during Redis shutdown: {exc}")
        try:
            from app.core.db import dispose_engine
            await dispose_engine()
        except Exception as exc:
            logger.warning(f"Error during database engine shutdown: {exc}")
        logger.info(f"Shutting down {settings.PROJECT_NAME} complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Register API Routers
app.include_router(sources_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(execution_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(metadata_router, prefix=settings.API_V1_STR)
app.include_router(migration_plans_router, prefix=settings.API_V1_STR)
app.include_router(observability_router, prefix=settings.API_V1_STR)
app.include_router(evaluation_router, prefix=settings.API_V1_STR)


# CORS Middleware Setup
# In compliance with UK GDPR / PECR (GDPR-SEC-001): Never use allow_origin_regex="^https?://.*$" with allow_credentials=True.
cors_origins = [origin.rstrip("/") for origin in settings.CORS_ORIGINS if origin != "*"]
clean_frontend = settings.FRONTEND_URL.rstrip("/")
if clean_frontend and clean_frontend not in cors_origins:
    cors_origins.append(clean_frontend)

host_ip = os.getenv("HOST_IP") or os.getenv("PUBLIC_IP")
if host_ip:
    clean_ip = host_ip.strip()
    for proto in ("http", "https"):
        ip_origin = f"{proto}://{clean_ip}:3000"
        if ip_origin not in cors_origins:
            cors_origins.append(ip_origin)
        ip_root = f"{proto}://{clean_ip}"
        if ip_root not in cors_origins:
            cors_origins.append(ip_root)

if not cors_origins:
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global catch-all exception handler to sanitize error messages,
    ensuring internal credentials, database URIs, and raw stacks are never leaked.
    """
    raw_error = str(exc)
    sanitized_error = CredentialSanitizer.mask_credentials(raw_error)
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {sanitized_error}",
        exc_info=False,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected internal server error occurred.",
            "error_detail": (
                sanitized_error
                if settings.ENVIRONMENT.lower() in ("development", "test", "local")
                else "Internal server error"
            ),
        },
    )



@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "live": f"{settings.API_V1_STR}/health/live",
        "ready": f"{settings.API_V1_STR}/health/ready",
    }


@app.get(f"{settings.API_V1_STR}/health", summary="System Health & Readiness Probe")
@app.get("/health", summary="Root Health Probe Alias")
async def health_check():
    """
    Active health and readiness probe: validates control-plane database connectivity (required)
    and Redis cache connectivity (optional, with in-memory fallback).
    Returns HTTP 200 when database is healthy, or HTTP 503 Service Unavailable when unreachable.
    """
    _, http_code, payload = await SystemHealthService.evaluate_readiness(session_factory=AsyncSessionLocal)
    return JSONResponse(status_code=http_code, content=payload)


@app.get(f"{settings.API_V1_STR}/health/live", summary="Process Liveness Probe")
@app.get("/live", summary="Root Liveness Probe Alias")
async def liveness_probe():
    """
    Zero-dependency liveness probe: verifies process event-loop responsiveness without touching external databases.
    Prevents cascading container restarts during downstream database degradation or temporary network partitions.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=SystemHealthService.evaluate_liveness(),
    )


@app.get(f"{settings.API_V1_STR}/health/ready", summary="Dependency Readiness Probe")
@app.get("/ready", summary="Root Readiness Probe Alias")
async def readiness_probe():
    """
    Readiness probe: validates that required startup dependencies (database) are operational.
    """
    _, http_code, payload = await SystemHealthService.evaluate_readiness(session_factory=AsyncSessionLocal)
    return JSONResponse(status_code=http_code, content=payload)
