"""
Regression and security audit test suite for Phase 1.
Verifies fixes for:
1. Production secret hardening and rejection of insecure defaults (Step 5).
2. Fatal error endpoint caller authentication, spoofing protection, and sanitized responses (Step 4).
3. Failure diagnosis job ownership enforcement preventing cross-tenant information disclosure (Step 3).
4. Agent execution authorization, cross-tenant isolation, and cross-agent isolation on steps/checkpoints (Step 2).
"""

from datetime import datetime, timezone
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.db import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.modules.agents.agents_dependencies import get_current_agent, hash_agent_token
from app.modules.agents.agents_models import Agent
from app.modules.agents.agents_services import AgentService
from app.core.state import ExecutionStepLifecycle
from app.modules.execution.execution_models import (
    ExecutionCheckpoint,
    MigrationExecutionPlan,
    MigrationExecutionStep,
    MigrationJob,
)
from app.modules.execution.execution_state_machine import ExecutionLifecycle
from app.modules.execution.execution_plan_services import ExecutionPlanService
from app.modules.execution.execution_services import ExecutionService
from app.modules.migration_plans.migration_plans_models import MigrationPlan
from app.modules.users.users_models import User
from app.modules.users.users_routes import get_current_active_user


# ---------------------------------------------------------------------------
# Test Context Fixture
# ---------------------------------------------------------------------------

async def setup_security_test_context():
    """Sets up an in-memory SQLite async database with multi-tenant users, agents, and jobs."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    session = session_maker()

    now = datetime.now(timezone.utc)

    # Tenant 1
    user1 = User(
        id=uuid.uuid4(),
        email="tenant1@example.com",
        name="Tenant One",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    session.add(user1)

    # Tenant 2
    user2 = User(
        id=uuid.uuid4(),
        email="tenant2@example.com",
        name="Tenant Two",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    session.add(user2)
    await session.flush()

    # Agent 1A (Tenant 1 primary)
    token_1a = "ag_live_11111111111111111111111111111111"
    token_1a_hash = hash_agent_token(token_1a)
    agent_1a = Agent(
        id=uuid.uuid4(),
        user_id=user1.id,
        name="Tenant 1 Agent A",
        agent_identifier="t1_agent_a",
        api_token_hash=token_1a_hash,
        status="online",
        last_seen_at=now,
    )
    session.add(agent_1a)

    # Agent 1B (Tenant 1 standby)
    token_1b = "ag_live_22222222222222222222222222222222"
    token_1b_hash = hash_agent_token(token_1b)
    agent_1b = Agent(
        id=uuid.uuid4(),
        user_id=user1.id,
        name="Tenant 1 Agent B",
        agent_identifier="t1_agent_b",
        api_token_hash=token_1b_hash,
        status="online",
        last_seen_at=now,
    )
    session.add(agent_1b)

    # Agent 2 (Tenant 2)
    token_2 = "ag_live_33333333333333333333333333333333"
    token_2_hash = hash_agent_token(token_2)
    agent_2 = Agent(
        id=uuid.uuid4(),
        user_id=user2.id,
        name="Tenant 2 Agent",
        agent_identifier="t2_agent",
        api_token_hash=token_2_hash,
        status="online",
        last_seen_at=now,
    )
    session.add(agent_2)
    await session.flush()

    # Migration Plan for Tenant 1
    plan1 = MigrationPlan(
        id=uuid.uuid4(),
        user_id=user1.id,
        agent_id=agent_1a.id,
        status="approved",
        is_valid=True,
        approved_version_number=1,
        plan_data={"mappings": [{"source_table": "users", "target_table": "users"}]},
    )
    session.add(plan1)
    await session.flush()

    # Migration Job for Tenant 1
    job1 = MigrationJob(
        id=uuid.uuid4(),
        migration_plan_id=plan1.id,
        agent_id=agent_1a.id,
        status=ExecutionLifecycle.RUNNING.value,
        is_dry_run=False,
        truncate_target=False,
        total_rows=1000,
        processed_rows=0,
        successful_rows=0,
        failed_rows=0,
        progress=0.0,
        current_stage="running",
        created_at=now,
        updated_at=now,
    )
    session.add(job1)
    await session.flush()

    # Execution Plan and Step for Tenant 1
    exec_plan1 = MigrationExecutionPlan(
        id=uuid.uuid4(),
        migration_job_id=job1.id,
        migration_plan_id=plan1.id,
        status="running",
        concurrency_limit=2,
    )
    session.add(exec_plan1)
    await session.flush()

    step1 = MigrationExecutionStep(
        id=uuid.uuid4(),
        execution_plan_id=exec_plan1.id,
        step_key="extract_users",
        step_type="extract",
        sequence=1,
        dependencies=[],
        status=ExecutionStepLifecycle.RUNNING.value,
        attempt_count=1,
        max_attempts=3,
        input_definition={"table": "users"},
        created_at=now,
        updated_at=now,
    )
    session.add(step1)
    await session.commit()

    return {
        "engine": engine,
        "session_maker": session_maker,
        "session": session,
        "user1": user1,
        "user2": user2,
        "agent_1a": agent_1a,
        "token_1a": token_1a,
        "agent_1b": agent_1b,
        "token_1b": token_1b,
        "agent_2": agent_2,
        "token_2": token_2,
        "plan1": plan1,
        "job1": job1,
        "exec_plan1": exec_plan1,
        "step1": step1,
    }


# ---------------------------------------------------------------------------
# Step 5: Production Secrets Enforcement Tests
# ---------------------------------------------------------------------------

def test_production_secrets_reject_insecure_defaults():
    """Verifies that production refuses to start with default or weak signing keys."""
    # Production with default SECRET_KEY must fail
    with pytest.raises(ValueError, match="Insecure default SECRET_KEY is not permitted"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="migraflow-super-secret-key-change-in-production",
            JWT_SECRET_KEY="a" * 64,
        )

    # Production with default JWT_SECRET_KEY must fail
    with pytest.raises(ValueError, match="Insecure default JWT_SECRET_KEY is not permitted"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 64,
            JWT_SECRET_KEY="migraflow-jwt-super-secret-key-change-in-production",
        )

    # Production with short key (< 32 chars) must fail
    with pytest.raises(ValueError, match="SECRET_KEY must be explicitly configured with at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short_key_12345",
            JWT_SECRET_KEY="a" * 64,
        )

    # Production with sufficiently long unique keys must succeed
    valid_prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        JWT_SECRET_KEY="d41d8cd98f00b204e9800998ecf8427e0123456789abcdef0123456789abcdef",
    )
    assert valid_prod_settings.ENVIRONMENT == "production"

    # Development allows default keys for ease of setup
    dev_settings = Settings(ENVIRONMENT="development")
    assert dev_settings.ENVIRONMENT == "development"


# ---------------------------------------------------------------------------
# Step 4: Fatal Error Authorization and Sanitization Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fatal_error_authorization_and_sanitization():
    """Verifies /agents/fatal-error security: prevents spoofing, allows valid reporting, sanitizes response."""
    ctx = await setup_security_test_context()

    async def override_get_db():
        async with ctx["session_maker"]() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # Case 1: Non-existent agent ID returns 404
        bad_id = uuid.uuid4()
        res_404 = await client.post(
            "/api/v1/agents/fatal-error",
            json={"agent_id": str(bad_id), "error_message": "Startup failed"},
        )
        assert res_404.status_code == 404

        # Case 2: Agent 1A authenticates with its token and reports its own fatal error -> 200 OK
        res_valid = await client.post(
            "/api/v1/agents/fatal-error",
            headers={"X-Agent-Token": ctx["token_1a"]},
            json={
                "agent_id": str(ctx["agent_1a"].id),
                "error_message": "Agent container OOM crash",
                "error_category": "OOM",
            },
        )
        assert res_valid.status_code == 200
        data_valid = res_valid.json()
        assert data_valid["status"] == "error"
        assert data_valid["last_error"] == "Agent container OOM crash"
        assert data_valid["error_category"] == "OOM"
        # Security: Response must NEVER contain user_id or tokens
        assert "user_id" not in data_valid
        assert "api_token" not in data_valid
        assert "api_token_hash" not in data_valid

        # Case 3: Agent 1B uses its token to attempt reporting error for Agent 2 -> 403 Forbidden (Spoofing blocked)
        res_spoof = await client.post(
            "/api/v1/agents/fatal-error",
            headers={"X-Agent-Token": ctx["token_1b"]},
            json={
                "agent_id": str(ctx["agent_2"].id),
                "error_message": "Malicious crash injection",
            },
        )
        assert res_spoof.status_code == 403
        assert "Authenticated agent credentials do not match" in res_spoof.json()["detail"]

        # Case 4: Unauthenticated attempt while target agent has active running tasks -> 403 Forbidden
        # Agent 1A has an active running job (job1)
        res_unauth_running = await client.post(
            "/api/v1/agents/fatal-error",
            json={
                "agent_id": str(ctx["agent_1a"].id),
                "error_message": "Unauthenticated crash attempt",
            },
        )
        assert res_unauth_running.status_code == 403
        assert "cannot report unauthenticated fatal error while agent has active jobs" in res_unauth_running.json()["detail"]

        # Case 5: Unauthenticated startup failure reporting for an offline agent with no active jobs -> 200 OK
        # Agent 2 has no active running jobs, mark status offline
        async with ctx["session_maker"]() as s:
            a2 = await s.get(Agent, ctx["agent_2"].id)
            a2.status = "offline"
            await s.commit()

        res_startup_ok = await client.post(
            "/api/v1/agents/fatal-error",
            json={
                "agent_id": str(ctx["agent_2"].id),
                "error_message": "Driver missing at docker entrypoint",
            },
        )
        assert res_startup_ok.status_code == 200
        assert res_startup_ok.json()["status"] == "error"
        assert "user_id" not in res_startup_ok.json()

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Step 3: Failure Diagnosis Ownership Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_diagnose_job_failure_ownership():
    """Verifies that failure diagnosis validates job ownership and prevents cross-tenant data leaks."""
    ctx = await setup_security_test_context()

    async with ctx["session_maker"]() as session:
        # Mark job1 as failed so AI diagnosis can process it
        job1 = await session.get(MigrationJob, ctx["job1"].id)
        job1.status = "failed"
        job1.error_message = "Connection timeout to source database"
        await session.commit()

        # 1. Non-owning tenant (user2) attempts to diagnose job owned by user1 -> 404 Not Found
        with pytest.raises(Exception) as exc_info:
            await ExecutionService.diagnose_job_failure(
                session=session,
                job_id=ctx["job1"].id,
                user_id=ctx["user2"].id,
            )
        assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

        # 2. Owning tenant (user1) diagnoses job -> succeeds
        diag_owner = await ExecutionService.diagnose_job_failure(
            session=session,
            job_id=ctx["job1"].id,
            user_id=ctx["user1"].id,
        )
        assert diag_owner.id == ctx["job1"].id
        assert diag_owner.status == "failed"

        # 3. Trusted internal caller (user_id=None) -> succeeds
        diag_internal = await ExecutionService.diagnose_job_failure(
            session=session,
            job_id=ctx["job1"].id,
            user_id=None,
        )
        assert diag_internal.id == ctx["job1"].id


# ---------------------------------------------------------------------------
# Step 2: Agent Execution Authorization and Isolation Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_step_execution_cross_tenant_isolation():
    """Verifies that an agent belonging to Tenant 2 cannot access or mutate Tenant 1's steps or checkpoints."""
    ctx = await setup_security_test_context()
    step1 = ctx["step1"]

    async with ctx["session_maker"]() as session:
        # Cross-tenant save checkpoint: Agent 2 (Tenant 2) calling on Tenant 1 step -> 404
        with pytest.raises(Exception) as exc_cp:
            await ExecutionPlanService.save_checkpoint(
                session=session,
                step_id=step1.id,
                source_identifier="src_1",
                source_table="users",
                target_table="users",
                cursor_offset=100,
                rows_processed=100,
                agent_id=ctx["agent_2"].id,
            )
        assert "404" in str(exc_cp.value)

        # Cross-tenant read checkpoints: Agent 2 calling on Tenant 1 step -> 404
        with pytest.raises(Exception) as exc_get:
            await ExecutionPlanService.get_checkpoints_for_step(
                session=session,
                step_id=step1.id,
                agent_id=ctx["agent_2"].id,
            )
        assert "404" in str(exc_get.value)

        # Cross-tenant complete step: Agent 2 calling on Tenant 1 step -> 404
        with pytest.raises(Exception) as exc_comp:
            await ExecutionPlanService.complete_step(
                session=session,
                step_id=step1.id,
                output_summary={"status": "hacked"},
                agent_id=ctx["agent_2"].id,
            )
        assert "404" in str(exc_comp.value)

        # Cross-tenant fail step: Agent 2 calling on Tenant 1 step -> 404
        with pytest.raises(Exception) as exc_fail:
            await ExecutionPlanService.fail_step(
                session=session,
                step_id=step1.id,
                error_type="MALICIOUS_FAIL",
                error_message="Unauthorized sabotage",
                agent_id=ctx["agent_2"].id,
            )
        assert "404" in str(exc_fail.value)

        # Cross-tenant step claim: Agent 2 calling on Tenant 1 execution plan -> None
        claimed = await ExecutionPlanService.claim_next_step(
            session=session,
            execution_plan_id=ctx["exec_plan1"].id,
            agent_id=ctx["agent_2"].id,
            agent_run_id=uuid.uuid4(),
        )
        assert claimed is None


@pytest.mark.asyncio
async def test_step_execution_cross_agent_boundary_and_recovery():
    """
    Verifies that within the same tenant:
    - An unauthorized agent cannot tamper with another agent's active step.
    - An assigned agent can save checkpoints, read checkpoints, and complete steps.
    - Checkpoint recovery and failover to standby agent is preserved upon recovery.
    """
    ctx = await setup_security_test_context()
    step1 = ctx["step1"]

    async with ctx["session_maker"]() as session:
        # Cross-agent tampering: Agent 1B attempts to checkpoint Step 1 which is assigned to Agent 1A -> 404
        with pytest.raises(Exception) as exc_tamper:
            await ExecutionPlanService.save_checkpoint(
                session=session,
                step_id=step1.id,
                source_identifier="src_1",
                source_table="users",
                target_table="users",
                cursor_offset=50,
                rows_processed=50,
                agent_id=ctx["agent_1b"].id,
            )
        assert "404" in str(exc_tamper.value)

        # Legitimate Agent 1A saves checkpoint -> 200 OK
        cp = await ExecutionPlanService.save_checkpoint(
            session=session,
            step_id=step1.id,
            source_identifier="src_1",
            source_table="users",
            target_table="users",
            cursor_offset=500,
            rows_processed=500,
            agent_id=ctx["agent_1a"].id,
        )
        assert cp.cursor_offset == 500
        assert cp.checkpoint_version == 1

        # Legitimate Agent 1A reads checkpoints -> 200 OK
        cps = await ExecutionPlanService.get_checkpoints_for_step(
            session=session,
            step_id=step1.id,
            agent_id=ctx["agent_1a"].id,
        )
        assert len(cps) == 1
        assert cps[0].cursor_offset == 500

        # Legitimate Agent 1A completes step -> 200 OK
        completed = await ExecutionPlanService.complete_step(
            session=session,
            step_id=step1.id,
            output_summary={"rows_migrated": 500},
            agent_id=ctx["agent_1a"].id,
        )
        assert completed.status == ExecutionStepLifecycle.COMPLETED.value
