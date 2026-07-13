"""User repository interface."""

from abc import ABC, abstractmethod
import uuid
from ..entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_wecom_userid(self, wecom_userid: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_store(self, store_id: uuid.UUID) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: User) -> User:
        raise NotImplementedError
