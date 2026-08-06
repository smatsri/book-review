# Architecture (current truth)

What the codebase does **today**. Vision and future agents live in [`idea.md`](../idea.md) until they are implemented.

## Purpose

Multi-agent pipeline for analyzing and enriching public-domain books.  
Current MVP: load one Gutenberg plain-text book, split into chapters, summarize each with an LLM, merge into one Markdown report.

## Pipeline

```
data/books/*.txt
        |
   book.py (load + strip Gutenberg wrapper + split CHAPTER headings)
        |
   list[Chapter]
        |
   +----+----+------------------+
   |         |                  |
chapters   summarize          report
(CLI)      (CLI → Gemini)     (CLI, no LLM)
   |         |                  |
state/     output/              output/book-report.md
chapters.json  chapter-NN-summary.md
               (map; --all then merge)
```

## Main pieces

| Path | Role |
|------|------|
| `book.py` | Load book text, strip Gutenberg markers, split into `Chapter` |
| `main.py` | CLI: `chapters`, `summarize` (`--chapter N` / `--all`, `--force`), `report` |
| `agents/summarizer.py` | Stage-1 single agent (Gemini generate_content → Markdown) |
| `data/books/` | Source texts (ignored by Cursor via `.cursorignore`) |
| `state/` | Intermediate JSON (e.g. chapter metadata) |
| `output/` | Per-chapter summaries + merged `book-report.md` |

## Data model

`Chapter` (`book.py`):

- `number` — Arabic chapter number (from Roman numeral)
- `roman` — Roman numeral from the heading
- `title` — first non-empty line after `CHAPTER …`
- `text` — chapter body
- `heading` — `CHAPTER {roman}. {title}`

## LLM (current)

- Provider: **Gemini** (`GEMINI_API_KEY`, optional `GEMINI_MODEL`)
- Default model: `gemini-3.5-flash`
- SDK: `google-genai` (`client.models.generate_content`)
- Output sections: plot summary, characters, themes/motifs, notable quotes
- Full-book report: deterministic merge of chapter files (no extra LLM call)

## Not built yet

Do not assume these exist in code:

- LLM reduce / book-level synthesis beyond concatenated chapter reports
- Reader / Critic / Editor agents
- RAG / embeddings
- Footnotes, visuals, export formats

Those are roadmap items in `todo.md` / `idea.md`.
