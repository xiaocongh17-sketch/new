"""RAG retriever: multi-strategy retrieval with result fusion."""

import uuid
import structlog
from app.domain.repositories.knowledge_repository import KnowledgeRepository, SearchResult

logger = structlog.get_logger()


class Retriever:
    """Multi-strategy retriever with Reciprocal Rank Fusion."""

    def __init__(self, knowledge_repo: KnowledgeRepository):
        self.knowledge_repo = knowledge_repo

    async def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        store_id: uuid.UUID | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Retrieve relevant documents using vector + keyword hybrid search."""
        vector_results = await self.knowledge_repo.search_by_vector(
            embedding=query_embedding,
            store_id=store_id,
            limit=top_k,
        )

        keyword_results = await self.knowledge_repo.search_by_keyword(
            query=query,
            store_id=store_id,
            limit=top_k,
        )

        fused = self._fusion_rank(vector_results, keyword_results, top_k)

        logger.info(
            "retrieval_complete",
            query_length=len(query),
            vector_results=len(vector_results),
            keyword_results=len(keyword_results),
            fused_results=len(fused),
        )
        return fused

    async def retrieve_keyword_only(
        self,
        query: str,
        store_id: uuid.UUID | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Retrieve using keyword search only (fallback when embedding unavailable)."""
        keyword_results = await self.knowledge_repo.search_by_keyword(
            query=query,
            store_id=store_id,
            limit=top_k,
        )
        return [
            SearchResult(document=doc, similarity=0.0)
            for doc in keyword_results
        ]

    def _fusion_rank(
        self,
        vector_results: list[SearchResult],
        keyword_results,
        top_k: int,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion (RRF) for combining two result sets."""
        doc_scores: dict[str, float] = {}

        for rank, result in enumerate(vector_results):
            doc_id = str(result.document.id)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1.0 / (rank + 60)

        for rank, doc in enumerate(keyword_results):
            doc_id = str(doc.id)
            score = 1.0 / (rank + 60)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + score

        ranked_ids = sorted(doc_scores, key=doc_scores.get, reverse=True)[:top_k]

        doc_map = {str(r.document.id): r for r in vector_results}
        for doc in keyword_results:
            doc_map[str(doc.id)] = SearchResult(document=doc, similarity=0.0)

        return [doc_map[doc_id] for doc_id in ranked_ids if doc_id in doc_map]
