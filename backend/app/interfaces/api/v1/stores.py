"""Store management API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.interfaces.api.deps import require_user, require_roles, get_store_repo, get_session
from app.domain.entities.user import User
from app.domain.value_objects.enums import UserRole
from app.domain.repositories.store_repository import StoreRepository
from app.domain.entities.store import Store
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/stores", tags=["门店管理"])


class StoreResponse(BaseModel):
    id: str
    name: str
    code: str
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool


class StoreCreateInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    code: str = Field(..., min_length=1, max_length=64)
    address: Optional[str] = None
    contact_phone: Optional[str] = None


@router.get("", summary="门店列表")
async def list_stores(
    current_user: User = Depends(require_user),
    store_repo: StoreRepository = Depends(get_store_repo),
):
    """List all stores (admin only) or current store."""
    if current_user.role == UserRole.ADMIN:
        stores = await store_repo.find_all()
    elif current_user.store_id:
        store = await store_repo.find_by_id(current_user.store_id)
        stores = [store] if store else []
    else:
        stores = []
    return {"items": [_store_to_response(s) for s in stores]}


@router.post("", response_model=StoreResponse, status_code=201, summary="创建门店")
async def create_store(
    input: StoreCreateInput,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    store_repo: StoreRepository = Depends(get_store_repo),
):
    """Create a new store (admin only)."""
    existing = await store_repo.find_by_code(input.code)
    if existing:
        raise HTTPException(status_code=409, detail="Store code already exists")
    store = Store.create(
        name=input.name, code=input.code,
        address=input.address, contact_phone=input.contact_phone,
    )
    saved = await store_repo.save(store)
    return _store_to_response(saved)


@router.get("/{store_id}", response_model=StoreResponse, summary="门店详情")
async def get_store(
    store_id: uuid.UUID,
    current_user: User = Depends(require_user),
    store_repo: StoreRepository = Depends(get_store_repo),
):
    """Get store details."""
    store = await store_repo.find_by_id(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return _store_to_response(store)


def _store_to_response(store: Store) -> StoreResponse:
    return StoreResponse(
        id=str(store.id), name=store.name, code=store.code,
        address=store.address, contact_phone=store.contact_phone,
        is_active=store.is_active,
    )
