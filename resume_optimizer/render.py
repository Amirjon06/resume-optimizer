"""Renders a Resume into styled HTML and PDF."""

from __future__ import annotations

from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Resume

TEMPLATE_DIR = Path(__file__).parent / "templates"
THEME_DIR = TEMPLATE_DIR / "themes"


def available_themes() -> List[str]:
    return sorted(p.stem for p in THEME_DIR.glob("*.css"))


def _load_theme(theme: str) -> str:
    path = THEME_DIR / f"{theme}.css"
    if not path.exists():
        raise ValueError(
            f"Unknown theme '{theme}'. Available: {', '.join(available_themes())}"
        )
    return path.read_text(encoding="utf-8")


def render_html(resume: Resume, theme: str = "modern") -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        # "j2" must be listed explicitly: select_autoescape looks at the final
        # extension, so resume.html.j2 would otherwise render unescaped.
        autoescape=select_autoescape(enabled_extensions=("html", "xml", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("resume.html.j2")
    return template.render(r=resume, theme_css=_load_theme(theme))


def render_pdf(resume: Resume, output: str | Path, theme: str = "modern") -> Path:
    from weasyprint import HTML

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    html = render_html(resume, theme=theme)
    # base_url lets the template reference local assets such as fonts or a photo.
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(output))
    return output
