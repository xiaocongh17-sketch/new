"""Initialize SQLite database: create all tables and seed default data."""
import uuid
import os
import sys
from datetime import datetime, timezone

# Change to backend directory to pick up .env
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.persistence.models import Base
from app.infrastructure.config.settings import settings
from sqlalchemy import create_engine, text


def init_db():
    sync_url = settings.database_sync_url
    print(f"Database URL: {sync_url}")
    engine = create_engine(sync_url, echo=False)

    # 1. Create all tables
    print("\n=== Creating tables ===")
    Base.metadata.create_all(engine)
    print("Tables created!")

    # 2. Seed default store
    print("\n=== Seeding default store ===")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM stores WHERE code = 'DEFAULT' LIMIT 1")
        )
        existing_store = result.fetchone()

        if existing_store:
            store_id = existing_store[0]
            print(f"Default store exists: {store_id}")
        else:
            store_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).replace(tzinfo=None)
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
            print(f"Created default store: {store_id}")

    # 3. Seed admin user
    print("\n=== Seeding admin user ===")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM users WHERE wecom_userid = 'ww7ee68b692eb16095' LIMIT 1")
        )
        existing_user = result.fetchone()

        if existing_user:
            print(f"Admin user exists: {existing_user[0]}")
        else:
            user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).replace(tzinfo=None)
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
            print(f"Created admin user: {user_id}")

    # 4. Verify
    print("\n=== Verification ===")
    with engine.connect() as conn:
        tables_result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ).fetchall()
        print(f"Tables ({len(tables_result)}):")
        for t in tables_result:
            count = conn.execute(text(f"SELECT COUNT(*) FROM [{t[0]}]")).scalar()
            print(f"  - {t[0]}: {count} rows")

    engine.dispose()
    print("\nDatabase initialization complete!")


if __name__ == "__main__":
    init_db()
