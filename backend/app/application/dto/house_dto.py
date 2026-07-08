"""Data transfer objects for house-related operations."""

from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from typing import Optional


class ExtractedHouseInfoDTO(BaseModel):
    community: Optional[str] = None
    area: Optional[Decimal] = None
    room_type: Optional[str] = None
    rent_price: Optional[Decimal] = None
    decoration: Optional[str] = None
    floor_info: Optional[str] = None


class ExtractHouseInfoInput(BaseModel):
    conversation_id: UUID
    raw_text: str
    existing_context: dict = Field(default_factory=dict)


class ExtractHouseInfoOutput(BaseModel):
    extracted_info: ExtractedHouseInfoDTO
    missing_fields: list[str]
    is_complete: bool
    suggestion: Optional[str] = None


class HouseResponse(BaseModel):
    id: UUID
    community: str
    area: Decimal
    room_type: str
    rent_price: Decimal
    unit_price: Optional[Decimal] = None
    decoration: Optional[str] = None
    floor_info: Optional[str] = None
    address: Optional[str] = None
    status: str
    owner_id: UUID
    store_id: Optional[UUID] = None
    created_at: datetime


class HouseCreateInput(BaseModel):
    community: str = Field(..., min_length=1, max_length=256)
    area: Decimal = Field(..., gt=0)
    room_type: str = Field(..., min_length=1)
    rent_price: Decimal = Field(..., gt=0)
    decoration: Optional[str] = None
    floor_info: Optional[str] = None
    address: Optional[str] = Field(None, max_length=512)
    owner_id: UUID


class HouseUpdateInput(BaseModel):
    community: Optional[str] = Field(None, max_length=256)
    area: Optional[Decimal] = Field(None, gt=0)
    room_type: Optional[str] = None
    rent_price: Optional[Decimal] = Field(None, gt=0)
    decoration: Optional[str] = None
    floor_info: Optional[str] = None
    status: Optional[str] = None


class HouseListResponse(BaseModel):
    items: list[HouseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChatInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    store_id: Optional[UUID] = None


class ChatOutput(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    id: UUID
    wecom_group_id: str
    participants: list[UUID]
    context: dict
    status: str
    created_at: datetime
    updated_at: datetime
