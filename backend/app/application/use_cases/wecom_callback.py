"""Use case: Route incoming WeCom messages to the appropriate handler."""

import structlog
from app.domain.interfaces.messaging import WeComMessage
from app.domain.repositories.user_repository import UserRepository
from .handle_landlord_message import HandleLandlordMessageUseCase

logger = structlog.get_logger()


class HandleWecomCallbackUseCase:
    """Route incoming WeCom messages to the appropriate handler."""

    def __init__(
        self,
        landlord_handler: HandleLandlordMessageUseCase,
        user_repo: UserRepository,
    ):
        self.landlord_handler = landlord_handler
        self.user_repo = user_repo

    async def execute(self, wecom_msg: WeComMessage) -> str | None:
        logger.info(
            "wecom_callback_received",
            msg_type=wecom_msg.msg_type,
            from_user=wecom_msg.from_user,
        )

        if wecom_msg.msg_type != "text":
            logger.debug("non_text_message_ignored", msg_type=wecom_msg.msg_type)
            return None

        reply = await self.landlord_handler.execute(
            wecom_userid=wecom_msg.from_user,
            wecom_group_id=wecom_msg.to_user,
            content=wecom_msg.content,
            wecom_msg_id=wecom_msg.msg_id,
        )
        return reply
