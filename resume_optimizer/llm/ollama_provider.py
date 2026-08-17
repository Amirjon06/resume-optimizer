"""Ollama backend for running an open-source model locally."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import LLMError, LLMProvider

DEFAULT_MODEL = "llama3.1"
DEFAULT_HOST = "http://localhost:11434"


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, model: str = DEFAULT_MODEL, host: str | None = None,
                 temperature: float = 0.4, timeout: int = 120):
        self.model = model
        self.host = (host or os.getenv("OLLAMA_HOST") or DEFAULT_HOST).rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": self.temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }).encode("utf-8")

        request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise LLMError(
                f"Could not reach Ollama at {self.host}. Is it running? ({exc})"
            ) from exc

        return body.get("message", {}).get("content", "")
