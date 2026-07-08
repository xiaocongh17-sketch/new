"""WeCom API client for sending messages and querying user info."""

import httpx
from app.domain.interfaces.messaging import MessageSender
from app.infrastructure.config.settings import settings


class WeComClient(MessageSender):
    """Enterprise WeChat API client."""

    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self, corp_id: str, agent_id: str, secret: str):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self._access_token: str | None = None
        self._token_expires_at: int = 0

    async def _get_access_token(self) -> str:
        """Get or refresh access token."""
        from datetime import datetime, timezone
        now = int(datetime.now(timezone.utc).timestamp())
        if self._access_token and now < self._token_expires_at:
            return self._access_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/gettoken",
                params={"corpid": self.corp_id, "corpsecret": self.secret},
            )
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"Failed to get token: {data.get('errmsg')}")
            self._access_token = data["access_token"]
            self._token_expires_at = now + data.get("expires_in", 7200) - 200
            return self._access_token

    async def send_text_message(self, touser: str, content: str,
                                chat_id: str | None = None) -> dict:
        """Send a text message to a user or group chat."""
        token = await self._get_access_token()
        payload = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": content},
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/message/send",
                params={"access_token": token},
                json=payload,
            )
            return resp.json()

    async def send_webhook_message(self, content: str) -> dict:
        """Send message via group robot webhook for notifications."""
        if not settings.wecom_webhook_url:
            raise RuntimeError("WeCom webhook URL not configured")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.wecom_webhook_url,
                json={"msgtype": "text", "text": {"content": content}},
            )
            return resp.json()

    async def get_user_info(self, userid: str) -> dict:
        """Get user details by WeCom user ID."""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/user/get",
                params={"access_token": token, "userid": userid},
            )
            return resp.json()
