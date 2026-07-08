"""Message domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from ..value_objects.enums import MessageType


@dataclass
class Message:
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    msg_type: MessageType = MessageType.TEXT
    wecom_msg_id: str | None = None
    created_at: datetime | None = None

    @classmethod
    def create(cls, conversation_id: uuid.UUID, sender_id: uuid.UUID,
               content: str, msg_type: MessageType = MessageType.TEXT,
               wecom_msg_id: str | None = None) -> "Message":
        return cls(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            msg_type=msg_type,
            wecom_msg_id=wecom_msg_id,
            created_at=datetime.now(timezone.utc),
        )
