"""Knowledge document ORM model with pgvector support."""

import uuid
from sqlalchemy import String, Text, ForeignKey, JSON, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class KnowledgeDocModel(Base, TimestampMixin):
    __tablename__ = "knowledge_docs"

    id: Mapped[uuid.UUID] = uuid_pk()
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("stores.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # SOP|TRAINING|FAQ|MARKET
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, default=dict, nullable=True
    )

    store = relationship("StoreModel", backref="knowledge_docs")

    __table_args__ = (
        Index("idx_knowledge_category", "category"),
        Index("idx_knowledge_store", "store_id"),
    )
