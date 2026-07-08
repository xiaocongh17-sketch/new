"""Dashboard statistics API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from app.interfaces.api.deps import require_user, get_session
from app.domain.entities.user import User
from app.infrastructure.persistence.models.house import HouseModel
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.models.conversation import ConversationModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/stats", summary="Dashboard 统计概览")
async def get_dashboard_stats(
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
):
    """Get dashboard statistics."""
    store_id = current_user.store_id

    # Houses count
    house_query = select(func.count()).select_from(HouseModel)
    if store_id:
        house_query = house_query.where(HouseModel.store_id == store_id)
    house_count = (await session.execute(house_query)).scalar() or 0

    # Active houses count
    active_query = select(func.count()).select_from(HouseModel).where(HouseModel.status == "active")
    if store_id:
        active_query = active_query.where(HouseModel.store_id == store_id)
    active_count = (await session.execute(active_query)).scalar() or 0

    # Employees count
    emp_query = select(func.count()).select_from(UserModel).where(
        UserModel.role.in_(["agent", "store_manager"])
    )
    if store_id:
        emp_query = emp_query.where(UserModel.store_id == store_id)
    emp_count = (await session.execute(emp_query)).scalar() or 0

    # Conversations count
    conv_query = select(func.count()).select_from(ConversationModel)
    if store_id:
        conv_query = conv_query.where(ConversationModel.store_id == store_id)
    conv_count = (await session.execute(conv_query)).scalar() or 0

    # Pending review
    review_query = select(func.count()).select_from(ConversationModel).where(
        ConversationModel.status == "pending_review"
    )
    if store_id:
        review_query = review_query.where(ConversationModel.store_id == store_id)
    review_count = (await session.execute(review_query)).scalar() or 0

    return {
        "total_houses": house_count,
        "active_houses": active_count,
        "total_employees": emp_count,
        "total_conversations": conv_count,
        "pending_review_conversations": review_count,
    }
