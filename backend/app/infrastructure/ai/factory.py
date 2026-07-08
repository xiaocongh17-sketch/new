"""AI model factory — creates model instances based on configuration."""

from app.infrastructure.config.settings import settings
from .base import BaseAIModel
from .deepseek import DeepSeekModel
from .openai_compat import OpenAICompatibleModel
from .ollama import OllamaModel

_model_instance: BaseAIModel | None = None


def get_ai_model() -> BaseAIModel:
    """Get or create the AI model singleton."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    if settings.ai_provider == "deepseek":
        _model_instance = DeepSeekModel(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            embed_model=settings.ai_embed_model,
        )
    elif settings.ai_provider == "ollama":
        _model_instance = OllamaModel(
            base_url=settings.ai_base_url or "http://localhost:11434/v1",
            model=settings.ai_model or "qwen2.5:7b",
            api_key=settings.ai_api_key or "ollama",
        )
    elif settings.ai_provider == "openai_compatible":
        _model_instance = OpenAICompatibleModel(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            embed_model=settings.ai_embed_model,
        )
    else:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")

    return _model_instance


def reset_ai_model() -> None:
    """Reset the model singleton (useful for testing)."""
    global _model_instance
    _model_instance = None
