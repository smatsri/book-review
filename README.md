# Book Review

Multi-agent pipeline for analyzing and enriching public-domain books.

Current MVP: load a Gutenberg plain-text book, split it into chapters, run Reader → Editor → Critic → revise per chapter, merge a Markdown report, roll up cross-chapter characters/themes into `state/book-rollup.json`, optionally LLM-merge aliases, optionally research footnotes into enriched chapter Markdown, optionally LLM-reduce a book-level synthesis into the report, and export the report to HTML/PDF/EPUB.

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

Optional footnotes (keeps summaries pristine; needs analysis + summary):

```powershell
python main.py footnotes
python main.py footnotes --chapter 1
```

Omitting `--chapter` resumes at the first chapter without footnotes. Writes `state/chapter-NN-footnotes.json` and `output/chapter-NN-enriched.md`. Then `report` prefers enriched files when present.

Optional book-level synthesis (needs analyses + summaries + rollup):

```powershell
python main.py reduce
```

Writes `output/book-synthesis.md` and rebuilds `book-report.md` with the overview woven in.

Export the merged report (needs `output/book-report.md` from `report` or `summarize --all`):

```powershell
python main.py export
```

Writes `output/book-report.html`, `.pdf`, and `.epub`. Use `--format html|pdf|epub` for one format; `--force` to regenerate.

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
agents/          # LLM agents (llm, reader, editor, critic, alias_merger, reducer, footnote)
data/books/      # Source texts (ignored by Cursor via .cursorignore)
docs/            # Current-truth documentation
output/          # Generated Markdown + HTML/PDF/EPUB
state/           # Intermediate artifacts (Reader/Editor/Critic, rollups, footnotes)
book.py          # Load book + split chapters
rollup.py        # Book-level character/theme merge + alias apply
footnotes.py     # Weave footnote JSON into enriched chapter Markdown
export_book.py   # Markdown report → HTML / PDF / EPUB
main.py          # CLI
AGENTS.md        # Agent/human workflow
docs/agent-playbook.md  # Checklist to copy into a new agent-first repo
idea.md          # Product / architecture vision
todo.md          # Session + roadmap checklist
```

## Roadmap (short)

1. Later: RAG, visuals; billing/hybrid when needed  

Details: `todo.md` and `idea.md`.
