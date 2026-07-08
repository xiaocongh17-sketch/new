"""Knowledge repository interface."""

from abc import ABC, abstractmethod
import uuid
from dataclasses import dataclass
from ..entities.knowledge import KnowledgeDocument


@dataclass
class SearchResult:
    document: KnowledgeDocument
    similarity: float


class KnowledgeRepository(ABC):
    @abstractmethod
    async def search_by_vector(self, embedding: list[float],
                               store_id: uuid.UUID | None = None,
                               limit: int = 10) -> list[SearchResult]:
        raise NotImplementedError

    @abstractmethod
    async def search_by_keyword(self, query: str,
                                store_id: uuid.UUID | None = None,
                                limit: int = 10) -> list[KnowledgeDocument]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def find_all(self, store_id: uuid.UUID | None = None,
                       category: str | None = None,
                       page: int = 1, page_size: int = 20) -> tuple[list[KnowledgeDocument], int]:
        raise NotImplementedError
