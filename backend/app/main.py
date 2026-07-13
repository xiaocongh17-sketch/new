"""AI Store Copilot — FastAPI Application Entry Point"""

import sys
import asyncio

# Windows fix: asyncpg + greenlet require SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.infrastructure.config.settings import settings
from app.interfaces.api.v1 import wecom, auth, houses, conversations, employees, knowledge, ai, stores, dashboard, communities
from app.interfaces.errors.handlers import register_error_handlers

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("app_starting", version="0.1.0", debug=settings.debug)

    # ── Initialise Redis ──────────────────────────────────────────
    from app.infrastructure.cache.redis_client import get_redis

    try:
        redis_client = await get_redis()
        if redis_client is not None:
            logger.info("redis_ready")
        else:
            logger.info("redis_not_configured")
    except Exception as e:
        logger.warning("redis_init_failed", error=str(e))

    # ── Test DB connection on startup ─────────────────────────────
    try:
        from app.infrastructure.persistence.database import async_session_factory
        from sqlalchemy import text

        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info("db_connected", result=result.scalar())
    except Exception as e:
        logger.error("db_connection_failed", error=str(e), type=type(e).__name__)

    yield

    # ── Shutdown ──────────────────────────────────────────────────
    from app.infrastructure.cache.redis_client import close_redis

    await close_redis()
    logger.info("app_stopped")


app = FastAPI(
    title="AI Store Copilot API",
    description="房地产 AI 门店经营助手 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    contact={
        "name": "AI Store Copilot Team",
    },
)

# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiting ─────────────────────────────────────────────────
from app.interfaces.middleware.rate_limit import get_rate_limiter, setup_rate_limiting

limiter = get_rate_limiter()
setup_rate_limiting(app, limiter)

# ── OpenTelemetry ─────────────────────────────────────────────────
from app.infrastructure.observability.telemetry import setup_observability

setup_observability(app)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(wecom.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(houses.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(stores.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(communities.router, prefix="/api/v1")

# ── Error handlers ───────────────────────────────────────────────
register_error_handlers(app)


@app.get("/api/health", tags=["系统"])
async def health():
    """Enhanced health check endpoint."""
    from app.infrastructure.cache.redis_client import get_redis
    from app.infrastructure.persistence.database import async_session_factory
    from sqlalchemy import text

    checks = {"status": "ok", "version": "0.1.0"}

    # DB check
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception:
        checks["database"] = "unreachable"
        checks["status"] = "degraded"

    # Redis check
    try:
        redis_client = await get_redis()
        if redis_client is not None:
            await redis_client.ping()
            checks["redis"] = "connected"
        else:
            checks["redis"] = "not_configured"
    except Exception:
        checks["redis"] = "unreachable"

    # AI provider
    checks["ai_provider"] = settings.ai_provider if settings.ai_api_key else "not_configured"

    return checks
