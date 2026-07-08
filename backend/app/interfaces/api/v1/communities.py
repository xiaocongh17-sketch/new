"""Community dictionary API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.interfaces.api.deps import require_user, get_session
from app.domain.entities.user import User

router = APIRouter(prefix="/communities", tags=["楼盘字典"])


@router.get("/search", summary="搜索楼盘小区（自动补全）")
async def search_communities(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
):
    """Search communities by name (autocomplete)."""
    result = await session.execute(
        text(
            "SELECT DISTINCT name, region FROM community_dict "
            "WHERE name LIKE :pattern ORDER BY name LIMIT :limit"
        ),
        {"pattern": f"%{q}%", "limit": limit},
    )
    rows = result.fetchall()
    return {
        "items": [{"name": r[0], "region": r[1]} for r in rows],
        "total": len(rows),
    }


@router.get("/check", summary="验证小区是否在楼盘字典中")
async def check_community(
    name: str = Query(..., min_length=1, max_length=256, description="小区名称"),
    current_user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
):
    """Check if a community name exists in the dictionary."""
    result = await session.execute(
        text(
            "SELECT name, region FROM community_dict WHERE name = :name LIMIT 1"
        ),
        {"name": name.strip()},
    )
    row = result.fetchone()
    if row:
        return {"exists": True, "name": row[0], "region": row[1]}
    return {"exists": False, "name": name, "suggestion": "该小区暂未开通服务"}
