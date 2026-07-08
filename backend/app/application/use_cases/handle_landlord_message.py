"""Use case: Handle incoming landlord message via AI."""

import structlog
from app.domain.entities.user import User
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.enums import UserRole, MessageType
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.conversation_repository import ConversationRepository
from app.domain.services.house_extraction_service import HouseExtractionService
from app.domain.services.conversation_manager import ConversationManager
from app.domain.interfaces.ai_model import BaseAIModel, ChatMessage
from app.domain.interfaces.messaging import MessageSender

logger = structlog.get_logger()

LANDLORD_SYSTEM_PROMPT = """你是一个专业的房地产AI门店助手，正在帮助房东出租房源。

回答风格：
- 专业、亲切、简洁
- 用中文回答
- 每次最多追问一个信息点

你的职责包括：
1. 回答房东关于佣金、出租流程、材料要求的问题
2. 收集房源信息：小区名称、面积、户型、期望租金、装修情况
3. 当信息不完整时，自然地追问缺失的信息
4. 如果房东有投诉、法律问题或特殊要求，礼貌地告知会转接人工

已收集的信息：{collected_info}
"""


class HandleLandlordMessageUseCase:
    """Process a landlord's message and generate AI response."""

    def __init__(
        self,
        user_repo: UserRepository,
        conversation_repo: ConversationRepository,
        ai_model: BaseAIModel,
        message_sender: MessageSender,
        extraction_service: HouseExtractionService | None = None,
        conversation_manager: ConversationManager | None = None,
    ):
        self.user_repo = user_repo
        self.conversation_repo = conversation_repo
        self.ai_model = ai_model
        self.message_sender = message_sender
        self.extraction_service = extraction_service or HouseExtractionService()
        self.conversation_manager = conversation_manager or ConversationManager()

    async def execute(self, wecom_userid: str, wecom_group_id: str,
                      content: str, wecom_msg_id: str | None = None) -> str:
        """Handle incoming landlord message. Returns AI reply content."""
        user = await self.user_repo.find_by_wecom_userid(wecom_userid)
        if not user:
            user = User.create(
                wecom_userid=wecom_userid,
                name=wecom_userid,
                role=UserRole.LANDLORD,
            )
            user = await self.user_repo.save(user)
            logger.info("new_landlord_registered", user_id=str(user.id))

        conv = await self.conversation_repo.find_active_by_group(wecom_group_id)
        if not conv:
            conv = Conversation.create(
                wecom_group_id=wecom_group_id,
                participants=[user.id],
            )
            conv = await self.conversation_repo.save(conv)
        elif user.id not in conv.participants:
            conv.participants.append(user.id)
            conv = await self.conversation_repo.save(conv)

        should_escalate, reason = self.conversation_manager.should_escalate(content)
        if should_escalate:
            conv.request_review()
            await self.conversation_repo.save(conv)
            logger.warning("conversation_escalated", conv_id=str(conv.id), reason=reason)
            reply = "很抱歉，您提到的问题我需要转接给人工客服处理。请您稍等，我们的专业顾问会尽快联系您。"
            return await self._send_reply(user, conv, reply)

        collected = {k: v for k, v in conv.context.items() if v}
        system_prompt = LANDLORD_SYSTEM_PROMPT.format(
            collected_info=str(collected) if collected else "暂无"
        )

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=content),
        ]
        response = await self.ai_model.chat(messages, temperature=0.7)

        msg = Message.create(
            conversation_id=conv.id,
            sender_id=user.id,
            content=content,
            msg_type=MessageType.TEXT,
            wecom_msg_id=wecom_msg_id,
        )
        await self.conversation_repo.add_message(msg)

        return await self._send_reply(user, conv, response.content)

    async def _send_reply(self, user: User, conv: Conversation,
                          reply_content: str) -> str:
        reply_msg = Message.create(
            conversation_id=conv.id,
            sender_id=user.id,
            content=reply_content,
            msg_type=MessageType.TEXT,
        )
        await self.conversation_repo.add_message(reply_msg)

        try:
            await self.message_sender.send_text_message(
                touser=user.wecom_userid,
                content=reply_content,
            )
        except Exception as e:
            logger.error("wecom_send_failed", error=str(e), user_id=str(user.id))

        return reply_content
