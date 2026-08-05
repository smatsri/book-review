# Book Review

Multi-agent pipeline for analyzing and enriching public-domain books.

Current MVP: load a Gutenberg plain-text book, split it into chapters, and summarize one chapter with an LLM.

Sample book: *Alice’s Adventures in Wonderland* (Lewis Carroll) under `data/books/`.

## Setup

Requires Python 3.9+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Add your API key to `.env`. The summarizer currently uses **OpenAI** (`OPENAI_API_KEY`). Switching to **Gemini** is planned — see `todo.md`.

Full commands and smoke checks: [`docs/runbook.md`](docs/runbook.md).

## Usage

List chapters (no LLM call):

```powershell
python main.py chapters
```

Summarize one chapter:

```powershell
python main.py summarize --chapter 1
```

Output is written to `output/chapter-01-summary.md`.

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
agents/          # LLM agents (stage-1 summarizer for now)
data/books/      # Source texts (ignored by Cursor via .cursorignore)
docs/            # Current-truth documentation
output/          # Generated Markdown
state/           # Intermediate JSON / analysis state
book.py          # Load book + split chapters
main.py          # CLI
AGENTS.md        # Agent/human workflow
idea.md          # Product / architecture vision
todo.md          # Session + roadmap checklist
```

## Roadmap (short)

1. Switch provider to Gemini  
2. Summarize all chapters and merge a full report  
3. Reader → Critic → Editor agent loop  
4. Later: RAG, footnotes, visuals, export formats  

Details: `todo.md` and `idea.md`.
