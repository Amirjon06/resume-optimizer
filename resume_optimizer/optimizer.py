"""Turns raw career notes into polished resume content."""

from __future__ import annotations

import re

from typing import Callable, List, Optional

from .llm import LLMError, LLMProvider, coerce_bullets, get_provider
from .llm import prompts
from .models import Resume, SkillGroup

ProgressHook = Optional[Callable[[str], None]]

BENEFIT_CLAUSE = re.compile(
    r",?\s+(?:to\s+)?(?:improving|enhancing|ensuring|enabling|streamlining|"
    r"fostering|boosting|driving|increasing|improve|enhance|ensure|enable)\b[^.]*",
    re.IGNORECASE,
)


def strip_unsupported_clause(bullet: str, notes: List[str]) -> str:
    """Drop a trailing benefit clause that the source notes do not support.

    The model reliably appends outcome clauses even when told not to, because
    resume prose is full of them. Prompt rules only reduce the rate, so the
    check is enforced here instead.
    """
    match = BENEFIT_CLAUSE.search(bullet)
    if not match:
        return bullet

    clause_words = set(re.findall(r"[a-z]{4,}", match.group(0).lower()))
    source = " ".join(notes).lower()
    supported = {word for word in clause_words if word in source}

    # The clause's own verb never appears in the notes, so allow one miss.
    if len(clause_words) > 1 and len(supported) >= len(clause_words) - 1:
        return bullet

    cleaned = bullet[: match.start()].rstrip(" ,;")
    return cleaned if cleaned.endswith(".") else cleaned + "."


class ResumeOptimizer:
    def __init__(self, provider: LLMProvider | None = None, max_bullets: int = 5,
                 on_progress: ProgressHook = None):
        self.provider = provider or get_provider("mock")
        self.max_bullets = max_bullets
        self._on_progress = on_progress

    def _log(self, message: str) -> None:
        if self._on_progress:
            self._on_progress(message)

    def optimize(self, resume: Resume) -> Resume:
        """Fill in bullets, summary and skills. Returns a new Resume."""
        result = resume.model_copy(deep=True)

        for job in result.experience:
            if not job.notes:
                continue
            self._log(f"Rewriting bullets: {job.role} at {job.company}")
            job.bullets = self._bullets(
                role=job.role,
                company=job.company,
                notes=job.notes,
                target_role=result.target_role,
                job_description=result.job_description,
            )

        for project in result.projects:
            if not project.notes:
                continue
            self._log(f"Rewriting bullets: {project.name}")
            project.bullets = self._bullets(
                role=project.name,
                company="Personal project",
                notes=project.notes,
                target_role=result.target_role,
                job_description=result.job_description,
                limit=3,
            )

        digest = _digest(result)

        self._log("Writing professional summary")
        result.summary = self._summary(digest, result.target_role, result.raw_summary)

        if not result.skills:
            self._log("Grouping skills")
            result.skills = self._skills(digest, result.target_role)

        return result

    def _bullets(self, role: str, company: str, notes: List[str],
                 target_role: Optional[str], job_description: Optional[str],
                 limit: int | None = None) -> List[str]:
        limit = limit or self.max_bullets
        prompt = prompts.bullets_prompt(
            role=role,
            company=company,
            notes=notes,
            target_role=target_role,
            job_description=job_description,
            max_bullets=limit,
        )
        try:
            data = self.provider.complete_json(prompts.SYSTEM, prompt)
        except LLMError as exc:
            self._log(f"  falling back to raw notes ({exc})")
            return notes[:limit]

        bullets = coerce_bullets(data.get("bullets"), limit) or notes[:limit]
        return [strip_unsupported_clause(bullet, notes) for bullet in bullets]

    def _summary(self, digest: str, target_role: Optional[str],
                 existing: Optional[str]) -> Optional[str]:
        prompt = prompts.summary_prompt(digest, target_role, existing)
        try:
            data = self.provider.complete_json(prompts.SYSTEM, prompt)
        except LLMError:
            return existing

        summary = str(data.get("summary") or "").strip()
        return summary or existing

    def _skills(self, digest: str, target_role: Optional[str]) -> List[SkillGroup]:
        prompt = prompts.skills_prompt(digest, target_role)
        try:
            data = self.provider.complete_json(prompts.SYSTEM, prompt)
        except LLMError:
            return []

        groups: List[SkillGroup] = []
        for entry in data.get("skills") or []:
            if not isinstance(entry, dict):
                continue
            items = [str(i).strip() for i in entry.get("items", []) if str(i).strip()]
            category = str(entry.get("category") or "Skills").strip()
            if items:
                groups.append(SkillGroup(category=category, items=items))
        return groups


def _digest(resume: Resume) -> str:
    """Compact plain-text view of the resume, used as context for the model."""
    lines: List[str] = []

    for job in resume.experience:
        lines.append(f"{job.role} at {job.company} ({job.dates})")
        for line in (job.bullets or job.notes):
            lines.append(f"- {line}")

    for project in resume.projects:
        tech = f" [{', '.join(project.tech)}]" if project.tech else ""
        lines.append(f"Project: {project.name}{tech}")
        for line in (project.bullets or project.notes):
            lines.append(f"- {line}")

    for school in resume.education:
        lines.append(f"{school.degree or 'Studied'}, {school.school} ({school.dates})")

    for group in resume.skills:
        lines.append(f"{group.category}: {', '.join(group.items)}")

    return "\n".join(lines)
