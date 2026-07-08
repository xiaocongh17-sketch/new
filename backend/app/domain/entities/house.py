"""House domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from ..value_objects.enums import HouseStatus


@dataclass
class House:
    id: uuid.UUID
    community: str
    area: Decimal
    room_type: str
    rent_price: Decimal
    owner_id: uuid.UUID
    store_id: uuid.UUID | None = None
    address: str | None = None
    unit_price: Decimal | None = None
    decoration: str | None = None
    floor_info: str | None = None
    # --- new fields for AI collection ---
    building_type: str | None = None       # 高层/小高层/洋房/超高层
    total_floors: int | None = None        # 总楼层
    has_parking: bool | None = None        # 是否有车位
    parking_count: int | None = None       # 车位数量
    occupancy_status: str | None = None    # 自住/出租/空置
    tenant_cooperation: str | None = None  # 租客是否配合看房
    lease_expiry: str | None = None        # 租约到期时间
    decoration_year: str | None = None     # 装修年份
    decoration_quality: str | None = None  # 装修保养描述
    key_location: str | None = None        # 钥匙存放地点
    viewing_password: str | None = None    # 看房密码
    listed_on_beike: bool | None = None    # 是否挂贝壳
    list_price: Decimal | None = None      # 挂牌售价
    list_duration: str | None = None       # 挂牌时长
    unsold_reason: str | None = None       # 未成交原因
    viewing_count: int | None = None       # 带看组数
    purchase_year: str | None = None       # 购置年份
    is_only_home: bool | None = None       # 是否唯一住房
    tax_note: str | None = None            # 税费备注
    seller_motivation: str | None = None   # 卖房动机
    ai_collected_fields: str | None = None # AI已采集字段(逗号分隔)
    collector_score: int | None = None     # 采集完整度(0-100)
    deal_probability: int | None = None    # 成交概率(0-100)
    # --- end new fields ---
    status: HouseStatus = HouseStatus.ACTIVE
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(
        cls,
        community: str,
        area: Decimal,
        room_type: str,
        rent_price: Decimal,
        owner_id: uuid.UUID,
        store_id: uuid.UUID | None = None,
        address: str | None = None,
        decoration: str | None = None,
        floor_info: str | None = None,
        **kwargs,
    ) -> "House":
        now = datetime.now(timezone.utc)
        unit_price = (rent_price / area).quantize(Decimal("0.01")) if area > 0 else None
        return cls(
            id=uuid.uuid4(),
            community=community,
            area=area,
            room_type=room_type,
            rent_price=rent_price,
            owner_id=owner_id,
            store_id=store_id,
            address=address,
            unit_price=unit_price,
            decoration=decoration,
            floor_info=floor_info,
            status=HouseStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            **kwargs,
        )

    def update_price(self, new_price: Decimal) -> None:
        if new_price <= 0:
            raise ValueError("Price must be positive")
        self.rent_price = new_price
        self.unit_price = (new_price / self.area).quantize(Decimal("0.01"))

    def mark_rented(self) -> None:
        self.status = HouseStatus.RENTED

    def mark_off(self) -> None:
        self.status = HouseStatus.OFF
