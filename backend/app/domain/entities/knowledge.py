"""Knowledge document domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class KnowledgeDocument:
    id: uuid.UUID
    title: str
    content: str
    category: str
    store_id: uuid.UUID | None = None
    metadata_: dict = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, title: str, content: str, category: str,
               store_id: uuid.UUID | None = None,
               metadata: dict | None = None) -> "KnowledgeDocument":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            title=title,
            content=content,
            category=category,
            store_id=store_id,
            metadata_=metadata or {},
            created_at=now,
            updated_at=now,
        )
