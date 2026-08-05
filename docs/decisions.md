# Decisions

Short records of choices that should stay true across sessions. Add a new entry when something lasting changes; do not rewrite history — append or supersede explicitly.

## 2026-08 — Start with a single OpenAI summarizer

**Status:** current  
**Context:** Need a working LLM path before multi-agent orchestration.  
**Decision:** Stage-1 agent in `agents/summarizer.py` uses OpenAI chat completions.  
**Consequences:** `.env` uses `OPENAI_API_KEY` / `OPENAI_MODEL`. Switching providers means changing this module, deps, and env docs together.

## 2026-08 — Prefer Gemini next

**Status:** planned (see `todo.md` Now)  
**Context:** Prefer Gemini for ongoing work.  
**Decision:** Replace OpenAI with Gemini as the next implementation slice; keep the same CLI and Markdown output contract.  
**Consequences:** Update `requirements.txt`, `.env.example`, `agents/summarizer.py`, README/runbook, then smoke-test `summarize --chapter 1`.

## 2026-08 — Docs split: session vs truth vs vision

**Status:** current  
**Context:** Agents and humans need continuity without mixing aspirational design into “what works now.”  
**Decision:**

| File | Job |
|------|-----|
| `todo.md` | Short-term memory / backlog |
| `docs/*` | Current truth (architecture, runbook, decisions) |
| `idea.md` | Vision / future architecture |
| `AGENTS.md` | How agents work in this repo |
| `README.md` | Entry point + links |

**Consequences:** Promote ideas into `docs/` only after they exist in code. Update the matching doc when finishing a task.
