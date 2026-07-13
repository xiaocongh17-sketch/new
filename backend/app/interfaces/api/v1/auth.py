"""Authentication API routes."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from jose import jwt
from app.infrastructure.config.settings import settings
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.persistence import database as db_module
from app.interfaces.api.deps import require_user, get_user_repo
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.enums import UserRole
from app.interfaces.middleware.rate_limit import get_rate_limiter
from app.infrastructure.auth.password import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["认证"])
limiter = get_rate_limiter()


# ---- Request / Response Models ----


class LoginInput(BaseModel):
    wecom_userid: str | None = Field(None, description="企业微信用户ID")
    username: str | None = Field(None, description="用户名")
    password: str | None = Field(None, description="密码")


class RegisterInput(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=1, max_length=128)
    wecom_userid: str | None = None
    role: str = "agent"
    phone: str | None = None


class ChangePasswordInput(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class RefreshInput(BaseModel):
    refresh_token: str = Field(..., description="Refresh Token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    id: str
    username: str | None = None
    wecom_userid: str | None = None
    name: str
    role: str
    store_id: str | None = None
    phone: str | None = None
    is_active: bool


# ---- Helpers ----


def _create_tokens(user: User) -> TokenResponse:
    """Create access and refresh tokens for a user."""
    now = datetime.now(timezone.utc)
    access_payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "store_id": str(user.store_id) if user.store_id else None,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "type": "access",
    }
    refresh_payload = {
        "sub": str(user.id),
        "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
        "type": "refresh",
    }
    return TokenResponse(
        access_token=jwt.encode(access_payload, settings.jwt_secret_key, algorithm="HS256"),
        refresh_token=jwt.encode(refresh_payload, settings.jwt_secret_key, algorithm="HS256"),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


# ---- Endpoints ----


@router.post("/login", response_model=TokenResponse, summary="用户登录")
@limiter.limit("5/minute")
async def login(request: Request, input: LoginInput):
    """Login with WeCom user ID or username + password.

    Supports two modes:
    1. Legacy: provide wecom_userid only
    2. Password: provide username + password
    """
    if not input.wecom_userid and not input.username:
        raise HTTPException(status_code=422, detail="Must provide wecom_userid or username")

    async with db_module.async_session_factory() as session:
        repo = SQLAlchemyUserRepository(session)
        user = None

        # Password-based login
        if input.username and input.password:
            user = await repo.find_by_username(input.username)
            if not user or not user.password_hash:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            if not verify_password(input.password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid username or password")

        # Legacy wecom_userid login
        elif input.wecom_userid:
            user = await repo.find_by_wecom_userid(input.wecom_userid)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return _create_tokens(user)


@router.post("/register", response_model=TokenResponse, summary="注册新用户")
@limiter.limit("3/minute")
async def register(request: Request, input: RegisterInput):
    """Register a new user with username and password."""
    async with db_module.async_session_factory() as session:
        repo = SQLAlchemyUserRepository(session)

        # Check if username already exists
        existing = await repo.find_by_username(input.username)
        if existing:
            raise HTTPException(status_code=409, detail="Username already exists")

        user = User.create(
            wecom_userid=input.wecom_userid or input.username,
            name=input.name,
            role=UserRole(input.role),
            phone=input.phone,
            username=input.username,
            password=input.password,
        )
        user = await repo.save(user)
        await session.commit()

        return _create_tokens(user)


@router.post("/change-password", summary="修改密码")
async def change_password(input: ChangePasswordInput, current_user: User = Depends(require_user)):
    """Change password for current user."""
    if not current_user.password_hash:
        raise HTTPException(status_code=400, detail="Password not set for this account")

    if not verify_password(input.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    async with db_module.async_session_factory() as session:
        repo = SQLAlchemyUserRepository(session)
        user = await repo.find_by_id(current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.password_hash = hash_password(input.new_password)
        await repo.save(user)

    return {"message": "Password changed successfully"}


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
async def refresh_token(input: RefreshInput):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(input.refresh_token, settings.jwt_secret_key, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    now = datetime.now(timezone.utc)
    access_payload = {
        "sub": payload["sub"],
        "role": payload.get("role"),
        "store_id": payload.get("store_id"),
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "type": "access",
    }
    return TokenResponse(
        access_token=jwt.encode(access_payload, settings.jwt_secret_key, algorithm="HS256"),
        refresh_token="",  # Keep same refresh token
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserProfileResponse, summary="获取当前用户信息")
async def get_current_user_profile(
    current_user: User = Depends(require_user),
):
    """Return the profile of the currently authenticated user."""
    return UserProfileResponse(
        id=str(current_user.id),
        username=current_user.username,
        wecom_userid=current_user.wecom_userid,
        name=current_user.name,
        role=current_user.role.value,
        store_id=str(current_user.store_id) if current_user.store_id else None,
        phone=current_user.phone,
        is_active=current_user.is_active,
    )
