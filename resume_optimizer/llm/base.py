"""Provider abstraction so the optimizer is independent of any single LLM vendor."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMError(RuntimeError):
    pass


class LLMProvider(ABC):
    """Minimal interface every backend must satisfy."""

    name: str = "base"

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the model's raw text response."""

    def complete_json(self, system: str, user: str, retries: int = 2) -> Dict[str, Any]:
        """Call the model and parse its response as JSON.

        Models sometimes wrap JSON in prose or code fences, so the response is
        salvaged before giving up. A retry appends a stricter instruction.
        """
        last_error: Exception | None = None
        prompt = user

        for attempt in range(retries + 1):
            raw = self.complete(system, prompt)
            try:
                return _extract_json(raw)
            except ValueError as exc:
                last_error = exc
                prompt = (
                    f"{user}\n\nYour previous reply was not valid JSON. "
                    "Reply with a single JSON object and nothing else."
                )

        raise LLMError(f"Could not parse JSON after {retries + 1} attempts: {last_error}")


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()

    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Fall back to the outermost braces in case the model added commentary.
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("No JSON object found in response.")
        parsed = json.loads(text[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object at the top level.")
    return parsed


def coerce_bullets(value: Any, limit: int = 6) -> List[str]:
    """Normalize whatever the model returned into a clean list of bullet strings."""
    if isinstance(value, str):
        value = [line for line in value.splitlines() if line.strip()]
    if not isinstance(value, list):
        return []

    bullets: List[str] = []
    for item in value:
        if isinstance(item, dict):
            item = item.get("text") or item.get("bullet") or ""
        text = str(item).strip().lstrip("-•*").strip()
        if text:
            bullets.append(text)

    return bullets[:limit]
