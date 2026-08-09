# Runbook

## Setup

Requires Python 3.9+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Copy `.env.example` to `.env`. Choose provider with `LLM_PROVIDER`:

- **gemini** (default): set `GEMINI_API_KEY`. Optional: `GEMINI_MODEL` (default `gemini-3.5-flash`).
- **lmstudio**: start LM Studio’s local server, load a model, set `LLM_PROVIDER=lmstudio`. Optional: `LMSTUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`), `LMSTUDIO_MODEL` (default `google/gemma-4-12b`), `LMSTUDIO_API_KEY` (default `lm-studio`).

## Commands

Optional `--book <id>` on every book-scoped command (default `alice-wonderland`; must appear in the catalog). Artifacts live under `state/<id>/` and `output/<id>/`; source under `data/books/<id>/<id>.txt`. Elsewhere below, bare `state/…` / `output/…` paths mean under that book id.

List registered books (no LLM; refreshes `data/books/catalog.json` from per-book `meta.json`):

```powershell
python main.py books
python main.py books --validate
```

List chapters (no LLM call; writes `state/<id>/chapters.json`):

```powershell
python main.py chapters
python main.py chapters --book alice-wonderland
```

Summarize one chapter (Reader → Editor → Critic → revise; needs API key):

```powershell
python main.py summarize --chapter 1
```

Writes `state/<id>/chapter-01-analysis.json`, `state/<id>/chapter-01-draft.md`, `state/<id>/chapter-01-critique.json`, then `output/<id>/chapter-01-summary.md`.

Summarize every chapter, then merge into `output/<id>/book-report.md`:

```powershell
python main.py summarize --all
```

Skips when the chapter summary file already exists. Soft-resumes from the first missing `state/<id>/` artifact when the summary is absent.

Force regenerates from Reader through summary:

```powershell
python main.py summarize --chapter 1 --force
python main.py summarize --all --force
```

Restart at a stage (reuse earlier artifacts; works even if summary exists):

```powershell
python main.py summarize --chapter 1 --from draft
python main.py summarize --chapter 1 --from critic
python main.py summarize --chapter 1 --from revise
```

`--force` and `--from` are mutually exclusive. `--from critic` needs analysis + draft; `--from revise` needs analysis + draft + critique.

Merge existing chapter summaries only (no LLM):

```powershell
python main.py report
```

Prefers enriched chapter MD over summaries; weaves `output/book-synthesis.md` after the header when present; inserts scene images from `output/illustrations/` under matching chapters when `state/book-visual-resolved.json` exists (relative `![…](illustrations/…)` paths; chapter source files unchanged).

Bind the reading edition (Gutenberg body + scene images + footnote endnotes; no LLM):

```powershell
python main.py enriched
```

Writes `output/book-enriched.md`. Uses `Chapter.text` as the spine; inserts scene images like `report`; appends per-chapter `### Notes` from `state/chapter-NN-footnotes.json` when present (no mid-body footnote markers). Always regenerates.

Merge chapter analyses into a book-level character/theme index (no LLM):

```powershell
python main.py rollup
```

Writes `state/book-rollup.json`. Requires every chapter’s `state/chapter-NN-analysis.json` (same completeness rule as `report` for summaries). `summarize --all` also writes the rollup after the report.

LLM alias merge of the rollup into `state/book-rollup-merged.json` (needs provider; not part of `summarize --all`):

```powershell
python main.py aliases
python main.py aliases --force
```

Requires `state/book-rollup.json`. Skips when the merged file already exists unless `--force`.

LLM book-level synthesis (needs all chapter analyses + summaries + rollup; not part of `summarize --all`):

```powershell
python main.py reduce
python main.py reduce --force
```

Writes `output/book-synthesis.md` from compact Reader analyses plus `book-rollup-merged.json` if present else `book-rollup.json`, then rebuilds `output/book-report.md` (synthesis woven after the header). Skips when the synthesis file already exists unless `--force`.

LLM book-level visual identity (needs all chapter analyses + rollup; not part of `summarize --all`):

```powershell
python main.py visual-identity
python main.py visual-identity --force
```

Writes `state/book-visual-identity.json` (style / palette / atmosphere / period / motifs with `kind` + `confidence`). Uses `book-rollup-merged.json` if present else `book-rollup.json`. Does not rebuild the report. Skips when the identity file already exists unless `--force`.

LLM character visual sheets (needs all chapter analyses + rollup + `visual-identity`; not part of `summarize --all`):

```powershell
python main.py visual-characters
python main.py visual-characters --force
```

Writes `state/book-visual-characters.json` (per-character `physical` / `personality` / `visual_language` trait arrays with `kind` + `confidence`). Uses `book-rollup-merged.json` if present else `book-rollup.json`, plus `state/book-visual-identity.json`. Does not rebuild the report. Skips when the characters file already exists unless `--force`.

LLM place / setting sheets (needs all chapter analyses + `visual-identity`; not part of `summarize --all`):

```powershell
python main.py visual-places
python main.py visual-places --force
```

Writes `state/book-visual-places.json` (per-place `architecture` / `climate` / `atmosphere` / `symbols` trait arrays with `kind` + `confidence`). Uses `state/book-visual-identity.json` plus compact chapter plot/events (LLM selects up to ~8 key places; no rollup required). Does not rebuild the report. Skips when the places file already exists unless `--force`.

LLM scene briefs (needs all chapter analyses + `visual-identity` + `visual-characters` + `visual-places`; not part of `summarize --all`):

```powershell
python main.py visual-scenes
python main.py visual-scenes --force
```

Writes `state/book-visual-scenes.json` (per-scene `title` / `chapter` / `characters` / `location` plus `emotional_focus` / `composition` trait arrays with `kind` + `confidence`). Uses identity + character sheets + place sheets plus compact chapter plot/events/cast (LLM selects up to ~8 illustration-worthy moments). Does not rebuild the report. Skips when the scenes file already exists unless `--force`.

Visual Bible handoff — open questions + consistency (needs identity + characters + places + scenes; not part of `summarize --all`):

```powershell
python main.py visual-handoff
python main.py visual-handoff --force
```

Writes `state/book-visual-handoff.json` (`open_questions` + `consistency_issues`). Uses the four bible JSON files only (no chapter analyses). Deterministic name/gap checks merge with one LLM pass for soft issues and open questions (each question includes up to 3 `options` and optional `suggested` index). Does not rewrite steps 1–4 or rebuild the report. Skips when the handoff file already exists unless `--force`.

Open the Visual Handoff HTML viewer (needs `state/<book-id>/book-visual-handoff.json`; no LLM):

```powershell
python main.py view-handoff
python main.py view-handoff --book alice-wonderland
```

Serves the repo root on `http://127.0.0.1:8765` and opens `web/handoff.html?book=<id>` (fetches `state/<id>/book-visual-handoff.json`). Also serves pipeline APIs (`/api/books`, `/api/status`, `/api/run`) so `web/pipeline.html` works on this port too. If port 8765 already serves this handoff **and** `/api/books`, re-running only reopens the browser (useful for the Cursor/VS Code task). If an old server is up without `/api/books`, stop it (Ctrl+C) and re-run. Pick a radio option per open question (suggested pre-selected when present), add optional notes, then **Download answers** → `book-visual-handoff-answers.json`. Save/move that file to `state/<id>/book-visual-handoff-answers.json` for `visual-resolve`. Stops with Ctrl+C when this process owns the server. Same command is available as the Cursor/VS Code task **Open visual handoff** (Command Palette → Tasks: Run Task).

Open the pipeline status board (status + allowlisted Run; no LLM in the server):

```powershell
python main.py view-pipeline
python main.py view-pipeline --book alice-wonderland
```

Serves the repo root on `http://127.0.0.1:8766` with `GET /api/books`, `GET /api/status?book=<id>`, `GET /api/run`, and `POST /api/run` (JSON `{ "book", "stage" }` → allowlisted `python main.py …` subprocess), and opens `web/pipeline.html?book=<id>`. Pick a catalog book to see stage badges (`done` / `partial` / `missing`), copy-paste CLI hints, or **Run** a runnable stage. Progress is polled via `/api/run` plus filesystem status refresh; one job at a time (`409` if busy). Artifacts: `state/<id>/run-status.json` and `pipeline-run.log`. Illustrations and handoff-answers are not runnable from the UI. If port 8766 already serves `/api/books`, re-running only reopens the browser. Stops with Ctrl+C when this process owns the server. Handoff Q&A remains on port 8765 (`view-handoff`); the same `/api/run` routes exist on that shared handler if needed.

Apply handoff answers into a locked resolved bible (needs four bible files + handoff + answers; no LLM):

```powershell
python main.py visual-resolve
python main.py visual-resolve --force
```

Writes `state/book-visual-resolved.json` (deep-copied identity / characters / places / scenes with answered options as `art_decision` traits, plus `resolutions` / `unresolved`). Does not rewrite steps 1–4 or rebuild the report. Skips when the resolved file already exists unless `--force`.

Research footnotes for a chapter (needs analysis + summary; not part of `summarize --all`):

```powershell
python main.py footnotes
python main.py footnotes --chapter 1
python main.py footnotes --all
python main.py footnotes --chapter 1 --force
```

Writes `state/chapter-NN-footnotes.json` and `output/chapter-NN-enriched.md` (Editor summary stays pristine). With no `--chapter`, resumes at the first chapter missing footnotes JSON. Explicit `--chapter` skips when that file already exists unless `--force`. `--all` also rebuilds `output/book-report.md` (prefers enriched chapter files when present).

Export binder Markdown to HTML, PDF, and/or EPUB (no LLM):

```powershell
python main.py export
python main.py export --mode report
python main.py export --mode enriched
python main.py export --format html
python main.py export --force
```

Default `--mode report` requires `output/book-report.md` (run `report` or `summarize --all` first) and writes `output/book-report.html`, `.pdf`, and `.epub`. `--mode enriched` requires `output/book-enriched.md` (run `enriched` first) and writes `output/book-enriched.{html,pdf,epub}`. Scene images referenced as `illustrations/…` stay relative for HTML (open beside `output/illustrations/`), are packed into the EPUB, and are resolved for PDF via xhtml2pdf (best-effort). Skips each file that already exists unless `--force`.

## Smoke checks

After changing the loader / splitter / `BookPaths` / catalog / CLI path wiring:

1. `python main.py books --validate` — expect `alice-wonderland` and `asimov-naked-sun` ok and refreshed `data/books/catalog.json`.
2. `python main.py chapters` and `python main.py chapters --book alice-wonderland` — expect a sensible chapter count and titles; both write `state/alice-wonderland/chapters.json`.
3. `python main.py chapters --book asimov-naked-sun` — expect **18** chapters (`CHAPTER I. A Question Is Asked` … `CHAPTER XVIII. …`); writes `state/asimov-naked-sun/chapters.json`.
4. `python main.py chapters --book no-such-book` — expect unknown-id error listing known books.
5. Confirm `state/alice-wonderland/chapters.json` (and Asimov path when testing EPUB) updated.
6. Optional: `python main.py report` / `enriched` / `rollup` / `export --format html --force` with `--book alice-wonderland` — under `state/alice-wonderland/` + `output/alice-wonderland/`.

After changing Reader / Editor / Critic:

1. `python main.py summarize --chapter 1 --force`
2. Open `state/chapter-01-analysis.json` — expect plot / characters / themes / quotes / events.
3. Open `state/chapter-01-draft.md` — expect draft Markdown (same section shape as the final summary).
4. Open `state/chapter-01-critique.json` — expect verdict / issues / must_fix / optional_improve.
5. Open `output/chapter-01-summary.md` — expect Markdown with the Editor section structure.

After changing LLM provider / local model:

1. For LM Studio: server running, model loaded, `LLM_PROVIDER=lmstudio` in `.env`.
2. `python main.py summarize --chapter 1 --force`
3. Same JSON + Markdown checks as Reader / Editor / Critic above.

After changing skip/force/`--from` behavior:

1. With an existing `output/chapter-01-summary.md`, run `python main.py summarize --chapter 1` — expect a skip message and no API call.
2. `python main.py summarize --chapter 1 --force` — expect Reader + draft + Critic + revise writes (including `state/chapter-01-draft.md`).
3. With analysis + draft present, `python main.py summarize --chapter 1 --from critic` — expect Critic + revise only (reuse analysis/draft).
4. With analysis + draft + critique present, `python main.py summarize --chapter 1 --from revise` — expect revise only.

After changing map/merge:

1. `python main.py summarize --all` — expect per-chapter files under `output/`, `output/book-report.md`, and `state/book-rollup.json`.
2. Re-run `python main.py summarize --all` — expect skips + refreshed report + rollup.
3. `python main.py report` — expect `book-report.md` rewritten from existing chapter files.
4. With resolved bible + JPGs present, `python main.py report` — expect `![…](illustrations/scene-…)` under each scene’s chapter (e.g. ch.1 Fall Through the Well); chapter enriched/summary files unchanged.
5. `python main.py rollup` — expect `state/book-rollup.json` with `chapters_included`, merged `characters` (`name` / `notes` / `chapters`), and `themes` (`theme` / `chapters`).

After changing alias merge:

1. With `state/book-rollup.json` present, `python main.py aliases --force` — expect `state/book-rollup-merged.json` with `source`, `characters` (`name` / `aliases` / `notes` / `chapters`), and `themes` (`theme` / `aliases` / `chapters`).
2. Re-run `python main.py aliases` — expect a skip message and no LLM call.
3. Prefer fewer character/theme rows than the baseline when the model merges aliases (e.g. Queen / Queen of Hearts).

After changing footnotes:

1. With chapter-1 analysis + summary present, `python main.py footnotes --chapter 1 --force` — expect `state/chapter-01-footnotes.json` and `output/chapter-01-enriched.md` with `[^ch01-…]` markers.
2. Re-run `python main.py footnotes --chapter 1` — expect a skip message and no LLM call.
3. With ch.1 footnotes present and later chapters summarized, `python main.py footnotes` — expect resume at the first chapter without footnotes JSON (not a ch.1 skip).
4. `python main.py report` then `python main.py export --format html --force` — expect footnotes in HTML when the report includes enriched chapters.

After changing reduce / book synthesis:

1. With all chapter analyses + summaries + `state/book-rollup.json` present, `python main.py reduce --force` — expect `output/book-synthesis.md` (overview / plot arc / characters / themes / closing note) and `book-report.md` with synthesis after the header.
2. Re-run `python main.py reduce` — expect a skip message and no LLM call.
3. `python main.py export --format html --force` — expect the book overview in HTML.

After changing visual identity:

1. With all chapter analyses + `state/book-rollup.json` present, `python main.py visual-identity --force` — expect `state/book-visual-identity.json` with `artistic_style` / `color_palette` / `atmosphere` / `period` / `motifs` trait objects (`value` / `kind` / `confidence` / `note`).
2. Re-run `python main.py visual-identity` — expect a skip message and no LLM call.
3. Confirm `output/book-report.md` is unchanged by this command.

After changing visual characters:

1. With all chapter analyses + rollup + `state/book-visual-identity.json` present, `python main.py visual-characters --force` — expect `state/book-visual-characters.json` with `characters` sheets (`physical` / `personality` / `visual_language` trait objects).
2. Re-run `python main.py visual-characters` — expect a skip message and no LLM call.
3. Confirm character names match the rollup cast and `output/book-report.md` is unchanged by this command.

After changing visual places:

1. With all chapter analyses + `state/book-visual-identity.json` present, `python main.py visual-places --force` — expect `state/book-visual-places.json` with `places` sheets (`architecture` / `climate` / `atmosphere` / `symbols` trait objects).
2. Re-run `python main.py visual-places` — expect a skip message and no LLM call.
3. Confirm `output/book-report.md` is unchanged by this command.

After changing visual scenes:

1. With all chapter analyses + `state/book-visual-identity.json` + `state/book-visual-characters.json` + `state/book-visual-places.json` present, `python main.py visual-scenes --force` — expect `state/book-visual-scenes.json` with `scenes` briefs (`title` / `chapter` / `characters` / `location` / `emotional_focus` / `composition`).
2. Re-run `python main.py visual-scenes` — expect a skip message and no LLM call.
3. Confirm `output/book-report.md` is unchanged by this command.

After changing visual handoff:

1. With `state/book-visual-identity.json` + `book-visual-characters.json` + `book-visual-places.json` + `book-visual-scenes.json` present, `python main.py visual-handoff --force` — expect `state/book-visual-handoff.json` with `open_questions` (`question` / `topic` / `related` / `note` / `options` / optional `suggested`) and `consistency_issues` (`summary` / `severity` / `related` / `suggestion`).
2. Re-run `python main.py visual-handoff` — expect a skip message and no LLM call.
3. Confirm steps 1–4 bible JSON files and `output/book-report.md` are unchanged by this command.
4. With handoff JSON present, `python main.py view-handoff` — expect a local server on port 8765, browser URL includes `?book=alice-wonderland`, and the page lists open questions (with selectable options / suggested pre-selected when present) and consistency issues (Ctrl+C to stop).
5. Pick options, add a note, **Download answers** — expect `book-visual-handoff-answers.json` with one `answers[]` row per open question (`index` / `question` / `chosen` / `chosen_text` / `note`); place it at `state/<id>/book-visual-handoff-answers.json`.

After changing pipeline status board (`view-pipeline` / `pipeline_status.py` / `pipeline_run.py` / `web/pipeline.html`):

1. `python main.py view-pipeline` — expect a local server on port **8766**, browser opens `web/pipeline.html?book=…`, `/api/books` lists catalog ids.
2. Select `alice-wonderland` — expect mostly `done` stages (summaries, report, visual bible, exports when present).
3. Select `asimov-naked-sun` — expect `chapters` done and later stages `missing` (until that book is run).
4. **Copy CLI** on a stage — expect a `python main.py … --book <id>` string on the clipboard.
5. On a fast no-LLM stage (e.g. **Report** or **Chapters** for Alice): **Run** — expect the run panel to show log output; `GET /api/run` moves from `running` to `finished` with `exit_code: 0`; status badges refresh.
6. While a run is active, a second **Run** is disabled / `POST /api/run` returns `409`.
7. **Illustrations** and **Handoff answers** rows — expect no **Run** button (Copy CLI / handoff link only).

After changing visual resolve:

1. With four bible JSON files + `state/book-visual-handoff.json` + `state/book-visual-handoff-answers.json` present, `python main.py visual-resolve --force` — expect `state/book-visual-resolved.json` with deep-copied sheets, `resolutions` (`applied` / `targets`), and `unresolved`.
2. Re-run `python main.py visual-resolve` — expect a skip message and no rewrite.
3. Confirm steps 1–4 bible JSON files and `output/book-report.md` are unchanged by this command.

After changing export:

1. With `output/book-report.md` present, `python main.py export --force` — expect `output/book-report.html`, `.pdf`, and `.epub`.
2. Re-run `python main.py export` — expect skip messages and no rewrite.
3. `python main.py export --format html --force` — expect only the HTML file refreshed.
4. With woven scene images in the report + JPGs under `output/illustrations/`, open HTML and EPUB after `--force` — expect scene images under matching chapters (EPUB file should be multi-MB when images pack; PDF best-effort).

After changing the enriched binder:

1. `python main.py enriched` — expect `output/book-enriched.md` with Gutenberg chapter prose (not Plot Summary), scene `![…](illustrations/…)` under matching chapters, and `### Notes` where footnote JSON exists.
2. `python main.py export --mode enriched --force` — expect `output/book-enriched.html`, `.pdf`, and `.epub`.
3. Open HTML/EPUB — expect readable Alice text, in-chapter images, and chapter endnotes; default `export` (report mode) still writes `book-report.*` only.

## Notes

- Sample book: *Alice’s Adventures in Wonderland* under `data/books/`.
- Book text is excluded from Cursor indexing via `.cursorignore`; agents should use `book.py` / CLI rather than reading the full raw file when possible.
- Fresh `--all` makes up to four LLM calls per missing chapter (Reader + Editor draft + Critic + revise); expect several minutes (longer on local models). Use `--from` to avoid replaying earlier stages while iterating on Critic/revise.
- Local Gemma (e.g. `google/gemma-4-12b` in LM Studio) can take several minutes per LLM call on a MacBook (slow prompt prefill on long chapters) and will warm the machine; prefer Gemini for fast iteration. Raise LM Studio context above 8k when Criticing long EPUB chapters. Thinking helps Critic most; keep it off for full-book thrash.
- Critic packs chapter + notes + draft; on ~8k local context it may head+tail-truncate long chapters (see `docs/decisions.md`). Raise LM Studio context if you want full-text critique. After an `exceed_context_size_error`, resume with `summarize --book <id> --chapter N --from critic`.
