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

## Notes

- Sample book: *Alice’s Adventures in Wonderland* under `data/books/`.
- Book text is excluded from Cursor indexing via `.cursorignore`; agents should use `book.py` / CLI rather than reading the full raw file when possible.
- Fresh `--all` makes up to four LLM calls per missing chapter (Reader + Editor draft + Critic + revise); expect several minutes (longer on local models). Use `--from` to avoid replaying earlier stages while iterating on Critic/revise.
- Local Qwen (e.g. `qwen/qwen3.5-9b` in LM Studio) can take ~10 minutes per LLM call on a MacBook when reasoning is on, and will warm the machine; prefer Gemini for fast iteration. Thinking helps Critic most; keep it off for full-book thrash.
