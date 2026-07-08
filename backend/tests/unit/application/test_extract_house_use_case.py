"""Tests for ExtractHouseInfoUseCase."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from pydantic import BaseModel
from app.application.use_cases.extract_house_info import ExtractHouseInfoUseCase
from app.domain.services.house_extraction_service import (
    HouseExtractionService, ExtractedHouseInfo,
)


class MockExtractOutput(BaseModel):
    community: str | None = None
    area: float | None = None
    room_type: str | None = None
    rent_price: float | None = None
    decoration: str | None = None
    floor_info: str | None = None


@pytest.fixture
def mock_ai():
    ai = AsyncMock()
    ai.structured_extract.return_value = MockExtractOutput(
        community="万科城",
        area=89.5,
        room_type="3室2厅2卫",
        rent_price=3500.0,
        decoration="精装",
        floor_info="18/18",
    )
    return ai


@pytest.fixture
def use_case(mock_ai):
    return ExtractHouseInfoUseCase(ai_model=mock_ai)


class TestExtractHouseInfoUseCase:
    async def test_extract_all_fields_success(self, use_case, mock_ai):
        """Should successfully extract all house fields from text."""
        result = await use_case.execute("我有万科城89.5平精装房要出租，3室2厅2卫，18楼总18层，租金3500")
        assert result["is_complete"] is True
        assert result["extracted_info"]["community"] == "万科城"
        assert result["extracted_info"]["area"] == 89.5
        assert result["extracted_info"]["room_type"] == "3室2厅2卫"
        assert result["extracted_info"]["rent_price"] == 3500.0
        assert result["extracted_info"]["decoration"] == "精装"
        assert len(result["missing_fields"]) == 0
        mock_ai.structured_extract.assert_called_once()

    async def test_extract_with_existing_context(self, use_case, mock_ai):
        """Should merge with existing context and show no missing fields."""
        existing = {"community": "万科城", "room_type": "3室2厅2卫"}
        mock_ai.structured_extract.return_value = MockExtractOutput(
            area=89.5, rent_price=3500.0,
        )
        result = await use_case.execute("面积89.5平，租金3500", existing_context=existing)
        assert result["is_complete"] is True
        assert result["extracted_info"]["community"] == "万科城"

    async def test_extract_missing_fields(self, use_case, mock_ai):
        """Should report missing fields when info is incomplete."""
        mock_ai.structured_extract.return_value = MockExtractOutput(community="万科城")
        result = await use_case.execute("我有一套万科城的房子")
        assert result["is_complete"] is False
        assert "area" in result["missing_fields"]
        assert "rent_price" in result["missing_fields"]
        assert "room_type" in result["missing_fields"]
        assert result["suggestion"] is not None

    async def test_extract_empty_text(self, use_case, mock_ai):
        """Should handle empty text gracefully."""
        mock_ai.structured_extract.return_value = MockExtractOutput()
        result = await use_case.execute("")
        assert result["is_complete"] is False
        assert len(result["missing_fields"]) == 4

    async def test_ai_extraction_failure(self, use_case, mock_ai):
        """Should return fallback response when AI call fails."""
        mock_ai.structured_extract.side_effect = Exception("API timeout")
        result = await use_case.execute("万科城89.5平")
        assert result["is_complete"] is False
        assert "抱歉" in result["suggestion"]
