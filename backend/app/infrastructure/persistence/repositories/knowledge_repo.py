"""SQLAlchemy implementation of KnowledgeRepository."""

import uuid
from sqlalchemy import select, func, or_, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.knowledge import KnowledgeDocument
from app.domain.repositories.knowledge_repository import KnowledgeRepository, SearchResult
from app.infrastructure.persistence.models.knowledge import KnowledgeDocModel


class SQLAlchemyKnowledgeRepository(KnowledgeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_by_vector(self, embedding: list[float],
                               store_id: uuid.UUID | None = None,
                               limit: int = 10) -> list[SearchResult]:
        """Vector similarity search using pgvector."""
        from sqlalchemy import text

        if store_id:
            sql = text("""
                SELECT id, title, content, category, metadata,
                       1 - (embedding <=> :embedding::vector) as similarity
                FROM knowledge_docs
                WHERE embedding IS NOT NULL AND (store_id = :store_id OR store_id IS NULL)
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            params = {
                "embedding": str(embedding),
                "store_id": store_id,
                "limit": limit,
            }
        else:
            sql = text("""
                SELECT id, title, content, category, metadata,
                       1 - (embedding <=> :embedding::vector) as similarity
                FROM knowledge_docs
                WHERE embedding IS NOT NULL
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            params = {
                "embedding": str(embedding),
                "limit": limit,
            }

        try:
            result = await self.session.execute(sql, params)
            rows = result.fetchall()
            return [
                SearchResult(
                    document=KnowledgeDocument(
                        id=row.id, title=row.title, content=row.content,
                        category=row.category, metadata_=row.metadata or {},
                    ),
                    similarity=float(row.similarity),
                )
                for row in rows
            ]
        except Exception:
            # Fallback: return empty if vector column not ready
            return []

    async def search_by_keyword(self, query: str,
                                store_id: uuid.UUID | None = None,
                                limit: int = 10) -> list[KnowledgeDocument]:
        # Split query into tokens for flexible matching
        # First try full query, then fall back to token-based search
        tokens = self._tokenize(query)
        clauses = [
            or_(
                KnowledgeDocModel.title.ilike(f"%{query}%"),
                KnowledgeDocModel.content.ilike(f"%{query}%"),
            )
        ]
        # Also match by individual tokens (for Chinese text flexibility)
        for token in tokens[:5]:
            clauses.append(
                or_(
                    KnowledgeDocModel.title.ilike(f"%{token}%"),
                    KnowledgeDocModel.content.ilike(f"%{token}%"),
                )
            )

        conditions = [or_(*clauses)]
        if store_id:
            conditions.append(
                or_(KnowledgeDocModel.store_id == store_id, KnowledgeDocModel.store_id.is_(None))
            )

        result = await self.session.execute(
            select(KnowledgeDocModel)
            .where(*conditions)
            .limit(limit)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Split Chinese text into meaningful search tokens."""
        # Remove common stop words and question particles
        stop_words = {"怎么","如何","什么","怎么样","吗","呢","啊","吧","的","了","是","我","你","他","个","有","在","不","这","那","请","问","一下","一个","操作","流程","步骤","方法","指南","能不能","可以","可不可以"}
        tokens = []
        # Generate 2-4 char sliding windows
        for size in (4, 3, 2):
            for i in range(len(text) - size + 1):
                token = text[i:i+size]
                if token not in stop_words:
                    tokens.append(token)
        return list(dict.fromkeys(tokens))  # dedupe preserving order

    async def save(self, doc: KnowledgeDocument) -> KnowledgeDocument:
        model = self._to_orm(doc)
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def delete(self, id: uuid.UUID) -> bool:
        result = await self.session.execute(
            sa_delete(KnowledgeDocModel).where(KnowledgeDocModel.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def find_all(self, store_id: uuid.UUID | None = None,
                       category: str | None = None,
                       page: int = 1, page_size: int = 20) -> tuple[list[KnowledgeDocument], int]:
        conditions = []
        if store_id:
            # Show both store-specific docs AND global docs
            conditions.append(
                or_(KnowledgeDocModel.store_id == store_id, KnowledgeDocModel.store_id.is_(None))
            )
        if category:
            conditions.append(KnowledgeDocModel.category == category)

        count_query = select(func.count()).select_from(KnowledgeDocModel)
        query = select(KnowledgeDocModel)
        if conditions:
            count_query = count_query.where(*conditions)
            query = query.where(*conditions)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(KnowledgeDocModel.created_at.desc()).offset(offset).limit(page_size)
        )
        items = [self._to_domain(m) for m in result.scalars().all()]
        return items, total

    def _to_domain(self, model: KnowledgeDocModel) -> KnowledgeDocument:
        return KnowledgeDocument(
            id=model.id,
            title=model.title,
            content=model.content,
            category=model.category,
            store_id=model.store_id,
            metadata_=model.metadata_ or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_orm(self, domain: KnowledgeDocument) -> KnowledgeDocModel:
        return KnowledgeDocModel(
            id=domain.id,
            title=domain.title,
            content=domain.content,
            category=domain.category,
            store_id=domain.store_id,
            metadata=domain.metadata_,
        )
