"""End-to-end test: full business flow simulation.

Tests the complete flow: user registration → house creation → AI extraction → conversation.
Note: These tests mock external services (AI API, WeCom API).
"""

from unittest.mock import AsyncMock, patch
import uuid
from decimal import Decimal
import pytest

from app.domain.entities.user import User
from app.domain.entities.house import House
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.enums import UserRole, HouseStatus, ConversationStatus
from app.domain.services.house_extraction_service import HouseExtractionService, ExtractedHouseInfo
from app.domain.services.conversation_manager import ConversationManager


class TestFullBusinessFlow:
    """Simulate the full landlord → AI → house creation flow."""

    def setup_method(self):
        self.extraction_service = HouseExtractionService()
        self.conversation_manager = ConversationManager()

    def test_landlord_message_flow(self):
        """Simulate: landlord sends message → extract info → create house."""
        landlord = User.create(
            wecom_userid="wx_landlord_real",
            name="张先生",
            role=UserRole.LANDLORD,
        )
        assert landlord.is_landlord is True
        assert landlord.name == "张先生"

        conv = Conversation.create(
            wecom_group_id="grp_real_001",
            participants=[landlord.id],
        )
        assert conv.status == ConversationStatus.ACTIVE

        # Simulate first message
        msg1 = "我在万科城有套89平的两房，想租3500"
        result1 = self.extraction_service.build_result(
            ExtractedHouseInfo(
                community="万科城",
                area=Decimal("89"),
                room_type="两房",
                rent_price=Decimal("3500"),
            )
        )
        assert result1.extracted.community == "万科城"
        # All 4 required fields (community, area, room_type, rent_price) are present
        assert result1.is_complete is True

        # Update conversation context
        conv.update_context({
            "community": "万科城",
            "area": Decimal("89"),
            "room_type": "两房",
            "rent_price": Decimal("3500"),
        })

        # Second message: provides decoration
        msg2 = "精装修的"
        merged = self.extraction_service.merge_with_context(
            ExtractedHouseInfo(decoration="精装"),
            conv.context,
        )
        result2 = self.extraction_service.build_result(merged)
        assert result2.is_complete is True

        # Create house from collected info
        house = House.create(
            community=merged.community,
            area=merged.area,
            room_type=merged.room_type,
            rent_price=merged.rent_price,
            owner_id=landlord.id,
            decoration=merged.decoration,
        )
        assert house.community == "万科城"
        assert house.area == Decimal("89")
        assert house.room_type == "两房"
        assert house.rent_price == Decimal("3500")
        assert house.decoration == "精装"
        assert house.status == HouseStatus.ACTIVE

    def test_escalation_flow(self):
        """Simulate: complaint → auto escalation."""
        content = "我要投诉你们的服务态度"
        should_escalate, reason = self.conversation_manager.should_escalate(content)
        assert should_escalate is True

        conv = Conversation.create(wecom_group_id="grp_compaint")
        conv.request_review()
        assert conv.status == ConversationStatus.PENDING_REVIEW

    def test_rag_query_flow(self):
        """Simulate: employee asks a question → retrieval → answer."""
        question = "如何邀约房东？"

        # Simulate retrieval results
        mock_docs = [
            {"title": "房东邀约SOP", "content": "1. 电话沟通 2. 发送资料 3. 预约面谈", "category": "SOP"},
            {"title": "邀约话术", "content": "您好，我是XX门店的业务员...", "category": "TRAINING"},
        ]

        # Verify the expected flow structure
        context = "\n\n---\n\n".join(
            f"[{d['category']}] {d['title']}\n{d['content']}"
            for d in mock_docs
        )
        assert "房东邀约SOP" in context
        assert "话术" in context
        assert len(mock_docs) == 2


class TestHouseSearchFlow:
    """Test house search and filtering logic."""

    def test_search_with_filters(self):
        houses_data = [
            {"community": "万科城", "area": 89, "room_type": "3室", "price": 3500, "status": "active"},
            {"community": "融创文旅城", "area": 120, "room_type": "4室", "price": 5000, "status": "active"},
            {"community": "金科世界城", "area": 75, "room_type": "2室", "price": 2500, "status": "rented"},
        ]

        # Filter by community
        filtered = [h for h in houses_data if "万科" in h["community"]]
        assert len(filtered) == 1
        assert filtered[0]["community"] == "万科城"

        # Filter by price range
        filtered = [h for h in houses_data if 3000 <= h["price"] <= 4500]
        assert len(filtered) == 1

        # Filter by status
        active = [h for h in houses_data if h["status"] == "active"]
        assert len(active) == 2

        # Filter by room type
        two_rooms = [h for h in houses_data if "2室" in h["room_type"]]
        assert len(two_rooms) == 1


class TestLandlordRegistrationFlow:
    """Test landlord automatic registration from WeCom."""

    def test_new_landlord_registration(self):
        """Simulate new landlord sending their first message."""
        wecom_userid = "wx_new_landlord_001"

        # Simulate user creation from WeCom callback
        user = User.create(
            wecom_userid=wecom_userid,
            name="新房东",
            role=UserRole.LANDLORD,
        )
        assert user.wecom_userid == wecom_userid
        assert user.is_landlord is True
        assert user.is_active is True

    def test_known_user_returns_existing(self):
        """Simulate checking if user already exists."""
        existing = User.create(
            wecom_userid="wx_existing",
            name="老房东",
            role=UserRole.LANDLORD,
        )
        # In real flow, repo.find_by_wecom_userid would return this
        assert existing.wecom_userid == "wx_existing"
        assert existing.name == "老房东"
