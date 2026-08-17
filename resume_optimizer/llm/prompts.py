"""Prompt templates for rewriting career details into resume content."""

from __future__ import annotations

import json
from typing import List, Optional

SYSTEM = """You are an experienced technical recruiter and resume writer.
You rewrite raw career notes into concise, high-impact resume bullet points.

Rules:
- Do not add outcome or benefit clauses that the notes do not state. "Fixed bugs in billing" must not become "improving reliability and user satisfaction".
- Do not add intensifiers such as "critical", "complex", or "major" unless the notes use them.
- Start every bullet with a strong past-tense action verb. Never use "Responsible for".
- Lead with the outcome when the notes state one, then the method.
  If the notes state no outcome, end the bullet after the method.
- Never invent metrics, employers, dates, or technologies that are not in the notes.
  If a bullet has no number, write it without one rather than fabricating.
- Keep each bullet to one line, roughly 15-30 words.
- Use plain language. No filler adjectives such as "dynamic" or "results-driven".
- Reply with a single JSON object and nothing else."""


def bullets_prompt(
    role: str,
    company: str,
    notes: List[str],
    target_role: Optional[str] = None,
    job_description: Optional[str] = None,
    max_bullets: int = 5,
) -> str:
    context = f"Role: {role}\nCompany: {company}\n"
    if target_role:
        context += f"Tailor the emphasis toward this target role: {target_role}\n"
    if job_description:
        context += f"\nTarget job description:\n{job_description.strip()[:1500]}\n"

    notes_block = "\n".join(f"- {note}" for note in notes)

    return f"""{context}
Raw notes from the candidate:
{notes_block}

Rewrite these into at most {max_bullets} resume bullet points.
Merge overlapping notes; drop anything trivial.

Respond in this exact shape:
{json.dumps({"bullets": ["bullet one", "bullet two"]}, indent=2)}"""


def summary_prompt(
    resume_digest: str,
    target_role: Optional[str] = None,
    existing: Optional[str] = None,
) -> str:
    goal = f"targeting a {target_role} role" if target_role else "for a general application"
    prior = f"\nTheir current summary draft:\n{existing}\n" if existing else ""

    return f"""Write a professional summary for this candidate, {goal}.

Candidate background:
{resume_digest}
{prior}
Two or three sentences, maximum 55 words. Write in third person without pronouns
(for example: "Backend engineer with six years..."). Ground every claim in the
background above.

Respond in this exact shape:
{json.dumps({"summary": "..."}, indent=2)}"""


def skills_prompt(resume_digest: str, target_role: Optional[str] = None) -> str:
    focus = f"Prioritize what matters for a {target_role} role." if target_role else ""

    return f"""Group this candidate's technical skills into 3-5 labeled categories.

Candidate background:
{resume_digest}

Only include skills evidenced by the background. {focus}
Order each category with the strongest skills first.

Respond in this exact shape:
{json.dumps({"skills": [{"category": "Languages", "items": ["Python", "Go"]}]}, indent=2)}"""
