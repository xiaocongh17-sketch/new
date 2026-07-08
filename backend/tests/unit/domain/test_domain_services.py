"""Unit tests for domain services."""

from decimal import Decimal
from app.domain.services.house_extraction_service import (
    HouseExtractionService,
    ExtractedHouseInfo,
)
from app.domain.services.conversation_manager import ConversationManager


class TestHouseExtractionService:
    def setup_method(self):
        self.service = HouseExtractionService()

    def test_complete_info_returns_no_missing(self):
        info = ExtractedHouseInfo(
            community="万科城",
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        missing = self.service.get_missing_fields(info)
        assert missing == []

    def test_missing_community(self):
        info = ExtractedHouseInfo(
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        missing = self.service.get_missing_fields(info)
        assert "community" in missing

    def test_missing_area_and_price(self):
        info = ExtractedHouseInfo(
            community="万科城",
            room_type="3室2厅",
        )
        missing = self.service.get_missing_fields(info)
        assert "area" in missing
        assert "rent_price" in missing

    def test_is_complete(self):
        info = ExtractedHouseInfo(
            community="万科城",
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        assert self.service.is_complete(info) is True

    def test_is_not_complete(self):
        info = ExtractedHouseInfo(community="万科城")
        assert self.service.is_complete(info) is False

    def test_merge_with_context(self):
        new_info = ExtractedHouseInfo(community="万科城")
        existing = {"room_type": "3室2厅", "area": Decimal("89.5")}
        merged = self.service.merge_with_context(new_info, existing)
        assert merged.community == "万科城"
        assert merged.room_type == "3室2厅"
        assert merged.area == Decimal("89.5")

    def test_merge_with_context_new_overrides(self):
        new_info = ExtractedHouseInfo(area=Decimal("100"))
        existing = {"area": Decimal("80"), "community": "旧小区"}
        merged = self.service.merge_with_context(new_info, existing)
        assert merged.area == Decimal("100")
        assert merged.community == "旧小区"

    def test_build_result_with_suggestion(self):
        info = ExtractedHouseInfo(community="万科城")
        result = self.service.build_result(info)
        assert result.is_complete is False
        assert "area" in result.missing_fields
        assert result.suggestion is not None

    def test_build_result_complete(self):
        info = ExtractedHouseInfo(
            community="万科城",
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        result = self.service.build_result(info)
        assert result.is_complete is True
        assert result.missing_fields == []
        assert result.suggestion is None


class TestConversationManager:
    def setup_method(self):
        self.manager = ConversationManager()

    def test_escalate_on_complaint(self):
        should, reason = self.manager.should_escalate("我要投诉你们的服务")
        assert should is True
        assert "投诉" in reason

    def test_escalate_on_legal(self):
        should, _ = self.manager.should_escalate("我要找律师处理")
        assert should is True

    def test_no_escalate_on_normal(self):
        should, _ = self.manager.should_escalate(
            "请问万科城3室2厅的租金大概多少？"
        )
        assert should is False

    def test_escalate_on_lawsuit(self):
        should, _ = self.manager.should_escalate("我要去法院起诉")
        assert should is True

    def test_get_next_prompt_community(self):
        prompt = self.manager.get_next_prompt(["community"])
        assert prompt is not None
        assert "小区" in prompt

    def test_get_next_prompt_none(self):
        prompt = self.manager.get_next_prompt([])
        assert prompt is None
