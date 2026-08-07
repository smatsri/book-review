# Architecture (current truth)

What the codebase does **today**. Vision and future agents live in [`idea.md`](../idea.md) until they are implemented.

## Purpose

Multi-agent pipeline for analyzing and enriching public-domain books.  
Current MVP: load one Gutenberg plain-text book, split into chapters, run Reader → Editor → Critic → revise per chapter, merge into one Markdown report, roll up cross-chapter characters/themes into structured state, optionally research footnotes into enriched chapter Markdown, optionally LLM-reduce into a book-level synthesis woven into the report, optionally derive book-level visual identity, character visual sheets, place / setting sheets, and scene briefs into structured state, and export the report to HTML/PDF/EPUB.

## Pipeline

```
data/books/*.txt
        |
   book.py (load + strip Gutenberg wrapper + split CHAPTER headings)
        |
   list[Chapter]
        |
   +----+----+--------+--------+--------+-----------+----------+----------------+------------------+---------------+---------------+
   |         |        |        |        |           |          |                |                  |               |               |
chapters summarize report  rollup  aliases footnotes  reduce  visual-identity  visual-characters visual-places visual-scenes
(CLI)    (CLI →    (CLI,   (CLI,   (CLI →  (CLI →    (CLI →   (CLI → Visual     (CLI → Visual     (CLI → Visual (CLI → Visual
         Reader →  no LLM) no LLM) Alias   Footnote  Reducer  Identity LLM)    Characters LLM)   Places LLM)   Scenes LLM)
         Editor →     |       |    Merger) LLM +     LLM)          |                  |               |               |
         Critic →     |       |      |     weave)      |           |                  |               |               |
         revise)      |       |      |       |         |           |                  |               |               |
   |         |        |       |      |       |         |           |                  |               |               |
state/   state/     prefers book-  book-  state/   output/   state/book-      state/book-      state/book-    state/book-
chapters chapter-NN enriched rollup rollup- chapter- book-    visual-         visual-         visual-        visual-
.json    analysis   else    .json  merged  NN-      synthesis identity.json  characters.json places.json   scenes.json
         + draft +  summary        .json   footnotes.md →     (no report      (needs identity;(needs identity;(needs identity
         critique → → book-                + enriched weave)  weave yet)      no report weave) no report weave)+ characters
         summary.md report.md              (--all then                                         + places; no
         (--all →   (weaves                 report)                                            report weave)
          report +  synthesis if
          rollup;   present)
          others
          separate)
                                    |
                                 export (CLI, no LLM)
                                    |
                         book-report.html / .pdf / .epub
```

## Main pieces

| Path | Role |
|------|------|
| `book.py` | Load book text, strip Gutenberg markers, split into `Chapter` |
| `rollup.py` | Deterministic merge of chapter analyses → book-level characters/themes; `apply_alias_clusters` for enrichment |
| `footnotes.py` | Deterministic Markdown Extra weave of footnote JSON into enriched chapter MD |
| `export_book.py` | Deterministic export of `book-report.md` → HTML / PDF / EPUB |
| `main.py` | CLI: `chapters`, `summarize`, `report`, `rollup`, `aliases`, `reduce`, `visual-identity`, `visual-characters`, `visual-places`, `visual-scenes`, `footnotes`, `export` |
| `agents/llm.py` | Shared LLM helper (Gemini or LM Studio) |
| `agents/reader.py` | Reader agent: chapter → structured JSON analysis |
| `agents/editor.py` | Editor agent: analysis → draft Markdown; revise draft using Critic JSON |
| `agents/critic.py` | Critic agent: chapter + analysis + draft → structured critique JSON |
| `agents/alias_merger.py` | Alias Merger: rollup name lists → character/theme alias clusters (JSON) |
| `agents/reducer.py` | Reducer agent: chapter summaries + rollup → book-level Markdown synthesis |
| `agents/visual_identity.py` | Visual Identity agent: compact analyses + rollup → book-level visual identity JSON |
| `agents/visual_characters.py` | Visual Characters agent: analyses + rollup + identity → character visual sheets JSON |
| `agents/visual_places.py` | Visual Places agent: analyses + identity → place / setting visual sheets JSON |
| `agents/visual_scenes.py` | Visual Scenes agent: analyses + identity + character/place sheets → scene briefs JSON |
| `agents/visual_traits.py` | Shared Visual Bible trait-row normalization (`value` / `kind` / `confidence` / `note`) |
| `agents/footnote.py` | Footnote agent: chapter + analysis → structured footnotes JSON |
| `data/books/` | Source texts (ignored by Cursor via `.cursorignore`) |
| `state/` | Chapter metadata + Reader/Editor/Critic artifacts + rollups + footnotes JSON |
| `output/` | Per-chapter summaries + enriched MD + synthesis + merged `book-report.md` + HTML/PDF/EPUB |

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

Chapter footnotes (`state/chapter-NN-footnotes.json`, from `footnotes`):

- `chapter`, `heading`
- `footnotes` — `{id, anchor, kind, note, confidence}` (`kind`: history/concept/culture/source; `confidence`: high/medium/low)
- `id` namespaced `chNN-…` for safe merge into `book-report.md`
- Editor `chapter-NN-summary.md` stays pristine; weave writes `output/chapter-NN-enriched.md`
- Unplaceable anchors listed under “Unplaced notes” in enriched MD
- Not run by `summarize --all`; requires analysis + summary; skip unless `--force`

Book synthesis (`output/book-synthesis.md`, from `reduce`):

- Markdown sections: Book overview, Plot arc, Characters, Themes / motifs, Closing note
- LLM inputs: compact Reader analyses (truncated plot + themes) plus slim rollup name lists (`book-rollup-merged.json` if present else `book-rollup.json`); sized for ~8k local context
- Also requires all `chapter-NN-summary.md` so the rebuilt report can include chapters
- No full book text / full summaries in the prompt; no author/genre external context
- `write_book_report` inserts synthesis after the report header when the file exists
- Not run by `summarize --all`; skip unless `--force`

Book visual identity (`state/book-visual-identity.json`, from `visual-identity`):

- `source_rollup` — which rollup file fed the prompt
- `chapters_included` — chapter numbers from the analyses
- `artistic_style`, `color_palette`, `atmosphere`, `period`, `motifs` — arrays of `{value, kind, confidence, note}`
- `kind`: `fact` | `interpretation` | `art_decision`; `confidence` 0.0–1.0 (vision scale)
- LLM inputs: same compact analyses + slim rollup as reduce; no full book text; no chapter summaries required
- Bad trait rows dropped; missing top-level keys fail
- Not woven into `book-report.md` yet; not run by `summarize --all`; skip unless `--force`

Character visual sheets (`state/book-visual-characters.json`, from `visual-characters`):

- `source_rollup`, `source_identity` — which rollup / identity files fed the prompt
- `chapters_included` — chapter numbers from the analyses
- `characters` — array of `{name, physical, personality, visual_language}` where each sheet array is `{value, kind, confidence, note}` traits
- Requires `book-visual-identity.json` plus all chapter analyses + rollup (`book-rollup-merged.json` if present else `book-rollup.json`)
- LLM inputs: slim identity trait values, enriched rollup cast (top ~8 by chapter count with notes), compact analyses (per-chapter character name/note only); sized for ~8k local context; no full book text
- Names must match the cast index; unknown / malformed character rows dropped; missing `characters` key fails
- Not woven into `book-report.md` yet; not run by `summarize --all`; skip unless `--force`

Place / setting sheets (`state/book-visual-places.json`, from `visual-places`):

- `source_identity` — which identity file fed the prompt
- `chapters_included` — chapter numbers from the analyses
- `places` — array of `{name, architecture, climate, atmosphere, symbols}` where each sheet array is `{value, kind, confidence, note}` traits
- Requires `book-visual-identity.json` plus all chapter analyses (no rollup / character sheets)
- LLM inputs: slim identity trait values + compact analyses (truncated plot + capped events); LLM selects up to ~8 key places; sized for ~8k local context; no full book text
- Malformed / duplicate place rows dropped; missing `places` key fails
- Not woven into `book-report.md` yet; not run by `summarize --all`; skip unless `--force`

Scene briefs (`state/book-visual-scenes.json`, from `visual-scenes`):

- `source_identity`, `source_characters`, `source_places` — which bible files fed the prompt
- `chapters_included` — chapter numbers from the analyses
- `scenes` — array of `{title, chapter, characters, location, emotional_focus, composition}` where `characters` / `location` are string lists and `emotional_focus` / `composition` are `{value, kind, confidence, note}` trait arrays
- Requires identity + character sheets + place sheets plus all chapter analyses
- LLM inputs: slim identity trait values, character/place sheet names, compact analyses (truncated plot + capped events + light cast names); LLM selects up to ~8 illustration-worthy moments; sized for ~8k local context; no full book text
- Soft preference for sheet names (no hard allowlist); malformed / duplicate `(chapter, title)` rows dropped; missing `scenes` key fails
- Not woven into `book-report.md` yet; not run by `summarize --all`; skip unless `--force`

## LLM (current)

- Switch: `LLM_PROVIDER` = `gemini` (default) or `lmstudio`
- Shared API: `agents/llm.py` → `generate_text(...)` (agents unchanged at call site)
- **Gemini:** `GEMINI_API_KEY`, optional `GEMINI_MODEL` (default `gemini-3.5-flash`); SDK `google-genai`
- **LM Studio:** OpenAI-compatible local server via `openai` SDK; `LMSTUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`), `LMSTUDIO_MODEL` (default `qwen/qwen3.5-9b`), optional `LMSTUDIO_API_KEY` (default `lm-studio`)
- Reader / Critic: JSON mode (Gemini mime type / LM Studio `response_format=json_schema`; LM Studio rejects OpenAI’s `json_object`)
- Editor draft + revise: Markdown sections — plot summary, characters, themes/motifs, notable quotes
- Full-book report: deterministic merge of chapter Markdown (prefer enriched over summary; weaves `book-synthesis.md` when present; no LLM in `report` itself)
- Book rollup: deterministic merge of Reader analyses into `state/book-rollup.json` (no LLM)
- Alias merge: one LLM call over rollup name lists → `state/book-rollup-merged.json`
- Reduce: one LLM call over compact analyses + slim rollup → `output/book-synthesis.md`; rebuilds report
- Visual identity: one LLM call over compact analyses + slim rollup → `state/book-visual-identity.json` (no report weave)
- Visual characters: one LLM call over compact analyses + enriched rollup cast + slim identity → `state/book-visual-characters.json` (no report weave)
- Visual places: one LLM call over compact analyses (plot + events) + slim identity → `state/book-visual-places.json` (no report weave)
- Visual scenes: one LLM call over compact analyses (plot + events + cast names) + slim identity + character/place sheet names → `state/book-visual-scenes.json` (no report weave)
- Footnotes: one LLM call per chapter → footnotes JSON; deterministic weave → enriched MD
- Export: deterministic MD → HTML/PDF/EPUB from `book-report.md` (no LLM; Markdown Extra footnotes supported via `extra`)
- Regenerating a chapter summary: up to four LLM calls (Reader, Editor draft, Critic, revise); fewer with soft resume or `--from`

## Skip / force / from

- Skip when `output/chapter-NN-summary.md` exists (unless `--force` or `--from`)
- Soft resume when summary is missing: reuse the contiguous prefix of artifacts (`analysis` → `draft` → `critique`), then continue from the first gap
- `--force` regenerates from Reader through summary (mutually exclusive with `--from`)
- `--from reader|draft|critic|revise` restarts at that stage (reuses earlier artifacts; requires them to exist); overrides skip when summary exists
- `aliases` skips when `state/book-rollup-merged.json` exists unless `--force`
- `reduce` skips when `output/book-synthesis.md` exists unless `--force`
- `visual-identity` skips when `state/book-visual-identity.json` exists unless `--force`
- `visual-characters` skips when `state/book-visual-characters.json` exists unless `--force`
- `visual-places` skips when `state/book-visual-places.json` exists unless `--force`
- `visual-scenes` skips when `state/book-visual-scenes.json` exists unless `--force`
- `footnotes` with no `--chapter` resumes at the first chapter missing footnotes JSON; with `--chapter` skips when that file exists unless `--force`
- `export` skips each existing `output/book-report.{html,pdf,epub}` unless `--force`

## Not built yet

Do not assume these exist in code:

- Multi-round critique (only one Critic → revise pass)
- RAG / embeddings
- Visual Bible beyond scene briefs (consistency handoff, image gen, report weave)

Those are roadmap items in `todo.md` / `idea.md`.
