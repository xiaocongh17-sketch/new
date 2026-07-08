"""RAG abstractions — ports for the domain layer."""

from abc import ABC, abstractmethod
import uuid


class Embedder(ABC):
    """Abstract interface for text embedding."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a text string."""
        raise NotImplementedError

    @abstractmethod
    async def embed_document(self, title: str, content: str) -> list[float]:
        """Generate embedding for a document."""
        raise NotImplementedError
