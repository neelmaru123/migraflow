"""
Unit Tests for UK GDPR, Data Protection Act 2018 & PECR Compliance Controls
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.credential_sanitizer import CredentialSanitizer
from app.core.db import Base, get_db
from app.core.email import mask_email
from app.core.security import create_access_token
from app.main import app
from app.modules.users.users_models import User


def test_credential_sanitizer_pii_and_sql_masking():
    """Verify CredentialSanitizer redacts credentials, emails, and database constraint detail values."""
    raw_error = (
        'duplicate key value violates unique constraint "uq_users_email" '
        'DETAIL: Key (email)=(test.user@example.co.uk) already exists. '
        'conn_str: postgresql://admin:super_secret_pw@db.internal:5432/prod'
    )
    sanitized = CredentialSanitizer.mask_credentials(raw_error)

    assert "super_secret_pw" not in sanitized
    assert "test.user@example.co.uk" not in sanitized
    assert "***REDACTED***" in sanitized
    assert "***REDACTED_VALUE***" in sanitized or "***REDACTED_EMAIL***" in sanitized


def test_mask_email_function():
    """Verify mask_email redacts local part while retaining domain for audit trail."""
    assert mask_email("alice@example.com") == "a***e@example.com"
    assert mask_email("al@example.com") == "a*@example.com"
    assert mask_email("invalid_string") == "[REDACTED_EMAIL]"


@pytest.mark.asyncio
async def test_gdpr_endpoints_and_security_controls():
    """Test data portability export, IDOR authorization, and account enumeration defenses."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_maker() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    # Create two test users: User A (regular) and User B (regular)
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    async with session_maker() as s:
        user_a = User(
            id=user_a_id,
            email="usera@example.com",
            name="User A",
            is_active=True,
            is_superuser=False,
        )
        user_b = User(
            id=user_b_id,
            email="userb@example.com",
            name="User B",
            is_active=True,
            is_superuser=False,
        )
        from app.modules.agents.agents_models import Agent
        from app.modules.sources.sources_models import DataSource
        from app.modules.migration_plans.migration_plans_models import MigrationPlan

        agent_a = Agent(
            id=uuid.uuid4(),
            user_id=user_a_id,
            name="Production Local Agent",
            agent_identifier="agent-prod-01",
            status="online",
        )
        s.add_all([user_a, user_b, agent_a])
        await s.commit()

        source_a = DataSource(
            id=uuid.uuid4(),
            agent_id=agent_a.id,
            name="Source DB",
            type="postgresql",
            role="source",
            identifier="source_db_local",
        )
        plan_a = MigrationPlan(
            id=uuid.uuid4(),
            user_id=user_a_id,
            agent_id=agent_a.id,
            status="completed",
            plan_data={"version": "1.0"},
        )
        s.add_all([source_a, plan_a])
        await s.commit()

    token_a = create_access_token(subject=user_a_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", token_a)

        # 1. Test Article 20 Right to Data Portability (GET /api/v1/users/me/export)
        export_resp = await client.get("/api/v1/users/me/export")
        assert export_resp.status_code == 200, export_resp.text
        export_data = export_resp.json()
        assert export_data["user"]["email"] == "usera@example.com"
        assert len(export_data["agents"]) == 1
        assert export_data["agents"][0]["name"] == "Production Local Agent"
        assert export_data["agents"][0]["agent_identifier"] == "agent-prod-01"
        assert len(export_data["data_sources"]) == 1
        assert export_data["data_sources"][0]["name"] == "Source DB"
        assert len(export_data["migration_plans"]) == 1
        assert "exported_at" in export_data

        # 2. Test IDOR Protection on User Profile (GET /api/v1/users/{user_id})
        # User A attempting to access User B's profile directly
        idor_resp = await client.get(f"/api/v1/users/{user_b_id}")
        assert idor_resp.status_code == 403, "Regular user should NOT be able to view another user's profile"
        assert "Access forbidden" in idor_resp.json()["detail"]

        # User A accessing their own profile directly by UUID
        self_resp = await client.get(f"/api/v1/users/{user_a_id}")
        assert self_resp.status_code == 200
        assert self_resp.json()["id"] == str(user_a_id)

        # 3. Test User List IDOR Protection (GET /api/v1/users)
        # Regular user should only see themselves
        list_resp = await client.get("/api/v1/users")
        assert list_resp.status_code == 200
        users_list = list_resp.json()
        assert len(users_list) == 1
        assert users_list[0]["id"] == str(user_a_id)

        # 4. Test Account Enumeration Defense in Forgot Password
        # Non-existent account should return the identical 200 generic message
        forgot_nonexistent = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody_exists_here@unknown.com"},
        )
        assert forgot_nonexistent.status_code == 200
        assert "If an account matches" in forgot_nonexistent.json()["message"]

    app.dependency_overrides.clear()
    await engine.dispose()
