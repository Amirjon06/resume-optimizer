"""LLM provider registry."""

from __future__ import annotations

from .base import LLMError, LLMProvider, coerce_bullets
from .mock import MockProvider

__all__ = ["LLMError", "LLMProvider", "coerce_bullets", "MockProvider", "get_provider"]


def get_provider(name: str = "mock", model: str | None = None, **kwargs) -> LLMProvider:
    """Instantiate a provider by name.

    Vendor SDKs are imported lazily so the package works with only the
    providers the user actually installed.
    """
    name = (name or "mock").lower()

    if name == "mock":
        return MockProvider()

    if name == "openai":
        from .openai_provider import DEFAULT_MODEL, OpenAIProvider
        return OpenAIProvider(model=model or DEFAULT_MODEL, **kwargs)

    if name == "ollama":
        from .ollama_provider import DEFAULT_MODEL, OllamaProvider
        return OllamaProvider(model=model or DEFAULT_MODEL, **kwargs)

    raise ValueError(f"Unknown provider '{name}'. Choose from: mock, openai, ollama.")
