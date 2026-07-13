"""Async Redis client and caching utilities.

Provides a shared async Redis client that gracefully degrades when
no REDIS_URL is configured.
"""

import functools
import hashlib
import json
from typing import Any, Callable, Optional, TypeVar

import structlog
from redis.asyncio import Redis as AsyncRedis

from app.infrastructure.config.settings import settings

logger = structlog.get_logger()

_redis: Optional[AsyncRedis] = None

# Type variable for the cached decorator
F = TypeVar("F", bound=Callable[..., Any])


async def get_redis() -> Optional[AsyncRedis]:
    """Return the global async Redis client, or ``None`` if unavailable."""
    global _redis
    if _redis is None and settings.redis_url:
        try:
            _redis = AsyncRedis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=5,
            )
            await _redis.ping()
            logger.info("redis_connected")
        except Exception as exc:
            logger.warning("redis_connect_failed", error=str(exc), type=type(exc).__name__)
            _redis = None
    return _redis


async def close_redis() -> None:
    """Close the global Redis connection if it was opened."""
    global _redis
    if _redis is not None:
        try:
            await _redis.close()
            logger.info("redis_disconnected")
        except Exception as exc:
            logger.warning("redis_close_failed", error=str(exc))
        finally:
            _redis = None


def cached(ttl: int = 300) -> Callable[[F], F]:
    """Decorator that caches async function results in Redis.

    The cache key is derived from the function's module, name, and
    JSON-serialised arguments.  If Redis is unavailable the function
    is called directly (transparent degradation).

    Parameters
    ----------
    ttl : int
        Time-to-live in seconds (default 300).
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = await get_redis()
            if client is None:
                # Degraded: Redis not available, call directly
                return await func(*args, **kwargs)

            # Build a deterministic cache key
            key_data = {
                "module": func.__module__,
                "name": func.__qualname__,
                "args": args,
                "kwargs": kwargs,
            }
            key = f"cache:{hashlib.sha256(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()}"

            try:
                cached_value = await client.get(key)
                if cached_value is not None:
                    return json.loads(cached_value)
            except Exception as exc:
                logger.warning("cache_read_failed", key=key, error=str(exc))

            result = await func(*args, **kwargs)

            try:
                await client.setex(key, ttl, json.dumps(result, default=str))
            except Exception as exc:
                logger.warning("cache_write_failed", key=key, error=str(exc))

            return result

        return wrapper  # type: ignore[return-value]

    return decorator
