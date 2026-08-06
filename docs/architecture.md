# Architecture (current truth)

What the codebase does **today**. Vision and future agents live in [`idea.md`](../idea.md) until they are implemented.

## Purpose

Multi-agent pipeline for analyzing and enriching public-domain books.  
Current MVP: load one Gutenberg plain-text book, split into chapters, run Reader → Editor → Critic → revise per chapter, merge into one Markdown report, and roll up cross-chapter characters/themes into structured state.

## Pipeline

```
data/books/*.txt
        |
   book.py (load + strip Gutenberg wrapper + split CHAPTER headings)
        |
   list[Chapter]
        |
   +----+----+------------------+---------------------------+
   |         |                  |                           |
chapters   summarize          report                      rollup
(CLI)      (CLI → Reader →    (CLI, no LLM)               (CLI, no LLM)
           Editor → Critic →        |                           |
           revise)            output/book-report.md   state/book-rollup.json
   |         |
state/     state/chapter-NN-analysis.json
chapters.json  state/chapter-NN-draft.md
               state/chapter-NN-critique.json
               → output/chapter-NN-summary.md
               (--all then report + rollup)
```

## Main pieces

| Path | Role |
|------|------|
| `book.py` | Load book text, strip Gutenberg markers, split into `Chapter` |
| `rollup.py` | Deterministic merge of chapter analyses → book-level characters/themes |
| `main.py` | CLI: `chapters`, `summarize` (`--chapter N` / `--all`, `--force`, `--from STAGE`), `report`, `rollup` |
| `agents/llm.py` | Shared LLM helper (Gemini or LM Studio) |
| `agents/reader.py` | Reader agent: chapter → structured JSON analysis |
| `agents/editor.py` | Editor agent: analysis → draft Markdown; revise draft using Critic JSON |
| `agents/critic.py` | Critic agent: chapter + analysis + draft → structured critique JSON |
| `data/books/` | Source texts (ignored by Cursor via `.cursorignore`) |
| `state/` | Chapter metadata + Reader JSON + Editor draft + Critic JSON + `book-rollup.json` |
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

Book rollup (`state/book-rollup.json`, from `rollup` / end of `summarize --all`):

- `chapters_included` — chapter numbers that contributed analyses
- `characters` — `{name, notes[], chapters[]}` merged by normalized name (casefold; strip leading `The `)
- `themes` — `{theme, chapters[]}` merged by case-insensitive exact string
- No LLM; no fuzzy alias merge (e.g. `Queen` vs `Queen of Hearts` stay separate)

## LLM (current)

- Switch: `LLM_PROVIDER` = `gemini` (default) or `lmstudio`
- Shared API: `agents/llm.py` → `generate_text(...)` (agents unchanged at call site)
- **Gemini:** `GEMINI_API_KEY`, optional `GEMINI_MODEL` (default `gemini-3.5-flash`); SDK `google-genai`
- **LM Studio:** OpenAI-compatible local server via `openai` SDK; `LMSTUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`), `LMSTUDIO_MODEL` (default `qwen/qwen3.5-9b`), optional `LMSTUDIO_API_KEY` (default `lm-studio`)
- Reader / Critic: JSON mode (Gemini mime type / LM Studio `response_format=json_schema`; LM Studio rejects OpenAI’s `json_object`)
- Editor draft + revise: Markdown sections — plot summary, characters, themes/motifs, notable quotes
- Full-book report: deterministic merge of chapter Markdown files (no LLM)
- Book rollup: deterministic merge of Reader analyses into `state/book-rollup.json` (no LLM)
- Regenerating a chapter: up to four LLM calls (Reader, Editor draft, Critic, revise); fewer with soft resume or `--from`

## Skip / force / from

- Skip when `output/chapter-NN-summary.md` exists (unless `--force` or `--from`)
- Soft resume when summary is missing: reuse the contiguous prefix of artifacts (`analysis` → `draft` → `critique`), then continue from the first gap
- `--force` regenerates from Reader through summary (mutually exclusive with `--from`)
- `--from reader|draft|critic|revise` restarts at that stage (reuses earlier artifacts; requires them to exist); overrides skip when summary exists

## Not built yet

Do not assume these exist in code:

- Multi-round critique (only one Critic → revise pass)
- Fuzzy character/theme alias merge beyond normalize rules above
- LLM reduce / book-level synthesis beyond concatenated chapter reports
- RAG / embeddings
- Footnotes, visuals, export formats

Those are roadmap items in `todo.md` / `idea.md`.
