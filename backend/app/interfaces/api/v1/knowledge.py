"""Knowledge base API routes."""

import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.interfaces.api.deps import require_user, require_roles, get_knowledge_repo
from app.domain.entities.user import User
from app.domain.value_objects.enums import UserRole
from app.domain.repositories.knowledge_repository import KnowledgeRepository
from app.domain.entities.knowledge import KnowledgeDocument

router = APIRouter(prefix="/knowledge", tags=["知识库"])


class KnowledgeDocResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str
    created_at: Optional[str] = None


class KnowledgeCreateInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    content: str = Field(..., min_length=1)
    category: str = Field(..., pattern="^(SOP|TRAINING|FAQ|MARKET)$")


@router.get("", summary="知识库文档列表")
async def list_knowledge(
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_user),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repo),
):
    """List knowledge base documents."""
    items, total = await knowledge_repo.find_all(
        store_id=current_user.store_id,
        category=category,
        page=page, page_size=page_size,
    )
    return {
        "items": [_doc_to_response(d) for d in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("", response_model=KnowledgeDocResponse, status_code=201, summary="创建知识文档")
async def create_knowledge(
    input: KnowledgeCreateInput,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_MANAGER])),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repo),
):
    """Create a new knowledge base document."""
    doc = KnowledgeDocument.create(
        title=input.title, content=input.content,
        category=input.category, store_id=current_user.store_id,
    )
    saved = await knowledge_repo.save(doc)
    return _doc_to_response(saved)


@router.delete("/{doc_id}", status_code=204, summary="删除知识文档")
async def delete_knowledge(
    doc_id: uuid.UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STORE_MANAGER])),
    knowledge_repo: KnowledgeRepository = Depends(get_knowledge_repo),
):
    """Delete a knowledge base document."""
    deleted = await knowledge_repo.delete(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")


def _doc_to_response(doc: KnowledgeDocument) -> KnowledgeDocResponse:
    return KnowledgeDocResponse(
        id=str(doc.id), title=doc.title, content=doc.content,
        category=doc.category,
        created_at=doc.created_at.isoformat() if doc.created_at else None,
    )
