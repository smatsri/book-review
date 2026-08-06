# Decisions

Short records of choices that should stay true across sessions. Add a new entry when something lasting changes; do not rewrite history — append or supersede explicitly.

## 2026-08 — Start with a single OpenAI summarizer

**Status:** superseded by “Switch summarizer to Gemini”  
**Context:** Need a working LLM path before multi-agent orchestration.  
**Decision:** Stage-1 agent in `agents/summarizer.py` uses OpenAI chat completions.  
**Consequences:** `.env` used `OPENAI_API_KEY` / `OPENAI_MODEL`.

## 2026-08 — Prefer Gemini next

**Status:** superseded by “Switch summarizer to Gemini” (implemented)  
**Context:** Prefer Gemini for ongoing work.  
**Decision:** Replace OpenAI with Gemini as the next implementation slice; keep the same CLI and Markdown output contract.

## 2026-08 — Switch summarizer to Gemini

**Status:** current  
**Context:** OpenAI was a temporary stage-1 path; Gemini is the preferred provider.  
**Decision:** `agents/summarizer.py` uses the `google-genai` SDK (`generate_content`) with `GEMINI_API_KEY` / optional `GEMINI_MODEL` (default `gemini-3.5-flash`). CLI and Markdown output sections unchanged.  
**Consequences:** No OpenAI dependency; runbook and `.env.example` document Gemini only.

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

## 2026-08 — Skip existing chapter summaries unless --force

**Status:** current  
**Context:** Full-book map and prompt iteration would re-call Gemini on chapters already summarized.  
**Decision:** `summarize` skips when `output/chapter-NN-summary.md` exists; `--force` regenerates. No prompt-hash cache yet.  
**Consequences:** Re-runs are cheap by default; prompt experiments use `--force` on a few chapters.

## 2026-08 — Full-book map + deterministic merge report

**Status:** current  
**Context:** Need all chapter summaries assembled into one artifact without inventing Reader/Editor agents yet.  
**Decision:** `summarize --all` maps every chapter (same skip/`--force` policy), then writes `output/book-report.md` by concatenating existing chapter Markdown. `report` merges without LLM. No LLM “reduce” synthesis yet.  
**Consequences:** Book report is only as good as per-chapter files; missing chapters fail `report` / end of `--all` merge with a clear error.
