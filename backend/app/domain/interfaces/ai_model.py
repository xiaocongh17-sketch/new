"""AI model abstraction — port for the domain layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """A single message in a chat conversation."""
    role: str       # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Response from an AI model chat completion."""
    content: str
    model: str
    usage: dict | None = None


class BaseAIModel(ABC):
    """Abstract base for all AI model providers (port)."""

    @abstractmethod
    async def chat(self, messages: list[ChatMessage],
                   temperature: float = 0.7,
                   max_tokens: int = 2048) -> ChatResponse:
        """Send a chat completion request."""
        raise NotImplementedError

    @abstractmethod
    async def structured_extract(self, messages: list[ChatMessage],
                                  output_schema: type) -> object:
        """Extract structured data from text."""
        raise NotImplementedError

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        raise NotImplementedError
