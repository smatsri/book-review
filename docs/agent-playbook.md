# Agent-first project playbook

Reusable checklist distilled from this repo. Copy into a new project on day one; trim what does not apply.

## Day-one skeleton

Create these before the first feature agent session:

| File | Job |
|------|-----|
| `todo.md` | Session + Now / Next / Later / Done |
| `AGENTS.md` | How agents work here (source-of-truth table + session workflow) |
| `docs/architecture.md` | What exists **today** |
| `docs/runbook.md` | How to run / verify |
| `docs/decisions.md` | Append-only lasting choices |
| `idea.md` | Vision only — not current truth |
| `.cursor/rules/` (optional) | Always-on hygiene: update todo + the one matching doc |

Rule: if `idea.md` conflicts with `docs/` or code, **code + docs win**.

## `todo.md` Session (keep short)

Aim for ~5–8 bullets total in Session:

- **Stopped at** — one sentence
- **Last success** — what just landed
- **Do not redo** — only *recent* settled work; push old items into Done / decisions
- **Parked** — deferred with a pointer (Later or `decisions.md`)

Agents read **Session + Now** first. One Now item (or one clear slice) per session.

## Session workflow (every agent turn that ships)

1. Start from Session / Now.
2. Do one Now slice.
3. Before ending: update code, `todo.md`, and **the one** doc that changed (`architecture` / `runbook` / `decisions`).
4. Open `idea/` only when Session or Now explicitly points there.

## Engineering habits that help agents

- **One user-facing entry** (CLI or clear main module) with skip / force / resume where work is expensive.
- **Artifacts on disk** (`state/`, `output/`) so “done” is a file, not chat memory.
- **Deterministic steps next to LLM steps** — merge, export, resolve without calling a model when possible.
- **Human-in-the-loop** where judgment beats the model (review UI, answers JSON, manual art).
- **Do not invent** env vars, commands, or modules missing from code + docs.

## Growth hygiene

- When Session “Do not redo” gets long → move frozen facts into `decisions.md` / Done.
- When architecture diagrams get dense → prefer a stages table (command → inputs → outputs → LLM?).
- Before a second product instance (e.g. multi-book), scope paths in a decision + runbook rewrite **before** the second title.
- Optional later: smoke that docs still match the CLI (`--help` vs runbook).

## Definition of done (typical)

- Matches the Now scope.
- Runbook smoke still applies (or runbook updated).
- `todo.md` reflects the new stopping point.
