"""Conversation repository interface."""

from abc import ABC, abstractmethod
import uuid
from ..entities.conversation import Conversation
from ..entities.message import Message


class ConversationRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> Conversation | None:
        raise NotImplementedError

    @abstractmethod
    async def find_active_by_group(self, wecom_group_id: str) -> Conversation | None:
        raise NotImplementedError

    @abstractmethod
    async def find_by_store(self, store_id: uuid.UUID,
                            page: int = 1,
                            page_size: int = 20) -> tuple[list[Conversation], int]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        raise NotImplementedError

    @abstractmethod
    async def add_message(self, message: Message) -> Message:
        raise NotImplementedError

    @abstractmethod
    async def get_messages(self, conversation_id: uuid.UUID,
                           limit: int = 50) -> list[Message]:
        raise NotImplementedError
