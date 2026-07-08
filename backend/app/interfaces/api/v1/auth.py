"""Authentication API routes."""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from jose import jwt
from app.infrastructure.config.settings import settings
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.persistence.database import async_session_factory
from app.interfaces.api.deps import require_user, get_user_repo
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginInput(BaseModel):
    wecom_userid: str = Field(..., description="企业微信用户ID")


class RefreshInput(BaseModel):
    refresh_token: str = Field(..., description="Refresh Token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse, summary="企业微信用户登录")
async def login(input: LoginInput):
    """Login with WeCom user ID.

    Simplified login for MVP. Production would use WeCom OAuth.
    """
    async with async_session_factory() as session:
        repo = SQLAlchemyUserRepository(session)
        user = await repo.find_by_wecom_userid(input.wecom_userid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

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


class UserProfileResponse(BaseModel):
    id: str
    wecom_userid: str
    name: str
    role: str
    store_id: str | None = None
    phone: str | None = None
    is_active: bool


@router.get("/me", response_model=UserProfileResponse, summary="获取当前用户信息")
async def get_current_user_profile(
    current_user: User = Depends(require_user),
):
    """Return the profile of the currently authenticated user."""
    return UserProfileResponse(
        id=str(current_user.id),
        wecom_userid=current_user.wecom_userid,
        name=current_user.name,
        role=current_user.role.value,
        store_id=str(current_user.store_id) if current_user.store_id else None,
        phone=current_user.phone,
        is_active=current_user.is_active,
    )
