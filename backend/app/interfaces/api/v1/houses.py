"""House management API routes."""

import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException
from app.interfaces.api.deps import require_user, require_roles, get_house_repo
from app.domain.entities.user import User
from app.domain.value_objects.enums import UserRole
from app.domain.repositories.house_repository import HouseRepository
from app.application.use_cases.house_management import (
    CreateHouseUseCase, GetHouseUseCase, UpdateHouseUseCase,
    DeleteHouseUseCase, SearchHousesUseCase,
)
from app.application.dto.house_dto import (
    HouseCreateInput, HouseUpdateInput, HouseListResponse, HouseResponse,
)

router = APIRouter(prefix="/houses", tags=["房源管理"])


def _house_to_response(house) -> HouseResponse:
    return HouseResponse(
        id=house.id, community=house.community, area=house.area,
        room_type=house.room_type, rent_price=house.rent_price,
        unit_price=house.unit_price, decoration=house.decoration,
        floor_info=house.floor_info, address=house.address,
        status=house.status.value if house.status else "active",
        owner_id=house.owner_id, store_id=house.store_id,
        created_at=house.created_at,
    )


@router.get("", response_model=HouseListResponse, summary="房源列表")
async def list_houses(
    community: str | None = Query(None, max_length=256),
    min_price: Decimal | None = Query(None, gt=0),
    max_price: Decimal | None = Query(None, gt=0),
    room_type: str | None = Query(None, max_length=64),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_user),
    house_repo: HouseRepository = Depends(get_house_repo),
):
    """Search houses with filters."""
    use_case = SearchHousesUseCase(house_repo)
    store_id = current_user.store_id if current_user.role != UserRole.ADMIN else None
    result = await use_case.execute(
        store_id=store_id, community=community,
        min_price=min_price, max_price=max_price,
        room_type=room_type, status=status,
        page=page, page_size=page_size,
    )
    return HouseListResponse(
        items=[_house_to_response(h) for h in result.items],
        total=result.total, page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.get("/{house_id}", response_model=HouseResponse, summary="房源详情")
async def get_house(
    house_id: uuid.UUID,
    current_user: User = Depends(require_user),
    house_repo: HouseRepository = Depends(get_house_repo),
):
    """Get house details by ID."""
    use_case = GetHouseUseCase(house_repo)
    house = await use_case.execute(house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return _house_to_response(house)


@router.post("", response_model=HouseResponse, status_code=201, summary="创建房源")
async def create_house(
    input: HouseCreateInput,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_MANAGER, UserRole.AGENT])),
    house_repo: HouseRepository = Depends(get_house_repo),
):
    """Create a new house listing."""
    use_case = CreateHouseUseCase(house_repo)
    house = await use_case.execute(
        community=input.community, area=input.area,
        room_type=input.room_type, rent_price=input.rent_price,
        owner_id=input.owner_id, decoration=input.decoration,
        floor_info=input.floor_info, address=input.address,
        store_id=current_user.store_id,
    )
    return _house_to_response(house)


@router.put("/{house_id}", response_model=HouseResponse, summary="更新房源")
async def update_house(
    house_id: uuid.UUID,
    input: HouseUpdateInput,
    current_user: User = Depends(require_user),
    house_repo: HouseRepository = Depends(get_house_repo),
):
    """Update house information."""
    use_case = UpdateHouseUseCase(house_repo)
    house = await use_case.execute(
        house_id,
        **input.model_dump(exclude_none=True),
    )
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return _house_to_response(house)


@router.delete("/{house_id}", status_code=204, summary="删除房源")
async def delete_house(
    house_id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_MANAGER])),
    house_repo: HouseRepository = Depends(get_house_repo),
):
    """Delete a house listing."""
    use_case = DeleteHouseUseCase(house_repo)
    deleted = await use_case.execute(house_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="House not found")
