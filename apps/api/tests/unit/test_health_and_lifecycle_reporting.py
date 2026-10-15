"""
Comprehensive Unit Tests for Health Reporting, Liveness/Readiness Semantics, and Production Lifecycle.

Validates:
1. All dependencies healthy (PostgreSQL & Redis connected -> HTTP 200, status ok).
2. Redis connection failure handled gracefully (Redis down -> HTTP 200, redis_connected=False, status ok).
3. Redis timeout behavior (bounded timeout -> HTTP 200, redis_connected=False).
4. Required dependency failure (Database down -> HTTP 503, success=False, status degraded).
5. Database timeout behavior (bounded timeout -> HTTP 503, no indefinite hang).
6. Liveness probe independence (returns HTTP 200 even when external DB & Redis are down).
7. Credential isolation (no passwords, URIs, or internal exceptions leaked).
8. Shared connection pool preserved (health check does not close shared Redis client).
9. Lifespan resource cleanup on application shutdown.
"""

import asyncio
from datetime import datetime, timezone
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import status
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.credential_sanitizer import CredentialSanitizer
import app.core.redis_client as redis_client_module
from app.main import app, health_check, liveness_probe, readiness_probe
from app.modules.observability.health_service import SystemHealthService


@pytest.mark.asyncio
async def test_health_all_dependencies_healthy():
    """Case 1: Both database and Redis are healthy -> HTTP 200, status ok."""
    mock_session = AsyncMock()
    mock_session.execute.return_value = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session

    with patch("app.main.AsyncSessionLocal", return_value=mock_ctx), \
         patch("app.modules.observability.health_service.check_redis_connectivity", return_value=True):
        resp = await health_check()
        assert resp.status_code == 200
        data = json.loads(resp.body.decode())
        assert data["success"] is True
        assert data["data"]["status"] == "ok"
        assert data["data"]["database_connected"] is True
        assert data["data"]["redis_connected"] is True
        assert data["data"]["dependencies"]["database"]["status"] == "ok"
        assert data["data"]["dependencies"]["redis"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_redis_connection_failure():
    """Case 2: Redis fails with connection error -> HTTP 200 because Redis is optional."""
    mock_session = AsyncMock()
    mock_session.execute.return_value = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session

    with patch("app.main.AsyncSessionLocal", return_value=mock_ctx), \
         patch("app.modules.observability.health_service.check_redis_connectivity", return_value=False):
        resp = await health_check()
        # Redis is optional; application readiness must remain HTTP 200
        assert resp.status_code == 200
        data = json.loads(resp.body.decode())
        assert data["success"] is True
        assert data["data"]["database_connected"] is True
        assert data["data"]["redis_connected"] is False
        assert data["data"]["status"] == "ok"
        assert "fallback" in data["message"].lower() or "cache" in data["message"].lower()
        assert data["data"]["dependencies"]["redis"]["required"] is False
        assert data["data"]["dependencies"]["redis"]["status"] == "degraded"


@pytest.mark.asyncio
async def test_health_redis_timeout_behavior():
    """Case 3: Redis ping times out -> Bounded timeout prevents hanging, returns HTTP 200."""
    mock_client = AsyncMock()
    # Mock ping to simulate timeout
    async def slow_ping():
        await asyncio.sleep(5)
        return True

    mock_client.ping = slow_ping

    with patch.object(redis_client_module, "get_redis_client", return_value=mock_client):
        # Bounded timeout of 0.05s should finish fast
        is_connected = await redis_client_module.check_redis_connectivity(timeout_seconds=0.05)
        assert is_connected is False


@pytest.mark.asyncio
async def test_readiness_fails_when_database_down():
    """Case 4: Required dependency (PostgreSQL) is unreachable -> HTTP 503."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.side_effect = ConnectionRefusedError("PostgreSQL server unreachable on port 5432")

    with patch("app.main.AsyncSessionLocal", return_value=mock_ctx), \
         patch("app.modules.observability.health_service.check_redis_connectivity", return_value=True):
        resp = await health_check()
        assert resp.status_code == 503
        data = json.loads(resp.body.decode())
        assert data["success"] is False
        assert data["data"]["database_connected"] is False
        assert data["data"]["status"] == "degraded"
        assert data["data"]["dependencies"]["database"]["required"] is True
        assert data["data"]["dependencies"]["database"]["status"] == "down"

        # Also test dedicated readiness probe
        resp_ready = await readiness_probe()
        assert resp_ready.status_code == 503


@pytest.mark.asyncio
async def test_database_timeout_behavior():
    """Case 5: Database query hangs indefinitely -> Bounded timeout catches it and returns False."""
    mock_session = AsyncMock()
    async def hanging_query(*args, **kwargs):
        await asyncio.sleep(10)
        return MagicMock()

    mock_session.execute = hanging_query
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_session
    mock_factory = MagicMock(return_value=mock_ctx)

    db_ok = await SystemHealthService.check_database(session_factory=mock_factory, timeout_seconds=0.05)
    assert db_ok is False


@pytest.mark.asyncio
async def test_liveness_probe_independent_of_dependencies():
    """Case 6: Liveness probe returns 200 immediately even if external DB & Redis are down."""
    # Liveness probe does not call DB or Redis
    resp = await liveness_probe()
    assert resp.status_code == 200
    data = json.loads(resp.body.decode())
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_no_credential_leakage_in_health_response():
    """Case 7: Exceptions containing database credentials or Redis URLs never leak to response body."""
    raw_error_with_creds = "Connection refused: postgresql+asyncpg://superadmin:P@ssw0rd99!@db.prod.internal:5432/secrets_db"
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.side_effect = RuntimeError(raw_error_with_creds)

    with patch("app.main.AsyncSessionLocal", return_value=mock_ctx):
        resp = await health_check()
        body_text = resp.body.decode()
        assert "superadmin" not in body_text
        assert "P@ssw0rd99!" not in body_text
        assert "secrets_db" not in body_text


@pytest.mark.asyncio
async def test_shared_connection_not_closed_by_health_check():
    """Case 8: Health checks do not close the shared singleton Redis client."""
    mock_client = AsyncMock()
    mock_client.ping.return_value = True

    with patch.object(redis_client_module, "get_redis_client", return_value=mock_client):
        # Run check
        ok = await redis_client_module.check_redis_connectivity(timeout_seconds=1.0)
        assert ok is True
        # Verify close/aclose was NOT called
        assert mock_client.close.call_count == 0
        if hasattr(mock_client, "aclose"):
            assert mock_client.aclose.call_count == 0


@pytest.mark.asyncio
async def test_lifespan_startup_and_shutdown_cleanup():
    """Case 9: Application lifespan cleans up background tasks, redis client, and database engine."""
    from app.main import lifespan

    mock_app = MagicMock()
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_engine.begin.return_value.__aenter__.return_value = mock_conn

    with patch("app.core.redis_client.close_redis_client", new_callable=AsyncMock) as mock_close_redis, \
         patch("app.core.db.dispose_engine", new_callable=AsyncMock) as mock_dispose_engine, \
         patch("app.core.db.engine", mock_engine):

        async with lifespan(mock_app):
            # Application is running
            pass

        # Verify clean shutdown hooks were invoked
        assert mock_close_redis.call_count >= 1
        assert mock_dispose_engine.call_count >= 1
