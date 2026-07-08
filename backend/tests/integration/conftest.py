"""Integration test fixtures — async DB session, repositories, sample data."""

import asyncio
import uuid
from decimal import Decimal
from typing import AsyncGenerator
from collections.abc import AsyncGenerator as AsyncGeneratorABC

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

# Mark all tests in this directory as asyncio
pytestmark = pytest.mark.asyncio(loop_scope="function")

from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.persistence.repositories.house_repo import SQLAlchemyHouseRepository
from app.infrastructure.persistence.repositories.store_repo import SQLAlchemyStoreRepository
from app.infrastructure.persistence.repositories.conversation_repo import SQLAlchemyConversationRepository
from app.domain.entities.store import Store
from app.domain.entities.user import User
from app.domain.entities.house import House
from app.domain.value_objects.enums import UserRole

# Use a test-specific database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create async engine for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing."""
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as s:
        yield s
        await s.rollback()


@pytest_asyncio.fixture
async def store_repo(session: AsyncSession):
    """Store repository fixture."""
    return SQLAlchemyStoreRepository(session)


@pytest_asyncio.fixture
async def user_repo(session: AsyncSession):
    """User repository fixture."""
    return SQLAlchemyUserRepository(session)


@pytest_asyncio.fixture
async def house_repo(session: AsyncSession):
    """House repository fixture."""
    return SQLAlchemyHouseRepository(session)


@pytest_asyncio.fixture
async def conv_repo(session: AsyncSession):
    """Conversation repository fixture."""
    return SQLAlchemyConversationRepository(session)


@pytest_asyncio.fixture
async def sample_store(store_repo) -> Store:
    """Create a sample store for testing."""
    store = Store.create(
        name="测试门店",
        code="TEST001",
        address="无锡市测试路1号",
        contact_phone="0510-88888888",
    )
    return await store_repo.save(store)


@pytest_asyncio.fixture
async def sample_landlord(user_repo, sample_store) -> User:
    """Create a sample landlord."""
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
    """Create a sample agent."""
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
    """Create a sample house."""
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
