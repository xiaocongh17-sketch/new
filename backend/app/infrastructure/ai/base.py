"""Base AI model abstraction — re-exports from domain interfaces."""

from app.domain.interfaces.ai_model import BaseAIModel, ChatMessage, ChatResponse

__all__ = ["BaseAIModel", "ChatMessage", "ChatResponse"]
