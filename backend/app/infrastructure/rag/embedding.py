"""Embedding service for RAG using the configured AI model."""

from app.domain.interfaces.rag import Embedder
from app.infrastructure.ai.factory import get_ai_model


class EmbeddingService(Embedder):
    """Generate embeddings for RAG using the configured AI model."""

    def __init__(self):
        self.model = get_ai_model()

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a text string."""
        return await self.model.embed(text)

    async def embed_document(self, title: str, content: str) -> list[float]:
        """Generate embedding for a document (title + content combined)."""
        combined = f"{title}\n{content}"
        return await self.model.embed(combined)
