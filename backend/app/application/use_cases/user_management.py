"""Use cases for user management."""

import uuid
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.enums import UserRole
from app.domain.interfaces.messaging import MessageSender


class RegisterUserFromWeComUseCase:
    """Register or lookup a user from WeCom user ID."""

    def __init__(self, user_repo: UserRepository, message_sender: MessageSender):
        self.user_repo = user_repo
        self.message_sender = message_sender

    async def execute(self, wecom_userid: str) -> User:
        existing = await self.user_repo.find_by_wecom_userid(wecom_userid)
        if existing:
            return existing

        try:
            # WeComClient implements both MessageSender and has get_user_info
            wecom_user = await self.message_sender.get_user_info(wecom_userid)  # type: ignore[attr-defined]
            name = wecom_user.get("name", wecom_userid)
        except Exception:
            name = wecom_userid

        user = User.create(
            wecom_userid=wecom_userid,
            name=name,
            role=UserRole.LANDLORD,
        )
        return await self.user_repo.save(user)
