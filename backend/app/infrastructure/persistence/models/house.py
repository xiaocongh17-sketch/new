"""House ORM model."""

import uuid
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, ForeignKey, Index, Uuid, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class HouseModel(Base, TimestampMixin):
    __tablename__ = "houses"

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True
    )
    community: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    area: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    room_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rent_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    decoration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    floor_info: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    # AI collection fields
    building_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_parking: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    parking_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occupancy_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    tenant_cooperation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lease_expiry: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decoration_year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decoration_quality: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    viewing_password: Mapped[str | None] = mapped_column(String(32), nullable=True)
    listed_on_beike: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    list_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    list_duration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unsold_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    viewing_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase_year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_only_home: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tax_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    seller_motivation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ai_collected_fields: Mapped[str | None] = mapped_column(String(256), nullable=True)
    collector_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deal_probability: Mapped[int | None] = mapped_column(Integer, nullable=True)

    owner = relationship("UserModel", backref="houses", foreign_keys=[owner_id])

    __table_args__ = (
        Index("idx_houses_store_status", "store_id", "status"),
        Index("idx_houses_community", "community"),
    )
