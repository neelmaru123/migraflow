"""
Operational Health Service
Decouples Agent Health (Docker container connectivity & heartbeat status)
from Job Health (DAG execution state, error rates, and verification outcomes).
"""

import asyncio
from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, List, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.credential_sanitizer import CredentialSanitizer
from app.core.db import AsyncSessionLocal
from app.core.redis_client import check_redis_connectivity
from app.core.state import AgentLifecycle, ExecutionLifecycle
from app.modules.agents.agents_models import Agent
from app.modules.execution.execution_models import MigrationJob
from app.modules.observability.observability_schemas import (
    AgentHealthStatus,
    JobHealthStatus,
    OperationalHealthResponse,
)

logger = logging.getLogger(__name__)


class OperationalHealthService:
    """
    Evaluates segregated health metrics for agents and migration jobs.
    """

    @classmethod
    async def evaluate_health(cls, session: AsyncSession) -> OperationalHealthResponse:
        """
        Calculates separate agent and job health summaries.
        Rule: An online agent does not guarantee its job is healthy,
        and a failed job does not mean the assigned agent is unhealthy.
        """
        now = datetime.now(timezone.utc)
        agent_cutoff = now - timedelta(seconds=60)

        # 1. Evaluate Agent Health
        stmt_agents = select(Agent)
        res_agents = await session.execute(stmt_agents)
        agents = list(res_agents.scalars().all())

        agent_statuses: List[AgentHealthStatus] = []
        online_count = 0
        offline_count = 0

        for a in agents:
            is_recent = a.last_seen_at is not None and (
                a.last_seen_at if a.last_seen_at.tzinfo else a.last_seen_at.replace(tzinfo=timezone.utc)
            ) >= agent_cutoff
            is_healthy = a.status in (AgentLifecycle.ONLINE.value, AgentLifecycle.BUSY.value) and is_recent

            if is_healthy:
                online_count += 1
            else:
                offline_count += 1

            agent_statuses.append(
                AgentHealthStatus(
                    agent_id=a.id,
                    name=a.name,
                    status=a.status,
                    is_healthy=is_healthy,
                    last_seen_at=a.last_seen_at,
                    version=a.version,
                )
            )

        agent_summary = {
            "total_agents": len(agents),
            "online_agents": online_count,
            "offline_agents": offline_count,
            "health_verdict": "HEALTHY" if offline_count == 0 and len(agents) > 0 else ("DEGRADED" if online_count > 0 else "UNHEALTHY"),
        }

        # 2. Evaluate Active Job Health
        stmt_jobs = (
            select(MigrationJob)
            .where(MigrationJob.status.in_([
                ExecutionLifecycle.QUEUED.value,
                ExecutionLifecycle.CLAIMED.value,
                ExecutionLifecycle.PREPARING.value,
                ExecutionLifecycle.RUNNING.value,
                ExecutionLifecycle.VERIFYING.value,
                ExecutionLifecycle.ASK_USER.value,
                ExecutionLifecycle.NEEDS_REVIEW.value,
                ExecutionLifecycle.FAILED.value,
            ]))
            .order_by(MigrationJob.created_at.desc())
            .limit(20)
        )
        res_jobs = await session.execute(stmt_jobs)
        jobs = list(res_jobs.scalars().all())

        job_statuses: List[JobHealthStatus] = []
        healthy_jobs = 0
        degraded_jobs = 0
        failed_jobs = 0

        for j in jobs:
            is_job_healthy = j.status in (
                ExecutionLifecycle.QUEUED.value,
                ExecutionLifecycle.CLAIMED.value,
                ExecutionLifecycle.PREPARING.value,
                ExecutionLifecycle.RUNNING.value,
                ExecutionLifecycle.VERIFYING.value,
            )
            if j.status == ExecutionLifecycle.FAILED.value:
                failed_jobs += 1
            elif j.status in (ExecutionLifecycle.ASK_USER.value, ExecutionLifecycle.NEEDS_REVIEW.value):
                degraded_jobs += 1
            else:
                healthy_jobs += 1

            job_statuses.append(
                JobHealthStatus(
                    job_id=j.id,
                    status=j.status,
                    is_healthy=is_job_healthy,
                    progress=j.progress,
                    failed_rows=j.failed_rows,
                    active_step=j.current_table,
                    error_message=j.error_message,
                )
            )

        job_summary = {
            "total_tracked_jobs": len(jobs),
            "healthy_jobs": healthy_jobs,
            "degraded_jobs": degraded_jobs,
            "failed_jobs": failed_jobs,
            "health_verdict": "HEALTHY" if failed_jobs == 0 and degraded_jobs == 0 else ("DEGRADED" if healthy_jobs > 0 else "UNHEALTHY"),
        }

        # Overall operational assessment
        if agent_summary["health_verdict"] == "HEALTHY" and job_summary["health_verdict"] == "HEALTHY":
            overall = "HEALTHY"
        elif agent_summary["health_verdict"] == "UNHEALTHY" or job_summary["health_verdict"] == "UNHEALTHY":
            overall = "UNHEALTHY"
        else:
            overall = "DEGRADED"

        return OperationalHealthResponse(
            overall_health=overall,
            agent_health_summary=agent_summary,
            job_health_summary=job_summary,
            agents=agent_statuses,
            active_jobs=job_statuses,
        )


class SystemHealthService:
    """
    Evaluates infrastructure health, liveness, and readiness with bounded timeouts.
    Distinguishes mandatory dependencies (database) from optional ones (Redis).
    """

    @classmethod
    async def check_database(cls, session_factory=None, timeout_seconds: float = 2.0) -> bool:
        """
        Bounded-time PostgreSQL / database connectivity probe.
        Does not hang or leak connection errors.
        """
        factory = session_factory or AsyncSessionLocal
        try:
            async with factory() as session:
                await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=timeout_seconds)
                return True
        except Exception as exc:
            masked = CredentialSanitizer.mask_credentials(str(exc))
            logger.warning(f"Database health probe failed: {masked}")
            return False

    @classmethod
    async def check_redis(cls, timeout_seconds: float = 1.5) -> bool:
        """
        Bounded-time Redis connectivity probe via shared client pool.
        """
        return await check_redis_connectivity(timeout_seconds=timeout_seconds)

    @classmethod
    def evaluate_liveness(cls) -> Dict[str, Any]:
        """
        Liveness probe: verifies process event-loop responsiveness without touching external systems.
        Prevents cascading container restarts during external dependency degradation.
        """
        return {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "0.1.0",
        }

    @classmethod
    async def evaluate_readiness(
        cls, session_factory=None, db_timeout: float = 2.0, redis_timeout: float = 1.5
    ) -> Tuple[bool, int, Dict[str, Any]]:
        """
        Readiness probe: validates required startup prerequisites.
        - Database: REQUIRED. If down, readiness fails (HTTP 503).
        - Redis: OPTIONAL (memory fallback available). If down, readiness succeeds (HTTP 200) with degraded status.
        Returns:
            (is_ready: bool, http_status_code: int, response_dict: dict)
        """
        db_ok = await cls.check_database(session_factory=session_factory, timeout_seconds=db_timeout)
        redis_ok = await cls.check_redis(timeout_seconds=redis_timeout)

        is_ready = db_ok
        http_code = 200 if is_ready else 503

        if db_ok and redis_ok:
            message = "System operational"
            status_verdict = "ok"
        elif db_ok and not redis_ok:
            message = "System operational (cache offline, using memory fallback)"
            status_verdict = "ok"
        else:
            message = "Database connectivity degraded"
            status_verdict = "degraded"

        payload = {
            "success": is_ready,
            "message": message,
            "data": {
                "status": status_verdict,
                "version": "0.1.0",
                "environment": settings.ENVIRONMENT,
                "database_connected": db_ok,
                "redis_connected": redis_ok,
                "dependencies": {
                    "database": {
                        "connected": db_ok,
                        "required": True,
                        "status": "ok" if db_ok else "down",
                    },
                    "redis": {
                        "connected": redis_ok,
                        "required": False,
                        "status": "ok" if redis_ok else "degraded",
                    },
                },
            },
        }
        return is_ready, http_code, payload
