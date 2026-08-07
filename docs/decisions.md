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

## 2026-08 — Park billing; local Qwen for current dev

**Status:** current  
**Context:** Dual providers work; free-tier Gemini quota was the original pain; local Qwen via LM Studio is acceptable for the current development loop.  
**Decision:** Do not decide paid Flash / Pro-Sonnet mix / per-agent hybrid now. Keep `LLM_PROVIDER=lmstudio` (local Qwen) as the default working setup for ongoing feature work. Revisit billing/hybrid when quota returns as a blocker or local quality/latency is insufficient.  
**Consequences:** Next product work can proceed without a billing choice; cost notes above remain reference material.  
**Supersedes:** the “open now” urgency of billing in “LLM cost / model choice (deferred)” — still Later, not Now.

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

## 2026-08 — Persist draft + `--from` stage restart

**Status:** current  
**Context:** Critic/revise iteration re-ran Reader + draft; local models make that expensive. Soft reuse only covered Reader JSON.  
**Decision:** Persist Editor draft as `state/chapter-NN-draft.md`. Soft-resume when summary is missing from the first gap in analysis → draft → critique. Add `summarize --from reader|draft|critic|revise` to restart mid-pipeline (requires upstream artifacts; overrides summary skip). `--force` remains full regen and is mutually exclusive with `--from`.  
**Consequences:** Crash recovery and Critic-only/revise-only smokes without separate CLI commands. Older chapters lack draft files until regenerated (`--force` or `--from draft`).  
**Extends:** “Skip existing chapter summaries unless --force” and “Critic loop (one-pass)”.

## 2026-08 — Book-level structured rollup (deterministic)

**Status:** current  
**Context:** Per-chapter Reader JSON has characters/themes but no shared book cast or theme index; `book-report.md` only concatenates Markdown. Downstream agents need structured cross-chapter state.  
**Decision:** Add `rollup.py` + CLI `rollup` writing `state/book-rollup.json` from all `chapter-NN-analysis.json` files (no LLM). Characters merge by normalized name (casefold, strip leading `The `); themes by case-insensitive exact string. Display name = most frequent raw form. `summarize --all` writes rollup after the report. Missing analyses fail like missing summaries for `report`.  
**Consequences:** Cheap book index without API cost; aliases like `Queen` vs `Queen of Hearts` stay separate until LLM alias merge. Distinct from Later “LLM reduce” prose synthesis.  
**Extends:** “Full-book map + deterministic merge report”.

## 2026-08 — LLM character/theme alias merge

**Status:** current  
**Context:** Deterministic rollup leaves true aliases split (`Queen` vs `Queen of Hearts`). Downstream cast/theme use needs a merged index without replacing the cheap baseline.  
**Decision:** Add Alias Merger agent + CLI `aliases` writing `state/book-rollup-merged.json` from `book-rollup.json`. One LLM call proposes clusters (exact input strings only); `apply_alias_clusters` in `rollup.py` validates, fills singletons, unions chapters/notes, and picks display name/theme as longest alias. Skip unless `--force`. Not invoked by `summarize --all`. No fuzzy string library in v1.  
**Consequences:** Enrichment is opt-in and provider-dependent; baseline rollup remains authoritative for exact-normalized merges. Bad LLM clusters fail closed (unknown/overlap dropped).  
**Extends:** “Book-level structured rollup (deterministic)”.

## 2026-08 — Export HTML / PDF / EPUB (pure Python)

**Status:** current  
**Context:** Pipeline stopped at Markdown; `idea.md` Layout Agent asks for HTML/PDF/EPUB without requiring another LLM role yet.  
**Decision:** Add `export_book.py` + CLI `export` converting `output/book-report.md` with pip-only libs (`markdown`, `ebooklib`, `xhtml2pdf`). Default `--format all`; per-format skip unless `--force`. Not part of `summarize --all`. No Pandoc/LaTeX.  
**Consequences:** One `pip install -r requirements.txt` path for all platforms; PDF styling is xhtml2pdf-limited; per-chapter export and enriched-book packaging stay Later.  
**Extends:** “Full-book map + deterministic merge report”.

## 2026-08 — Footnote agent + enriched report weave

**Status:** current  
**Context:** Vision Footnote Agent (`idea.md`) needs historical/cultural notes without folding research into the Reader→Editor→Critic fidelity loop or mutating Editor summaries. Export already supports Markdown Extra footnotes.  
**Decision:** Separate CLI `footnotes` (like `aliases`): Footnote LLM writes `state/chapter-NN-footnotes.json`; `footnotes.py` weaves into `output/chapter-NN-enriched.md` with chapter-namespaced `[^chNN-…]` IDs. Summaries stay pristine. `write_book_report` prefers enriched over summary. No web/RAG; no fabricated URLs. Not part of `summarize --all`. Skip unless `--force`. Bare `footnotes` (no `--chapter`) resumes at the first chapter without footnotes JSON; `--chapter N` keeps the skip/force policy for that chapter.  
**Consequences:** Opt-in LLM cost per chapter; stale enriched files possible after `--force` summarize until footnotes re-run; unplaceable anchors listed instead of inventing placement; one-chapter-at-a-time progress without remembering the next number.  
**Extends:** “Export HTML / PDF / EPUB (pure Python)”.

## 2026-08 — LLM reduce / book-level synthesis

**Status:** current  
**Context:** `book-report.md` only concatenated chapter Markdown; rollup is structured index, not prose. Need whole-book overview without re-reading full text or folding synthesis into Reader→Editor→Critic.  
**Decision:** Separate CLI `reduce` (like `aliases`): Reducer LLM writes `output/book-synthesis.md` from compact Reader analyses (truncated plot + themes) + slim rollup name lists (`book-rollup-merged.json` if present else `book-rollup.json`). Chapter summaries still required so the rebuilt report is complete, but full summary Markdown is not sent to the model (keeps Alice-sized reduce under ~8k local context). Fixed Markdown sections (overview, plot arc, characters, themes, closing note). No full book text; no author/genre external context. `write_book_report` weaves synthesis after the header when present; `reduce` rebuilds the report. Not part of `summarize --all`. Skip unless `--force`.  
**Consequences:** One opt-in LLM call for book prose; stale synthesis possible after chapter regen until `reduce --force`; export picks up overview via rebuilt `book-report.md`.  
**Extends:** “Full-book map + deterministic merge report”; distinct from rollup/aliases (structured) and footnotes (chapter enrichment).

## 2026-08 — Visual Bible step 1 (book-level visual identity)

**Status:** current  
**Context:** Vision Visual Bible (`idea/visual_bible_for_books.md`) needs a consistent style handoff before character sheets / scenes / image generation. Literary analyses and rollup already exist; no new Reader pass.  
**Decision:** Separate CLI `visual-identity` (like `reduce` / `aliases`): Visual Identity LLM writes `state/book-visual-identity.json` from compact Reader analyses + slim rollup (`book-rollup-merged.json` if present else `book-rollup.json`). Trait arrays: `artistic_style`, `color_palette`, `atmosphere`, `period`, `motifs`, each `{value, kind, confidence, note}` with `kind` in `fact` | `interpretation` | `art_decision`. No full book text; no report/export weave yet. Not part of `summarize --all`. Skip unless `--force`. Bad trait rows dropped; missing keys fail.  
**Consequences:** One opt-in LLM call for book visual identity; later bible steps (characters / places / scenes) and product weave stay separate.  
**Extends:** bible-first Visual split in `todo.md`; distinct from reduce (prose) and rollup (literary index).

## 2026-08 — Visual Bible step 2 (character visual sheets)

**Status:** current  
**Context:** After book-level identity, illustrators need stable per-character looks with fact vs interpretation vs art_decision, before places/scenes/image gen.  
**Decision:** Separate CLI `visual-characters` (like `visual-identity`): Visual Characters LLM writes `state/book-visual-characters.json` from compact Reader analyses (per-chapter character name/note only; no plot) + enriched rollup cast (top ~8 by chapter count; `book-rollup-merged.json` if present else `book-rollup.json`) + slim `book-visual-identity.json` trait values. Sized for ~8k local context (LM Studio / Qwen) with capped output tokens. Each character: `physical` / `personality` / `visual_language` trait arrays (`value` / `kind` / `confidence` / `note`). Requires identity file first. Names must match cast index; unknown/malformed rows dropped; missing `characters` key fails. Shared trait normalize in `agents/visual_traits.py`. No full book text; no report/export weave. Not part of `summarize --all`. Skip unless `--force`.  
**Consequences:** One opt-in LLM call for character sheets; places / scenes / handoff / product weave stay later.  
**Extends:** Visual Bible step 1 (book-level visual identity).

## 2026-08 — Visual Bible step 3 (key places / settings)

**Status:** current  
**Context:** After identity + character sheets, illustrators need stable looks for recurring / illustration-worthy places before scene briefs / image gen. No places index exists in Reader/rollup.  
**Decision:** Separate CLI `visual-places` (like `visual-characters`): Visual Places LLM writes `state/book-visual-places.json` from compact Reader analyses (truncated plot + capped events) + slim `book-visual-identity.json` trait values. LLM selects up to ~8 key places (no Reader/rollup schema change). Sized for ~8k local context with capped output tokens. Each place: `architecture` / `climate` / `atmosphere` / `symbols` trait arrays (`value` / `kind` / `confidence` / `note`). Requires identity file first; does not require rollup or character sheets. Duplicate/malformed place rows dropped; missing `places` key fails. Shared trait normalize in `agents/visual_traits.py`. No full book text; no report/export weave. Not part of `summarize --all`. Skip unless `--force`.  
**Consequences:** One opt-in LLM call for place sheets; scene briefs / handoff / product weave stay later.  
**Extends:** Visual Bible step 2 (character visual sheets).

## 2026-08 — Visual Bible step 4 (scene briefs)

**Status:** current  
**Context:** After identity + character + place sheets, illustrators need capped illustration-worthy scene briefs (composition / emotional focus) before consistency handoff / image gen.  
**Decision:** Separate CLI `visual-scenes` (like `visual-places`): Visual Scenes LLM writes `state/book-visual-scenes.json` from compact Reader analyses (truncated plot + capped events + light cast names) + slim `book-visual-identity.json` trait values + character/place sheet **names**. LLM selects up to ~8 scenes (no Reader/rollup schema change). Sized for ~8k local context with capped output tokens. Each scene: `title`, `chapter`, `characters` / `location` string lists, plus `emotional_focus` / `composition` trait arrays (`value` / `kind` / `confidence` / `note`; vision camera/focus flattened into `composition`). Requires identity + character sheets + place sheets first. Soft preference for sheet names (no hard allowlist); duplicate/malformed scene rows dropped; missing `scenes` key fails. Shared trait normalize in `agents/visual_traits.py`. No full book text; no report/export weave. Not part of `summarize --all`. Skip unless `--force`.  
**Consequences:** One opt-in LLM call for scene briefs; product weave / image gen stay later.  
**Extends:** Visual Bible step 3 (key places / settings).  
**Superseded in part by:** Visual Bible step 5 (handoff) for the consistency handoff slice.

## 2026-08 — Visual Bible step 5 (handoff)

**Status:** current  
**Context:** After identity + character + place + scene sheets, illustrators need a single handoff artifact: unresolved art questions plus consistency issues — without rewriting the four bible files or generating images.  
**Decision:** Separate CLI `visual-handoff` (like `visual-scenes`): hybrid pass writes `state/book-visual-handoff.json` from the four bible JSON files only (no chapter analyses). Deterministic checks flag scene cast/location name mismatches vs sheets, empty trait lists, and duplicate scene titles. One LLM call over slim identity / character / place / scene summaries adds `open_questions` (`question` / `topic` / `related` / `note` / `options` [2–3 concrete art choices] / optional `suggested` 0-based index; topic allowlist style|character|place|scene|other) and soft `consistency_issues` (`summary` / `severity` / `related` / `suggestion`; severity allowlist conflict|gap|name_mismatch|ambiguity). Merge + dedupe; cap ~12 each. Sized for ~8k local context with capped output tokens. Requires all four bible files first; does not mutate them. Malformed rows dropped; missing top-level keys fail. No report/export weave. Not part of `summarize --all`. Skip unless `--force`.  
**Consequences:** One opt-in LLM call closes the Visual Bible as a handoff artifact; product weave / image gen stay later.  
**Extends:** Visual Bible step 4 (scene briefs).

## 2026-08 — Visual handoff question options

**Status:** current  
**Context:** Open questions alone are hard for a human to answer; consistency issues already carry a `suggestion`, but questions had no menus.  
**Decision:** Each `open_questions` row may include `options` (normalized string list, cap 3) and optional `suggested` (0-based index into `options`, dropped if out of range). Prompt asks for 2–3 mutually exclusive concrete art choices; empty/malformed options kept as `[]` without dropping the question. Viewer (`web/handoff.html`) lists options and highlights the suggested pick. Still proposals only — does not write back into bible sheets.  
**Consequences:** Handoff stays one LLM call; humans pick from menus instead of inventing art direction from scratch.  
**Extends:** Visual Bible step 5 (handoff).

## 2026-08 — Visual handoff local viewer

**Status:** current  
**Context:** `state/book-visual-handoff.json` is useful to skim in a browser, but `tmp/` is gitignored and `output/` is for generated exports — the static UI should be committed and easy to open.  
**Decision:** Keep `web/handoff.html` (committed static viewer fetching `../state/book-visual-handoff.json`). CLI `view-handoff` serves the repo root on `127.0.0.1:8765`, opens the page, and blocks until Ctrl+C (no LLM; requires handoff JSON first). Cursor/VS Code task **Open visual handoff** wraps the same CLI. Not woven into report/export.  
**Consequences:** Illustrators can review open questions / consistency issues locally without copying JSON into chat; fuller bible browse / report weave stay later.  
**Extends:** Visual Bible step 5 (handoff).

## 2026-08 — Visual handoff answers → resolve (next)

**Status:** planned  
**Context:** Handoff + options/viewer close the agent side of the Visual Bible, but choices stay proposals — steps 1–4 are not mutated, and image gen should not guess open questions.  
**Decision:** Split into two slices: (1) viewer writes `state/book-visual-handoff-answers.json` (chosen `options` index per open question, optional notes); (2) resolve/apply CLI consumes that file and produces a resolved bible for image gen. Prefer a new state artifact and/or deterministic patches over re-running identity→scenes; LLM only if soft merge is needed. Report/export weave stays later. Answers live under `state/` (already gitignored).  
**Consequences:** Image generation waits on resolved bible; handoff remains the questionnaire, not the final art direction.  
**Extends:** Visual handoff question options.
