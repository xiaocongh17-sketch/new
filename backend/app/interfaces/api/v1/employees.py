"""Employee management API routes."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.interfaces.api.deps import require_user, require_roles, get_user_repo, get_session
from app.domain.entities.user import User
from app.domain.value_objects.enums import UserRole
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.persistence.repositories.store_repo import SQLAlchemyStoreRepository
from app.infrastructure.persistence.database import async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/employees", tags=["员工管理"])


class EmployeeResponse(BaseModel):
    id: str
    wecom_userid: str
    name: str
    role: str
    phone: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None


class EmployeeUpdateInput(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("", summary="员工列表")
async def list_employees(
    current_user: User = Depends(require_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """List employees (store-scoped for managers, all for admins)."""
    if current_user.role == UserRole.ADMIN:
        async with async_session_factory() as session:
            store_repo = SQLAlchemyStoreRepository(session)
            stores = await store_repo.find_all()
            all_users = []
            for store in stores:
                users = await user_repo.find_by_store(store.id)
                all_users.extend(users)
            return {"items": [_user_to_response(u) for u in all_users]}
    elif current_user.store_id:
        users = await user_repo.find_by_store(current_user.store_id)
        return {"items": [_user_to_response(u) for u in users]}
    return {"items": []}


@router.put("/{user_id}", summary="更新员工信息")
async def update_employee(
    user_id: uuid.UUID,
    input: EmployeeUpdateInput,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_MANAGER])),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Update employee information."""
    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Employee not found")
    if input.name is not None:
        user.name = input.name
    if input.role is not None:
        user.role = UserRole(input.role)
    if input.phone is not None:
        user.phone = input.phone
    if input.is_active is not None:
        user.is_active = input.is_active
    saved = await user_repo.save(user)
    return _user_to_response(saved)


def _user_to_response(u: User) -> EmployeeResponse:
    return EmployeeResponse(
        id=str(u.id), wecom_userid=u.wecom_userid,
        name=u.name, role=u.role.value, phone=u.phone,
        is_active=u.is_active,
        created_at=u.created_at.isoformat() if u.created_at else None,
    )
