"""Ollama local model implementation of BaseAIModel."""

import json
from openai import AsyncOpenAI
from pydantic import BaseModel
from .base import BaseAIModel, ChatMessage, ChatResponse


class OllamaModel(BaseAIModel):
    """Ollama local model implementation (OpenAI-compatible API)."""

    def __init__(self, base_url: str = "http://localhost:11434/v1",
                 model: str = "qwen2.5:7b", api_key: str = "ollama"):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.base_url = base_url

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
            f"Extract structured information from the input. "
            f"Output JSON matching this schema:\n{output_schema.model_json_schema()}\n"
            f"Only output JSON, nothing else."
        )
        full = [ChatMessage(role="system", content=system_msg)] + messages
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in full],
            temperature=0.1,
            max_tokens=1024,
        )
        content = response.choices[0].message.content or "{}"
        # Clean markdown code fences
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return output_schema.model_validate_json(content.strip())

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
