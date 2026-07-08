"""SQLAlchemy implementation of StoreRepository."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.store import Store
from app.domain.repositories.store_repository import StoreRepository
from app.infrastructure.persistence.models.store import StoreModel


class SQLAlchemyStoreRepository(StoreRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: uuid.UUID) -> Store | None:
        result = await self.session.execute(select(StoreModel).where(StoreModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_code(self, code: str) -> Store | None:
        result = await self.session.execute(select(StoreModel).where(StoreModel.code == code))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_all(self) -> list[Store]:
        result = await self.session.execute(select(StoreModel).order_by(StoreModel.name))
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, store: Store) -> Store:
        # Check if existing — merge/update, don't always insert
        if store.id:
            existing = await self.session.get(StoreModel, store.id)
            if existing:
                existing.name = store.name
                existing.code = store.code
                existing.address = store.address
                existing.contact_phone = store.contact_phone
                existing.is_active = store.is_active
                await self.session.flush()
                await self.session.refresh(existing)
                return self._to_domain(existing)

        model = self._to_orm(store)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: StoreModel) -> Store:
        return Store(
            id=model.id,
            name=model.name,
            code=model.code,
            address=model.address,
            contact_phone=model.contact_phone,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_orm(self, domain: Store) -> StoreModel:
        return StoreModel(
            id=domain.id,
            name=domain.name,
            code=domain.code,
            address=domain.address,
            contact_phone=domain.contact_phone,
            is_active=domain.is_active,
        )
