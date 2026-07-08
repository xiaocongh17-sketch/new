"""SQLAlchemy implementation of HouseRepository."""

import uuid
from decimal import Decimal
from sqlalchemy import select, func, delete as sa_delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.house import House
from app.domain.repositories.house_repository import HouseRepository, HouseFilter, Page
from app.domain.value_objects.enums import HouseStatus
from app.infrastructure.persistence.models.house import HouseModel


class SQLAlchemyHouseRepository(HouseRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: uuid.UUID) -> House | None:
        result = await self.session.execute(select(HouseModel).where(HouseModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_store(self, store_id: uuid.UUID | None = None,
                            filter: HouseFilter | None = None,
                            page: int = 1, page_size: int = 20) -> Page[House]:
        conditions = []
        if store_id is not None:
            conditions.append(HouseModel.store_id == store_id)
        query = select(HouseModel).where(*conditions) if conditions else select(HouseModel)
        count_query = select(func.count()).select_from(HouseModel).where(*conditions) if conditions else select(func.count()).select_from(HouseModel)

        if filter:
            conditions = []
            if filter.community:
                conditions.append(HouseModel.community.ilike(f"%{filter.community}%"))
            if filter.min_price is not None:
                conditions.append(HouseModel.rent_price >= filter.min_price)
            if filter.max_price is not None:
                conditions.append(HouseModel.rent_price <= filter.max_price)
            if filter.room_type:
                conditions.append(HouseModel.room_type == filter.room_type)
            if filter.status:
                conditions.append(HouseModel.status == filter.status)
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(HouseModel.created_at.desc()).offset(offset).limit(page_size)
        )
        items = [self._to_domain(m) for m in result.scalars().all()]

        return Page(items=items, total=total, page=page, page_size=page_size)

    async def save(self, house: House) -> House:
        model = self._to_orm(house)
        # Check if existing
        if house.id:
            existing = await self.session.get(HouseModel, house.id)
            if existing:
                for key, value in self._to_orm_dict(house).items():
                    if key != 'id' and key != 'created_at':
                        setattr(existing, key, value)
                await self.session.flush()
                await self.session.refresh(existing)
                return self._to_domain(existing)

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def delete(self, id: uuid.UUID) -> bool:
        result = await self.session.execute(
            sa_delete(HouseModel).where(HouseModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    def _to_domain(self, model: HouseModel) -> House:
        return House(
            id=model.id, community=model.community, area=model.area,
            room_type=model.room_type, rent_price=model.rent_price,
            owner_id=model.owner_id, store_id=model.store_id,
            address=model.address, unit_price=model.unit_price,
            decoration=model.decoration, floor_info=model.floor_info,
            building_type=model.building_type, total_floors=model.total_floors,
            has_parking=model.has_parking, parking_count=model.parking_count,
            occupancy_status=model.occupancy_status,
            tenant_cooperation=model.tenant_cooperation,
            lease_expiry=model.lease_expiry,
            decoration_year=model.decoration_year,
            decoration_quality=model.decoration_quality,
            key_location=model.key_location,
            viewing_password=model.viewing_password,
            listed_on_beike=model.listed_on_beike,
            list_price=model.list_price,
            list_duration=model.list_duration,
            unsold_reason=model.unsold_reason,
            viewing_count=model.viewing_count,
            purchase_year=model.purchase_year,
            is_only_home=model.is_only_home,
            tax_note=model.tax_note,
            seller_motivation=model.seller_motivation,
            ai_collected_fields=model.ai_collected_fields,
            collector_score=model.collector_score,
            deal_probability=model.deal_probability,
            status=HouseStatus(model.status) if model.status else HouseStatus.ACTIVE,
            created_at=model.created_at, updated_at=model.updated_at,
        )

    def _to_orm(self, domain: House) -> HouseModel:
        return HouseModel(
            id=domain.id, community=domain.community, area=domain.area,
            room_type=domain.room_type, rent_price=domain.rent_price,
            owner_id=domain.owner_id, store_id=domain.store_id,
            address=domain.address, unit_price=domain.unit_price,
            decoration=domain.decoration, floor_info=domain.floor_info,
            building_type=domain.building_type, total_floors=domain.total_floors,
            has_parking=domain.has_parking, parking_count=domain.parking_count,
            occupancy_status=domain.occupancy_status,
            tenant_cooperation=domain.tenant_cooperation,
            lease_expiry=domain.lease_expiry,
            decoration_year=domain.decoration_year,
            decoration_quality=domain.decoration_quality,
            key_location=domain.key_location,
            viewing_password=domain.viewing_password,
            listed_on_beike=domain.listed_on_beike,
            list_price=domain.list_price,
            list_duration=domain.list_duration,
            unsold_reason=domain.unsold_reason,
            viewing_count=domain.viewing_count,
            purchase_year=domain.purchase_year,
            is_only_home=domain.is_only_home,
            tax_note=domain.tax_note,
            seller_motivation=domain.seller_motivation,
            ai_collected_fields=domain.ai_collected_fields,
            collector_score=domain.collector_score,
            deal_probability=domain.deal_probability,
            status=domain.status.value if domain.status else "active",
        )

    def _to_orm_dict(self, domain: House) -> dict:
        return {
            'id': domain.id, 'community': domain.community, 'area': domain.area,
            'room_type': domain.room_type, 'rent_price': domain.rent_price,
            'owner_id': domain.owner_id, 'store_id': domain.store_id,
            'address': domain.address, 'unit_price': domain.unit_price,
            'decoration': domain.decoration, 'floor_info': domain.floor_info,
            'building_type': domain.building_type, 'total_floors': domain.total_floors,
            'has_parking': domain.has_parking, 'parking_count': domain.parking_count,
            'occupancy_status': domain.occupancy_status,
            'tenant_cooperation': domain.tenant_cooperation,
            'lease_expiry': domain.lease_expiry,
            'decoration_year': domain.decoration_year,
            'decoration_quality': domain.decoration_quality,
            'key_location': domain.key_location,
            'viewing_password': domain.viewing_password,
            'listed_on_beike': domain.listed_on_beike,
            'list_price': domain.list_price,
            'list_duration': domain.list_duration,
            'unsold_reason': domain.unsold_reason,
            'viewing_count': domain.viewing_count,
            'purchase_year': domain.purchase_year,
            'is_only_home': domain.is_only_home,
            'tax_note': domain.tax_note,
            'seller_motivation': domain.seller_motivation,
            'ai_collected_fields': domain.ai_collected_fields,
            'collector_score': domain.collector_score,
            'deal_probability': domain.deal_probability,
            'status': domain.status.value if domain.status else "active",
        }
