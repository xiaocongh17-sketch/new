"""SQLAlchemy implementation of UserRepository."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.enums import UserRole
from app.infrastructure.persistence.models.user import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: uuid.UUID) -> User | None:
        result = await self.session.execute(select(UserModel).where(UserModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_wecom_userid(self, wecom_userid: str) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.wecom_userid == wecom_userid)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_store(self, store_id: uuid.UUID) -> list[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.store_id == store_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, user: User) -> User:
        model = self._to_orm(user)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            wecom_userid=model.wecom_userid,
            name=model.name,
            role=UserRole(model.role),
            store_id=model.store_id,
            phone=model.phone,
            username=model.username,
            password_hash=model.password_hash,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_orm(self, domain: User) -> UserModel:
        return UserModel(
            id=domain.id,
            wecom_userid=domain.wecom_userid,
            name=domain.name,
            role=domain.role.value,
            store_id=domain.store_id,
            phone=domain.phone,
            username=domain.username,
            password_hash=domain.password_hash,
            is_active=domain.is_active,
        )
