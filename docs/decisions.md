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

**Status:** superseded by “Dual providers: Gemini + LM Studio”  
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

**Working hypothesis (2026-08, chapter-1 smoke — quality lean, not billing):**

- Local **Qwen-3.5-9B** stayed closer to the text (micro-plot, chapter ending) than **Gemini-3.5-Flash**, which compressed into a bird’s-eye summary with more abstract themes.
- Cost: ~**5–10 min/chapter** on MacBook M2 for that local run → fine for single-chapter smoke; painful for full-book thrash (Reader+Editor already 2 calls; Critic adds more).
- Lean for **dev**: local Qwen via LM Studio for Reader / fidelity iteration; keep hybrid open (local facts → cloud Editor/Critic) if latency blocks Critic work.
- Essay / enrichment sketch (aspirational only): [`idea/model_comparison_and_context_enrichment.md`](../idea/model_comparison_and_context_enrichment.md).

**Open (billing / quality mix):** paid Flash; Flash+Pro/Sonnet mix; per-agent hybrid. Provider plumbing is decided below.  
**Tracked in:** `todo.md` Later.

## 2026-08 — Dual providers: Gemini + LM Studio

**Status:** current  
**Context:** Free-tier Gemini 429s blocked iteration; local LM Studio (e.g. `qwen/qwen3.5-9b`) is available; Gemini should remain supported.  
**Decision:** `LLM_PROVIDER` selects `gemini` (default) or `lmstudio`. Both paths share `agents/llm.py` → `generate_text`. LM Studio uses the OpenAI-compatible local server (`LMSTUDIO_BASE_URL` / `LMSTUDIO_MODEL`). No CLI `--provider` flag; no per-agent hybrid yet.  
**Consequences:** Switch providers in `.env`; install both `google-genai` and `openai`. LM Studio JSON mode uses `json_schema` (not `json_object`). Local 9B runs are slow/hot vs Gemini. Billing / paid Flash vs Pro mix and local+cloud hybrid remain open (Later).  
**Supersedes:** “LLM cost / model choice (deferred)” for the provider-switch question only.

## 2026-08 — Critic loop (one-pass)

**Status:** current  
**Context:** Reader JSON + Editor Markdown were publishable without a quality gate; `idea.md` stage 3 asks for critique → revision.  
**Decision:** `summarize` runs Reader → Editor draft → Critic (`state/chapter-NN-critique.json`) → one Editor revise → `output/chapter-NN-summary.md`. Critic returns structured `verdict` / `issues` / `must_fix` / `optional_improve`. No multi-round loop yet. Skip/force unchanged (skip on existing summary; `--force` regenerates analysis + critique + summary).  
**Consequences:** Up to four LLM calls per regenerated chapter. Thinking/reasoning (LM Studio UI) is optional and most useful on Critic; not a code toggle.  
**Extends:** “Reader → Editor role split”.
