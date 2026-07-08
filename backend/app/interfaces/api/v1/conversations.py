"""Conversation API routes."""

import uuid
from fastapi import APIRouter, Depends, Query
from app.interfaces.api.deps import require_user, get_conversation_repo
from app.domain.entities.user import User
from app.domain.repositories.conversation_repository import ConversationRepository
from app.application.dto.house_dto import ConversationResponse

router = APIRouter(prefix="/conversations", tags=["对话管理"])


def _conv_to_response(conv) -> ConversationResponse:
    return ConversationResponse(
        id=conv.id, wecom_group_id=conv.wecom_group_id,
        participants=conv.participants, context=conv.context,
        status=conv.status.value if conv.status else "active",
        created_at=conv.created_at, updated_at=conv.updated_at,
    )


@router.get("", summary="对话列表")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_user),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """List conversations for current user's store."""
    store_id = current_user.store_id
    if not store_id:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    items, total = await conv_repo.find_by_store(store_id, page, page_size)
    return {
        "items": [_conv_to_response(c) for c in items],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/{conversation_id}", response_model=ConversationResponse, summary="对话详情")
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(require_user),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Get conversation details including messages."""
    from fastapi import HTTPException
    conv = await conv_repo.find_by_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await conv_repo.get_messages(conversation_id)
    response = _conv_to_response(conv)
    return {
        **response.model_dump(),
        "messages": [
            {"id": str(m.id), "sender_id": str(m.sender_id),
             "content": m.content, "msg_type": m.msg_type.value,
             "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in messages
        ],
    }
