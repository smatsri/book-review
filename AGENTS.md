# AGENTS.md

How to work in this repo (humans and Cursor agents).

## Source of truth

| Need | Read |
|------|------|
| Where we stopped / what’s next | [`todo.md`](todo.md) |
| How the system works **today** | [`docs/architecture.md`](docs/architecture.md) |
| How to run / verify | [`docs/runbook.md`](docs/runbook.md) |
| Why we chose X | [`docs/decisions.md`](docs/decisions.md) |
| Vision / future agents | [`idea.md`](idea.md) — aspirational only; detailed specs under [`idea/`](idea/) when linked from there |

Do not invent APIs, agents, or env vars that are not in code + `docs/`.  
If `idea.md` conflicts with `docs/` or code, **code + docs win**.

## Session workflow

1. Start from `todo.md` **Session** / **Now**.
2. Do **one** Now item (or a clearly scoped slice).
3. Before ending, update:
   - code
   - `todo.md` (Session + move Done/Next)
   - the **one** doc that changed (`architecture`, `runbook`, or `decisions`)

Prefer small patches to the right file over rewriting everything.

## Coding norms

- Python 3.9+, keep the CLI (`main.py`) as the user-facing entry.
- Agents live under `agents/`; shared book I/O stays in `book.py`.
- Generated artifacts go to `output/` and `state/` — do not commit secrets; follow `.gitignore`.
- Book full text is under `data/books/` and is Cursor-ignored; prefer `book.py` / CLI over stuffing whole chapters into prompts when not needed.
- Do not commit `.env` or API keys.

## Definition of done (typical)

- Change matches the Now issue scope.
- Smoke check from `docs/runbook.md` still applies (or runbook updated).
- `todo.md` reflects the new stopping point.
