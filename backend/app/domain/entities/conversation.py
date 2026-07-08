"""Conversation domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..value_objects.enums import ConversationStatus


@dataclass
class Conversation:
    id: uuid.UUID
    wecom_group_id: str
    participants: list[uuid.UUID] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    status: ConversationStatus = ConversationStatus.ACTIVE
    store_id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, wecom_group_id: str,
               participants: list[uuid.UUID] | None = None,
               store_id: uuid.UUID | None = None) -> "Conversation":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            wecom_group_id=wecom_group_id,
            participants=participants or [],
            context={},
            status=ConversationStatus.ACTIVE,
            store_id=store_id,
            created_at=now,
            updated_at=now,
        )

    def update_context(self, new_info: dict) -> None:
        """Merge new extracted info into conversation context."""
        self.context.update(new_info)
        self.updated_at = datetime.now(timezone.utc)

    def request_review(self) -> None:
        """Mark conversation as pending human review (escalation)."""
        self.status = ConversationStatus.PENDING_REVIEW

    def close(self) -> None:
        self.status = ConversationStatus.CLOSED
