"""WeCom callback API routes."""

from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import Response
from app.infrastructure.wecom.crypto import verify_url, decrypt_message, encrypt_message, get_crypto
from app.infrastructure.wecom.callback import parse_message_xml
from app.infrastructure.config.settings import settings
from app.infrastructure.wecom.client import WeComClient
from app.application.use_cases.answer_employee_query import AnswerEmployeeQueryUseCase
from app.infrastructure.ai.factory import get_ai_model
from app.infrastructure.persistence.repositories.knowledge_repo import SQLAlchemyKnowledgeRepository
from app.infrastructure.persistence.repositories.conversation_repo import SQLAlchemyConversationRepository
from app.infrastructure.persistence.database import async_session_factory
from app.domain.entities.conversation import Conversation as ConversationEntity
from app.domain.entities.message import Message as MessageEntity
from app.domain.value_objects.enums import MessageType
from app.domain.services.conversation_manager import ESCALATION_KEYWORDS, ConversationManager
from datetime import datetime
import structlog
import uuid

router = APIRouter(prefix="/wecom", tags=["企业微信"])
logger = structlog.get_logger()


@router.get("/callback")
async def verify_callback(
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
):
    """Verify WeCom callback URL challenge (GET)."""
    try:
        decrypted = verify_url(msg_signature, timestamp, nonce, echostr)
        return int(decrypted)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def build_text_reply_xml(to_user: str, from_user: str, content: str) -> str:
    """Build an unencrypted text reply XML."""
    now = str(int(datetime.now().timestamp()))
    return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{now}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""


# Debug endpoint: test WeCom crypto chain
@router.get("/crypto-test")
async def crypto_test():
    """Test WeCom encryption/decryption chain."""
    try:
        crypto = get_crypto()
        test_msg = "Hello World"
        from datetime import timezone
        ts = str(int(datetime.now(timezone.utc).timestamp()))
        nonce = "1234567890"

        # Test encrypt
        xml = build_text_reply_xml("test_user", "test_app", test_msg)
        encrypted = encrypt_message(xml, nonce, ts)
        return {"status": "ok", "encrypted_length": len(encrypted), "encrypted_preview": encrypted[:100]}
    except Exception as e:
        logger.exception("crypto_test_failed")
        return {"status": "error", "error": str(e)}


@router.post("/callback")
async def handle_callback(
    request: Request,
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
):
    """Handle WeCom callback message (POST) — decrypt => AI reply => encrypt response."""
    body = await request.body()
    xml_data = body.decode("utf-8")

    try:
        # 1. Decrypt the incoming message
        decrypted_xml = decrypt_message(msg_signature, timestamp, nonce, xml_data)
        logger.info("wecom_decrypted", decrypted_xml=decrypted_xml[:500])

        wecom_msg = parse_message_xml(decrypted_xml)
        is_group = wecom_msg.chat_id is not None
        logger.info("wecom_msg_received",
                     msg_type=wecom_msg.msg_type,
                     from_user=wecom_msg.from_user,
                     to_user=wecom_msg.to_user,
                     content_len=len(wecom_msg.content or ""),
                     content_preview=(wecom_msg.content or "")[:80],
                     msg_id=wecom_msg.msg_id,
                     chat_id=wecom_msg.chat_id,
                     is_group=is_group)

        # 2. If it's a text message, check escalation then generate AI reply
        msg_content = (wecom_msg.content or "").strip()
        if wecom_msg.msg_type == "text" and msg_content:
            logger.info("wecom_ai_processing",
                         query=msg_content[:100],
                         is_group=is_group)

            async with async_session_factory() as session:
                # 2a. Check if message triggers escalation keywords
                conv_manager = ConversationManager()
                should_escalate, reason = conv_manager.should_escalate(msg_content)

                if should_escalate:
                    conv_repo = SQLAlchemyConversationRepository(session)
                    conv = await conv_repo.find_active_by_group(wecom_msg.from_user)
                    if not conv:
                        conv = ConversationEntity.create(
                            wecom_group_id=wecom_msg.from_user,
                        )
                    conv.request_review()
                    await conv_repo.save(conv)
                    logger.warning("wecom_escalated",
                                    user=wecom_msg.from_user,
                                    reason=reason)
                    reply_content = "很抱歉，您提到的问题需要转接给人工客服处理。请您稍等，我们的专业顾问会尽快联系您。"
                else:
                    # 2b. Normal AI processing
                    knowledge_repo = SQLAlchemyKnowledgeRepository(session)
                    ai_model = get_ai_model()
                    use_case = AnswerEmployeeQueryUseCase(
                        ai_model=ai_model,
                        knowledge_repo=knowledge_repo,
                    )
                    try:
                        result = await use_case.execute(
                            query=msg_content,
                            store_id=None,
                        )
                        reply_content = result.get("answer", "")
                    except Exception as e:
                        logger.error("ai_reply_error", error=str(e))
                        reply_content = "抱歉，AI 服务暂时不可用，请联系管理员。"

            # 3. Build reply — for group chat, prefix @username so the asker knows it's for them
            if is_group:
                reply_content = f"@{wecom_msg.from_user} {reply_content}"

            logger.info("wecom_ai_reply_ready",
                         reply_len=len(reply_content),
                         is_group=is_group)

            # 4. Build and encrypt the reply
            reply_xml = build_text_reply_xml(
                to_user=wecom_msg.from_user,
                from_user=wecom_msg.to_user,
                content=reply_content,
            )
            encrypted_reply = encrypt_message(reply_xml, nonce, timestamp)
            logger.info("wecom_reply_encrypted", reply_len=len(encrypted_reply))
            return Response(content=encrypted_reply, media_type="application/xml")

        else:
            logger.info("wecom_no_reply_needed",
                         reason="empty_content" if not msg_content else "non_text_msg",
                         msg_type=wecom_msg.msg_type)

    except Exception as e:
        logger.error("wecom_callback_error", error=str(e))

    # Default: return success (no reply)
    return Response(content="", media_type="text/plain")
