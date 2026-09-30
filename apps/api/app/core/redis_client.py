"""
Async Redis Client & Password Reset Cache Management
"""

import json
import logging
from typing import Any, Dict, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


def get_redis_client() -> aioredis.Redis:
    """Return singleton async Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )
    return _redis_client


class PasswordResetCache:
    """Redis operations for password reset token lifecycle and rate limiting."""

    TOKEN_KEY_PREFIX = "pwd_reset:token:"
    RATE_LIMIT_KEY_PREFIX = "pwd_reset:rate_limit:"

    @classmethod
    async def set_reset_token(
        cls,
        token: str,
        user_id: str,
        email: str,
        ttl_seconds: int = 300,
    ) -> bool:
        """
        Store password reset token in Redis with exact TTL (default: 5 min / 300 sec).
        Token auto-evicts after ttl_seconds.
        """
        try:
            r = get_redis_client()
            key = f"{cls.TOKEN_KEY_PREFIX}{token}"
            data = json.dumps({"user_id": str(user_id), "email": email.lower().strip()})
            await r.set(key, data, ex=ttl_seconds)
            return True
        except Exception as exc:
            logger.error(f"Failed to store reset token in Redis: {exc}")
            raise

    @classmethod
    async def get_reset_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve reset token data from Redis.
        Returns dict with 'user_id' and 'email', or None if expired/non-existent.
        """
        try:
            r = get_redis_client()
            key = f"{cls.TOKEN_KEY_PREFIX}{token}"
            val = await r.get(key)
            if not val:
                return None
            return json.loads(val)
        except Exception as exc:
            logger.error(f"Failed to fetch reset token from Redis: {exc}")
            return None

    @classmethod
    async def delete_reset_token(cls, token: str) -> None:
        """
        Delete reset token from Redis immediately after use (enforce single-use).
        """
        try:
            r = get_redis_client()
            key = f"{cls.TOKEN_KEY_PREFIX}{token}"
            await r.delete(key)
        except Exception as exc:
            logger.error(f"Failed to delete reset token from Redis: {exc}")

    @classmethod
    async def check_rate_limit(cls, email: str) -> Optional[int]:
        """
        Check if password reset requests for this email are throttled.
        Returns remaining cooldown seconds if throttled, or None if permitted.
        """
        try:
            r = get_redis_client()
            key = f"{cls.RATE_LIMIT_KEY_PREFIX}{email.lower().strip()}"
            ttl = await r.ttl(key)
            if ttl is not None and ttl > 0:
                return ttl
            return None
        except Exception as exc:
            logger.warning(f"Failed to check Redis rate limit: {exc}")
            return None

    @classmethod
    async def set_rate_limit(cls, email: str, cooldown_seconds: int = 60) -> None:
        """
        Set 1-minute rate limiting cooldown lock for this email.
        """
        try:
            r = get_redis_client()
            key = f"{cls.RATE_LIMIT_KEY_PREFIX}{email.lower().strip()}"
            await r.set(key, "1", ex=cooldown_seconds)
        except Exception as exc:
            logger.warning(f"Failed to set Redis rate limit: {exc}")
