"""Data models for resume input and optimized output."""

from __future__ import annotations

from typing import Annotated, List, Optional

from pydantic import BaseModel, BeforeValidator, Field


def _as_text(value: object) -> object:
    """Accept bare years from YAML, which parse as ints rather than strings."""
    if isinstance(value, (int, float)):
        return str(value)
    return value


DateText = Annotated[Optional[str], BeforeValidator(_as_text)]


class Contact(BaseModel):
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None

    def links(self) -> List[str]:
        out = []
        for value in (self.email, self.phone, self.location, self.website,
                      self.linkedin, self.github):
            if value:
                out.append(value)
        return out


class Experience(BaseModel):
    company: str
    role: str
    start: DateText = None
    end: DateText = None
    location: Optional[str] = None
    # Raw, messy notes from the user. The LLM turns these into bullets.
    notes: List[str] = Field(default_factory=list)
    # Populated by the optimizer.
    bullets: List[str] = Field(default_factory=list)

    @property
    def dates(self) -> str:
        if self.start and self.end:
            return f"{self.start} – {self.end}"
        return self.start or self.end or ""


class Project(BaseModel):
    name: str
    url: Optional[str] = None
    tech: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)


class Education(BaseModel):
    school: str
    degree: Optional[str] = None
    start: DateText = None
    end: DateText = None
    location: Optional[str] = None
    details: List[str] = Field(default_factory=list)

    @property
    def dates(self) -> str:
        if self.start and self.end:
            return f"{self.start} – {self.end}"
        return self.start or self.end or ""


class SkillGroup(BaseModel):
    category: str
    items: List[str] = Field(default_factory=list)


class Resume(BaseModel):
    """Full resume document: user input plus LLM-generated content."""

    contact: Contact
    target_role: Optional[str] = None
    job_description: Optional[str] = None
    summary: Optional[str] = None
    raw_summary: Optional[str] = None
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[SkillGroup] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    def has_content(self) -> bool:
        return bool(self.experience or self.projects or self.education)
