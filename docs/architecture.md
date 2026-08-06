# Architecture (current truth)

What the codebase does **today**. Vision and future agents live in [`idea.md`](../idea.md) until they are implemented.

## Purpose

Multi-agent pipeline for analyzing and enriching public-domain books.  
Current MVP: load one Gutenberg plain-text book, split into chapters, run Reader → Editor per chapter, merge into one Markdown report.

## Pipeline

```
data/books/*.txt
        |
   book.py (load + strip Gutenberg wrapper + split CHAPTER headings)
        |
   list[Chapter]
        |
   +----+----+---------------------------+
   |         |                           |
chapters   summarize                   report
(CLI)      (CLI → Reader → Editor)     (CLI, no LLM)
   |         |                           |
state/     state/chapter-NN-analysis.json
chapters.json  → output/chapter-NN-summary.md
               (--all then merge → output/book-report.md)
```

## Main pieces

| Path | Role |
|------|------|
| `book.py` | Load book text, strip Gutenberg markers, split into `Chapter` |
| `main.py` | CLI: `chapters`, `summarize` (`--chapter N` / `--all`, `--force`), `report` |
| `agents/llm.py` | Shared Gemini client helper |
| `agents/reader.py` | Reader agent: chapter → structured JSON analysis |
| `agents/editor.py` | Editor agent: analysis JSON → human Markdown |
| `data/books/` | Source texts (ignored by Cursor via `.cursorignore`) |
| `state/` | Chapter metadata + per-chapter Reader JSON |
| `output/` | Per-chapter summaries + merged `book-report.md` |

## Data model

`Chapter` (`book.py`):

- `number` — Arabic chapter number (from Roman numeral)
- `roman` — Roman numeral from the heading
- `title` — first non-empty line after `CHAPTER …`
- `text` — chapter body
- `heading` — `CHAPTER {roman}. {title}`

Reader analysis (`state/chapter-NN-analysis.json`):

- `chapter`, `heading`
- `plot`, `characters` (`name` / `note`), `themes`, `quotes`, `events`

## LLM (current)

- Provider: **Gemini** (`GEMINI_API_KEY`, optional `GEMINI_MODEL`)
- Default model: `gemini-3.5-flash`
- SDK: `google-genai` (`client.models.generate_content`)
- Reader: JSON mode (`response_mime_type=application/json`)
- Editor: Markdown sections — plot summary, characters, themes/motifs, notable quotes
- Full-book report: deterministic merge of chapter files (no extra LLM call)

## Skip / force

- Skip when `output/chapter-NN-summary.md` exists (unless `--force`)
- If summary is missing but Reader JSON exists, Editor reuses notes (one LLM call)
- `--force` regenerates both Reader notes and Editor summary

## Not built yet

Do not assume these exist in code:

- Critic agent / critique → revise loop
- LLM reduce / book-level synthesis beyond concatenated chapter reports
- RAG / embeddings
- Footnotes, visuals, export formats

Those are roadmap items in `todo.md` / `idea.md`.
