"""User ORM model."""

import uuid
from sqlalchemy import Boolean, ForeignKey, String, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
    )
    wecom_userid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # admin|store_manager|agent|landlord
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    username: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("StoreModel", backref="users")
