"""Extracted house info ORM model (AI extraction results)."""

import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class ExtractedHouseInfoModel(Base, TimestampMixin):
    __tablename__ = "extracted_house_info"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    community: Mapped[str | None] = mapped_column(String(256), nullable=True)
    area: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    room_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rent_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    decoration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    floor_info: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    conversation = relationship("ConversationModel", backref="extracted_info")
