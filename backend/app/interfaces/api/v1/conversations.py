"""Conversation API routes."""

import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from app.interfaces.api.deps import require_user, get_conversation_repo
from app.domain.entities.user import User
from app.domain.entities.message import Message
from app.domain.repositories.conversation_repository import ConversationRepository
from app.domain.value_objects.enums import MessageType
from app.application.dto.house_dto import ConversationResponse

router = APIRouter(prefix="/conversations", tags=["对话管理"])


class ReplyInput(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


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


@router.get("/pending", summary="待审核对话列表")
async def list_pending_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_user),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """List conversations pending human review (all stores, admin/manager only)."""
    items, total = await conv_repo.find_pending_review(page, page_size)
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


@router.post("/{conversation_id}/reply", summary="回复对话（人工客服）")
async def reply_conversation(
    conversation_id: uuid.UUID,
    body: ReplyInput,
    current_user: User = Depends(require_user),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Send a reply as the current user (store manager/admin) in a conversation."""
    conv = await conv_repo.find_by_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save reply message
    reply_msg = Message.create(
        conversation_id=conv.id,
        sender_id=current_user.id,
        content=body.content,
        msg_type=MessageType.TEXT,
    )
    await conv_repo.add_message(reply_msg)

    # If conversation was pending review, move it back to active
    if conv.status.value == "pending_review":
        from app.domain.value_objects.enums import ConversationStatus
        conv.status = ConversationStatus.ACTIVE
        await conv_repo.save(conv)

    # Try to send the reply via WeCom if we have a group ID
    if conv.wecom_group_id:
        try:
            from app.infrastructure.wecom.client import WeComClient
            from app.infrastructure.config.settings import settings
            client = WeComClient(
                corp_id=settings.wecom_corp_id,
                agent_id=settings.wecom_agent_id,
                secret=settings.wecom_secret,
            )
            await client.send_text_message(
                touser=conv.wecom_group_id,
                content=body.content,
            )
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("wecom_reply_send_failed", error=str(e), conv_id=str(conv.id))

    return {"status": "ok", "message_id": str(reply_msg.id)}


@router.patch("/{conversation_id}/close", summary="关闭对话")
async def close_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(require_user),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Close a conversation."""
    conv = await conv_repo.find_by_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.close()
    await conv_repo.save(conv)
    return {"status": "ok", "message": "对话已关闭"}
