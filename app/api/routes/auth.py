"""Authentication routes."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.family import Family
from app.models.user import EmailVerificationToken, PasswordResetToken, RefreshToken, User
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services.email_service import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/register", response_model=dict)
async def register(
    response: Response,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user and family."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create family
    family = Family(name=data.family_name)
    db.add(family)
    await db.flush()

    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        family_id=family.id,
        role="admin",  # First user is admin
    )
    db.add(user)
    await db.flush()

    # Generate tokens
    access_token = create_access_token(str(user.id), str(user.family_id))
    refresh_token, refresh_expires = create_refresh_token(str(user.id))

    # Store refresh token hash
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expires,
    )
    db.add(db_token)

    # Create email verification token
    verification_token = generate_verification_token()
    email_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(verification_token),
        expires_at=datetime.utcnow()
        + timedelta(hours=settings.email_verification_expire_hours),
    )
    db.add(email_token)
    await db.commit()

    # Send verification email (don't fail registration if email fails)
    await send_verification_email(user.email, verification_token, user.full_name)

    # Set cookies
    _set_auth_cookies(response, access_token, refresh_token)

    return {
        "message": "Registration successful. Please check your email to verify your account.",
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            family_id=str(user.family_id),
            role=user.role,
        ),
    }


@router.post("/login", response_model=dict)
async def login(
    response: Response,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and set JWT cookies."""
    # Find user
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled",
        )

    # Generate tokens
    access_token = create_access_token(str(user.id), str(user.family_id))
    refresh_token, refresh_expires = create_refresh_token(str(user.id))

    # Store refresh token hash
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=refresh_expires,
    )
    db.add(db_token)

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Set cookies
    _set_auth_cookies(response, access_token, refresh_token)

    return {
        "message": "Login successful",
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            family_id=str(user.family_id),
            role=user.role,
        ),
    }


@router.post("/refresh", response_model=dict)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token with rotation."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    # Decode token
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is in database and not revoked
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked or invalid",
        )

    # Revoke old token (rotation)
    db_token.revoked_at = datetime.utcnow()

    # Get user
    result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Issue new tokens
    new_access = create_access_token(str(user.id), str(user.family_id))
    new_refresh, new_expires = create_refresh_token(str(user.id))

    # Store new refresh token
    new_db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        expires_at=new_expires,
    )
    db.add(new_db_token)
    await db.commit()

    # Set new cookies
    _set_auth_cookies(response, new_access, new_refresh)

    return {"message": "Tokens refreshed"}


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Logout user and revoke refresh token."""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        # Revoke the refresh token
        token_hash = hash_token(refresh_token)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        db_token = result.scalar_one_or_none()
        if db_token:
            db_token.revoked_at = datetime.utcnow()
            await db.commit()

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")
    response.delete_cookie("csrf_token")

    return {"message": "Logged out successfully"}


@router.post("/verify-email", response_model=dict)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Verify email using token."""
    token_hash = hash_token(token)

    # Find valid token
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > datetime.utcnow(),
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Get user and verify
    result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Mark token as used and user as verified
    db_token.used_at = datetime.utcnow()
    user.email_verified = True
    await db.commit()

    return {"message": "Email verified successfully"}


@router.post("/resend-verification", response_model=dict)
async def resend_verification(
    data: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resend verification email."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal if email exists
        return {"message": "If an account exists, a verification email has been sent."}

    if user.email_verified:
        return {"message": "Email is already verified."}

    # Create new verification token
    verification_token = generate_verification_token()
    email_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(verification_token),
        expires_at=datetime.utcnow()
        + timedelta(hours=settings.email_verification_expire_hours),
    )
    db.add(email_token)
    await db.commit()

    # Send verification email
    await send_verification_email(user.email, verification_token, user.full_name)

    return {"message": "If an account exists, a verification email has been sent."}


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal if email exists
        return {"message": "If an account exists, a password reset email has been sent."}

    # Create password reset token
    reset_token = generate_verification_token()
    db_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(reset_token),
        expires_at=datetime.utcnow()
        + timedelta(hours=settings.password_reset_expire_hours),
    )
    db.add(db_token)
    await db.commit()

    # Send reset email
    await send_password_reset_email(user.email, reset_token, user.full_name)

    return {"message": "If an account exists, a password reset email has been sent."}


@router.post("/reset-password", response_model=dict)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using token."""
    token_hash = hash_token(data.token)

    # Find valid token
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Get user
    result = await db.execute(select(User).where(User.id == db_token.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # Update password
    user.hashed_password = hash_password(data.new_password)
    db_token.used_at = datetime.utcnow()

    # Revoke all refresh tokens for security
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    for token in result.scalars().all():
        token.revoked_at = datetime.utcnow()

    await db.commit()

    return {"message": "Password reset successfully. Please log in with your new password."}


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set authentication cookies on response."""
    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.debug,  # Secure in production
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    # Refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth/refresh",  # Only sent to refresh endpoint
    )

    # CSRF token (readable by JavaScript)
    from app.core.security import generate_csrf_token

    response.set_cookie(
        key="csrf_token",
        value=generate_csrf_token(),
        httponly=False,
        secure=not settings.debug,
        samesite="lax",
    )
