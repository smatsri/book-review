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

Skips the LLM call if that output file already exists. Force a regenerate:

```powershell
python main.py summarize --chapter 1 --force
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

## Notes

- Sample book: *Alice’s Adventures in Wonderland* under `data/books/`.
- Book text is excluded from Cursor indexing via `.cursorignore`; agents should use `book.py` / CLI rather than reading the full raw file when possible.
