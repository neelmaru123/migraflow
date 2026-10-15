"""
Comprehensive unit tests for destructive operation approvals, safety gating, and bypass prevention.

Covers:
1. Truncation requested without approval (rejected 400).
2. Approval for a different target (rejected 400).
3. Approval for a different plan version (rejected 400).
4. Approved truncation (succeeds, job has truncate_target=True).
5. Non-destructive migration (succeeds, job has truncate_target=False).
6. Dry-run execution with truncate_target=True (succeeds, job and step have truncate_target=False).
7. Repeated execution or retry with idempotency key (returns existing job safely).
8. Expired approval rejection (rejected 400).
9. Invalidation on plan modification (rejected 400).
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.core.security import hash_password
from app.modules.agents.agents_models import Agent
from app.modules.execution.execution_models import DestructiveOperationApproval, MigrationJob
from app.modules.execution.execution_services import ExecutionService
from app.modules.execution.safety_services import DestructiveApprovalManager
from app.modules.migration_plans.migration_plans_models import MigrationPlan, MigrationPlanVersion
from app.modules.users.users_models import User


async def create_test_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    agent_id = uuid.uuid4()
    plan_id = uuid.uuid4()

    async with session_maker() as session:
        user = User(
            id=user_id,
            email="owner@example.com",
            name="Owner",
            password_hash=hash_password("Password123!"),
            is_active=True,
        )
        session.add(user)

        agent = Agent(
            id=agent_id,
            user_id=user_id,
            name="Test Agent",
            agent_identifier="test_agent",
            api_token_hash="dummy_hash",
            status="online",
            last_seen_at=now,
        )
        session.add(agent)

        plan = MigrationPlan(
            id=plan_id,
            user_id=user_id,
            agent_id=agent_id,
            status="approved",
            is_valid=True,
            approved_version_number=1,
            plan_data={
                "table_mappings": [
                    {
                        "source_table": "users",
                        "target_table": "dim_users",
                        "cleanup_action": "NONE",
                    }
                ]
            },
        )
        session.add(plan)
        await session.commit()

    return engine, session_maker, user_id, agent_id, plan_id


@pytest.mark.asyncio
async def test_truncation_requested_without_approval_rejected():
    """Case 1: Truncation requested without any approval must raise HTTP 400."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            with pytest.raises(HTTPException) as exc_info:
                await ExecutionService.create_execution_job(
                    session=session,
                    user_id=user_id,
                    plan_id=plan_id,
                    is_dry_run=False,
                    truncate_target=True,
                )
            assert exc_info.value.status_code == 400
            assert "Destructive operation(s) require explicit approval" in exc_info.value.detail
            assert "truncate_all_targets on *" in exc_info.value.detail
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approval_for_different_target_rejected():
    """Case 2: Approval for target table A does not approve global clean wipe or target B."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            # Create approval for dim_other_table instead of dim_users or *
            approval = await DestructiveApprovalManager.get_or_create_approval_request(
                session=session,
                plan_id=plan_id,
                plan_version_number=1,
                target_table="dim_other_table",
                operation_type="truncate_table",
            )
            await DestructiveApprovalManager.grant_approval(
                session=session,
                approval_id=approval.id,
                user_id=user_id,
            )

            # Global truncate requested -> must be rejected because dim_other_table does not cover dim_users or *
            with pytest.raises(HTTPException) as exc_info:
                await ExecutionService.create_execution_job(
                    session=session,
                    user_id=user_id,
                    plan_id=plan_id,
                    is_dry_run=False,
                    truncate_target=True,
                )
            assert exc_info.value.status_code == 400
            assert "Destructive operation(s) require explicit approval" in exc_info.value.detail
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approval_for_different_plan_version_rejected():
    """Case 3: Approval for version 1 cannot authorize execution of version 2."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            # Grant approval for version 1
            approval = await DestructiveApprovalManager.get_or_create_approval_request(
                session=session,
                plan_id=plan_id,
                plan_version_number=1,
                target_table="*",
                operation_type="truncate_all_targets",
            )
            await DestructiveApprovalManager.grant_approval(
                session=session,
                approval_id=approval.id,
                user_id=user_id,
            )

            # Update plan to version 2
            plan = await session.get(MigrationPlan, plan_id)
            plan.approved_version_number = 2
            session.add(
                MigrationPlanVersion(
                    migration_plan_id=plan.id,
                    version_number=2,
                    edit_type="refinement",
                    plan_data=plan.plan_data,
                )
            )
            await session.commit()

            # Try to execute version 2 with approval from version 1 -> rejected
            with pytest.raises(HTTPException) as exc_info:
                await ExecutionService.create_execution_job(
                    session=session,
                    user_id=user_id,
                    plan_id=plan_id,
                    is_dry_run=False,
                    truncate_target=True,
                )
            assert exc_info.value.status_code == 400
            assert "Destructive operation(s) require explicit approval for plan version 2" in exc_info.value.detail
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_approved_truncation_succeeds():
    """Case 4: Properly approved truncation creates a job with truncate_target=True."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            approval = await DestructiveApprovalManager.get_or_create_approval_request(
                session=session,
                plan_id=plan_id,
                plan_version_number=1,
                target_table="*",
                operation_type="truncate_all_targets",
            )
            await DestructiveApprovalManager.grant_approval(
                session=session,
                approval_id=approval.id,
                user_id=user_id,
            )

            job = await ExecutionService.create_execution_job(
                session=session,
                user_id=user_id,
                plan_id=plan_id,
                is_dry_run=False,
                truncate_target=True,
            )

            assert job.truncate_target is True
            assert job.is_dry_run is False
            assert job.status == "queued"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_non_destructive_migration_succeeds_without_approval():
    """Case 5: Normal non-destructive migration does not require destructive approval."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            job = await ExecutionService.create_execution_job(
                session=session,
                user_id=user_id,
                plan_id=plan_id,
                is_dry_run=False,
                truncate_target=False,
            )
            assert job.truncate_target is False
            assert job.is_dry_run is False
            assert job.status == "queued"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_dry_run_execution_never_destructive():
    """Case 6: Dry-run executions never perform destructive operations even if requested."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            # Request truncate_target=True on dry run WITHOUT any approval
            job = await ExecutionService.create_execution_job(
                session=session,
                user_id=user_id,
                plan_id=plan_id,
                is_dry_run=True,
                truncate_target=True,
            )
            assert job.is_dry_run is True
            assert job.truncate_target is False

            # Verify derived execution plan steps sanitize truncate_target
            exec_plan = await ExecutionService.get_execution_plan_for_job(
                session=session, job_id=job.id, user_id=user_id
            )
            assert exec_plan is not None
            pre_ddl_step = next(s for s in exec_plan.steps if s.step_key == "pre_ddl")
            assert pre_ddl_step.input_definition.get("truncate_target") is False
            assert pre_ddl_step.input_definition.get("is_dry_run") is True
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_idempotent_retry_preserves_state():
    """Case 7: Repeated execution with same idempotency key returns existing job safely."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            approval = await DestructiveApprovalManager.get_or_create_approval_request(
                session=session,
                plan_id=plan_id,
                plan_version_number=1,
                target_table="*",
                operation_type="truncate_all_targets",
            )
            await DestructiveApprovalManager.grant_approval(
                session=session,
                approval_id=approval.id,
                user_id=user_id,
            )

            job1 = await ExecutionService.create_execution_job(
                session=session,
                user_id=user_id,
                plan_id=plan_id,
                is_dry_run=False,
                truncate_target=True,
                idempotency_key="idempotency-key-12345",
            )

            # Retry with identical idempotency key
            job2 = await ExecutionService.create_execution_job(
                session=session,
                user_id=user_id,
                plan_id=plan_id,
                is_dry_run=False,
                truncate_target=True,
                idempotency_key="idempotency-key-12345",
            )

            assert job1.id == job2.id
            assert job2.truncate_target is True
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_expired_approval_rejected():
    """Case 8: Expired destructive approvals are rejected."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            approval = await DestructiveApprovalManager.get_or_create_approval_request(
                session=session,
                plan_id=plan_id,
                plan_version_number=1,
                target_table="*",
                operation_type="truncate_all_targets",
            )
            await DestructiveApprovalManager.grant_approval(
                session=session,
                approval_id=approval.id,
                user_id=user_id,
            )

            # Manually set expiration in the past
            approval_db = await session.get(DestructiveOperationApproval, approval.id)
            approval_db.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            await session.commit()

            with pytest.raises(HTTPException) as exc_info:
                await ExecutionService.create_execution_job(
                    session=session,
                    user_id=user_id,
                    plan_id=plan_id,
                    is_dry_run=False,
                    truncate_target=True,
                )
            assert exc_info.value.status_code == 400
            assert "Destructive operation(s) require explicit approval" in exc_info.value.detail
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_invalidated_approval_rejected():
    """Case 9: Invalidated approval cannot be used for execution."""
    engine, session_maker, user_id, agent_id, plan_id = await create_test_env()
    try:
        async with session_maker() as session:
            approval = await DestructiveApprovalManager.get_or_create_approval_request(
                session=session,
                plan_id=plan_id,
                plan_version_number=1,
                target_table="*",
                operation_type="truncate_all_targets",
            )
            await DestructiveApprovalManager.grant_approval(
                session=session,
                approval_id=approval.id,
                user_id=user_id,
            )

            # Invalidate all approvals for the plan
            await DestructiveApprovalManager.invalidate_all_for_plan(
                session=session,
                plan_id=plan_id,
                reason="Schema changed",
            )

            with pytest.raises(HTTPException) as exc_info:
                await ExecutionService.create_execution_job(
                    session=session,
                    user_id=user_id,
                    plan_id=plan_id,
                    is_dry_run=False,
                    truncate_target=True,
                )
            assert exc_info.value.status_code == 400
            assert "Destructive operation(s) require explicit approval" in exc_info.value.detail
    finally:
        await engine.dispose()
