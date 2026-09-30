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
    """Redis operations for password reset token lifecycle and rate limiting with in-memory fallback."""

    TOKEN_KEY_PREFIX = "pwd_reset:token:"
    RATE_LIMIT_KEY_PREFIX = "pwd_reset:rate_limit:"

    # In-memory fallbacks for resilient local development if Redis is unreachable
    _memory_tokens: Dict[str, Dict[str, Any]] = {}
    _memory_rate_limits: Dict[str, float] = {}

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
        Falls back to in-memory store if Redis is unavailable.
        """
        import time
        try:
            r = get_redis_client()
            key = f"{cls.TOKEN_KEY_PREFIX}{token}"
            data = json.dumps({"user_id": str(user_id), "email": email.lower().strip()})
            await r.set(key, data, ex=ttl_seconds)
            return True
        except Exception as exc:
            logger.warning(f"Redis unavailable, storing reset token in memory fallback: {exc}")
            cls._memory_tokens[token] = {
                "data": {"user_id": str(user_id), "email": email.lower().strip()},
                "expires_at": time.time() + ttl_seconds,
            }
            return True

    @classmethod
    async def get_reset_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve reset token data from Redis or memory fallback.
        Returns dict with 'user_id' and 'email', or None if expired/non-existent.
        """
        import time
        try:
            r = get_redis_client()
            key = f"{cls.TOKEN_KEY_PREFIX}{token}"
            val = await r.get(key)
            if val:
                return json.loads(val)
        except Exception as exc:
            logger.warning(f"Redis unavailable, checking memory fallback for reset token: {exc}")

        # Check memory fallback
        cached = cls._memory_tokens.get(token)
        if cached:
            if cached["expires_at"] > time.time():
                return cached["data"]
            else:
                cls._memory_tokens.pop(token, None)
        return None

    @classmethod
    async def delete_reset_token(cls, token: str) -> None:
        """
        Delete reset token from Redis and memory immediately after use (enforce single-use).
        """
        try:
            r = get_redis_client()
            key = f"{cls.TOKEN_KEY_PREFIX}{token}"
            await r.delete(key)
        except Exception as exc:
            logger.warning(f"Failed to delete reset token from Redis: {exc}")
        cls._memory_tokens.pop(token, None)

    @classmethod
    async def check_rate_limit(cls, email: str) -> Optional[int]:
        """
        Check if password reset requests for this email are throttled.
        Returns remaining cooldown seconds if throttled, or None if permitted.
        """
        import time
        email_clean = email.lower().strip()
        try:
            r = get_redis_client()
            key = f"{cls.RATE_LIMIT_KEY_PREFIX}{email_clean}"
            ttl = await r.ttl(key)
            if ttl is not None and ttl > 0:
                return ttl
            return None
        except Exception as exc:
            logger.warning(f"Failed to check Redis rate limit, checking memory fallback: {exc}")

        expires_at = cls._memory_rate_limits.get(email_clean)
        if expires_at:
            remaining = int(expires_at - time.time())
            if remaining > 0:
                return remaining
            else:
                cls._memory_rate_limits.pop(email_clean, None)
        return None

    @classmethod
    async def set_rate_limit(cls, email: str, cooldown_seconds: int = 60) -> None:
        """
        Set rate limiting cooldown lock for this email.
        """
        import time
        email_clean = email.lower().strip()
        try:
            r = get_redis_client()
            key = f"{cls.RATE_LIMIT_KEY_PREFIX}{email_clean}"
            await r.set(key, "1", ex=cooldown_seconds)
        except Exception as exc:
            logger.warning(f"Failed to set Redis rate limit, using memory fallback: {exc}")
        cls._memory_rate_limits[email_clean] = time.time() + cooldown_seconds
