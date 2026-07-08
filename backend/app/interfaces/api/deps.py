"""API dependency injection — JWT auth + RBAC + DB session."""

import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.config.settings import settings
from app.infrastructure.persistence.database import async_session_factory
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.persistence.repositories.house_repo import SQLAlchemyHouseRepository
from app.infrastructure.persistence.repositories.store_repo import SQLAlchemyStoreRepository
from app.infrastructure.persistence.repositories.conversation_repo import SQLAlchemyConversationRepository
from app.infrastructure.persistence.repositories.knowledge_repo import SQLAlchemyKnowledgeRepository
from app.domain.entities.user import User
from app.domain.value_objects.enums import UserRole
from app.infrastructure.ai.factory import get_ai_model
from typing import Callable, Awaitable

security = HTTPBearer(auto_error=False)


async def get_session():
    """Dependency: get async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_user_repo(session: AsyncSession = Depends(get_session)):
    return SQLAlchemyUserRepository(session)


async def get_house_repo(session: AsyncSession = Depends(get_session)):
    return SQLAlchemyHouseRepository(session)


async def get_store_repo(session: AsyncSession = Depends(get_session)):
    return SQLAlchemyStoreRepository(session)


async def get_conversation_repo(session: AsyncSession = Depends(get_session)):
    return SQLAlchemyConversationRepository(session)


async def get_knowledge_repo(session: AsyncSession = Depends(get_session)):
    return SQLAlchemyKnowledgeRepository(session)


async def get_ai_model_dep():
    """Dependency: get AI model instance."""
    return get_ai_model()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repo),
) -> User | None:
    """Validate JWT and return current user. Returns None if no token (for public endpoints)."""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user = await user_repo.find_by_id(uuid.UUID(user_id))
    if user is None or not user.is_active:
        return None
    return user


async def require_user(
    user: User | None = Depends(get_current_user),
) -> User:
    """Require authenticated user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def require_roles(allowed_roles: list[UserRole]) -> Callable[[User], Awaitable[User]]:
    """RBAC: check user has one of the allowed roles."""
    async def role_checker(user: User = Depends(require_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' not allowed for this endpoint",
            )
        return user
    return role_checker
