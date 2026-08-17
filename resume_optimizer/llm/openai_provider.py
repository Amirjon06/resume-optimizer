"""OpenAI backend."""

from __future__ import annotations

import os

from .base import LLMError, LLMProvider

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None,
                 temperature: float = 0.4):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMError("The openai package is required: pip install openai") from exc

        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise LLMError("OPENAI_API_KEY is not set.")

        self._client = OpenAI(api_key=key)
        self.model = model
        self.temperature = temperature

    def complete(self, system: str, user: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc

        return response.choices[0].message.content or ""
