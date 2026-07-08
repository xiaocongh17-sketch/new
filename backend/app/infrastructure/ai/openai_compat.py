"""OpenAI-compatible API implementation for BaseAIModel.

Supports providers like Qwen (通义千问), GLM (智谱), Ollama, etc.
"""

from openai import AsyncOpenAI
from pydantic import BaseModel
from .base import BaseAIModel, ChatMessage, ChatResponse


class OpenAICompatibleModel(BaseAIModel):
    """OpenAI-compatible API implementation."""

    def __init__(self, api_key: str, base_url: str, model: str,
                 embed_model: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
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
        return ChatResponse(content=choice.message.content or "", model=self.model)

    async def structured_extract(self, messages: list[ChatMessage],
                                  output_schema: type[BaseModel]) -> BaseModel:
        system_msg = (
            f"从用户输入中提取结构化信息，以JSON格式输出。\n"
            f"Schema:\n{output_schema.model_json_schema()}\n"
            f"只输出JSON。"
        )
        full_messages = [ChatMessage(role="system", content=system_msg)] + messages
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in full_messages],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return output_schema.model_validate_json(response.choices[0].message.content or "{}")

    async def embed(self, text: str) -> list[float]:
        if not self.embed_model:
            raise NotImplementedError("Embedding not supported by this provider")
        response = await self.client.embeddings.create(
            model=self.embed_model, input=text,
        )
        return response.data[0].embedding
