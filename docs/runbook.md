# Runbook

## Setup

Requires Python 3.9+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Put `GEMINI_API_KEY` in `.env`. Optional: `GEMINI_MODEL` (default `gemini-3.5-flash`).

## Commands

List chapters (no LLM call; writes `state/chapters.json`):

```powershell
python main.py chapters
```

Summarize one chapter (needs API key; writes `output/chapter-NN-summary.md`):

```powershell
python main.py summarize --chapter 1
```

Summarize every chapter, then merge into `output/book-report.md`:

```powershell
python main.py summarize --all
```

Skips the LLM call for any chapter whose output file already exists. Force regenerates:

```powershell
python main.py summarize --chapter 1 --force
python main.py summarize --all --force
```

Merge existing chapter summaries only (no LLM):

```powershell
python main.py report
```

## Smoke checks

After changing the loader / splitter:

1. `python main.py chapters` — expect a sensible chapter count and titles.
2. Confirm `state/chapters.json` updated.

After changing the summarizer / provider:

1. `python main.py summarize --chapter 1 --force`
2. Open `output/chapter-01-summary.md` — expect Markdown with the section structure from the agent prompt.

After changing skip/force behavior:

1. With an existing `output/chapter-01-summary.md`, run `python main.py summarize --chapter 1` — expect a skip message and no API call.
2. `python main.py summarize --chapter 1 --force` — expect a write.

After changing map/merge:

1. `python main.py summarize --all` — expect per-chapter files under `output/` and `output/book-report.md`.
2. Re-run `python main.py summarize --all` — expect skips + refreshed report.
3. `python main.py report` — expect `book-report.md` rewritten from existing chapter files.

## Notes

- Sample book: *Alice’s Adventures in Wonderland* under `data/books/`.
- Book text is excluded from Cursor indexing via `.cursorignore`; agents should use `book.py` / CLI rather than reading the full raw file when possible.
- Full-book `--all` makes one Gemini call per missing chapter; expect several minutes for a fresh run.
