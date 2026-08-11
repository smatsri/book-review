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

**Status:** superseded by “Local LM Studio model: Gemma 4 12B for current dev”  
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

**Status:** superseded by “Alias merge harden (notes + validators + display-by-chapters)”  
**Context:** Deterministic rollup leaves true aliases split (`Queen` vs `Queen of Hearts`). Downstream cast/theme use needs a merged index without replacing the cheap baseline.  
**Decision:** Add Alias Merger agent + CLI `aliases` writing `state/book-rollup-merged.json` from `book-rollup.json`. One LLM call proposes clusters (exact input strings only); `apply_alias_clusters` in `rollup.py` validates, fills singletons, unions chapters/notes, and picks display name/theme as longest alias. Skip unless `--force`. Not invoked by `summarize --all`. No fuzzy string library in v1.  
**Consequences:** Enrichment is opt-in and provider-dependent; baseline rollup remains authoritative for exact-normalized merges. Bad LLM clusters fail closed (unknown/overlap dropped).  
**Extends:** “Book-level structured rollup (deterministic)”.

## 2026-08 — Alias merge harden (notes + validators + display-by-chapters)

**Status:** current  
**Context:** Naked Sun `aliases` wrongly clustered Elijah Baley / Jessie Baley into Albert Minnim (surname merge; names-only prompt). Display-by-longest then labeled the protagonist Minnim; `visual-characters` cast index followed that.  
**Decision:** (1) Alias Merger prompt includes compact per-character `chapters` count + up to 2 short notes (not names-only); stricter “shared surname ≠ same person” rules. (2) `apply_alias_clusters` runs deterministic `refine_character_alias_clusters` before merge: split clusters that mix distinct strong identities (different givens / family surname collisions); re-attach short/surname-only forms by surname or substring (chapter-count tie-break); titled ambiguous shorts (`Dr. X` matching multiple people) stay singletons; optional `alias_warnings` in merged JSON + CLI print. (3) Display `name` / `theme` = most source-row chapters (ties → longer, then alphabetical)—not longest string.  
**Consequences:** Bad LLM people-merges fail softer (split + warn) instead of poisoning the cast index; re-run `aliases --force` then downstream visual/reduce as needed. Theme clustering unchanged beyond display rule. Single-token mis-attachments without a conflicting strong pair (e.g. `Gladia`→`Klorissa Cantoro`) still need notes/LLM caution.  
**Extends / supersedes:** “LLM character/theme alias merge”.

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

**Status:** superseded by “Visual characters full cast (batched)”  
**Context:** After book-level identity, illustrators need stable per-character looks with fact vs interpretation vs art_decision, before places/scenes/image gen.  
**Decision:** Separate CLI `visual-characters` (like `visual-identity`): Visual Characters LLM writes `state/book-visual-characters.json` from compact Reader analyses (per-chapter character name/note only; no plot) + enriched rollup cast (top ~8 by chapter count; `book-rollup-merged.json` if present else `book-rollup.json`) + slim `book-visual-identity.json` trait values. Sized for ~8k local context (LM Studio / Qwen) with capped output tokens. Each character: `physical` / `personality` / `visual_language` trait arrays (`value` / `kind` / `confidence` / `note`). Requires identity file first. Names must match cast index; unknown/malformed rows dropped; missing `characters` key fails. Shared trait normalize in `agents/visual_traits.py`. No full book text; no report/export weave. Not part of `summarize --all`. Skip unless `--force`.  
**Consequences:** One opt-in LLM call for character sheets; places / scenes / handoff / product weave stay later.  
**Extends:** Visual Bible step 1 (book-level visual identity).

## 2026-08 — Visual characters full cast (batched)

**Status:** superseded by “Visual characters illustration cast (threshold + batch)”  
**Context:** Top-~8-by-chapter-count cast for `visual-characters` was an ~8k context shortcut; with a poisoned alias merge it dropped Elijah Baley (absorbed as Albert Minnim) and omitted the rest of the rollup cast. Users expect every rollup character to get a sheet.  
**Decision:** `visual-characters` uses the **full** rollup cast (`book-rollup-merged.json` if present else `book-rollup.json`) with no top-N truncation. Sheets are generated in LLM batches (~6 names), with chapter notes filtered to that batch’s names/aliases; one retry pass for any missing names; fail if still incomplete. Trait schema unchanged. Alias quality remains a separate prerequisite (see alias merge harden).  
**Consequences:** More LLM calls on large casts; local ~8k still workable per batch; cast completeness is enforced in code rather than hoped for in one giant completion.  
**Extends / supersedes:** Visual Bible step 2 (character visual sheets).

## 2026-08 — Visual characters illustration cast (threshold + batch)

**Status:** current  
**Context:** Full-rollup sheets (28 Naked Sun rows incl. robot codes / one-shots) were slow and still truncated JSON on a 6-name batch (`max_output_tokens`). Literary rollup ≠ illustration cast.  
**Decision:** Select an **illustration cast** from the rollup: keep names with ≥3 chapter hits (fill up to 8 by rank if needed; hard-keep #1-by-chapters; cap 12). Generate sheets in LLM batches of **3** with stricter 2-trait compact JSON, `parse_json_object`, one parse retry, and a missing-name retry (batch size 2). Fail if still incomplete. Alias quality remains a separate prerequisite.  
**Consequences:** Recurring cast (e.g. Baley/Gladia/Daneel) gets sheets; walk-ons and serial numbers are skipped; fewer/safer local LLM calls than full cast.  
**Extends / supersedes:** “Visual characters full cast (batched)”.

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

**Status:** superseded (slice 1 → “Visual handoff answers download (viewer)”; slice 2 → “Visual handoff answers resolve/apply CLI”)  
**Context:** Handoff + options/viewer close the agent side of the Visual Bible, but choices stay proposals — steps 1–4 are not mutated, and image gen should not guess open questions.  
**Decision:** Split into two slices: (1) viewer writes `state/book-visual-handoff-answers.json` (chosen `options` index per open question, optional notes); (2) resolve/apply CLI consumes that file and produces a resolved bible for image gen. Prefer a new state artifact and/or deterministic patches over re-running identity→scenes; LLM only if soft merge is needed. Report/export weave stays later. Answers live under `state/` (already gitignored).  
**Consequences:** Image generation waits on resolved bible; handoff remains the questionnaire, not the final art direction.  
**Extends:** Visual handoff question options.

## 2026-08 — Visual handoff answers download (viewer)

**Status:** current  
**Context:** Slice (1) of handoff answers → resolve: humans need to pick from question `options` without a resolve CLI yet; browsers cannot write into `state/` from static HTML.  
**Decision:** `web/handoff.html` makes open-question options radio picks (pre-select `suggested` when present) plus optional per-question notes. Selection state is keyed by `open_questions` index and survives topic filter re-renders. **Download answers** emits `book-visual-handoff-answers.json`: `{source_handoff, answers[{index, question, chosen, chosen_text, note}]}` — one row per question (`chosen` null if unanswered / no options). User places the file at `state/book-visual-handoff-answers.json`. No new CLI, no LLM, no server POST; consistency issues stay read-only.  
**Consequences:** Answers artifact feeds `visual-resolve`; image gen waits on the resolved bible.  
**Extends / implements slice (1) of:** Visual handoff answers → resolve (next).

## 2026-08 — Visual handoff answers resolve/apply CLI

**Status:** current  
**Context:** Slice (2) of handoff answers → resolve: answers JSON exists, but image gen must not guess open questions or mutate steps 1–4.  
**Decision:** Separate CLI `visual-resolve` (no LLM): join `state/book-visual-handoff-answers.json` to handoff `open_questions` by index + exact `question` text; deep-copy the four bible sheets into `state/book-visual-resolved.json`; append each answered option as `{value, kind: art_decision, confidence: 1.0, note}` using authoritative `handoff.options[chosen]`. Topic routing: `style` → `identity.artistic_style`; `character` → matched `characters[].visual_language` via `related` names; `place` → `places[].atmosphere`; `scene` → `scenes[].title` → `composition`; `other` → `identity.motifs`. Name match exact then casefold. Unanswered → `unresolved` only; failed matches stay in `resolutions` with `applied: false`. Audit trail: `resolutions` + `unresolved`. Hard-fail on length/index/question/`chosen` range mismatches. Does not rewrite steps 1–4, ignore consistency issues, no report/export weave. Skip unless `--force`.  
**Consequences:** Image gen can consume one locked bible; handoff + answers remain the questionnaire trail.  
**Extends / implements slice (2) of:** Visual handoff answers → resolve (next).

## 2026-08 — Scene images manual; art consistency is human for now

**Status:** current  
**Context:** Resolved bible is ready; automated image gen and Vision-LLM consistency review are not built. Eight scene illustrations were produced externally (Bing) from the resolved scene briefs.  
**Decision:** Store accepted scene art under `output/illustrations/` as `scene-NN-chNN-<slug>.jpg`, ordered to match `state/book-visual-resolved.json` `scenes[]`. Treat post-gen consistency review as a **human pass** for now (no Vision CLI / multimodal `llm.py` path). Current Alice set: human-accepted. Vision-LLM or hybrid review stays Later if regen loops or multi-book scale need it. Report weave and export embed are built.  
**Consequences:** No new agent for gen or art QA yet; weave/export can assume files in `output/illustrations/` match the resolved scene list.  
**Extends:** Visual handoff answers resolve/apply CLI (locked bible for image gen).

## 2026-08 — Report weave for scene illustrations

**Status:** current  
**Context:** Accepted JPGs live beside the report; draft-1 needs them visible in `book-report.md` without mutating enriched chapter files or teaching export yet.  
**Decision:** Deterministic `illustrations.py` maps `book-visual-resolved.json` `scenes.scenes[]` (1-based index) → `output/illustrations/scene-NN-chCC-*.jpg`. `write_book_report` inserts `![title](illustrations/…)` plus italic caption after each chapter’s first `#` heading. Missing resolved file or JPG skips that scene. No new CLI — every report rebuild stays illustration-aware. Export packing of image assets stays a separate step.  
**Consequences:** Markdown preview and export share one weave path; chapter summaries/enriched MD stay text-only.  
**Extends:** Scene images manual; art consistency is human for now.

## 2026-08 — Export embed of scene illustrations

**Status:** current  
**Context:** Report already weaves `![…](illustrations/…)` links; HTML/PDF/EPUB export ignored image assets (broken EPUB `img`, unresolved PDF URIs).  
**Decision:** Teach `export_book.py` only: scrape `illustrations/…` from converted HTML; HTML keeps relative paths beside `output/` + `img` max-width CSS; EPUB adds matching `EpubItem` JPGs; PDF uses xhtml2pdf `link_callback` against `output/` (best-effort). Missing files skipped. No new CLI flags.  
**Consequences:** `export --force` is the product pack step after weave; PDF layout polish stays Later if xhtml2pdf limits show.  
**Extends:** Report weave for scene illustrations.

## 2026-08 — After Alice: multi-book, PDF next title, grow pipeline UI

**Status:** current (direction only — not implemented)  
**Context:** Handoff local viewer worked well; next human product need is pipeline control + progress. Second title planned: Asimov *The Naked Sun* from a PDF. Flat single-book `state/` / `output/` cannot host two titles.  
**Decision:**
1. Finish Alice draft-1 (weave scenes → export) before multi-book / UI / Naked Sun work.
2. Introduce **book-id–scoped** data/state/output (migrate Alice) before ingesting a second book.
3. Treat **PDF ingest + book-specific chapter split** as required for Naked Sun (not Gutenberg `CHAPTER` headings).
4. Grow `web/` into a **local pipeline operator UI** (status, run steps, progress) that wraps the CLI — CLI remains source of truth; no parallel business logic in the browser.
5. Spec lives in [`idea/pipeline_ui_and_multi_book.md`](../idea/pipeline_ui_and_multi_book.md); backlog in `todo.md` Later.

**Consequences:** No code change yet; agents must not assume multi-book paths or a control UI exist. When implementing, update architecture/runbook and supersede this entry’s “not implemented” note.  
**Extends:** Visual handoff local viewer (web as human surface); Export HTML/PDF/EPUB (Alice product gate before second book).

## 2026-08 — Multi-book foundation: five implementation slices

**Status:** current (MB1–MB5 done)  
**Context:** Enriched Alice v1 shipped; multi-book is the next product slice. Need reviewable chunks and a safe Alice migration.  
**Decision:** Implement foundation as **MB1–MB5** (path contract → wire CLI → migrate Alice → light catalog → book-scoped handoff viewer). One PR/chat per slice; **MB3 alone**. Flat-path compat until MB3. PDF ingest / Naked Sun / pipeline UI stay after foundation. Slice list: [`idea/pipeline_ui_and_multi_book.md`](../idea/pipeline_ui_and_multi_book.md); live backlog: `todo.md` Now/Next.  
**Consequences:** Foundation complete; next product work is Naked Sun PDF ingest / pipeline UI from `todo.md` Next — not more MB slices.  
**Extends:** “After Alice: multi-book…”; supersedes enriched-priority hold on multi-book (enriched v1 done).

## 2026-08 — MB1 path contract (`BookPaths` + `--book`)

**Status:** superseded by MB3 (contract still in force; flat Alice compat removed)  
**Context:** Need a stable book-id path API before wiring every command or moving Alice files.  
**Decision:**
1. Default book id is `alice-wonderland` (slug; source file remains `data/books/alice-adventures-in-wonderland.txt`).
2. `BookPaths` in `book.py`: if `state/<id>/` or `data/books/<id>/` exists as a directory, use scoped layout; else `alice-wonderland` stays flat (`state/`, `output/`, flat txt); other ids use scoped paths even when empty.
3. CLI: every subcommand accepts `--book` (parent parser); `main()` builds `args.paths` and mkdirs state/output. Command bodies still use flat module constants until MB2.
4. No file moves in MB1.

**Consequences:** Path API landed; MB2 wires I/O through it.  
**Extends:** Multi-book foundation five slices (MB1 implemented).

## 2026-08 — MB2 wire CLI through `BookPaths`

**Status:** superseded by MB3 (CLI still resolves via `BookPaths`)  
**Context:** MB1 added `--book` + `BookPaths` but command bodies still used flat `state/` / `output/` constants.  
**Decision:** Every CLI command (and `enriched_book` / `export_book`) resolves source + artifacts via `BookPaths` from `args.paths`. Alice default still flat (compat until MB3). No file moves.  
**Consequences:** Non-Alice `--book` ids read/write scoped dirs; Alice smoke paths unchanged. Next: **MB3** migrate Alice under `<book-id>` and drop flat fallback.  
**Extends:** MB1 path contract.

## 2026-08 — MB3 migrate Alice (always-scoped paths)

**Status:** current  
**Context:** MB1–MB2 kept Alice on flat `state/` / `output/` / flat Gutenberg txt for compat. Multi-book needs one layout for every id.  
**Decision:**
1. One-time move: source → `data/books/alice-wonderland/alice-wonderland.txt`; artifacts → `state/alice-wonderland/` and `output/alice-wonderland/` (keep root `.gitkeep`s).
2. `BookPaths` always scoped: `state/<id>/`, `output/<id>/`, `data/books/<id>/<id>.txt`. Drop `_use_scoped` and Alice flat fallback.
3. `web/handoff.html` temporarily pointed at Alice scoped handoff until MB5 (`view-handoff --book` + dynamic fetch).
4. Update architecture / runbook smoke; do not build catalog (MB4) or Naked Sun / PDF / pipeline UI here.

**Consequences:** Default `--book alice-wonderland` reads/writes scoped trees only. Flat Alice paths are gone.  
**Extends:** MB2 wire CLI; Multi-book foundation five slices (MB3 implemented).

## 2026-08 — MB4 light catalog (`meta.json` / `catalog.json`)

**Status:** current  
**Context:** After scoped paths, operators need a registry of known book ids before a second title or pipeline UI.  
**Decision:**
1. Per-book `data/books/<id>/meta.json` is source of truth: `id`, `title`, `author`, `source_kind` (`gutenberg_txt` \| `plain_txt` \| `pdf` \| `epub`).
2. `data/books/catalog.json` is a derived snapshot rewritten by CLI `books` from discovered metas.
3. CLI `books` lists/validates (source file present for kind); `--validate` exits non-zero on problems.
4. Book-scoped commands reject unknown `--book` ids with a known-id hint. Do not build MB5 handoff scoping, PDF ingest, or pipeline UI here.

**Consequences:** New books need a `meta.json` before CLI work; Alice ships with one. MB5 book-scoped handoff viewer completed next.  
**Extends:** MB3 migrate Alice; Multi-book foundation five slices (MB4 implemented).

## 2026-08 — MB5 book-scoped handoff viewer

**Status:** current  
**Context:** After MB3 scoped paths + MB4 catalog, `web/handoff.html` still hardcoded Alice’s handoff URL.  
**Decision:**
1. CLI `view-handoff` opens `web/handoff.html?book=<id>` (from `--book` / default) after verifying `state/<id>/book-visual-handoff.json` exists.
2. Viewer reads `?book=`, validates a slug, fetches `../state/<id>/book-visual-handoff.json`; missing/invalid query falls back to `alice-wonderland`.
3. If port 8765 already serves that handoff JSON, re-run opens the browser and exits (so the Cursor/VS Code task does not fail on bind).
4. Manual “Load JSON…” and answers download filename unchanged. No pipeline UI / PDF / Naked Sun here.

**Consequences:** Multi-book foundation (MB1–MB5) complete; operators can hand off any cataloged book with handoff JSON.  
**Extends:** Visual handoff local viewer; MB3/MB4; Multi-book foundation five slices (MB5 implemented).

## 2026-08 — Asimov source as `plain_txt` (not PDF yet)

**Status:** superseded by Asimov `epub` source  
**Context:** Second title arrived as publisher plain text (`tmp/…txt`), not a PDF; catalog only allowed `gutenberg_txt` \| `pdf`.  
**Decision:**
1. Book id `asimov-naked-sun`; source at `data/books/asimov-naked-sun/asimov-naked-sun.txt` + `meta.json`.
2. Add `source_kind` value `plain_txt` (same on-disk check as Gutenberg: `<id>.txt` present). Chapter split for numbered headings is still separate work.
3. Do not pretend this file is Gutenberg or invent PDF ingest here.

**Consequences:** `books --validate` accepts the second title; `chapters` still uses Gutenberg `CHAPTER` rules until a plain-text splitter lands.  
**Extends:** MB4 light catalog.

## 2026-08 — Asimov primary source is EPUB

**Status:** current  
**Context:** Publisher EPUB available; plain-text dump has heavy front/back matter and weak chapter markers vs spine/TOC.  
**Decision:**
1. Canonical source for `asimov-naked-sun` is `data/books/asimov-naked-sun/asimov-naked-sun.epub` with `meta.source_kind` = `epub`.
2. Catalog accepts `epub` and validates `<id>.epub` presence (same pattern as `pdf`). Leave leftover `.txt` optional; do not invent EPUB→chapter ingest in this placement step.
3. Prefer EPUB ingest (ebooklib read + spine/nav) over inventing numbered-heading rules for the dump.

**Consequences:** `books --validate` passes once the EPUB is on disk; `chapters --book asimov-naked-sun` still fails until EPUB ingest lands.  
**Extends / supersedes:** Asimov `plain_txt` placement; MB4 light catalog.

## 2026-08 — EPUB ingest via numbered TOC

**Status:** current  
**Context:** Asimov EPUB on disk; need `Chapter` list without inventing plain-text heading rules. Spine includes front/back and a non-TOC teaser.  
**Decision:**
1. `load_chapters_for_book` dispatches on `meta.source_kind`: Gutenberg/plain_txt keep existing `.txt` + `CHAPTER` split; `epub` uses ebooklib; `pdf` raises not-implemented.
2. EPUB chapters come only from TOC titles matching `N. Title` (Arabic number + period). That skips front/back without a title denylist; do not treat full spine as chapters.
3. HTML→plain text via stdlib HTMLParser; strip leading number/title echo from body; `roman` derived with `_int_to_roman` so `Chapter.heading` stays compatible with the rest of the pipeline.
4. `BookPaths.epub_path` = `data/books/<id>/<id>.epub`; CLI `_chapters` always goes through catalog meta.

**Consequences:** `chapters --book asimov-naked-sun` yields 18 Naked Sun chapters into `state/asimov-naked-sun/chapters.json`. Publisher `.txt` may remain on disk unused; EPUB is canonical. Plain_txt numbered-heading splitter not planned for this title.  
**Extends:** Asimov primary source is EPUB; MB4 light catalog.

## 2026-08 — Agent-first playbook for next repos

**Status:** current  
**Context:** First project proved Session/`todo.md` + docs/idea split makes Agents-window work reliable; want a short reusable checklist without rewriting AGENTS for every clone.  
**Decision:** Keep a copyable checklist in [`docs/agent-playbook.md`](agent-playbook.md). This repo’s live workflow stays in `AGENTS.md` + `todo.md`; the playbook is the template for day-one skeleton on the next project.  
**Consequences:** Link from `AGENTS.md` / README; do not duplicate Session rules into multiple homes — playbook summarizes, AGENTS remains this repo’s contract.

## 2026-08 — Enriched book is product north star

**Status:** current (Alice enriched v1 binder shipped)  
**Context:** Draft-1 shipped companion `book-report` HTML/PDF/EPUB with scene images. That matches an editorial dossier, not `idea.md`’s enriched *edition* of the source text. Willing to reconsider; chose to keep enrichment as the primary product.  
**Decision:**
1. **North star:** packaging the original book body with enrichment layers (images, footnotes, later light chapter openers) — Alice enriched v1 spec in [`idea/enriched_book_export.md`](../idea/enriched_book_export.md).
2. **Companion report stays** as a second export / review artifact (`book-report.*`); do not remove or freeze feature work that only helps the report if it also feeds layers.
3. **Alice enriched v1 (minimal):** Gutenberg chapter text as spine + scene JPGs at chapter/scene breaks (reuse `illustrations.py` map) + footnotes as chapter endnotes from existing JSON; no new LLM; reuse export image packing. Implemented as `enriched` CLI + `export --mode enriched` → `book-enriched.*`.
4. **Priority:** enriched pack for Alice before multi-book / Naked Sun / pipeline UI (those stay Later; Alice report draft-1 smoke remains done).
5. Human iterate on report placement stays optional/small; does not block starting the enriched binder.

**Consequences:** Agents must not treat `book-report.epub` as the only product destination. Architecture / runbook document both binders; v2+ (inline markers, mid-chapter scenes, plates) stays in the idea spec.  
**Supersedes (priority only):** the implication in “After Alice: multi-book…” that multi-book is the immediate next product slice after draft-1 — enriched book pack comes first; multi-book decision content otherwise unchanged.

## 2026-08 — Pipeline UI-1: read-only status board

**Status:** current  
**Context:** Multi-book foundation + handoff viewer done; operators need artifact status across books before run controls. Spec sequences status → run → progress in [`idea/pipeline_ui_and_multi_book.md`](../idea/pipeline_ui_and_multi_book.md).  
**Decision:**
1. Ship **UI-1 only**: `pipeline_status.py` scans `BookPaths` trees → JSON (`done` / `partial` / `missing`; no stale mtimes yet).
2. CLI `view-pipeline` serves repo root on **8766** with `GET /api/books` + `GET /api/status?book=`; opens `web/pipeline.html` (book picker, stage list, copy CLI). Does not subprocess pipeline steps.
3. Keep `view-handoff` on **8765**; status page may deep-link to handoff when handoff JSON exists.
4. CLI remains source of truth — UI does not fork business logic into JS (path knowledge stays in Python).

**Consequences:** Run controls + live progress are Next (UI-2+); do not invent a job DB for UI-1. Architecture / runbook document `view-pipeline`.  
**Extends:** “After Alice: multi-book…” pipeline UI intent; MB5 handoff viewer pattern.

## 2026-08 — Pipeline UI-2: allowlisted Run + poll

**Status:** current  
**Context:** UI-1 status board shipped; operators still copy CLI to run steps. Spec’s next slice is run controls + progress poll ([`idea/pipeline_ui_and_multi_book.md`](../idea/pipeline_ui_and_multi_book.md)).  
**Decision:**
1. Ship **UI-2**: `pipeline_run.py` allowlists stage ids → fixed `python main.py … --book` argv; one global subprocess at a time.
2. Persist `state/<id>/run-status.json` + `pipeline-run.log`; expose `POST /api/run` (`202`) and `GET /api/run` (log tail + state). Second start → `409`.
3. `web/pipeline.html` adds **Run** for `runnable` stages, polls ~1.5s, refreshes `/api/status` while running. No `--force` / `--from` UI; no SSE; no job DB.
4. Not runnable: `illustrations` (manual JPGs), `visual_answers` (`view-handoff` nested server). Keep Copy CLI / handoff link.
5. Primary port remains **8766** (`view-pipeline`); shared handler also serves `/api/run` on 8765.

**Consequences:** UI-3 (handoff integrated in the console) shipped next. Architecture / runbook document Run APIs and smoke.  
**Extends:** Pipeline UI-1 status board.

## 2026-08 — Pipeline UI-3: handoff in operator console

**Status:** current  
**Context:** UI-2 Run shipped; console still deep-linked handoff Q&A to port 8765 (`view-handoff`), so operators needed a second server mental model. Spec slice: book-scoped path to existing handoff UI ([`idea/pipeline_ui_and_multi_book.md`](../idea/pipeline_ui_and_multi_book.md)).  
**Decision:**
1. Ship **UI-3**: when `book-visual-handoff.json` exists, status stages emit `links.handoff` = `/web/handoff.html?book=<id>`; `web/pipeline.html` **Open handoff** uses that path same-origin (works on `view-pipeline` **8766** without hardcoding 8765).
2. Answers: **Save to state** via `POST /api/handoff-answers` (`{ book, answers }`) writes `state/<id>/book-visual-handoff-answers.json` after validate-against-handoff; **Download answers** kept as backup. `visual_answers` stays non-runnable.
3. `view-handoff` on **8765** remains the dedicated CLI / Cursor task entry; both CLIs share the same static+API handler.

**Consequences:** Operator console alone is enough for handoff Q&A when handoff JSON exists. Pipeline layout polish stays Later.  
**Extends:** Pipeline UI-2 allowlisted Run + poll; MB5 book-scoped handoff viewer.
**Supersedes in part:** “Visual handoff answers download (viewer)” — no server POST — for the primary operator path (download remains available).

## 2026-08 — Critic JSON resilience for local models

**Status:** superseded by “Critic prompt fit for ~8k local context”  
**Context:** Naked Sun ch15 Critic failed with `JSONDecodeError: Unterminated string` from local Qwen; chapters 1–14 already had valid critiques. Same flaky truncation/escape pattern as other LM Studio JSON stages.  
**Decision:**
1. Shared `agents/json_util.parse_json_object` strips optional \`\`\`json fences and requires a top-level object.
2. Critic uses it, sets `max_output_tokens=4096` (like visual-* agents), prompts for short single-line string fields, and retries the LLM **once** on parse failure; second failure includes a short raw snippet.
3. Critic still receives full chapter text (quality gate unchanged). Other agents may adopt `json_util` later; out of this change.

**Consequences:** Resume mid-pipeline with `summarize --from critic` after a Critic JSON blip without `--force`. Does not fix weak literary critique quality on 9B models.  
**Extends:** Dual LLM providers (LM Studio `json_schema`); Critic one-pass.

## 2026-08 — Critic prompt fit for ~8k local context

**Status:** current  
**Context:** Naked Sun ch18 Critic failed under LM Studio with `exceed_context_size_error` (prompt ~8479 tokens vs `n_ctx` 8192). Critic is the heaviest summarize stage (full chapter + Reader notes + draft). Reader alone fit; ch16–17 Critic fit; ch18 chapter body is the longest in the book.  
**Decision:** Size Critic for ~8k local context like visual-* agents: compact notes JSON (no indent), reserve headroom for chat template + output, and when chapter + fixed prompt parts exceed the budget, truncate chapter text with a clear marker keeping **head + tail** (openings and endings stay available). Prefer raising LM Studio context for full-text critique when possible; code path must not hard-fail long EPUB chapters on 8k defaults. JSON resilience (`parse_json_object`, `max_output_tokens=4096`, one retry) unchanged.  
**Consequences:** Long chapters may lose mid-body evidence in the Critic prompt; draft + Reader notes still present. Resume with `summarize --book … --chapter N --from critic`.  
**Extends / supersedes:** Critic JSON resilience point 3 (“full chapter text” always).

## 2026-08 — Local LM Studio model: Gemma 4 12B for current dev

**Status:** current  
**Context:** Dev loop stays on `LLM_PROVIDER=lmstudio`. Local **Qwen-3.5-9B** worked for Alice fidelity but on *The Naked Sun* hit ~8k Critic context overflows and occasional invalid JSON. Trial of **Gemma 4 12B** (`google/gemma-4-12b`) produced valid footnotes JSON on long chapters; billing / paid cloud mix remains Later.  
**Decision:** Default local model for ongoing feature work is **`google/gemma-4-12b`** via LM Studio (`LMSTUDIO_MODEL` / `agents/llm.py` fallback / `.env.example`). Keep `LLM_PROVIDER=lmstudio` as the working provider; do not decide paid Flash / Pro-Sonnet mix or per-agent hybrid now. Prefer raising LM Studio `n_ctx` for full-text Critic when hardware allows; code still sizes prompts for ~8k.  
**Consequences:** Docs and example env point at Gemma. Prefill can be slow on MacBook (especially long chapter footnotes/Critic); tune GPU offload / cache in LM Studio. Historical Qwen vs Flash notes in this file and `idea/model_comparison_and_context_enrichment.md` remain reference, not the current default.  
**Supersedes:** “Park billing; local Qwen for current dev” for the **which local model** question only (billing still parked / Later).

## 2026-08 — Retrospective: visual quality vs rewrite; JSON reliability

**Status:** current  
**Context:** After Naked Sun report + manual images: feeding `book-visual-resolved.json` into Gemini to invent image prompts produced weak art; ChatGPT prompts written from book knowledge looked better. That raised doubt about the whole Visual Bible / Python pipeline and interest in a full rewrite (new orchestration library and/or non-Python). Separately: recurring LLM JSON parse failures (especially local / truncated output).

**Decision:**
1. **Do not rewrite the repo or switch language** for image quality. Literary pipeline + enriched export still have value; the gap is a missing **bible → image-prompt compiler**, not “multi-agent analysis is wrong.”
2. Treat `book-visual-resolved.json` as locked art direction, **not** a paste-ready image prompt. Next product slice stays the prompt pack in [`idea/visual_image_prompts.md`](../idea/visual_image_prompts.md) (`visual-resolve` → prompts → external gen). Optional: thin parallel experiments for prompt craft without deleting this codebase.
3. **JSON:** failures are mostly **model + truncation / weak schema**, not missing a magic parser. Packages help at layers — validate shape (`pydantic` / `jsonschema`), best-effort repair (`json-repair`), real structured-output schemas at the API — but none guarantee valid JSON. Prefer stronger models + real schemas + short outputs; keep `json_util` / retry as damage control (Critic already).

**Consequences:** Prioritize prompt-pack work over greenfield rewrite. Do not judge the whole project by raw-resolved→image quality. JSON hardening stays incremental; do not expect a library alone to fix local-model flakiness.
**Extends:** Scene images manual; Visual resolve; Critic JSON resilience; Visual image prompts idea.

## 2026-08 — Lab book: park Naked Sun; move to Kafka *In the Penal Colony*

**Status:** current  
**Context:** Naked Sun exposed real Visual Bible gaps (theme/psychology painted as planetary surface; report-faithful prompts ≠ book landscape) and is expensive to iterate on a local ~8k model (18 chapters, fat cast, Critic context). Prompt-only fixes are not enough for multi-book confidence; need a short, concrete lab title. Metamorphosis rejected as too familiar / meme-overfit.

**Decision:**
1. **Stop active work** on *The Naked Sun* (no further visual bible re-runs, prompt experiments, or feature driving from that title). Keep it in catalog for **occasional** smoke/stress (EPUB, long chapter, illustration-cast) only.
2. **Next lab book:** Kafka *In the Penal Colony* — planned id `kafka-penal-colony` (public-domain short story; small cast; apparatus + valley as surface-vs-mood stress). Catalog + source not added in this docs-only change.
3. **Regression:** Alice remains the fast visual/pipeline regression. Prompt-pack slice stays valuable but is **Next** until the Penal Colony loop (or Alice) is the active bible under test.
4. Do not treat fixing one Solaria landscape sheet as multi-book confidence; evidence/schema/eval still needed later.

**Consequences:** Operators and agents read `todo.md` Now for Penal Colony onboarding; Naked Sun historical decisions/smoke in runbook remain valid.  
**Extends:** Retrospective (visual quality vs rewrite); multi-book catalog; Visual Bible places/identity.
