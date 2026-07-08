"""Store domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Store:
    id: uuid.UUID
    name: str
    code: str
    address: str | None = None
    contact_phone: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, name: str, code: str, address: str | None = None,
               contact_phone: str | None = None) -> "Store":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            name=name,
            code=code,
            address=address,
            contact_phone=contact_phone,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
