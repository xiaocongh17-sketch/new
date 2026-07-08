"""Store repository interface."""

from abc import ABC, abstractmethod
import uuid
from ..entities.store import Store


class StoreRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> Store | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_code(self, code: str) -> Store | None:
        raise NotImplementedError

    @abstractmethod
    async def find_all(self) -> list[Store]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, store: Store) -> Store:
        raise NotImplementedError
