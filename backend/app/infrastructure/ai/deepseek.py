"""DeepSeek API implementation of BaseAIModel."""

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel
from .base import BaseAIModel, ChatMessage, ChatResponse


class DeepSeekModel(BaseAIModel):
    """DeepSeek API implementation."""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-chat",
                 embed_model: str = "deepseek-embedding"):
        # Bypass Windows system proxy (e.g. LightningX VPN) that breaks SSL
        http_client = httpx.AsyncClient(proxy=None, trust_env=False)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
        self.model = model
        self.embed_model = embed_model

    async def chat(self, messages: list[ChatMessage],
                   temperature: float = 0.7,
                   max_tokens: int = 2048) -> ChatResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )

    async def structured_extract(self, messages: list[ChatMessage],
                                  output_schema: type[BaseModel]) -> BaseModel:
        system_msg = (
            f"你是一个数据提取助手。从用户输入中提取结构化信息，"
            f"以JSON格式输出，schema如下：\n{output_schema.model_json_schema()}\n"
            f"只输出JSON，不要包含其他内容。"
        )
        full_messages = [ChatMessage(role="system", content=system_msg)] + messages
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in full_messages],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return output_schema.model_validate_json(content)

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.embed_model,
            input=text,
        )
        return response.data[0].embedding
