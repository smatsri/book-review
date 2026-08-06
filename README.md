# Book Review

Multi-agent pipeline for analyzing and enriching public-domain books.

Current MVP: load a Gutenberg plain-text book, split it into chapters, run Reader → Editor → Critic → revise per chapter, and merge a Markdown report.

Sample book: *Alice’s Adventures in Wonderland* (Lewis Carroll) under `data/books/`.

## Setup

Requires Python 3.9+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Add provider settings to `.env`. Default is **Gemini** (`GEMINI_API_KEY`); set `LLM_PROVIDER=lmstudio` for a local LM Studio server. Details: [`docs/runbook.md`](docs/runbook.md).

## Usage

List chapters (no LLM call):

```powershell
python main.py chapters
```

Summarize one chapter (Reader → Editor → Critic → revise):

```powershell
python main.py summarize --chapter 1
```

Writes `state/chapter-01-analysis.json`, `state/chapter-01-draft.md`, `state/chapter-01-critique.json`, and `output/chapter-01-summary.md`. Re-runs skip if the summary exists; use `--force` for a full regen or `--from draft|critic|revise` to restart mid-pipeline.

## Knowledge base

| File | Purpose |
|------|---------|
| [`AGENTS.md`](AGENTS.md) | How humans and agents work in this repo |
| [`todo.md`](todo.md) | Session memory + backlog |
| [`docs/architecture.md`](docs/architecture.md) | Current system (truth) |
| [`docs/runbook.md`](docs/runbook.md) | Run / verify |
| [`docs/decisions.md`](docs/decisions.md) | Lasting choices |
| [`idea.md`](idea.md) | Vision / future (not current truth) |

## Layout

```
agents/          # LLM agents (llm, reader, editor, critic)
data/books/      # Source texts (ignored by Cursor via .cursorignore)
docs/            # Current-truth documentation
output/          # Generated Markdown
state/           # Intermediate artifacts (Reader JSON, Editor draft, Critic JSON)
book.py          # Load book + split chapters
main.py          # CLI
AGENTS.md        # Agent/human workflow
idea.md          # Product / architecture vision
todo.md          # Session + roadmap checklist
```

## Roadmap (short)

1. Book-level structured rollup in `state/`  
2. Later: RAG, footnotes, visuals, export formats  

Details: `todo.md` and `idea.md`.
