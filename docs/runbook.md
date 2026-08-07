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
- **lmstudio**: start LM Studio’s local server, load a model, set `LLM_PROVIDER=lmstudio`. Optional: `LMSTUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`), `LMSTUDIO_MODEL` (default `qwen/qwen3.5-9b`), `LMSTUDIO_API_KEY` (default `lm-studio`).

## Commands

List chapters (no LLM call; writes `state/chapters.json`):

```powershell
python main.py chapters
```

Summarize one chapter (Reader → Editor → Critic → revise; needs API key):

```powershell
python main.py summarize --chapter 1
```

Writes `state/chapter-01-analysis.json`, `state/chapter-01-draft.md`, `state/chapter-01-critique.json`, then `output/chapter-01-summary.md`.

Summarize every chapter, then merge into `output/book-report.md`:

```powershell
python main.py summarize --all
```

Skips when the chapter summary file already exists. Soft-resumes from the first missing `state/` artifact when the summary is absent.

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

Research footnotes for a chapter (needs analysis + summary; not part of `summarize --all`):

```powershell
python main.py footnotes
python main.py footnotes --chapter 1
python main.py footnotes --all
python main.py footnotes --chapter 1 --force
```

Writes `state/chapter-NN-footnotes.json` and `output/chapter-NN-enriched.md` (Editor summary stays pristine). With no `--chapter`, resumes at the first chapter missing footnotes JSON. Explicit `--chapter` skips when that file already exists unless `--force`. `--all` also rebuilds `output/book-report.md` (prefers enriched chapter files when present).

Export the merged Markdown report to HTML, PDF, and/or EPUB (no LLM):

```powershell
python main.py export
python main.py export --format html
python main.py export --force
```

Requires `output/book-report.md` (run `report` or `summarize --all` first). Default `--format all` writes `output/book-report.html`, `.pdf`, and `.epub`. Skips each file that already exists unless `--force`.

## Smoke checks

After changing the loader / splitter:

1. `python main.py chapters` — expect a sensible chapter count and titles.
2. Confirm `state/chapters.json` updated.

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
4. `python main.py rollup` — expect `state/book-rollup.json` with `chapters_included`, merged `characters` (`name` / `notes` / `chapters`), and `themes` (`theme` / `chapters`).

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

After changing export:

1. With `output/book-report.md` present, `python main.py export --force` — expect `output/book-report.html`, `.pdf`, and `.epub`.
2. Re-run `python main.py export` — expect skip messages and no rewrite.
3. `python main.py export --format html --force` — expect only the HTML file refreshed.

## Notes

- Sample book: *Alice’s Adventures in Wonderland* under `data/books/`.
- Book text is excluded from Cursor indexing via `.cursorignore`; agents should use `book.py` / CLI rather than reading the full raw file when possible.
- Fresh `--all` makes up to four LLM calls per missing chapter (Reader + Editor draft + Critic + revise); expect several minutes (longer on local models). Use `--from` to avoid replaying earlier stages while iterating on Critic/revise.
- Local Qwen (e.g. `qwen/qwen3.5-9b` in LM Studio) can take ~10 minutes per LLM call on a MacBook when reasoning is on, and will warm the machine; prefer Gemini for fast iteration. Thinking helps Critic most; keep it off for full-book thrash.
