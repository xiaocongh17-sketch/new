"""Rate limiting middleware using slowapi.

Provides a pre-configured :class:`slowapi.Limiter` with IP-based rate
limiting.  Uses Redis-backed storage when ``settings.redis_url`` is set,
otherwise falls back to in-memory storage.

Default limits
--------------
* All routes: **60 requests per minute**.
* AI endpoints (prefix ``/api/v1/ai/``) should apply ``@limiter.limit("10/minute")``.
* Login endpoints (prefix ``/api/v1/auth/login``) should apply
  ``@limiter.limit("5/minute")``.
"""

from typing import Optional

import structlog
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.infrastructure.config.settings import settings

logger = structlog.get_logger()

_limiter: Optional[Limiter] = None


def get_rate_limiter() -> Limiter:
    """Return (or create) the application-wide :class:`Limiter` instance.

    The limiter is cached after first creation so that subsequent calls
    return the same instance (important for route decorators).

    Storage
    -------
    * ``settings.redis_url`` set → Redis-backed storage.
    * Otherwise → in-memory storage (single-process only).
    """
    global _limiter
    if _limiter is not None:
        return _limiter

    storage_uri: str = settings.redis_url if settings.redis_url else "memory://"
    _limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["60/minute"],
        storage_uri=storage_uri,
        headers_enabled=not settings.debug,
    )
    logger.info(
        "rate_limiter_initialised",
        default_limits="60/minute",
        storage="redis" if settings.redis_url else "memory",
    )
    return _limiter


def setup_rate_limiting(app: FastAPI, limiter: Optional[Limiter] = None) -> None:
    """Register the rate limiter on a FastAPI application.

    Call this during startup **after** the app is created.  If *limiter* is
    not provided, :func:`get_rate_limiter` is called automatically.
    """
    if limiter is None:
        limiter = get_rate_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)
    logger.info("rate_limiting_middleware_registered")
