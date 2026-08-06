# Architecture (current truth)

What the codebase does **today**. Vision and future agents live in [`idea.md`](../idea.md) until they are implemented.

## Purpose

Multi-agent pipeline for analyzing and enriching public-domain books.  
Current MVP: load one Gutenberg plain-text book, split into chapters, run Reader → Editor → Critic → revise per chapter, merge into one Markdown report.

## Pipeline

```
data/books/*.txt
        |
   book.py (load + strip Gutenberg wrapper + split CHAPTER headings)
        |
   list[Chapter]
        |
   +----+----+------------------------------------------+
   |         |                                          |
chapters   summarize                                  report
(CLI)      (CLI → Reader → Editor → Critic → revise)  (CLI, no LLM)
   |         |                                          |
state/     state/chapter-NN-analysis.json
chapters.json  state/chapter-NN-critique.json
               → output/chapter-NN-summary.md
               (--all then merge → output/book-report.md)
```

## Main pieces

| Path | Role |
|------|------|
| `book.py` | Load book text, strip Gutenberg markers, split into `Chapter` |
| `main.py` | CLI: `chapters`, `summarize` (`--chapter N` / `--all`, `--force`), `report` |
| `agents/llm.py` | Shared LLM helper (Gemini or LM Studio) |
| `agents/reader.py` | Reader agent: chapter → structured JSON analysis |
| `agents/editor.py` | Editor agent: analysis → draft Markdown; revise draft using Critic JSON |
| `agents/critic.py` | Critic agent: chapter + analysis + draft → structured critique JSON |
| `data/books/` | Source texts (ignored by Cursor via `.cursorignore`) |
| `state/` | Chapter metadata + per-chapter Reader JSON + Critic JSON |
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

Critic critique (`state/chapter-NN-critique.json`):

- `chapter`, `heading`
- `verdict` — `ok` or `needs_fixes`
- `issues` — `{severity, severity, detail}`
- `must_fix`, `optional_improve` — string arrays

## LLM (current)

- Switch: `LLM_PROVIDER` = `gemini` (default) or `lmstudio`
- Shared API: `agents/llm.py` → `generate_text(...)` (agents unchanged at call site)
- **Gemini:** `GEMINI_API_KEY`, optional `GEMINI_MODEL` (default `gemini-3.5-flash`); SDK `google-genai`
- **LM Studio:** OpenAI-compatible local server via `openai` SDK; `LMSTUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`), `LMSTUDIO_MODEL` (default `qwen/qwen3.5-9b`), optional `LMSTUDIO_API_KEY` (default `lm-studio`)
- Reader / Critic: JSON mode (Gemini mime type / LM Studio `response_format=json_schema`; LM Studio rejects OpenAI’s `json_object`)
- Editor draft + revise: Markdown sections — plot summary, characters, themes/motifs, notable quotes
- Full-book report: deterministic merge of chapter files (no extra LLM call)
- Regenerating a chapter: up to four LLM calls (Reader, Editor draft, Critic, revise)

## Skip / force

- Skip when `output/chapter-NN-summary.md` exists (unless `--force`)
- If summary is missing but Reader JSON exists, Reader is reused; Editor draft → Critic → revise still run
- `--force` regenerates Reader notes, critique, and summary

## Not built yet

Do not assume these exist in code:

- Multi-round critique (only one Critic → revise pass)
- LLM reduce / book-level synthesis beyond concatenated chapter reports
- RAG / embeddings
- Footnotes, visuals, export formats

Those are roadmap items in `todo.md` / `idea.md`.
