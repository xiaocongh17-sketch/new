"""Initialize database: create all tables and seed default data.

Uses the SYNC database URL to bypass asyncpg connection issues.
Run:  cd backend && python init_db.py
"""

import uuid
from datetime import datetime, timezone

# Import all models so they register on Base.metadata
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.models.store import StoreModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.house import HouseModel
from app.infrastructure.persistence.models.conversation import ConversationModel
from app.infrastructure.persistence.models.message import MessageModel
from app.infrastructure.persistence.models.extracted_info import ExtractedHouseInfoModel
from app.infrastructure.persistence.models.knowledge import KnowledgeDocModel
from app.infrastructure.persistence.models.audit_log import AuditLogModel

from app.infrastructure.config.settings import settings
from sqlalchemy import create_engine, text


def init_db():
    """Create all tables and seed default data."""

    sync_url = settings.database_sync_url
    print(f"Connecting to: {sync_url.split('@')[1] if '@' in sync_url else sync_url}")
    engine = create_engine(sync_url, echo=False)

    # ── 1. Create all tables ──────────────────────────────────
    print("\n=== Creating all tables ===")
    Base.metadata.create_all(engine)
    print("✓ All tables created successfully.")

    # ── 2. Seed default store ─────────────────────────────────
    print("\n=== Seeding default store ===")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM stores WHERE code = 'DEFAULT' LIMIT 1")
        )
        existing_store = result.fetchone()

        if existing_store:
            store_id = existing_store[0]
            print(f"→ Default store already exists: {store_id}")
        else:
            store_id = uuid.uuid4()
            now = datetime.now(timezone.utc)
            conn.execute(
                text("""
                    INSERT INTO stores (id, name, code, address, contact_phone, is_active, created_at, updated_at)
                    VALUES (:id, :name, :code, :address, :phone, :active, :now, :now)
                """),
                {
                    "id": store_id,
                    "name": "默认门店",
                    "code": "DEFAULT",
                    "address": "系统默认门店",
                    "phone": "",
                    "active": True,
                    "now": now,
                },
            )
            conn.commit()
            print(f"✓ Created default store: {store_id}")

    # ── 3. Seed admin user ────────────────────────────────────
    print("\n=== Seeding admin user ===")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM users WHERE wecom_userid = 'ww7ee68b692eb16095' LIMIT 1")
        )
        existing_user = result.fetchone()

        if existing_user:
            print(f"→ Admin user already exists: {existing_user[0]}")
        else:
            user_id = uuid.uuid4()
            now = datetime.now(timezone.utc)
            conn.execute(
                text("""
                    INSERT INTO users (id, store_id, wecom_userid, name, role, phone, is_active, created_at, updated_at)
                    VALUES (:id, :store_id, :wecom_userid, :name, :role, :phone, :active, :now, :now)
                """),
                {
                    "id": user_id,
                    "store_id": store_id,
                    "wecom_userid": "ww7ee68b692eb16095",
                    "name": "管理员",
                    "role": "admin",
                    "phone": "",
                    "active": True,
                    "now": now,
                },
            )
            conn.commit()
            print(f"✓ Created admin user: {user_id} (wecom_userid=ww7ee68b692eb16095)")

    # ── 4. Verify ─────────────────────────────────────────────
    print("\n=== Verification ===")
    with engine.connect() as conn:
        tables = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        ).fetchall()
        print(f"Tables created ({len(tables)}):")
        for t in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t[0]}")).scalar()
            print(f"  • {t[0]}: {count} rows")

    engine.dispose()
    print("\n✅ Database initialization complete.")


if __name__ == "__main__":
    init_db()
