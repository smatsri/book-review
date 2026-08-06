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

## 2026-08 — Reader → Editor role split

**Status:** current  
**Context:** Stage-1 single summarizer mixed analysis and prose; Stage 2 needs separate roles before a Critic loop.  
**Decision:** Replace `agents/summarizer.py` with `agents/reader.py` (chapter → JSON in `state/chapter-NN-analysis.json`) and `agents/editor.py` (JSON → `output/chapter-NN-summary.md`). Shared Gemini helper in `agents/llm.py`. CLI stays `summarize` / `--force` / `--all`; skip when summary exists; reuse Reader JSON when summary is missing.  
**Consequences:** Up to two LLM calls per regenerated chapter; Markdown section contract for humans unchanged; structured notes enable Critic later.

## 2026-08 — LLM cost / model choice (deferred)

**Status:** deferred — not decided  
**Context:** Free-tier Gemini hit `generate_content_free_tier_requests` (20/day on `gemini-3.5-flash`). Reader+Editor = 2 calls/chapter; Critic/footnotes will raise call count. Paying is mostly for quota; Alice-sized text cost is small.  
**Summary (ballpark, analysis only, no image gen):**

- Paid Flash list: ~$1.50/1M in, ~$9/1M out (thinking counts as output).
- Clean Alice today (Reader+Editor): ~$0.25–1 per full pass.
- Fuller stack (Critic + rollup + footnotes): ~$1–few $ per clean pass on Flash; Pro ~1.3×; Sonnet ~2×; Opus/Sol-class ~3×.
- Dev thrash (`--force` full-book regen) dominates the bill more than one production run.
- Likely pattern if upgrading quality: Flash for map/Reader, stronger model for Critic/Editor.

**Local models (also open):**

- Feasible for this repo: all LLM calls go through `agents/llm.py`; Alice chapter size is local-friendly.
- Upside: no free-tier 429s, ~$0 API — useful for MacBook / offline Critic iteration.
- Tradeoffs: slower full-book runs; weaker models often break Reader JSON; literary quality usually behind Flash/Pro unless the machine can run a strong quantized model.
- Hybrid option: local for map/smoke, cloud for Critic/final edit (same idea as Flash-for-map / stronger-for-Critic).

**Open choice:** stay free + wait; enable billing on Flash; Flash+Pro/Sonnet mix; local-only (e.g. Ollama/LM Studio); or local+cloud hybrid.  
**Not decided:** do not change `GEMINI_MODEL` / provider / `agents/llm.py` until this is resolved.  
**Tracked in:** `todo.md` Later.
