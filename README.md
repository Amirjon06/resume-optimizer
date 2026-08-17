# Resume Optimizer

A command line tool that turns rough career notes into a formatted resume PDF.
You write messy bullet points; a language model rewrites them into tight,
outcome-first resume lines, and the result is rendered through an HTML/CSS
template into a PDF.

Works with the OpenAI API, a local Ollama model, or fully offline with a
built-in mock backend so the pipeline can be run and tested without an API key.

## Why

Most resume tools either template your text without improving it, or generate
generic filler. This one keeps your raw notes as the source of truth in a YAML
file, and treats the rewrite as a separate, re-runnable step. The optimized
output is saved as JSON, so you can hand-edit any bullet and re-render without
paying for another API call.

## Install

Requires Python 3.10+.

```bash
git clone https://github.com/Amirjon06/resume-optimizer
cd resume-optimizer
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

WeasyPrint depends on Pango and Cairo. On macOS:

```bash
brew install pango libffi
```

On Debian/Ubuntu:

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
```

If you cannot install those, `--html` will write a styled HTML file you can
print to PDF from a browser.

## Usage

Copy the sample input and replace it with your own details:

```bash
cp examples/sample_input.yaml my_resume.yaml
```

Run offline to check the layout:

```bash
python -m resume_optimizer.cli build my_resume.yaml -o out/resume.pdf
```

Run with a real model:

```bash
export OPENAI_API_KEY=sk-...
python -m resume_optimizer.cli build my_resume.yaml --provider openai --model gpt-4o-mini
```

Or locally with Ollama:

```bash
ollama serve
python -m resume_optimizer.cli build my_resume.yaml --provider ollama --model llama3.1
```

### Options

| Flag | Default | Description |
| --- | --- | --- |
| `--output`, `-o` | `out/resume.pdf` | Output path |
| `--provider`, `-p` | `mock` | `mock`, `openai`, or `ollama` |
| `--model`, `-m` | provider default | Model name |
| `--theme`, `-t` | `modern` | `modern` or `classic` |
| `--max-bullets` | `5` | Bullets per role |
| `--save-json` | — | Save optimized content for later editing |
| `--html` | off | Write HTML instead of PDF |

### Edit and re-render

```bash
python -m resume_optimizer.cli build my_resume.yaml --provider openai --save-json out/optimized.json
# edit out/optimized.json by hand
python -m resume_optimizer.cli render out/optimized.json -o out/final.pdf --theme classic
```

## Input format

Only `contact.name` is required. Everything else is optional.

```yaml
contact:
  name: Jane Doe
  email: jane@example.com

target_role: Senior Backend Engineer

experience:
  - company: Acme
    role: Backend Engineer
    start: Mar 2023
    end: Present
    notes:
      - cut p95 latency from 800ms to 210ms with redis caching
      - set up CI with github actions
```

Write `notes` however you think of them. Don't polish them — that is the tool's
job. Include real numbers where you have them; the prompt forbids the model from
inventing metrics, so anything quantified in the output came from your notes.

If you omit the `skills` section entirely, the model infers and groups your
skills from the rest of the resume.

Adding a `job_description` biases the rewrite toward that posting's language.

## How it works

```
YAML input → Pydantic validation → LLM rewrite → Jinja2 template → WeasyPrint → PDF
```

- `models.py` — schema for the resume. Each role holds both raw `notes` and
  generated `bullets`, so the original input survives a re-run.
- `llm/` — provider abstraction. `base.py` handles the JSON contract, including
  salvaging responses wrapped in code fences or prose, and retrying once with a
  stricter instruction.
- `optimizer.py` — orchestrates the rewrite. Falls back to the raw notes if the
  model fails, so a bad API response degrades the output instead of crashing.
- `render.py` — renders the Jinja template with a theme stylesheet.
- `templates/themes/` — one CSS file per theme; drop in a new file and it is
  picked up automatically.

## Themes

`modern` is a sans-serif layout with a blue accent. `classic` is a centered
serif layout. Both are tuned to fit a typical resume on one page.

To add your own, copy a file in `resume_optimizer/templates/themes/` and rename
it. `python -m resume_optimizer.cli themes` lists what is available.

## Tests

```bash
pytest
```

The suite runs against the mock provider, so it needs no network access or API
key.

## License

MIT
