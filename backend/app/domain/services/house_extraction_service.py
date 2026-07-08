"""Domain service for extracting house information from natural language."""

from decimal import Decimal
from dataclasses import dataclass


@dataclass
class ExtractedHouseInfo:
    community: str | None = None
    area: Decimal | None = None
    room_type: str | None = None
    rent_price: Decimal | None = None
    decoration: str | None = None
    floor_info: str | None = None


@dataclass
class ExtractionResult:
    extracted: ExtractedHouseInfo
    missing_fields: list[str]
    is_complete: bool
    suggestion: str | None = None


REQUIRED_FIELDS = ["community", "area", "room_type", "rent_price"]

FIELD_PROMPTS = {
    "community": "请问您的小区名称是什么呢？",
    "area": "房子的面积大概是多少平方米呢？",
    "room_type": "请问是几室几厅的户型？",
    "rent_price": "您期望的租金大概是多少？",
    "decoration": "房子的装修情况怎么样？（毛坯/简装/精装/豪装）",
    "floor_info": "房子在几楼？总共多少层？",
}


class HouseExtractionService:
    """Domain service: validate extracted info and determine missing fields."""

    def get_missing_fields(self, info: ExtractedHouseInfo) -> list[str]:
        """Return list of required fields that are still missing."""
        missing = []
        if not info.community:
            missing.append("community")
        if info.area is None or info.area <= 0:
            missing.append("area")
        if not info.room_type:
            missing.append("room_type")
        if info.rent_price is None or info.rent_price <= 0:
            missing.append("rent_price")
        return missing

    def is_complete(self, info: ExtractedHouseInfo) -> bool:
        """Check if enough info has been collected to create a house listing."""
        return len(self.get_missing_fields(info)) == 0

    def merge_with_context(self, new_info: ExtractedHouseInfo,
                           existing: dict | None) -> ExtractedHouseInfo:
        """Merge newly extracted info with existing conversation context."""
        context = existing or {}
        return ExtractedHouseInfo(
            community=new_info.community or context.get("community"),
            area=new_info.area or context.get("area"),
            room_type=new_info.room_type or context.get("room_type"),
            rent_price=new_info.rent_price or context.get("rent_price"),
            decoration=new_info.decoration or context.get("decoration"),
            floor_info=new_info.floor_info or context.get("floor_info"),
        )

    def build_result(self, info: ExtractedHouseInfo) -> ExtractionResult:
        """Build the final extraction result with suggestion text."""
        missing = self.get_missing_fields(info)
        complete = len(missing) == 0

        suggestion = None
        if not complete:
            next_field = missing[0]
            suggestion = FIELD_PROMPTS.get(next_field, "请问还有其他信息可以补充吗？")

        return ExtractionResult(
            extracted=info,
            missing_fields=missing,
            is_complete=complete,
            suggestion=suggestion,
        )
