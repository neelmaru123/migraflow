"""
User Module Database CRUD Service Layer
"""

import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.modules.users.users_models import User
from app.modules.users.users_schemas import UserRegister, UserUpdate


class UserService:
    """Async database operations for User domain entity."""

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary key UUID."""
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        stmt = select(User).where(User.email == email.lower().strip())
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[User]:
        """Fetch user by Google subject ID."""
        stmt = select(User).where(User.google_id == google_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, payload: UserRegister) -> User:
        """
        Register new user account with bcrypt password hashing.
        Rejects registration if an account already exists with the email.
        Provides explicit error message if the existing account is a Google account.
        """
        existing = await UserService.get_user_by_email(db, payload.email)
        if existing:
            if existing.google_id and not existing.password_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email was created using Google Sign-In. Please sign in with Google.",
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists. Please log in.",
            )

        hashed_pwd = hash_password(payload.password)
        user = User(
            email=payload.email.lower().strip(),
            password_hash=hashed_pwd,
            name=payload.name.strip(),
            is_active=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_or_create_google_user(
        db: AsyncSession,
        google_id: str,
        email: str,
        name: str,
        email_verified: bool = True,
    ) -> User:
        """
        Authenticate or register a Google user account.
        Enforces strict account isolation:
        - If email_verified is False, rejects authentication.
        - If user with google_id exists -> Returns user (if active).
        - If user registered via Password and has no google_id -> Restricts Google login with explicit conflict error.
        - If user is new -> Creates new Google account.
        """
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email is not verified.",
            )

        # 1. Existing Google account by Google ID
        user = await UserService.get_user_by_google_id(db, google_id)
        if user:
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account is deactivated.",
                )
            return user

        # 2. Existing account by email
        user_by_email = await UserService.get_user_by_email(db, email)
        if user_by_email:
            if not user_by_email.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account is deactivated.",
                )

            if user_by_email.google_id and user_by_email.google_id != google_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email address is associated with a different Google account.",
                )

            # Restrict Google sign-in if account was created with email/password and hasn't been linked
            if user_by_email.password_hash and not user_by_email.google_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists using password authentication. Please log in with your email and password.",
                )

            user_by_email.google_id = google_id
            await db.commit()
            await db.refresh(user_by_email)
            return user_by_email

        # 3. Create new Google user
        new_user = User(
            email=email.lower().strip(),
            name=name.strip(),
            google_id=google_id,
            password_hash=None,
            is_active=True,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        """
        Validate user credentials against stored bcrypt password hash.
        Raises HTTP exceptions for deactivated or Google-only accounts.
        """
        user = await UserService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated.",
            )

        if not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account was created using Google Sign-In. Please sign in with Google.",
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        return user

    @staticmethod
    async def update_user(db: AsyncSession, user: User, payload: UserUpdate) -> User:
        """Update profile attributes and re-hash password if updated."""
        if payload.email is not None and payload.email.lower().strip() != user.email:
            existing = await UserService.get_user_by_email(db, payload.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email address is already in use by another account.",
                )
            user.email = payload.email.lower().strip()

        if payload.name is not None:
            user.name = payload.name.strip()

        if payload.password is not None:
            user.password_hash = hash_password(payload.password)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User) -> None:
        """Delete user account and cascade delete related records."""
        await db.delete(user)
        await db.commit()

    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 50) -> List[User]:
        """Fetch paginated list of users."""
        stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def reset_user_password(
        db: AsyncSession,
        user_id: uuid.UUID,
        new_password: str,
    ) -> User:
        """
        Encrypt and update user password following token verification.
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated.",
            )

        user.password_hash = hash_password(new_password)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def export_user_data(db: AsyncSession, user: User) -> dict:
        """
        Aggregate all user data across agents, migration plans, jobs, and sources
        for UK GDPR Article 20 Right to Data Portability.
        """
        from datetime import datetime, timezone
        from app.modules.agents.agents_models import Agent
        from app.modules.migration_plans.migration_plans_models import MigrationPlan
        from app.modules.execution.execution_models import MigrationJob
        from app.modules.sources.sources_models import DataSource

        # Fetch Agents
        agents_stmt = select(Agent).where(Agent.user_id == user.id)
        agents_res = await db.execute(agents_stmt)
        agents = agents_res.scalars().all()
        agent_ids = [a.id for a in agents]

        # Fetch Data Sources
        sources_list = []
        if agent_ids:
            sources_stmt = select(DataSource).where(DataSource.agent_id.in_(agent_ids))
            sources_res = await db.execute(sources_stmt)
            sources = sources_res.scalars().all()
            for s in sources:
                sources_list.append({
                    "id": str(s.id),
                    "agent_id": str(s.agent_id),
                    "name": getattr(s, "name", ""),
                    "type": getattr(s, "type", ""),
                    "role": getattr(s, "role", "source"),
                    "identifier": getattr(s, "identifier", ""),
                    "status": getattr(s, "status", "untested"),
                    "created_at": s.created_at.isoformat() if getattr(s, "created_at", None) else None,
                })

        # Fetch Plans
        plans_stmt = select(MigrationPlan).where(MigrationPlan.user_id == user.id)
        plans_res = await db.execute(plans_stmt)
        plans = plans_res.scalars().all()
        plan_ids = [p.id for p in plans]

        # Fetch Jobs
        jobs_list = []
        if plan_ids:
            jobs_stmt = select(MigrationJob).where(MigrationJob.migration_plan_id.in_(plan_ids))
            jobs_res = await db.execute(jobs_stmt)
            jobs = jobs_res.scalars().all()
            for j in jobs:
                jobs_list.append({
                    "id": str(j.id),
                    "migration_plan_id": str(j.migration_plan_id),
                    "agent_id": str(j.agent_id) if getattr(j, "agent_id", None) else None,
                    "status": getattr(j, "status", "unknown"),
                    "is_dry_run": getattr(j, "is_dry_run", False),
                    "progress": getattr(j, "progress", 0.0),
                    "total_rows": getattr(j, "total_rows", 0),
                    "processed_rows": getattr(j, "processed_rows", 0),
                    "successful_rows": getattr(j, "successful_rows", 0),
                    "failed_rows": getattr(j, "failed_rows", 0),
                    "started_at": j.started_at.isoformat() if getattr(j, "started_at", None) else None,
                    "completed_at": j.completed_at.isoformat() if getattr(j, "completed_at", None) else None,
                    "created_at": j.created_at.isoformat() if getattr(j, "created_at", None) else None,
                })

        agents_data = [
            {
                "id": str(a.id),
                "name": getattr(a, "name", ""),
                "agent_identifier": getattr(a, "agent_identifier", ""),
                "status": getattr(a, "status", "offline"),
                "version": getattr(a, "version", None),
                "last_seen_at": a.last_seen_at.isoformat() if getattr(a, "last_seen_at", None) else None,
                "idle_since": a.idle_since.isoformat() if getattr(a, "idle_since", None) else None,
                "created_at": a.created_at.isoformat() if getattr(a, "created_at", None) else None,
                "updated_at": a.updated_at.isoformat() if getattr(a, "updated_at", None) else None,
            }
            for a in agents
        ]

        plans_data = [
            {
                "id": str(p.id),
                "status": getattr(p, "status", "draft"),
                "agent_id": str(p.agent_id) if getattr(p, "agent_id", None) else None,
                "ai_model": getattr(p, "ai_model", None),
                "confidence_score": getattr(p, "confidence_score", 1.0),
                "approved_version_number": getattr(p, "approved_version_number", None),
                "created_at": p.created_at.isoformat() if getattr(p, "created_at", None) else None,
                "updated_at": p.updated_at.isoformat() if getattr(p, "updated_at", None) else None,
            }
            for p in plans
        ]

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "is_active": user.is_active,
                "is_superuser": getattr(user, "is_superuser", False),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            },
            "agents": agents_data,
            "migration_plans": plans_data,
            "migration_jobs": jobs_list,
            "data_sources": sources_list,
        }

