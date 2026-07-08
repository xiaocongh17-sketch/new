"""Unit tests for domain entities."""

import uuid
from decimal import Decimal
from app.domain.entities.user import User
from app.domain.entities.house import House
from app.domain.entities.store import Store
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.enums import (
    UserRole, HouseStatus, MessageType,
)


class TestUserEntity:
    def test_create_landlord(self):
        user = User.create(
            wecom_userid="wx_123",
            name="张三",
            role=UserRole.LANDLORD,
        )
        assert user.wecom_userid == "wx_123"
        assert user.name == "张三"
        assert user.role == UserRole.LANDLORD
        assert user.is_landlord is True
        assert user.is_agent is False
        assert user.is_active is True

    def test_create_agent(self):
        store_id = uuid.uuid4()
        user = User.create(
            wecom_userid="wx_456",
            name="李四",
            role=UserRole.AGENT,
            store_id=store_id,
            phone="13800138000",
        )
        assert user.store_id == store_id
        assert user.phone == "13800138000"
        assert user.is_agent is True

    def test_role_properties(self):
        admin = User.create(wecom_userid="a1", name="Admin", role=UserRole.ADMIN)
        sm = User.create(wecom_userid="m1", name="Mgr", role=UserRole.STORE_MANAGER)
        agent = User.create(wecom_userid="ag1", name="Agent", role=UserRole.AGENT)
        landlord = User.create(wecom_userid="l1", name="Landlord", role=UserRole.LANDLORD)

        assert admin.is_admin is True
        assert sm.is_store_manager is True
        assert agent.is_agent is True
        assert landlord.is_landlord is True


class TestHouseEntity:
    def test_create_house_calculates_unit_price(self):
        house = House.create(
            community="万科城",
            area=Decimal("89.50"),
            room_type="3室2厅2卫",
            rent_price=Decimal("3500"),
            owner_id=uuid.uuid4(),
            decoration="精装",
            floor_info="18/18",
        )
        assert house.community == "万科城"
        assert house.area == Decimal("89.50")
        assert house.room_type == "3室2厅2卫"
        assert house.rent_price == Decimal("3500")
        assert house.unit_price == Decimal("39.11")
        assert house.status == HouseStatus.ACTIVE

    def test_update_price_recalculates_unit_price(self):
        house = House.create(
            community="测试小区", area=Decimal("100"),
            room_type="3室2厅", rent_price=Decimal("3000"),
            owner_id=uuid.uuid4(),
        )
        house.update_price(Decimal("3500"))
        assert house.rent_price == Decimal("3500")
        assert house.unit_price == Decimal("35.00")

    def test_mark_rented(self):
        house = House.create(
            community="测试", area=Decimal("80"), room_type="2室1厅",
            rent_price=Decimal("2000"), owner_id=uuid.uuid4(),
        )
        house.mark_rented()
        assert house.status == HouseStatus.RENTED

    def test_mark_off(self):
        house = House.create(
            community="测试", area=Decimal("80"), room_type="2室1厅",
            rent_price=Decimal("2000"), owner_id=uuid.uuid4(),
        )
        house.mark_off()
        assert house.status == HouseStatus.OFF

    def test_negative_price_raises(self):
        import pytest
        house = House.create(
            community="测试", area=Decimal("80"), room_type="2室1厅",
            rent_price=Decimal("2000"), owner_id=uuid.uuid4(),
        )
        with pytest.raises(ValueError, match="Price must be positive"):
            house.update_price(Decimal("-100"))


class TestStoreEntity:
    def test_create_store(self):
        store = Store.create(
            name="锡上好房旗舰店",
            code="WXHQD",
            address="无锡市梁溪区",
            contact_phone="0510-12345678",
        )
        assert store.name == "锡上好房旗舰店"
        assert store.code == "WXHQD"
        assert store.is_active is True

    def test_deactivate_and_activate(self):
        store = Store.create(name="测试店", code="TEST")
        assert store.is_active is True
        store.deactivate()
        assert store.is_active is False
        store.activate()
        assert store.is_active is True


class TestConversationEntity:
    def test_create_conversation(self):
        user_id = uuid.uuid4()
        conv = Conversation.create(
            wecom_group_id="grp_123",
            participants=[user_id],
        )
        assert conv.wecom_group_id == "grp_123"
        assert user_id in conv.participants
        assert conv.context == {}

    def test_update_context(self):
        conv = Conversation.create(wecom_group_id="grp_123")
        conv.update_context({"community": "万科城"})
        assert conv.context["community"] == "万科城"

    def test_request_review(self):
        conv = Conversation.create(wecom_group_id="grp_123")
        conv.request_review()
        assert conv.status.value == "pending_review"

    def test_close(self):
        conv = Conversation.create(wecom_group_id="grp_123")
        conv.close()
        assert conv.status.value == "closed"


class TestMessageEntity:
    def test_create_text_message(self):
        conv_id = uuid.uuid4()
        user_id = uuid.uuid4()
        msg = Message.create(
            conversation_id=conv_id,
            sender_id=user_id,
            content="你好",
        )
        assert msg.conversation_id == conv_id
        assert msg.sender_id == user_id
        assert msg.content == "你好"
        assert msg.msg_type == MessageType.TEXT
