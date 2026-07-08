"""Message ORM model."""

import uuid
from sqlalchemy import String, Text, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class MessageModel(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    msg_type: Mapped[str] = mapped_column(String(32), default="text", nullable=False)
    wecom_msg_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    conversation = relationship("ConversationModel", backref="messages")
    sender = relationship("UserModel", backref="messages")

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id", "created_at"),
    )
