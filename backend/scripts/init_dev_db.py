"""Initialize development database — create DB, run migrations, seed data."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.config.settings import settings


async def init_db():
    print(f"[1/4] Connecting to PostgreSQL at {settings.pg_host}:{settings.pg_port}...")
    # Try to create database if not exists (connect to default 'postgres' db first)
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            user=settings.pg_user,
            password=settings.pg_password,
            database="postgres",
        )
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", settings.pg_database
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{settings.pg_database}"')
            print(f"[1/4] Database '{settings.pg_database}' created.")
        else:
            print(f"[1/4] Database '{settings.pg_database}' already exists.")
        await conn.close()
    except Exception as e:
        print(f"[1/4] ERROR: Could not connect to PostgreSQL: {e}")
        print("Make sure Docker PostgreSQL is running: cd docker && docker compose up -d db")
        sys.exit(1)

    # Run Alembic migrations
    print("[2/4] Running Alembic migrations...")
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("[2/4] Migrations up to date.")

    # Seed data
    print("[3/4] Seeding data...")
    from app.infrastructure.persistence.database import async_session_factory
    async with async_session_factory() as session:
        from app.infrastructure.persistence.repositories.store_repo import SQLAlchemyStoreRepository
        from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
        from app.domain.entities.store import Store
        from app.domain.entities.user import User
        from app.domain.value_objects.enums import UserRole

        store_repo = SQLAlchemyStoreRepository(session)
        user_repo = SQLAlchemyUserRepository(session)

        # Check if seed data exists
        existing_stores = await store_repo.find_all()
        if existing_stores:
            print("[3/4] Seed data already exists, skipping.")
            return

        # Create sample store
        store = Store.create(name="示范门店", code="DEMO001", address="无锡市示范路88号", contact_phone="0510-88886666")
        store = await store_repo.save(store)
        print(f"  Created store: {store.name}")

        # Create sample users
        users_data = [
            ("admin", "管理员", UserRole.ADMIN),
            ("agent01", "张业务员", UserRole.AGENT),
            ("agent02", "李业务员", UserRole.AGENT),
            ("landlord01", "王房东", UserRole.LANDLORD),
        ]
        for wecom_id, name, role in users_data:
            user = User.create(wecom_userid=wecom_id, name=name, role=role, store_id=store.id)
            user = await user_repo.save(user)
            print(f"  Created user: {user.name} ({role.value})")

        await session.commit()
    print("[3/4] Seed data created.")

    print("[4/4] Database initialization complete!")
    print(f"    Connection: postgresql://{settings.pg_user}:****@{settings.pg_host}:{settings.pg_port}/{settings.pg_database}")


if __name__ == "__main__":
    asyncio.run(init_db())
