"""Use cases for house management."""

import uuid
from decimal import Decimal
import structlog
from app.domain.entities.house import House
from app.domain.repositories.house_repository import HouseRepository, HouseFilter, Page

logger = structlog.get_logger()


class CreateHouseUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, community: str, area: Decimal, room_type: str,
                      rent_price: Decimal, owner_id: uuid.UUID,
                      decoration: str | None = None,
                      floor_info: str | None = None,
                      address: str | None = None,
                      store_id: uuid.UUID | None = None) -> House:
        house = House.create(
            community=community, area=area, room_type=room_type,
            rent_price=rent_price, owner_id=owner_id,
            store_id=store_id, decoration=decoration, floor_info=floor_info,
            address=address,
        )
        saved = await self.house_repo.save(house)
        logger.info("house_created", house_id=str(saved.id), owner_id=str(owner_id))
        return saved


class GetHouseUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, house_id: uuid.UUID) -> House | None:
        return await self.house_repo.find_by_id(house_id)


class UpdateHouseUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, house_id: uuid.UUID, **kwargs) -> House | None:
        house = await self.house_repo.find_by_id(house_id)
        if not house:
            return None

        if "rent_price" in kwargs:
            house.update_price(Decimal(str(kwargs.pop("rent_price"))))
        for key, value in kwargs.items():
            if hasattr(house, key) and value is not None:
                setattr(house, key, value)

        saved = await self.house_repo.save(house)
        logger.info("house_updated", house_id=str(house_id))
        return saved


class DeleteHouseUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, house_id: uuid.UUID) -> bool:
        result = await self.house_repo.delete(house_id)
        if result:
            logger.info("house_deleted", house_id=str(house_id))
        return result


class SearchHousesUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, store_id: uuid.UUID | None = None,
                      community: str | None = None,
                      min_price: Decimal | None = None,
                      max_price: Decimal | None = None,
                      room_type: str | None = None,
                      status: str | None = None,
                      page: int = 1, page_size: int = 20) -> Page[House]:
        filter_obj = HouseFilter(
            community=community, min_price=min_price, max_price=max_price,
            room_type=room_type, status=status, store_id=store_id,
        )
        return await self.house_repo.find_by_store(
            store_id=store_id,
            filter=filter_obj, page=page, page_size=page_size,
        )
