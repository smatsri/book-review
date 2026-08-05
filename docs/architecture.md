# Architecture (current truth)

What the codebase does **today**. Vision and future agents live in [`idea.md`](../idea.md) until they are implemented.

## Purpose

Multi-agent pipeline for analyzing and enriching public-domain books.  
Current MVP: load one Gutenberg plain-text book, split into chapters, summarize one chapter with an LLM.

## Pipeline

```
data/books/*.txt
        |
   book.py (load + strip Gutenberg wrapper + split CHAPTER headings)
        |
   list[Chapter]
        |
   +----+----+
   |         |
chapters   summarize
(CLI)      (CLI → agents/summarizer.py → OpenAI)
   |         |
state/     output/chapter-NN-summary.md
chapters.json
```

## Main pieces

| Path | Role |
|------|------|
| `book.py` | Load book text, strip Gutenberg markers, split into `Chapter` |
| `main.py` | CLI: `chapters`, `summarize --chapter N` |
| `agents/summarizer.py` | Stage-1 single agent (OpenAI chat completion → Markdown) |
| `data/books/` | Source texts (ignored by Cursor via `.cursorignore`) |
| `state/` | Intermediate JSON (e.g. chapter metadata) |
| `output/` | Generated Markdown summaries |

## Data model

`Chapter` (`book.py`):

- `number` — Arabic chapter number (from Roman numeral)
- `roman` — Roman numeral from the heading
- `title` — first non-empty line after `CHAPTER …`
- `text` — chapter body
- `heading` — `CHAPTER {roman}. {title}`

## LLM (current)

- Provider: **OpenAI** (`OPENAI_API_KEY`, optional `OPENAI_MODEL`)
- Default model: `gpt-4o-mini`
- Output sections: plot summary, characters, themes/motifs, notable quotes

Planned switch: Gemini — see [`todo.md`](../todo.md) and [`decisions.md`](decisions.md).

## Not built yet

Do not assume these exist in code:

- Full-book map/reduce summary
- Reader / Critic / Editor agents
- RAG / embeddings
- Footnotes, visuals, export formats

Those are roadmap items in `todo.md` / `idea.md`.
