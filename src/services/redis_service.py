import json
import logging

from redis.asyncio import Redis

from src.conf.config import settings

logger = logging.getLogger(__name__)
redis_client: Redis | None = None


async def init_redis() -> None:
    """Initialize shared asynchronous Redis client."""
    global redis_client
    try:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await redis_client.ping()
    except Exception:
        logger.exception("Redis initialization failed. Cache will be disabled.")
        redis_client = None


async def close_redis() -> None:
    """Close Redis client and release resources."""
    global redis_client
    if redis_client is not None:
        try:
            await redis_client.aclose()
        except Exception:
            logger.exception("Failed to close Redis client")
        finally:
            redis_client = None


async def get_user_cache(email: str) -> dict | None:
    """Get cached user payload by email."""
    if redis_client is None:
        return None
    key = f"user:by_email:{email.lower()}"
    try:
        data = await redis_client.get(key)
        if data is None:
            return None
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        logger.exception("Failed to read user cache for email=%s", email)
    return None


async def set_user_cache(email: str, payload: dict) -> None:
    """Cache user payload with configured TTL."""
    if redis_client is None:
        return
    key = f"user:by_email:{email.lower()}"
    try:
        await redis_client.set(
            key,
            json.dumps(payload),
            ex=settings.REDIS_USER_CACHE_TTL_SECONDS,
        )
    except Exception:
        logger.exception("Failed to write user cache for email=%s", email)


async def delete_user_cache(email: str) -> None:
    """Delete user cache key by email."""
    if redis_client is None:
        return
    key = f"user:by_email:{email.lower()}"
    try:
        await redis_client.delete(key)
    except Exception:
        logger.exception("Failed to invalidate user cache for email=%s", email)
