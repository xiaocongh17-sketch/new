"""User domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from ..value_objects.enums import UserRole


@dataclass
class User:
    id: uuid.UUID
    wecom_userid: str
    name: str
    role: UserRole
    store_id: uuid.UUID | None = None
    phone: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, wecom_userid: str, name: str, role: UserRole,
               store_id: uuid.UUID | None = None, phone: str | None = None) -> "User":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            wecom_userid=wecom_userid,
            name=name,
            role=role,
            store_id=store_id,
            phone=phone,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_landlord(self) -> bool:
        return self.role == UserRole.LANDLORD

    @property
    def is_agent(self) -> bool:
        return self.role == UserRole.AGENT

    @property
    def is_store_manager(self) -> bool:
        return self.role == UserRole.STORE_MANAGER

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
