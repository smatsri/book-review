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
   +----+----+------------------+---------------------------+----------+
   |         |                  |                           |          |
chapters   summarize          report                      rollup     aliases
(CLI)      (CLI → Reader →    (CLI, no LLM)               (CLI,      (CLI → Alias
           Editor → Critic →        |                      no LLM)    Merger LLM)
           revise)            output/book-report.md   book-rollup.json  |
   |         |                                              |     book-rollup-
state/     state/chapter-NN-analysis.json                   |     merged.json
chapters.json  state/chapter-NN-draft.md                    +----------+
               state/chapter-NN-critique.json
               → output/chapter-NN-summary.md
               (--all then report + rollup; aliases is separate)
```

## Main pieces

| Path | Role |
|------|------|
| `book.py` | Load book text, strip Gutenberg markers, split into `Chapter` |
| `rollup.py` | Deterministic merge of chapter analyses → book-level characters/themes; `apply_alias_clusters` for enrichment |
| `main.py` | CLI: `chapters`, `summarize` (`--chapter N` / `--all`, `--force`, `--from STAGE`), `report`, `rollup`, `aliases` |
| `agents/llm.py` | Shared LLM helper (Gemini or LM Studio) |
| `agents/reader.py` | Reader agent: chapter → structured JSON analysis |
| `agents/editor.py` | Editor agent: analysis → draft Markdown; revise draft using Critic JSON |
| `agents/critic.py` | Critic agent: chapter + analysis + draft → structured critique JSON |
| `agents/alias_merger.py` | Alias Merger: rollup name lists → character/theme alias clusters (JSON) |
| `data/books/` | Source texts (ignored by Cursor via `.cursorignore`) |
| `state/` | Chapter metadata + Reader JSON + Editor draft + Critic JSON + `book-rollup.json` + `book-rollup-merged.json` |
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
- No LLM; aliases like `Queen` vs `Queen of Hearts` stay separate until `aliases`

Merged rollup (`state/book-rollup-merged.json`, from `aliases`):

- `source` — `book-rollup.json`
- `chapters_included` — copied from baseline rollup
- `characters` — `{name, aliases[], notes[], chapters[]}` after LLM clustering + deterministic apply
- `themes` — `{theme, aliases[], chapters[]}` likewise
- Display `name` / `theme` = longest alias (ties → more source chapters, then alphabetical)
- Unknown / overlapping LLM labels dropped; uncovered labels become singletons
- Not run by `summarize --all`; requires existing `book-rollup.json`; skip unless `--force`

## LLM (current)

- Switch: `LLM_PROVIDER` = `gemini` (default) or `lmstudio`
- Shared API: `agents/llm.py` → `generate_text(...)` (agents unchanged at call site)
- **Gemini:** `GEMINI_API_KEY`, optional `GEMINI_MODEL` (default `gemini-3.5-flash`); SDK `google-genai`
- **LM Studio:** OpenAI-compatible local server via `openai` SDK; `LMSTUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`), `LMSTUDIO_MODEL` (default `qwen/qwen3.5-9b`), optional `LMSTUDIO_API_KEY` (default `lm-studio`)
- Reader / Critic: JSON mode (Gemini mime type / LM Studio `response_format=json_schema`; LM Studio rejects OpenAI’s `json_object`)
- Editor draft + revise: Markdown sections — plot summary, characters, themes/motifs, notable quotes
- Full-book report: deterministic merge of chapter Markdown files (no LLM)
- Book rollup: deterministic merge of Reader analyses into `state/book-rollup.json` (no LLM)
- Alias merge: one LLM call over rollup name lists → `state/book-rollup-merged.json`
- Regenerating a chapter: up to four LLM calls (Reader, Editor draft, Critic, revise); fewer with soft resume or `--from`

## Skip / force / from

- Skip when `output/chapter-NN-summary.md` exists (unless `--force` or `--from`)
- Soft resume when summary is missing: reuse the contiguous prefix of artifacts (`analysis` → `draft` → `critique`), then continue from the first gap
- `--force` regenerates from Reader through summary (mutually exclusive with `--from`)
- `--from reader|draft|critic|revise` restarts at that stage (reuses earlier artifacts; requires them to exist); overrides skip when summary exists
- `aliases` skips when `state/book-rollup-merged.json` exists unless `--force`

## Not built yet

Do not assume these exist in code:

- Multi-round critique (only one Critic → revise pass)
- LLM reduce / book-level synthesis beyond concatenated chapter reports
- RAG / embeddings
- Footnotes, visuals, export formats

Those are roadmap items in `todo.md` / `idea.md`.
