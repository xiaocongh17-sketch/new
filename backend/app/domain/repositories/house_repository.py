"""House repository interface."""

from abc import ABC, abstractmethod
import uuid
from decimal import Decimal
from dataclasses import dataclass
from typing import Generic, TypeVar

from ..entities.house import House

T = TypeVar("T")


@dataclass
class HouseFilter:
    community: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    room_type: str | None = None
    status: str | None = None
    store_id: uuid.UUID | None = None


@dataclass
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size if self.page_size > 0 else 0


class HouseRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> House | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_store(self, store_id: uuid.UUID,
                            filter: HouseFilter | None = None,
                            page: int = 1, page_size: int = 20) -> Page[House]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, house: House) -> House:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool:
        raise NotImplementedError
