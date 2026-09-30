"""
FastAPI Routes for User Domain & Authentication System
"""

import secrets
import urllib.parse
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import httpx
from jwt import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.email import send_password_reset_email
from app.core.redis_client import PasswordResetCache
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
)
from app.modules.users.users_dependencies import (
    get_current_active_user,
    get_current_user,
)
from app.modules.users.users_models import User
from app.modules.users.users_schemas import (
    ForgotPasswordRequest,
    GoogleAuthRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.modules.users.users_services import UserService

router = APIRouter(tags=["Authentication & Users"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Helper to set HTTP-only access and refresh token cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Helper to clear HTTP-only authentication cookies."""
    response.delete_cookie(key="access_token", path="/", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie(key="refresh_token", path="/", domain=settings.COOKIE_DOMAIN)


# -----------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# -----------------------------------------------------------------------------

@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register_user(
    payload: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account, hash the password, issue access (15 min) and
    refresh (7 day) tokens, and attach them via HTTP-only cookies.
    """
    user = await UserService.create_user(db, payload)

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    _set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(
        message="User account created successfully.",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login user and issue HTTP-only cookies",
)
async def login_user(
    payload: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user credentials, generate 15-minute access token and 7-day
    refresh token, and set HTTP-only cookies.
    """
    user = await UserService.authenticate_user(db, payload.email, payload.password)

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    _set_auth_cookies(response, access_token, refresh_token)

    return TokenResponse(
        message="Login successful.",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/auth/google/login",
    summary="Initiate Google OAuth 2.0 Authorization Flow",
)
async def google_oauth_login(response: Response):
    """
    Generate Google OAuth 2.0 Authorization URL with state token for CSRF protection,
    and return URL to redirect user to Google's authentication consent screen.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google Client ID is not configured on server.",
        )

    state = secrets.token_urlsafe(32)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        max_age=600,  # 10 minutes
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

    return {"url": auth_url, "message": "Redirect user to this URL"}


@router.get(
    "/auth/google/callback",
    response_class=RedirectResponse,
    summary="Handle Google OAuth 2.0 Authorization Callback",
)
async def google_oauth_callback(
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Callback endpoint for Google OAuth authorization code exchange.
    Verifies CSRF state, exchanges authorization code for tokens, verifies Google ID token,
    creates/links application user, sets HTTP-only session cookies, and redirects to frontend.
    """
    try:
        if error:
            err_msg = f"Google authorization failed: {error}"
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(err_msg)}",
                status_code=status.HTTP_302_FOUND
            )

        if not code:
            err_msg = "Authorization code missing from Google callback."
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(err_msg)}",
                status_code=status.HTTP_302_FOUND
            )

        saved_state = request.cookies.get("oauth_state")
        if saved_state and state and not secrets.compare_digest(saved_state, state):
            err_msg = "OAuth state verification failed (CSRF mismatch)."
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(err_msg)}",
                status_code=status.HTTP_302_FOUND
            )

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(token_url, data=token_data)
            res_data = res.json()

        if res.status_code != 200:
            err_msg = res_data.get("error_description") or res_data.get("error") or "Failed token exchange"
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(f'Google Token Exchange Error: {err_msg}')}",
                status_code=status.HTTP_302_FOUND
            )

        google_id_token = res_data.get("id_token")
        if not google_id_token:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote('Google response did not include id_token.')}",
                status_code=status.HTTP_302_FOUND
            )

        id_info = id_token.verify_oauth2_token(
            google_id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None,
            clock_skew_in_seconds=10,
        )

        google_sub = id_info.get("sub")
        email = id_info.get("email")
        name = id_info.get("name") or email.split("@")[0]
        email_verified = id_info.get("email_verified", True)

        if not google_sub or not email:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote('Google token missing sub or email claims.')}",
                status_code=status.HTTP_302_FOUND
            )

        user = await UserService.get_or_create_google_user(
            db, google_id=google_sub, email=email, name=name, email_verified=email_verified
        )

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        redirect_response = RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard",
            status_code=status.HTTP_302_FOUND
        )
        redirect_response.delete_cookie(key="oauth_state", path="/")
        _set_auth_cookies(redirect_response, access_token, refresh_token)

        return redirect_response

    except HTTPException as http_exc:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(http_exc.detail)}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as exc:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error={urllib.parse.quote(f'Google authentication failed: {str(exc)}')}",
            status_code=status.HTTP_302_FOUND
        )


@router.post(
    "/auth/google",
    response_model=TokenResponse,
    summary="Authenticate via Google OAuth ID Token (SPA / Popup Flow)",
)
async def google_auth_credential(
    payload: GoogleAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user using verified Google OAuth ID Token (SPA / Popup flow).
    Validates token signature via `google-auth` library against Google OAuth public keys,
    finds or creates user, and sets HTTP-only cookies.
    """
    try:
        id_info = id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None,
            clock_skew_in_seconds=10,
        )

        google_sub = id_info.get("sub")
        email = id_info.get("email")
        name = id_info.get("name") or email.split("@")[0]
        email_verified = id_info.get("email_verified", True)

        if not google_sub or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google Token claims.",
            )

        user = await UserService.get_or_create_google_user(
            db, google_id=google_sub, email=email, name=name, email_verified=email_verified
        )

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        _set_auth_cookies(response, access_token, refresh_token)

        return TokenResponse(
            message="Google authentication successful.",
            user=UserResponse.model_validate(user),
        )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {str(exc)}",
        )


@router.post(
    "/auth/logout",
    response_model=MessageResponse,
    summary="Logout user and clear HTTP-only cookies",
)
async def logout_user(response: Response):
    """Clear authentication cookies."""
    _clear_auth_cookies(response)
    return MessageResponse(message="Successfully logged out.")


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="Generate new access and refresh tokens (Token Rotation)",
)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Dedicated Token Refresh Endpoint.
    Reads `refresh_token` from HTTP-only cookie, validates token type == 'refresh',
    generates a NEW access token (15 mins) and NEW refresh token (7 days),
    and updates HTTP-only cookies (Token Rotation).
    """
    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing from HTTP-only cookie.",
        )

    try:
        payload = decode_jwt_token(token)
        user_id_str: Optional[str] = payload.get("sub")
        token_type: Optional[str] = payload.get("type")

        if not user_id_str or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload.",
            )

        user_id = uuid.UUID(user_id_str)
    except (PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token. Please log in again.",
        )

    user = await UserService.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active or valid.",
        )

    # Token Rotation: Issue new access token AND new refresh token
    new_access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)

    _set_auth_cookies(response, new_access_token, new_refresh_token)

    return TokenResponse(
        message="Tokens refreshed successfully.",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/auth/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset link (5-min expiration, 1-min cooldown via Redis)",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a 5-minute password reset link and dispatch it via Google Gmail SMTP.
    Rate-limited via Redis: Users must wait 60 seconds before requesting another reset email.
    """
    # 1. Check if user exists
    user = await UserService.get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please check your email or register.",
        )

    # Check if user registered via Google only without password
    if user.google_id and not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was registered using Google Sign-In. Please sign in with Google.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user account is deactivated.",
        )

    # 2. Check 1-minute rate limiting cooldown
    remaining_seconds = await PasswordResetCache.check_rate_limit(payload.email)
    if remaining_seconds is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining_seconds} seconds before requesting another password reset email.",
        )

    # 3. Generate cryptographic token and store in cache with 5-minute TTL
    token = secrets.token_urlsafe(32)
    ttl_seconds = settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES * 60
    await PasswordResetCache.set_reset_token(
        token=token,
        user_id=str(user.id),
        email=user.email,
        ttl_seconds=ttl_seconds,
    )

    # 4. Set 1-minute rate limiting cooldown lock
    await PasswordResetCache.set_rate_limit(
        email=payload.email,
        cooldown_seconds=settings.RESET_PASSWORD_COOLDOWN_SECONDS,
    )

    # 5. Dispatch email via Google SMTP (executed non-blocking in threadpool)
    await send_password_reset_email(
        to_email=user.email,
        reset_token=token,
        user_name=user.name,
    )

    return MessageResponse(
        message=f"Password reset link has been dispatched to {user.email}."
    )


@router.post(
    "/auth/reset-password",
    response_model=MessageResponse,
    summary="Reset password using 5-minute expiring token",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate password reset token from Redis, encrypt new password via bcrypt,
    update database record, and invalidate token immediately (single-use).
    """
    # 1. Fetch and validate token from Redis
    token_data = await PasswordResetCache.get_reset_token(payload.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset link is invalid or has expired (links expire after 5 minutes). Please request a new one.",
        )

    user_id_str = token_data.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted token payload. Please request a new password reset link.",
        )

    user_id = uuid.UUID(user_id_str)

    # 2. Update password in database with fresh bcrypt hash
    await UserService.reset_user_password(db, user_id, payload.new_password)

    # 3. Invalidate token immediately to ensure single-use protection
    await PasswordResetCache.delete_reset_token(payload.token)

    return MessageResponse(
        message="Password reset successfully. You can now log in with your new password."
    )


# -----------------------------------------------------------------------------
# USER PROFILE & CRUD ROUTES
# -----------------------------------------------------------------------------

@router.get(
    "/users/me",
    response_model=UserResponse,
    summary="Get current logged-in user profile",
)
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """Fetch profile of currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.put(
    "/users/me",
    response_model=UserResponse,
    summary="Update current logged-in user profile",
)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile details (name, email, password) for authenticated user."""
    updated_user = await UserService.update_user(db, current_user, payload)
    return UserResponse.model_validate(updated_user)


@router.delete(
    "/users/me",
    response_model=MessageResponse,
    summary="Delete current logged-in user account",
)
async def delete_my_account(
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete authenticated user account and cascade delete related records."""
    await UserService.delete_user(db, current_user)
    _clear_auth_cookies(response)
    return MessageResponse(message="Account deleted successfully.")


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user profile by UUID",
)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch user profile by UUID (Requires authentication)."""
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )
    return UserResponse.model_validate(user)


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users (Paginated)",
)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List registered users with pagination (Requires authentication)."""
    users = await UserService.list_users(db, skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]
