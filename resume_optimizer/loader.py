"""Load and validate resume input from YAML or JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from .models import Resume


def load_resume(path: str | Path) -> Resume:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data: Dict[str, Any] = json.loads(text)
    else:
        data = yaml.safe_load(text) or {}

    if not isinstance(data, dict):
        raise ValueError("Input file must contain a mapping at the top level.")

    # Preserve the user's own summary so the optimizer can rewrite it
    # without losing the original phrasing on a re-run.
    if data.get("summary") and not data.get("raw_summary"):
        data["raw_summary"] = data["summary"]

    return Resume.model_validate(data)


def save_resume(resume: Resume, path: str | Path) -> Path:
    """Write an optimized resume to JSON so it can be edited and re-rendered."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(resume.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path
