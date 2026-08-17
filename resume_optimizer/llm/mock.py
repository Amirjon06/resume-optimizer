"""Offline provider used for tests and for running the pipeline without an API key."""

from __future__ import annotations

import json
import re
from typing import List

from .base import LLMProvider

ACTION_VERBS = ["Built", "Led", "Shipped", "Automated", "Designed", "Scaled"]


class MockProvider(LLMProvider):
    """Applies deterministic rewrites so the full pipeline can run offline.

    This is not a language model. It reshapes the input notes just enough to
    exercise the JSON contract that the real providers satisfy.
    """

    name = "mock"

    def complete(self, system: str, user: str) -> str:
        if '"summary"' in user:
            return json.dumps({"summary": self._summary(user)})
        if '"skills"' in user:
            return json.dumps({"skills": self._skills(user)})
        return json.dumps({"bullets": self._bullets(user)})

    @staticmethod
    def _notes(user: str) -> List[str]:
        block = re.findall(r"^- (.+)$", user, re.MULTILINE)
        return [line.strip() for line in block if line.strip()]

    def _bullets(self, user: str) -> List[str]:
        bullets = []
        for i, note in enumerate(self._notes(user)[:5]):
            text = note[0].lower() + note[1:] if note else note
            text = re.sub(
                r"^(worked on|helped|did|was responsible for|built|created|made|"
                r"wrote|set up|handled|mentored|cut)\s+",
                "", text, flags=re.I,
            )
            bullets.append(f"{ACTION_VERBS[i % len(ACTION_VERBS)]} {text.rstrip('.')}.")
        return bullets

    @staticmethod
    def _summary(user: str) -> str:
        match = re.search(r"targeting a (.+?) role", user)
        role = match.group(1) if match else "Engineer"
        return (
            f"{role} with a track record of shipping production systems end to end. "
            "Comfortable owning a problem from design through deployment and iteration."
        )

    @staticmethod
    def _skills(user: str) -> List[dict]:
        found = sorted(set(re.findall(
            r"\b(Python|Go|Java|JavaScript|TypeScript|SQL|React|Django|Flask|FastAPI|"
            r"Docker|Kubernetes|AWS|GCP|Postgres|PostgreSQL|Redis|Kafka|Terraform)\b",
            user,
        )))
        if not found:
            found = ["Python", "SQL"]
        return [{"category": "Technical", "items": found}]
