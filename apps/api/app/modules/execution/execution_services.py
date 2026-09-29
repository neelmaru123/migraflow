"""
Execution Domain Business Services
"""

import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import AsyncSessionLocal
from app.modules.agents.agents_models import Agent
from app.modules.execution.execution_models import MigrationJob
from app.modules.execution.execution_schemas import (
    ExecutionProgressUpdate,
    ExecutionStartRequest,
)
from app.modules.migration_plans.migration_plans_models import MigrationPlan
from app.modules.sources.sources_models import DataSource
from app.modules.metadata.metadata_services import MetadataService
from app.core.config import settings
from app.core.logging import logger
from app.core.websocket_manager import manager


class ExecutionService:
    """Business logic for Migration Execution Jobs lifecycle."""

    @staticmethod
    async def check_target_tables_existing_data(
        session: AsyncSession, plan: MigrationPlan
    ) -> list[dict]:
        """
        Preflight check querying the target data source via the agent's most recent
        metadata snapshot (without live DB connection from the API) to check if any of
        the plan's target tables already contain rows.
        """
        if not plan.agent_id or not plan.plan_data:
            return []

        target_table_names: list[str] = []
        if isinstance(plan.plan_data, dict):
            for tm in plan.plan_data.get("table_mappings", []):
                tbl = tm.get("target_table_name")
                if tbl and tbl not in target_table_names:
                    target_table_names.append(tbl)

        if not target_table_names:
            return []

        # Find target DataSource(s) for the agent
        target_config = plan.target_config if isinstance(plan.target_config, dict) else {}
        target_identifier = target_config.get("identifier")

        stmt_ds = select(DataSource).where(
            DataSource.agent_id == plan.agent_id,
            or_(
                DataSource.role.in_(["target", "both"]),
                DataSource.identifier == target_identifier if target_identifier else False,
            ),
        )
        res_ds = await session.execute(stmt_ds)
        target_data_sources = list(res_ds.scalars().all())

        # If none marked target/both, fallback to matching target_db_type or checking all agent data sources
        if not target_data_sources:
            target_db_type = (target_config.get("database_type") or "").lower()
            stmt_all = select(DataSource).where(DataSource.agent_id == plan.agent_id)
            res_all = await session.execute(stmt_all)
            all_ds = list(res_all.scalars().all())
            for ds in all_ds:
                if target_db_type and ds.type.lower() == target_db_type:
                    target_data_sources.append(ds)

        target_tables_with_existing_data: list[dict] = []
        seen_tables = set()
        target_tables_norm = {t.lower(): t for t in target_table_names}

        for ds in target_data_sources:
            snapshot = await MetadataService.get_latest_snapshot_for_source(session, ds.id)
            if not snapshot or not snapshot.schemas:
                continue
            for schema in snapshot.schemas:
                for table in (schema.tables or []):
                    table_norm = table.table_name.lower()
                    if table_norm in target_tables_norm and table.row_count > 0:
                        original_name = target_tables_norm[table_norm]
                        if original_name not in seen_tables:
                            seen_tables.add(original_name)
                            target_tables_with_existing_data.append({
                                "table_name": original_name,
                                "existing_row_count": table.row_count,
                            })

        return target_tables_with_existing_data

    @staticmethod
    async def create_execution_job(
        session: AsyncSession,
        user_id: uuid.UUID,
        plan_id: uuid.UUID,
        is_dry_run: bool = False,
        truncate_target: bool = False,
    ) -> MigrationJob:
        # Check plan existence and ownership
        stmt_plan = select(MigrationPlan).where(
            MigrationPlan.id == plan_id, MigrationPlan.user_id == user_id
        )
        res_plan = await session.execute(stmt_plan)
        plan = res_plan.scalar_one_or_none()
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Migration plan not found or access denied.",
            )

        if not plan.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot execute invalid plan! Fix schema feasibility errors first.",
            )

        if plan.status != "completed" and plan.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot execute unapproved migration plan. Plan status is '{plan.status}'. User approval is required.",
            )

        # Check for active running job for this plan
        stmt_active = select(MigrationJob).where(
            MigrationJob.migration_plan_id == plan_id,
            MigrationJob.status.in_(["queued", "preparing", "running"]),
        )
        res_active = await session.execute(stmt_active)
        if res_active.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An active execution job is already in progress for this plan.",
            )

        # Check assigned Docker Agent online status before queuing execution
        if plan.agent_id:
            stmt_agent = select(Agent).where(Agent.id == plan.agent_id)
            res_agent = await session.execute(stmt_agent)
            agent = res_agent.scalar_one_or_none()

            now_utc = datetime.now(timezone.utc)

            # Adaptive cutoff based on agent power/heartbeat mode:
            # Active mode (heartbeat every 20s): cutoff is 60s
            # Standby mode (idle 5+ min, heartbeat every 300s): cutoff is 360s
            is_standby = False
            if agent and agent.idle_since is not None:
                idle_since_aware = (
                    agent.idle_since
                    if agent.idle_since.tzinfo
                    else agent.idle_since.replace(tzinfo=timezone.utc)
                )
                if (now_utc - idle_since_aware).total_seconds() >= 300:
                    is_standby = True

            effective_threshold_sec = 360 if is_standby else 60
            cutoff_utc = now_utc - timedelta(seconds=effective_threshold_sec)
            cutoff_naive_utc = now_utc.replace(tzinfo=None) - timedelta(seconds=effective_threshold_sec)
            cutoff_naive_local = datetime.now() - timedelta(seconds=effective_threshold_sec)

            is_offline = False
            if not agent or not agent.last_seen_at:
                is_offline = True
            elif agent.status in ("error", "offline"):
                is_offline = True
            elif agent.last_seen_at.tzinfo is not None and agent.last_seen_at < cutoff_utc:
                is_offline = True
            elif agent.last_seen_at.tzinfo is None and agent.last_seen_at < cutoff_naive_utc and agent.last_seen_at < cutoff_naive_local:
                is_offline = True

            if is_offline:
                agent_name = agent.name if agent else "Assigned Agent"
                status_detail = f" (status: '{agent.status}')" if agent and agent.status else ""
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Cannot execute plan: {agent_name} is currently offline or unreachable{status_detail}. Ensure the agent Docker container is actively running on the host.",
                )

        # Reset idle_since: agent is now active with a new job
        if plan.agent_id:
            stmt_reset_idle = select(Agent).where(Agent.id == plan.agent_id)
            res_reset_idle = await session.execute(stmt_reset_idle)
            agent_for_reset = res_reset_idle.scalar_one_or_none()
            if agent_for_reset:
                agent_for_reset.idle_since = None

        # Check if target tables already contain rows (preflight check via snapshot)
        existing_data_warnings = await ExecutionService.check_target_tables_existing_data(
            session=session, plan=plan
        )
        if existing_data_warnings:
            logger.warning(
                f"Preflight alert for plan '{plan_id}': Target tables already contain rows: {existing_data_warnings}"
            )

        job = MigrationJob(
            migration_plan_id=plan_id,
            agent_id=plan.agent_id,
            status="queued",
            is_dry_run=is_dry_run,
            truncate_target=truncate_target,
            total_rows=0,
            processed_rows=0,
            successful_rows=0,
            failed_rows=0,
            progress=0.0,
            current_stage="queued",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        # Attach preflight warnings for response serialization
        setattr(job, "target_tables_with_existing_data", existing_data_warnings)

        logger.info(
            f"Created execution job '{job.id}' for plan '{plan_id}' (Agent ID: {plan.agent_id})."
        )
        return job

    @staticmethod
    async def get_pending_tasks_for_agent(
        session: AsyncSession, agent_id: uuid.UUID
    ) -> List[MigrationJob]:
        """
        Returns queued or stale preparing migration jobs assigned to a specific Docker Agent,
        atomically claiming them with row-level locking (SKIP LOCKED) and transitioning
        status to 'preparing' within the same transaction to prevent double execution.
        """
        cutoff_preparing = datetime.now(timezone.utc) - timedelta(seconds=30)
        stmt_select = (
            select(MigrationJob.id)
            .where(
                MigrationJob.agent_id == agent_id,
                or_(
                    MigrationJob.status == "queued",
                    and_(
                        MigrationJob.status == "preparing",
                        MigrationJob.updated_at < cutoff_preparing,
                    ),
                ),
            )
            .order_by(MigrationJob.created_at.asc())
            .with_for_update(skip_locked=True)
        )
        res_ids = await session.execute(stmt_select)
        job_ids = list(res_ids.scalars().all())

        if not job_ids:
            return []

        now = datetime.now(timezone.utc)
        stmt_update = (
            update(MigrationJob)
            .where(
                MigrationJob.id.in_(job_ids),
                or_(
                    MigrationJob.status == "queued",
                    and_(
                        MigrationJob.status == "preparing",
                        MigrationJob.updated_at < cutoff_preparing,
                    ),
                ),
            )
            .values(status="preparing", updated_at=now)
        )
        res_update = await session.execute(stmt_update)
        if res_update.rowcount == 0:
            await session.rollback()
            return []

        await session.commit()

        stmt_fetch = select(MigrationJob).where(MigrationJob.id.in_(job_ids))
        res_fetch = await session.execute(stmt_fetch)
        return list(res_fetch.scalars().all())

    @staticmethod
    async def check_stale_jobs(
        session: AsyncSession, stale_threshold_seconds: int = 300
    ) -> int:
        """
        Backend Watchdog: Detects execution jobs stuck in 'running' or 'preparing'
        with no progress update for longer than stale_threshold_seconds (default 5 minutes).
        Transitions stuck jobs to 'failed' with an explicit error message.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=stale_threshold_seconds)
        stmt = select(MigrationJob).where(
            MigrationJob.status.in_(["queued", "running", "preparing"]),
            MigrationJob.updated_at < cutoff,
        )
        res = await session.execute(stmt)
        stale_jobs = list(res.scalars().all())

        if not stale_jobs:
            return 0

        now = datetime.now(timezone.utc)
        for job in stale_jobs:
            job.status = "failed"
            job.completed_at = now
            job.error_message = (
                f"Migration job stalled: no progress updates received from agent for over {stale_threshold_seconds} seconds."
            )
            logger.error(
                f"Watchdog failed stale job '{job.id}' (last updated: {job.updated_at})."
            )
            if job.agent_id:
                await manager.broadcast_to_agent(
                    str(job.agent_id),
                    {
                        "event": "JOB_FAILED",
                        "agent_id": str(job.agent_id),
                        "job_id": str(job.id),
                        "status": "failed",
                        "error_message": job.error_message,
                    },
                )

        await session.commit()
        return len(stale_jobs)

    @staticmethod
    async def get_job_by_id(
        session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> MigrationJob:
        """
        Fetches a MigrationJob by ID, verifying user ownership via attached MigrationPlan.
        """
        await ExecutionService.check_stale_jobs(session)
        stmt = (
            select(MigrationJob)
            .join(MigrationPlan, MigrationJob.migration_plan_id == MigrationPlan.id)
            .where(MigrationJob.id == job_id, MigrationPlan.user_id == user_id)
        )
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution job '{job_id}' not found or access denied.",
            )
        return job

    @staticmethod
    async def cancel_execution_job(
        session: AsyncSession,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> MigrationJob:
        """
        Cancels an active ('queued', 'preparing', 'running') execution job.
        Frees the migration plan for subsequent runs and resets the assigned Docker Agent status.
        """
        stmt = (
            select(MigrationJob)
            .join(MigrationPlan, MigrationJob.migration_plan_id == MigrationPlan.id)
            .where(MigrationJob.id == job_id, MigrationPlan.user_id == user_id)
        )
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution job '{job_id}' not found or access denied.",
            )

        if job.status not in ["queued", "preparing", "running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel execution job with status '{job.status}'. Only active jobs (queued, preparing, running) can be cancelled.",
            )

        now = datetime.now(timezone.utc)
        job.status = "cancelled"
        job.completed_at = now
        job.current_stage = "cancelled"
        job.error_message = reason or "Execution cancelled by user."

        # Reset assigned Docker Agent status to online
        if job.agent_id:
            stmt_agent = select(Agent).where(Agent.id == job.agent_id)
            res_agent = await session.execute(stmt_agent)
            agent_obj = res_agent.scalar_one_or_none()
            if agent_obj:
                if agent_obj.status in ["busy", "offline", "error"]:
                    agent_obj.status = "online"
                agent_obj.idle_since = now

            # Broadcast cancellation event via WebSocket
            await manager.broadcast_to_agent(
                str(job.agent_id),
                {
                    "event_type": "EXECUTION_PROGRESS",
                    "data": {
                        "job_id": str(job.id),
                        "status": "cancelled",
                        "progress": job.progress,
                        "processed_rows": job.processed_rows,
                        "successful_rows": job.successful_rows,
                        "failed_rows": job.failed_rows,
                        "current_stage": "cancelled",
                        "error_message": job.error_message,
                    },
                    "job_id": str(job.id),
                    "status": "cancelled",
                    "error_message": job.error_message,
                },
            )

        await session.commit()
        await session.refresh(job)
        logger.info(f"Execution job '{job.id}' was cancelled by user '{user_id}'. Reason: {job.error_message}")
        return job

    @staticmethod
    async def list_jobs_for_user(
        session: AsyncSession, user_id: uuid.UUID
    ) -> List[MigrationJob]:
        """
        Lists all execution jobs for a user across all migration plans.
        """
        await ExecutionService.check_stale_jobs(session)
        stmt = (
            select(MigrationJob)
            .join(MigrationPlan, MigrationJob.migration_plan_id == MigrationPlan.id)
            .where(MigrationPlan.user_id == user_id)
            .order_by(MigrationJob.created_at.desc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_job_progress(
        session: AsyncSession,
        job_id: uuid.UUID,
        update: ExecutionProgressUpdate,
        agent_id: Optional[uuid.UUID] = None,
    ) -> MigrationJob:
        """
        Updates live metrics and status for a MigrationJob from Docker Agent progress payload.
        Ensures the updating agent is the one assigned to the job.
        """
        stmt = select(MigrationJob).where(MigrationJob.id == job_id)
        if agent_id:
            stmt = stmt.where(MigrationJob.agent_id == agent_id)

        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution job '{job_id}' not found or access denied for this agent.",
            )

        # If job was already cancelled by the user, return cancelled status immediately without overwriting
        if job.status == "cancelled":
            return job

        now = datetime.now(timezone.utc)
        if update.status == "running" and job.started_at is None:
            job.started_at = now
        elif update.status in ["completed", "failed", "dry_run_completed"]:
            job.completed_at = now

        job.status = update.status
        job.progress = update.progress
        if update.total_rows > 0:
            job.total_rows = update.total_rows
        if update.processed_rows > 0 or job.processed_rows is None:
            job.processed_rows = update.processed_rows
        if update.successful_rows > 0 or job.successful_rows is None:
            job.successful_rows = update.successful_rows
        if update.failed_rows > 0 or job.failed_rows is None:
            job.failed_rows = update.failed_rows
        if update.current_table:
            job.current_table = update.current_table
        if update.current_stage:
            job.current_stage = update.current_stage
        if update.error_message:
            job.error_message = update.error_message
        elif update.status in ["completed", "dry_run_completed"]:
            job.error_message = None

        # Refresh agent last_seen_at, status, and idle_since to prevent heartbeat starvation during ETL execution
        if job.agent_id:
            stmt_agent = select(Agent).where(Agent.id == job.agent_id)
            res_agent = await session.execute(stmt_agent)
            agent_obj = res_agent.scalar_one_or_none()
            if agent_obj:
                agent_obj.last_seen_at = now
                if update.status == "running":
                    agent_obj.status = "busy"
                    agent_obj.idle_since = None   # Actively running — clear idle marker
                elif update.status in ["completed", "dry_run_completed"]:
                    agent_obj.status = "online"
                    agent_obj.idle_since = now    # Job done — start idle tracking for Option C/A
                elif update.status == "failed":
                    agent_obj.status = "error"
                    agent_obj.last_error = f"Migration job '{job.id}' failed: {update.error_message or 'Fatal execution failure.'}"
                    agent_obj.error_category = "JOB_EXECUTION_FAILURE"
                    agent_obj.last_error_at = now
                    agent_obj.idle_since = now

        await session.commit()
        await session.refresh(job)

        # Auto-trigger AI diagnosis in background with fresh session (Fix #1 & #7)
        if update.status == "failed" and job.error_message and not job.ai_diagnosis:
            asyncio.create_task(_run_diagnosis_background(job.id))

        # Broadcast progress via WebSocket
        if job.agent_id:
            await manager.broadcast_to_agent(
                str(job.agent_id),
                {
                    "event_type": "EXECUTION_PROGRESS",
                    "data": {
                        "job_id": str(job.id),
                        "status": job.status,
                        "progress": job.progress,
                        "processed_rows": job.processed_rows,
                        "successful_rows": job.successful_rows,
                        "failed_rows": job.failed_rows,
                        "current_table": job.current_table,
                        "current_stage": job.current_stage,
                        "ai_diagnosis": job.ai_diagnosis,
                    },
                },
            )

        return job

    @staticmethod
    async def list_jobs_for_plan(
        session: AsyncSession, plan_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[MigrationJob]:
        """Fetch all execution jobs for a migration plan owned by user, ordered by newest first (Fix #8)."""
        stmt = (
            select(MigrationJob)
            .join(MigrationPlan, MigrationJob.migration_plan_id == MigrationPlan.id)
            .where(
                MigrationJob.migration_plan_id == plan_id,
                MigrationPlan.user_id == user_id,
            )
            .order_by(MigrationJob.created_at.desc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def diagnose_job_failure(
        session: AsyncSession, job_id: uuid.UUID
    ) -> MigrationJob:
        """Synthesizes raw job error traceback into plain-English diagnosis & remediation actions using LLM."""
        # Atomic lock & guard: only process if ai_diagnosis is NULL (Fix #2)
        stmt = (
            select(MigrationJob)
            .where(MigrationJob.id == job_id)
            .with_for_update(skip_locked=True)
            .options(
                selectinload(MigrationJob.agent).selectinload(Agent.data_sources),
                selectinload(MigrationJob.plan),
            )
        )
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Execution job '{job_id}' not found.",
            )

        # Early guard: AI diagnosis only available for failed jobs (Fix #6)
        if job.status != "failed":
            if job.ai_diagnosis:
                return job
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"AI diagnosis is only available for failed execution jobs. Current status is '{job.status}'.",
            )

        # Return existing diagnosis if already populated (idempotent)
        if job.ai_diagnosis:
            return job

        err_msg = job.error_message or "Unknown execution error."
        stage = job.current_stage or "ETL processing"
        tbl = job.current_table or "N/A"

        # Heuristic & LLM Failure Synthesizer
        diag_summary = f"Migration failed during '{stage}' stage on table '{tbl}'."
        category = "UNKNOWN_ERROR"
        user_env_issue = False
        fix_steps: List[str] = []
        copyable_cmd: Optional[str] = None

        # 1. Attempt Intelligent LLM-Powered Diagnosis (Gemini / OpenAI)
        llm_success = False
        if settings.GEMINI_API_KEY or settings.OPENAI_API_KEY:
            try:
                from langchain_core.messages import HumanMessage
                from pydantic import BaseModel, Field

                class LLMDiagnosisResponse(BaseModel):
                    summary: str = Field(..., description="A friendly, clear, plain-English explanation of why the migration failed, written like an expert database architect talking to a developer. Name exact tables, columns, constraints, or configurations involved.")
                    root_cause_category: str = Field(..., description="One of: NOT_NULL_CONSTRAINT_VIOLATION, UNIQUE_CONSTRAINT_VIOLATION, FOREIGN_KEY_CONSTRAINT_VIOLATION, TARGET_TABLE_MISSING, HIGH_ROW_ERROR_RATE, NETWORK_CONNECTION_FAILED, DATABASE_AUTHENTICATION_FAILED, SQL_DIALECT_ERROR, SCHEMA_MISMATCH, UNKNOWN_ERROR")
                    is_user_environment_issue: bool = Field(..., description="True ONLY if the issue is container/network/auth. False if it is a database schema, table, constraint, or SQL issue.")
                    fix_steps: List[str] = Field(..., description="List of 2-4 concrete, actionable remediation steps for the developer.")
                    copyable_fix_command: Optional[str] = Field(None, description="Exact copyable SQL command (e.g. ALTER TABLE ... or TRUNCATE ...) to fix or inspect the database.")
                    copyable_fix_label: Optional[str] = Field(None, description="Label for the command, e.g., 'SQL Schema Fix (Run in Destination DB)'")

                plan_title = job.plan.title if job.plan else "Migration Plan"
                target_engine = "postgresql"
                if job.agent and job.agent.data_sources:
                    for ds in job.agent.data_sources:
                        if (ds.role or "").lower() in ("target", "destination", "dest"):
                            target_engine = ds.type or "postgresql"
                            break

                llm_prompt = f"""You are an expert database migration architect and friendly AI pair programmer (like Antigravity).
A database migration job just failed with an error. Provide a clear, intuitive, plain-English explanation of why it failed and the exact SQL or CLI command to resolve it.

Migration Context:
- Plan Title: {plan_title}
- Stage: {stage}
- Current Table: {tbl}
- Target Database Engine: {target_engine}
- Raw Error Trace:
{err_msg}

Rules:
1. Explain in simple, conversational terms so a developer immediately understands what happened in their database.
2. If the error mentions a table constraint (e.g. NOT NULL on a column, unique constraint, or foreign key), pinpoint the exact column and table.
3. If it's a database schema constraint or missing column, DO NOT suggest Docker commands. Instead, provide the exact SQL statement (e.g. ALTER TABLE "{tbl}" ALTER COLUMN "<col>" DROP NOT NULL; or DROP TABLE IF EXISTS "{tbl}" CASCADE;) that the developer can copy and paste into DBeaver/pgAdmin/psql.
4. If it's a network or connection error, explain how to fix the container or host.
"""
                provider = settings.LLM_PROVIDER.lower()
                llm = None
                if provider == "gemini" and settings.GEMINI_API_KEY:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    llm = ChatGoogleGenerativeAI(
                        model=settings.LLM_MODEL or "gemini-1.5-flash",
                        google_api_key=settings.GEMINI_API_KEY,
                        temperature=0.1,
                        request_timeout=20,
                    )
                elif settings.OPENAI_API_KEY:
                    from langchain_openai import ChatOpenAI
                    llm = ChatOpenAI(
                        model=settings.LLM_MODEL or "gpt-4o-mini",
                        api_key=settings.OPENAI_API_KEY,
                        temperature=0.1,
                        request_timeout=20,
                    )

                if llm:
                    structured_llm = llm.with_structured_output(LLMDiagnosisResponse)
                    diag_obj: LLMDiagnosisResponse = await structured_llm.ainvoke([HumanMessage(content=llm_prompt)])
                    if diag_obj and diag_obj.summary:
                        diag_summary = diag_obj.summary
                        category = diag_obj.root_cause_category
                        user_env_issue = diag_obj.is_user_environment_issue
                        fix_steps = diag_obj.fix_steps
                        copyable_cmd = diag_obj.copyable_fix_command
                        copyable_cmd_label = diag_obj.copyable_fix_label or ("SQL Schema Fix (Run in Destination DB)" if not user_env_issue else "Container Command")
                        llm_success = True
            except Exception as llm_exc:
                logger.warning(f"Notice: LLM diagnosis generation fell back to heuristic engine: {llm_exc}")

        if not llm_success:
            # Deterministic Heuristic Fallback
            err_lower = err_msg.lower()

            # Strict Network Error Detection Patterns & Port Regex (Fix #4)
            network_patterns = [
                "connection refused",
                "connectionrefused",
                "could not connect to server",
                "could not connect to host",
                "no route to host",
                "network is unreachable",
                "connection timed out",
                "name or service not known",
                "getaddrinfofailed",
                "failed to connect",
            ]
            port_re = re.compile(r':(5\d{3}|27017|3306|5432|3307)\b')
            is_network_err = any(p in err_lower for p in network_patterns) or bool(port_re.search(err_msg))

        # Check NOT NULL constraint violations (extract column and relation)
        not_null_match = re.search(r'null value in column "([^"]+)" of relation "([^"]+)"', err_msg, re.IGNORECASE)
        if not not_null_match:
            not_null_match = re.search(r'null value in column "([^"]+)"', err_msg, re.IGNORECASE)
        if not not_null_match:
            not_null_match = re.search(r"column ['\"]([^'\"]+)['\"] cannot be null", err_msg, re.IGNORECASE)

        # Check unique constraint violations
        unique_match = re.search(r'duplicate key value violates unique constraint "([^"]+)"', err_msg, re.IGNORECASE)
        if not unique_match:
            unique_match = re.search(r"duplicate entry '([^']+)' for key '([^']+)'", err_msg, re.IGNORECASE)

        # Check foreign key constraint violations
        fk_match = re.search(r'violates foreign key constraint "([^"]+)"', err_msg, re.IGNORECASE)

        copyable_cmd_label: Optional[str] = None

        if is_network_err:
            category = "NETWORK_CONNECTION_FAILED"
            user_env_issue = True
            diag_summary = f"The agent could not connect to database on host/port specified during stage '{stage}'."
            fix_steps = [
                "Verify database host and port mapping (e.g. use host.docker.internal:5435 instead of localhost:5432).",
                "Ensure database container is running and accepting incoming connections.",
                "Verify --add-host=host.docker.internal:host-gateway flag is included in docker run."
            ]
        elif not_null_match or "notnullviolation" in err_lower or "null value in column" in err_lower or "cannot be null" in err_lower:
            category = "NOT_NULL_CONSTRAINT_VIOLATION"
            user_env_issue = False
            col_name = not_null_match.group(1) if not_null_match else None
            rel_name = not_null_match.group(2) if (not_null_match and len(not_null_match.groups()) > 1) else tbl
            if col_name:
                diag_summary = (
                    f"Destination database table '{rel_name}' rejected row insertions because column '{col_name}' "
                    f"has a strict NOT NULL constraint with no default value in your database, but this column is not "
                    f"mapped in your migration plan."
                )
                fix_steps = [
                    f"Run the SQL fix command below directly on your destination database to allow NULL values or set a default value: ALTER TABLE \"{rel_name}\" ALTER COLUMN \"{col_name}\" DROP NOT NULL;",
                    "Or enable 'Clean Wipe' in migration execution options if you want the pipeline to drop old legacy tables and recreate them cleanly according to the plan.",
                    f"Or edit your migration plan in the UI to map a source column or constant value to '{col_name}'."
                ]
                copyable_cmd = f'ALTER TABLE "{rel_name}" ALTER COLUMN "{col_name}" DROP NOT NULL;'
                copyable_cmd_label = "SQL Schema Fix (Run in Destination DB)"
            else:
                diag_summary = f"Target table '{rel_name}' rejected insertion due to a NOT NULL column constraint in your destination database."
                fix_steps = [
                    "Enable 'Clean Wipe' in migration execution options to recreate all target tables cleanly according to the plan.",
                    "Or edit the transformation blueprint in the UI to map all NOT NULL target columns."
                ]
        elif unique_match or "duplicate key" in err_lower or "unique constraint" in err_lower:
            category = "UNIQUE_CONSTRAINT_VIOLATION"
            user_env_issue = False
            diag_summary = (
                f"Destination database table '{tbl}' rejected insertion because a record already exists with the same "
                f"primary key or unique index."
            )
            fix_steps = [
                "Enable 'Clean Wipe' in migration execution options to clear previous conflicting test data before migrating.",
                "Or adjust Conflict Resolution in your transformation plan to 'Skip on Conflict' (ON CONFLICT DO NOTHING) or 'Update on Conflict'."
            ]
            copyable_cmd = f'-- Run in destination database to clear previous conflicting records:\nTRUNCATE TABLE "{tbl}" CASCADE;'
            copyable_cmd_label = "SQL Cleanup Command (Run in Destination DB)"
        elif fk_match or "foreign key" in err_lower:
            category = "FOREIGN_KEY_CONSTRAINT_VIOLATION"
            user_env_issue = False
            fk_name = fk_match.group(1) if fk_match else "foreign key"
            diag_summary = (
                f"Destination database table '{tbl}' rejected insertion because a foreign key references a parent record "
                f"that does not exist in the referenced parent table (violates constraint '{fk_name}')."
            )
            fix_steps = [
                "Ensure parent tables are migrated before child tables in the execution order.",
                "Check source database for orphan records that reference non-existent parent IDs."
            ]
        elif "nosuchmoduleerror" in err_lower or "sqlalchemy.dialects:mongodb" in err_lower:
            category = "NOSQL_DIALECT_MISMATCH"
            user_env_issue = False
            diag_summary = "Relational DDL statement execution was attempted on a MongoDB document database."
            fix_steps = [
                "Re-run the updated agent container image (data-migration-agent:latest) which skips relational DDL for MongoDB.",
                "MongoDB target collections are created automatically upon document streaming."
            ]
        elif "access denied" in err_lower or "authentication failed" in err_lower or "password" in err_lower:
            category = "DATABASE_AUTHENTICATION_FAILED"
            user_env_issue = True
            diag_summary = "Database rejected authentication credentials provided in agent environment variables."
            fix_steps = [
                "Verify database usernames and passwords in container environment variables.",
                "Ensure password placeholders like <SRC_SRC_DB_1_PASSWORD> are replaced with valid credentials."
            ]
        elif "undefinedtable" in err_lower or ("relation" in err_lower and "does not exist" in err_lower):
            category = "TARGET_TABLE_MISSING"
            user_env_issue = False
            diag_summary = f"Target table '{tbl}' does not exist in target database because pre-migration DDL table creation failed or was skipped."
            fix_steps = [
                "Enable 'Clean Wipe' before executing to automatically create all missing target tables.",
                "Verify target DDL statements use valid SQL syntax for the target database engine (e.g. gen_random_uuid() on PostgreSQL).",
                "Ensure pre-migration DDL statements execute without errors before starting data streaming."
            ]
        elif "undefinedfunction" in err_lower or "function uuid_v4() does not exist" in err_lower or "function does not exist" in err_lower:
            category = "SQL_DIALECT_FUNCTION_ERROR"
            user_env_issue = False
            diag_summary = f"Pre-migration DDL referenced an unsupported SQL function (e.g. uuid_v4() on PostgreSQL)."
            fix_steps = [
                "Use native PostgreSQL gen_random_uuid() or uuid_generate_v4() instead of uuid_v4().",
                "Update agent container to auto-heal dialect functions and re-run the execution job."
            ]
        elif "error rate exceeded" in err_lower:
            category = "HIGH_ROW_ERROR_RATE"
            user_env_issue = False
            diag_summary = (
                f"ETL pipeline aborted for table '{tbl}' because over 50% of records failed insertion into your destination database. "
                f"This typically indicates an unmapped NOT NULL column, a data type mismatch, or a missing table in your destination."
            )
            fix_steps = [
                f"Inspect table '{tbl}' in your destination database for columns with strict NOT NULL constraints or unique indexes.",
                "Enable 'Clean Wipe' in execution options to recreate all destination tables cleanly according to the plan.",
                "Review the agent container terminal output above for specific database error lines."
            ]
            copyable_cmd = (
                f"-- Option 1: Drop legacy destination table so the migration creates it cleanly according to your plan:\n"
                f"DROP TABLE IF EXISTS \"{tbl}\" CASCADE;\n\n"
                f"-- Option 2: Inspect columns in destination DB to find unmapped NOT NULL constraints or mismatched types:\n"
                f"SELECT column_name, data_type, is_nullable, column_default\n"
                f"FROM information_schema.columns\n"
                f"WHERE table_name = '{tbl}';"
            )
            copyable_cmd_label = "SQL Schema Fix & Inspection (Run in Destination DB)"
        elif "cannot cast 'object' type" in err_lower or "computerror: cannot cast" in err_lower:
            category = "SCHEMA_POLARS_TYPE_ERROR"
            user_env_issue = False
            diag_summary = f"Polars columnar transformation encountered unconverted Python Object/UUID columns in table '{tbl}'."
            fix_steps = [
                "Ensure source database driver columns (UUID/JSON) are sanitized to string before Polars cast operations.",
                "Re-run migration using updated Docker Agent image (data-migration-agent:latest)."
            ]
        else:
            diag_summary = f"ETL pipeline encountered an unexpected error during stage '{stage}': {err_msg[:200]}"
            fix_steps = [
                "Review target database constraints and column mapping specifications.",
                "Verify source data quality and re-run execution job."
            ]

        # Build copyable container run command ONLY if it is an environment/connectivity/auth issue (Fix #3)
        if user_env_issue and copyable_cmd is None and job.agent:
            ag = job.agent
            cmd_lines = [
                "docker run -d \\",
                f"  --name {ag.agent_identifier or 'data-agent'} \\",
                "  --restart unless-stopped \\",
                "  --add-host=host.docker.internal:host-gateway \\",
                '  -e BACKEND_URL="http://host.docker.internal:8000" \\',
                f'  -e AGENT_TOKEN="AG_TOKEN_PLACEHOLDER" \\',
                f'  -e AGENT_ID="{ag.id}" \\',
                f'  -e AGENT_IDENTIFIER="{ag.agent_identifier}" \\',
            ]
            if ag.version:
                cmd_lines.append(f'  -e AGENT_VERSION="{ag.version}" \\')

            if ag.data_sources:
                src_i = 1
                dst_i = 1
                for ds in ag.data_sources:
                    role_str = (ds.role or "").lower().strip()
                    ds_type = (ds.type or "postgresql").lower().strip()
                    if role_str in ("source", "src"):
                        cmd_lines.append(f'  -e SRC_SRC_DB_{src_i}_TYPE="{ds_type}" \\')
                        cmd_lines.append(f'  -e SRC_SRC_DB_{src_i}_URL="{ds_type}://user:<SRC_SRC_DB_{src_i}_PASSWORD>@host.docker.internal:port/{ds.identifier}" \\')
                        src_i += 1
                    elif role_str in ("destination", "target", "dest"):
                        cmd_lines.append(f'  -e DEST_DST_DB_{dst_i}_TYPE="{ds_type}" \\')
                        cmd_lines.append(f'  -e DEST_DST_DB_{dst_i}_URL="{ds_type}://user:<DEST_DST_DB_{dst_i}_PASSWORD>@host.docker.internal:port/{ds.identifier}" \\')
                        cmd_lines.append(f'  -e DEST_DB_URL="{ds_type}://user:<DEST_DST_DB_{dst_i}_PASSWORD>@host.docker.internal:port/{ds.identifier}" \\')
                        dst_i += 1

            cmd_lines.append(f"  {settings.AGENT_DOCKER_IMAGE}")
            copyable_cmd = "\n".join(cmd_lines)
            copyable_cmd_label = "Copyable Container Fix Command (Password Placeholders Retained)"

        job.ai_diagnosis = {
            "summary": diag_summary,
            "root_cause_category": category,
            "is_user_environment_issue": user_env_issue,
            "fix_steps": fix_steps,
            "copyable_fix_command": copyable_cmd,
            "copyable_fix_label": copyable_cmd_label,
            "raw_error_snippet": err_msg[:500],
        }

        await session.commit()
        await session.refresh(job)
        return job


async def _run_diagnosis_background(job_id: uuid.UUID):
    """Background coroutine running AI failure diagnosis with fresh AsyncSession (Fix #1)."""
    async with AsyncSessionLocal() as fresh_session:
        try:
            await ExecutionService.diagnose_job_failure(fresh_session, job_id)
        except Exception as diag_err:
            logger.warning(f"Background AI failure diagnosis failed for job '{job_id}': {diag_err}")
