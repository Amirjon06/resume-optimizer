"""Command line interface."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from .llm import LLMError, get_provider
from .loader import load_resume, save_resume
from .optimizer import ResumeOptimizer
from .render import available_themes, render_html, render_pdf

app = typer.Typer(add_completion=False, help="LLM-powered resume optimizer and PDF generator.")


def _echo(message: str) -> None:
    typer.echo(f"  {message}")


@app.command()
def build(
    input_file: Path = typer.Argument(..., help="Resume input file (YAML or JSON)."),
    output: Path = typer.Option("out/resume.pdf", "--output", "-o", help="Output PDF path."),
    provider: str = typer.Option("mock", "--provider", "-p", help="mock, openai, or ollama."),
    model: str = typer.Option(None, "--model", "-m", help="Model name for the provider."),
    theme: str = typer.Option("modern", "--theme", "-t", help="Visual theme."),
    max_bullets: int = typer.Option(5, "--max-bullets", help="Bullets per role."),
    save_json: Path = typer.Option(None, "--save-json", help="Also write optimized content as JSON."),
    html_only: bool = typer.Option(False, "--html", help="Write HTML instead of PDF."),
):
    """Optimize a resume and render it to PDF."""
    try:
        resume = load_resume(input_file)
    except (FileNotFoundError, ValueError) as exc:
        typer.secho(f"Input error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not resume.has_content():
        typer.secho("Nothing to optimize: add experience, projects, or education.",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    typer.echo(f"Provider: {provider}" + (f" ({model})" if model else ""))

    try:
        backend = get_provider(provider, model=model)
    except (LLMError, ValueError) as exc:
        typer.secho(f"Provider error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    optimizer = ResumeOptimizer(backend, max_bullets=max_bullets, on_progress=_echo)
    optimized = optimizer.optimize(resume)

    if save_json:
        save_resume(optimized, save_json)
        typer.echo(f"Wrote {save_json}")

    try:
        if html_only:
            output = output.with_suffix(".html")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_html(optimized, theme=theme), encoding="utf-8")
        else:
            render_pdf(optimized, output, theme=theme)
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except ImportError:
        typer.secho(
            "WeasyPrint is not installed, or its system libraries are missing.\n"
            "See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html\n"
            "You can use --html in the meantime.",
            fg=typer.colors.RED, err=True,
        )
        raise typer.Exit(1)

    typer.secho(f"Done: {output}", fg=typer.colors.GREEN)


@app.command()
def render(
    input_file: Path = typer.Argument(..., help="Optimized resume JSON."),
    output: Path = typer.Option("out/resume.pdf", "--output", "-o"),
    theme: str = typer.Option("modern", "--theme", "-t"),
):
    """Re-render an already-optimized resume without calling the LLM again."""
    resume = load_resume(input_file)
    render_pdf(resume, output, theme=theme)
    typer.secho(f"Done: {output}", fg=typer.colors.GREEN)


@app.command()
def themes():
    """List available themes."""
    for name in available_themes():
        typer.echo(name)


def main() -> None:
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
