"""Integration test fixtures - SQLite in-memory, FastAPI test client, JWT auth.

Provides two sets of fixtures:

**Repository-level tests** (backward-compatible with test_repositories.py)
  ``engine``, ``session``, ``store_repo``, ``user_repo``, ``house_repo``,
  ``conv_repo``, ``sample_store``, ``sample_landlord``, ``sample_agent``,
  ``sample_house``
  Data is isolated via transaction rollback (no commit in fixtures).

**API-level tests** (new test_auth_api.py, test_houses_api.py, ...)
  ``test_db``        - factory for creating test sessions
  ``test_client``    - httpx.AsyncClient with overridden FastAPI deps
  ``test_store``     - committed store record
  ``test_user``      - committed AGENT user + ``auth_headers`` JWT
  ``test_landlord``  - committed LANDLORD user (house owner)
  ``test_admin_user``- committed ADMIN user + ``admin_auth_headers`` JWT
  ``test_house``     - committed house record
  Data is committed so the API (which uses its own sessions) can see it.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# ---------------------------------------------------------------------------
# Settings & URLs - pin test-friendly JWT values
# ---------------------------------------------------------------------------
from app.infrastructure.config.settings import settings

settings.jwt_secret_key = "test-secret-key-for-testing-only"
settings.jwt_access_token_expire_minutes = 30
settings.jwt_refresh_token_expire_days = 7

# In-memory SQLite - no file I/O, fully isolated per engine
TEST_DATABASE_URL = "sqlite+aiosqlite://"

# ---------------------------------------------------------------------------
# ORM & domain imports (after settings so no circular-import surprises)
# ---------------------------------------------------------------------------
from app.infrastructure.persistence import database as db_module
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.repositories.store_repo import SQLAlchemyStoreRepository
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.persistence.repositories.house_repo import SQLAlchemyHouseRepository
from app.infrastructure.persistence.repositories.conversation_repo import (
    SQLAlchemyConversationRepository,
)
from app.domain.entities.store import Store
from app.domain.entities.user import User
from app.domain.entities.house import House
from app.domain.value_objects.enums import UserRole
from app.main import app


# ===================================================================
# In-memory engine (fresh per test, no event-loop scope conflicts)
# ===================================================================
@pytest_asyncio.fixture
async def engine():
    """Create a fresh in-memory engine per test."""
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


# ---------------------------------------------------------------------------
# Repository-layer fixtures (backward-compatible with test_repositories.py)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new session on the shared engine. Rolls back after the test."""
    connection = await engine.connect()
    transaction = await connection.begin()
    factory = async_sessionmaker(bind=connection, class_=AsyncSession, expire_on_commit=False)

    async with factory() as s:
        yield s
        await s.close()

    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def store_repo(session: AsyncSession):
    return SQLAlchemyStoreRepository(session)


@pytest_asyncio.fixture
async def user_repo(session: AsyncSession):
    return SQLAlchemyUserRepository(session)


@pytest_asyncio.fixture
async def house_repo(session: AsyncSession):
    return SQLAlchemyHouseRepository(session)


@pytest_asyncio.fixture
async def conv_repo(session: AsyncSession):
    return SQLAlchemyConversationRepository(session)


@pytest_asyncio.fixture
async def sample_store(store_repo) -> Store:
    store = Store.create(
        name="测试门店",
        code="TEST001",
        address="无锡市测试路1号",
        contact_phone="0510-88888888",
    )
    return await store_repo.save(store)


@pytest_asyncio.fixture
async def sample_landlord(user_repo, sample_store) -> User:
    user = User.create(
        wecom_userid="wx_landlord_001",
        name="测试房东",
        role=UserRole.LANDLORD,
        store_id=sample_store.id,
        phone="13800138001",
    )
    return await user_repo.save(user)


@pytest_asyncio.fixture
async def sample_agent(user_repo, sample_store) -> User:
    user = User.create(
        wecom_userid="wx_agent_001",
        name="测试业务员",
        role=UserRole.AGENT,
        store_id=sample_store.id,
        phone="13800138002",
    )
    return await user_repo.save(user)


@pytest_asyncio.fixture
async def sample_house(house_repo, sample_landlord, sample_store) -> House:
    house = House.create(
        community="万科城",
        area=Decimal("89.50"),
        room_type="3室2厅2卫",
        rent_price=Decimal("3500"),
        owner_id=sample_landlord.id,
        store_id=sample_store.id,
        decoration="精装",
        floor_info="18/18",
    )
    return await house_repo.save(house)


# ===================================================================
# API-level fixtures - fresh in-memory DB + commit-based data setup
# ===================================================================
@pytest_asyncio.fixture
async def test_db():
    """Create a temporary in-memory SQLite database and patch the module-level
    ``async_session_factory`` so everything - including endpoints that import it
    directly (e.g. ``/api/v1/auth/login``) - hits the test database.

    NOTE: ``Base.metadata.create_all`` is used instead of running Alembic
    migrations because the existing migrations contain PostgreSQL-specific
    constructs (``CREATE EXTENSION``, ``gen_random_uuid()``, ``jsonb``, etc.)
    that are incompatible with SQLite. The ORM models define the same schema
    and are the source of truth.

    Yields an ``async_sessionmaker`` bound to this database.
    """
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    # Patch the global factory so direct imports also use our test DB
    original = db_module.async_session_factory
    db_module.async_session_factory = factory
    try:
        yield factory
    finally:
        db_module.async_session_factory = original
        await _engine.dispose()


@pytest_asyncio.fixture
async def test_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Return an ``httpx.AsyncClient`` wired to the FastAPI app with:

    * ``get_session`` overridden to use the test database,
    * ``get_ai_model_dep`` overridden to return a mock (no real API calls).
    """
    factory = test_db

    from app.interfaces.api import deps

    async def override_get_session():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[deps.get_session] = override_get_session

    # Disable rate limiter for tests — the @limiter.limit decorator on
    # endpoints conflicts with httpx ASGITransport (the decorator expects
    # a starlette Response but receives a bare dict from FastAPI).
    from app.interfaces.middleware.rate_limit import get_rate_limiter
    rate_limiter = get_rate_limiter()
    rate_limiter.enabled = False

    async def override_ai_model():
        mock = AsyncMock()
        mock.chat.return_value = None
        mock.structured_extract.return_value = None
        mock.embed.return_value = [0.0] * 256
        return mock

    app.dependency_overrides[deps.get_ai_model_dep] = override_ai_model

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Committed data fixtures (used when the API must find records in the DB)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def test_store(test_db) -> Store:
    """Create and commit a store record."""
    factory = test_db
    async with factory() as session:
        repo = SQLAlchemyStoreRepository(session)
        store = Store.create(
            name="测试门店",
            code="TEST001",
            address="无锡市测试路1号",
            contact_phone="0510-88888888",
        )
        saved = await repo.save(store)
        await session.commit()
        return saved


@pytest_asyncio.fixture
async def test_landlord(test_db, test_store) -> User:
    """Create and commit a LANDLORD user (used as house owner)."""
    factory = test_db
    async with factory() as session:
        repo = SQLAlchemyUserRepository(session)
        user = User.create(
            wecom_userid="wx_landlord_001",
            name="测试房东",
            role=UserRole.LANDLORD,
            store_id=test_store.id,
            phone="13800138002",
        )
        saved = await repo.save(user)
        await session.commit()
        return saved


@pytest_asyncio.fixture
async def test_user(test_db, test_store) -> User:
    """Create and commit an AGENT user (default authenticated user)."""
    factory = test_db
    async with factory() as session:
        repo = SQLAlchemyUserRepository(session)
        user = User.create(
            wecom_userid="wx_test_agent",
            name="测试业务员",
            role=UserRole.AGENT,
            store_id=test_store.id,
            phone="13800138001",
        )
        saved = await repo.save(user)
        await session.commit()
        return saved


@pytest_asyncio.fixture
async def test_admin_user(test_db, test_store) -> User:
    """Create and commit an ADMIN user."""
    factory = test_db
    async with factory() as session:
        repo = SQLAlchemyUserRepository(session)
        user = User.create(
            wecom_userid="wx_admin_001",
            name="测试管理员",
            role=UserRole.ADMIN,
            store_id=test_store.id,
            phone="13800138000",
        )
        saved = await repo.save(user)
        await session.commit()
        return saved


@pytest_asyncio.fixture
async def test_house(test_db, test_store, test_landlord) -> House:
    """Create and commit a house listing."""
    factory = test_db
    async with factory() as session:
        repo = SQLAlchemyHouseRepository(session)
        house = House.create(
            community="万科城",
            area=Decimal("89.50"),
            room_type="3室2厅2卫",
            rent_price=Decimal("3500"),
            owner_id=test_landlord.id,
            store_id=test_store.id,
            decoration="精装",
            floor_info="18/18",
        )
        saved = await repo.save(house)
        await session.commit()
        return saved


# ---------------------------------------------------------------------------
# JWT auth-header helpers
# ---------------------------------------------------------------------------
def _make_token(user: User) -> dict[str, str]:
    """Build ``Authorization: Bearer <jwt>`` headers for *user*."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "store_id": str(user.store_id) if user.store_id else None,
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict[str, str]:
    """JWT auth headers for the default AGENT test user."""
    return _make_token(test_user)


@pytest_asyncio.fixture
async def admin_auth_headers(test_admin_user) -> dict[str, str]:
    """JWT auth headers for the ADMIN test user."""
    return _make_token(test_admin_user)
