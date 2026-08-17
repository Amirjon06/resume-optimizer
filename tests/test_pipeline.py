import json

import pytest

from resume_optimizer.llm import MockProvider, get_provider
from resume_optimizer.llm.base import _extract_json, coerce_bullets
from resume_optimizer.loader import load_resume
from resume_optimizer.models import Contact, Experience, Resume
from resume_optimizer.optimizer import ResumeOptimizer, strip_unsupported_clause
from resume_optimizer.render import available_themes, render_html

SAMPLE = "examples/sample_input.yaml"


def test_loads_sample_input():
    resume = load_resume(SAMPLE)
    assert resume.contact.name
    assert resume.experience
    assert resume.has_content()


def test_dates_fall_back_to_single_value():
    job = Experience(company="Acme", role="Dev", start="2021")
    assert job.dates == "2021"


def test_extract_json_handles_code_fences():
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_handles_surrounding_prose():
    assert _extract_json('Sure! {"a": 1} Hope that helps.') == {"a": 1}


def test_extract_json_rejects_garbage():
    with pytest.raises(ValueError):
        _extract_json("no json here")


def test_coerce_bullets_strips_markers_and_limits():
    result = coerce_bullets(["- one", "• two", "* three", "four"], limit=3)
    assert result == ["one", "two", "three"]


def test_coerce_bullets_accepts_dicts():
    assert coerce_bullets([{"text": "shipped it"}]) == ["shipped it"]


def test_optimizer_produces_bullets_for_every_role():
    resume = load_resume(SAMPLE)
    result = ResumeOptimizer(MockProvider()).optimize(resume)

    for job in result.experience:
        assert job.bullets, f"no bullets for {job.company}"
    assert result.summary


def test_optimizer_does_not_mutate_input():
    resume = load_resume(SAMPLE)
    ResumeOptimizer(MockProvider()).optimize(resume)
    assert all(not job.bullets for job in resume.experience)


def test_falls_back_to_raw_notes_when_provider_fails():
    class BrokenProvider(MockProvider):
        def complete(self, system, user):
            return "not json at all"

    resume = Resume(
        contact=Contact(name="Test"),
        experience=[Experience(company="Acme", role="Dev", notes=["built a thing"])],
    )
    result = ResumeOptimizer(BrokenProvider()).optimize(resume)
    assert result.experience[0].bullets == ["built a thing"]


def test_render_html_escapes_user_input():
    resume = Resume(contact=Contact(name="<script>alert(1)</script>"))
    html = render_html(resume)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_html_includes_theme_css():
    resume = load_resume(SAMPLE)
    html = render_html(resume, theme="classic")
    assert "Georgia" in html


def test_unknown_theme_raises():
    with pytest.raises(ValueError):
        render_html(Resume(contact=Contact(name="X")), theme="nope")


def test_themes_are_discovered():
    assert {"modern", "classic"} <= set(available_themes())


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_provider("gpt-nonsense")

def test_strips_unsupported_benefit_clause():
    result = strip_unsupported_clause(
        "Mentored two junior developers, enhancing team skills and knowledge.",
        ["mentored 2 junior devs"],
    )
    assert result == "Mentored two junior developers."


def test_keeps_clause_the_notes_support():
    bullet = "Established CI with GitHub Actions, ensuring tests run on every PR."
    notes = ["set up CI with github actions, tests now run on every PR"]
    assert strip_unsupported_clause(bullet, notes) == bullet


def test_leaves_bullets_without_clauses_untouched():
    bullet = "Reduced p95 latency from 800ms to 210ms with Redis caching."
    assert strip_unsupported_clause(bullet, ["cut p95 latency 800ms to 210ms"]) == bullet


def test_optimizer_strips_padding_from_model_output():
    class PaddingProvider(MockProvider):
        def complete(self, system, user):
            return json.dumps({"bullets": ["Built a parser, improving developer velocity."]})

    resume = Resume(
        contact=Contact(name="Test"),
        experience=[Experience(company="Acme", role="Dev", notes=["built a parser"])],
    )
    result = ResumeOptimizer(PaddingProvider()).optimize(resume)
    assert result.experience[0].bullets == ["Built a parser."]