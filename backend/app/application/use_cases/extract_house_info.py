"""Use case: Extract structured house info from natural language using AI."""

import structlog
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from app.domain.services.house_extraction_service import (
    HouseExtractionService, ExtractedHouseInfo,
)
from app.domain.interfaces.ai_model import BaseAIModel, ChatMessage

logger = structlog.get_logger()


class HouseExtractionSchema(BaseModel):
    """Schema for AI structured output extraction."""
    community: Optional[str] = Field(None, description="小区名称")
    area: Optional[float] = Field(None, description="面积，单位：平方米")
    room_type: Optional[str] = Field(None, description="户型，如3室2厅2卫")
    rent_price: Optional[float] = Field(None, description="期望租金，单位：元/月")
    decoration: Optional[str] = Field(None, description="装修情况：毛坯/简装/精装/豪装")
    floor_info: Optional[str] = Field(None, description="楼层信息，如18/18")


class ExtractHouseInfoUseCase:
    """Extract structured house info from natural language using AI."""

    def __init__(self, ai_model: BaseAIModel,
                 extraction_service: HouseExtractionService | None = None):
        self.ai_model = ai_model
        self.extraction_service = extraction_service or HouseExtractionService()

    async def execute(self, raw_text: str,
                      existing_context: dict | None = None) -> dict:
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "你是一个房源信息提取助手。从用户的对话中提取房源相关信息，"
                    "以JSON格式输出。如果某个信息没有提到，不要猜测，设为null。"
                ),
            ),
            ChatMessage(role="user", content=raw_text),
        ]

        try:
            extracted = await self.ai_model.structured_extract(
                messages=messages,
                output_schema=HouseExtractionSchema,
            )
        except Exception as e:
            logger.error("ai_extraction_failed", error=str(e), text=raw_text)
            return {
                "extracted_info": {},
                "missing_fields": ["community", "area", "room_type", "rent_price"],
                "is_complete": False,
                "suggestion": "抱歉，我没有理解您的信息，能请您再说一遍吗？",
            }

        domain_info = ExtractedHouseInfo(
            community=extracted.community,
            area=Decimal(str(extracted.area)) if extracted.area else None,
            room_type=extracted.room_type,
            rent_price=Decimal(str(extracted.rent_price)) if extracted.rent_price else None,
            decoration=extracted.decoration,
            floor_info=extracted.floor_info,
        )

        merged = self.extraction_service.merge_with_context(domain_info, existing_context)
        result = self.extraction_service.build_result(merged)

        return {
            "extracted_info": {
                "community": merged.community,
                "area": float(merged.area) if merged.area else None,
                "room_type": merged.room_type,
                "rent_price": float(merged.rent_price) if merged.rent_price else None,
                "decoration": merged.decoration,
                "floor_info": merged.floor_info,
            },
            "missing_fields": result.missing_fields,
            "is_complete": result.is_complete,
            "suggestion": result.suggestion,
        }
