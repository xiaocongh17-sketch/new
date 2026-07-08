"""Integration tests for SQLAlchemy repositories."""

import uuid
from decimal import Decimal
import pytest
from app.domain.entities.store import Store
from app.domain.entities.user import User
from app.domain.entities.house import House
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.enums import UserRole, HouseStatus, MessageType
from app.domain.repositories.house_repository import HouseFilter


class TestStoreRepository:
    async def test_create_and_find(self, store_repo):
        store = Store.create(name="新门店", code="NEW001", address="地址")
        saved = await store_repo.save(store)
        assert saved.id is not None
        assert saved.name == "新门店"

        found = await store_repo.find_by_id(saved.id)
        assert found is not None
        assert found.code == "NEW001"

    async def test_find_by_code(self, store_repo, sample_store):
        found = await store_repo.find_by_code("TEST001")
        assert found is not None
        assert found.name == "测试门店"

        not_found = await store_repo.find_by_code("NONEXIST")
        assert not_found is None

    async def test_find_all(self, store_repo, sample_store):
        """Delete sample_store and create fresh stores to avoid conflict."""
        import sqlalchemy as sa
        from app.infrastructure.persistence.models.store import StoreModel
        await store_repo.session.execute(sa.delete(StoreModel))
        await store_repo.session.flush()

        await store_repo.save(Store.create(name="门店A", code="A001"))
        await store_repo.save(Store.create(name="门店B", code="B002"))
        stores = await store_repo.find_all()
        assert len(stores) == 2

    async def test_deactivate(self, store_repo, sample_store):
        sample_store.deactivate()
        saved = await store_repo.save(sample_store)
        assert saved.is_active is False


class TestUserRepository:
    async def test_create_landlord(self, user_repo, sample_store):
        user = User.create(
            wecom_userid="wx_new",
            name="新房东",
            role=UserRole.LANDLORD,
            store_id=sample_store.id,
        )
        saved = await user_repo.save(user)
        assert saved.id is not None
        assert saved.is_landlord is True

    async def test_find_by_wecom_userid(self, user_repo, sample_landlord):
        found = await user_repo.find_by_wecom_userid("wx_landlord_001")
        assert found is not None
        assert found.name == "测试房东"

    async def test_find_by_store(self, user_repo, sample_store, sample_landlord, sample_agent):
        users = await user_repo.find_by_store(sample_store.id)
        # sample_landlord + sample_agent (both in sample_store)
        assert len(users) >= 2

    async def test_find_by_id_not_found(self, user_repo):
        found = await user_repo.find_by_id(uuid.uuid4())
        assert found is None


class TestHouseRepository:
    async def test_create_house(self, house_repo, sample_landlord, sample_store):
        house = House.create(
            community="融创文旅城",
            area=Decimal("120.00"),
            room_type="4室2厅2卫",
            rent_price=Decimal("5000"),
            owner_id=sample_landlord.id,
            store_id=sample_store.id,
            decoration="精装",
        )
        saved = await house_repo.save(house)
        assert saved.id is not None
        assert saved.unit_price == Decimal("41.67")

    async def test_find_by_id(self, house_repo, sample_house):
        found = await house_repo.find_by_id(sample_house.id)
        assert found is not None
        assert found.community == "万科城"
        assert found.rent_price == Decimal("3500")

    async def test_find_by_store_paginated(self, house_repo, sample_house, sample_store):
        result = await house_repo.find_by_store(sample_store.id, page=1, page_size=10)
        assert result.total >= 1
        assert len(result.items) >= 1
        assert result.page == 1

    async def test_find_by_store_with_filter(self, house_repo, sample_house, sample_store):
        filter_obj = HouseFilter(community="万科城")
        result = await house_repo.find_by_store(sample_store.id, filter=filter_obj)
        assert result.total >= 1

        filter_obj = HouseFilter(community="不存在的")
        result = await house_repo.find_by_store(sample_store.id, filter=filter_obj)
        assert result.total == 0

    async def test_update_price(self, house_repo, sample_house):
        sample_house.update_price(Decimal("4000"))
        saved = await house_repo.save(sample_house)
        assert saved.rent_price == Decimal("4000")
        assert saved.unit_price == Decimal("44.69")

    async def test_mark_rented(self, house_repo, sample_house):
        sample_house.mark_rented()
        saved = await house_repo.save(sample_house)
        assert saved.status == HouseStatus.RENTED

    async def test_delete_house(self, house_repo, sample_house):
        deleted = await house_repo.delete(sample_house.id)
        assert deleted is True

        found = await house_repo.find_by_id(sample_house.id)
        assert found is None


class TestConversationRepository:
    async def test_create_conversation(self, conv_repo):
        conv = Conversation.create(
            wecom_group_id="grp_test_001",
            participants=[uuid.uuid4()],
        )
        saved = await conv_repo.save(conv)
        assert saved.id is not None
        assert saved.wecom_group_id == "grp_test_001"

    async def test_find_active_by_group(self, conv_repo):
        conv = Conversation.create(wecom_group_id="grp_active_001")
        await conv_repo.save(conv)

        found = await conv_repo.find_active_by_group("grp_active_001")
        assert found is not None
        assert found.status.value == "active"

    async def test_add_message(self, conv_repo):
        conv = Conversation.create(wecom_group_id="grp_msg_test")
        conv = await conv_repo.save(conv)

        msg = Message.create(
            conversation_id=conv.id,
            sender_id=uuid.uuid4(),
            content="测试消息",
        )
        saved_msg = await conv_repo.add_message(msg)
        assert saved_msg.id is not None
        assert saved_msg.content == "测试消息"

        messages = await conv_repo.get_messages(conv.id)
        assert len(messages) == 1
        assert messages[0].content == "测试消息"
