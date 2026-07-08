"""Message abstractions — ports for the domain layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WeComMessage:
    """Parsed WeCom callback message (DTO)."""
    msg_id: str
    from_user: str          # 发送者 UserId
    to_user: str            # 接收者（应用ID或群ID）
    content: str
    msg_type: str           # text, image, event
    create_time: int
    agent_id: str | None = None
    chat_id: str | None = None  # 群聊ID


class MessageSender(ABC):
    """Abstract interface for sending messages (port)."""

    @abstractmethod
    async def send_text_message(self, touser: str, content: str,
                                chat_id: str | None = None) -> dict:
        """Send a text message to a user or group chat."""
        raise NotImplementedError

    @abstractmethod
    async def send_webhook_message(self, content: str) -> dict:
        """Send message via webhook for notifications."""
        raise NotImplementedError
