# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Docs-only backlog: after Alice draft-1 export → multi-book + PDF (*Naked Sun*) + pipeline control UI (vision in `idea/pipeline_ui_and_multi_book.md`). Now/Next still Alice footnotes → weave → export.
- **Last success:** Added `docs/agent-playbook.md` (copyable agent-first checklist); linked from `AGENTS.md` / README + decisions entry. Prior: 8 Bing scene JPGs accepted; multi-book before second title.
- **Do not redo:** Project skeleton, Alice loader/splitter, knowledge base, OpenAI→Gemini, skip/force, map/merge CLI, Reader/Editor split, dual providers, Gemini vs Qwen chapter-1 comparison, Critic one-pass loop (no multi-round), draft persist + `--from`, book rollup normalize rules, alias merge CLI/agent, export CLI, footnote enriched weave, LLM reduce synthesis, footnotes resume, visual-identity book identity, visual-characters sheets, visual-places sheets, visual-scenes briefs, visual-handoff, handoff HTML viewer + `view-handoff`, handoff question options, handoff answers download, visual-resolve, manual Bing scene images + human art consistency pass (see `docs/decisions.md`).
- **Parked:** Paid Flash / Pro-Sonnet mix / per-agent hybrid — see Later + `docs/decisions.md`. Gutenberg/external book context (not needed this stage). Vision-LLM art consistency review (human pass for now). Perfect layout / full-novel packaging (draft-1 is illustrated companion report). Pipeline UI / multi-book / PDF ingest — Later only until Alice export lands.

## Now

- [ ] Finish footnotes for remaining chapters (6–12) — existing CLI only: `python main.py footnotes` (resumes at first gap); then `report` if needed so enriched files land in `book-report.md`
- [ ] Draft-1 step 1 — Weave scene illustrations into `book-report.md`
  - Deterministic: `book-visual-resolved.json` `scenes[]` → `output/illustrations/scene-NN-chNN-*.jpg`
  - Insert per matching chapter (caption = scene title); no LLM
  - Prefer rebuilding via `report` (or a thin weave helper) so regen stays skip/force-friendly

## Next

- [ ] Draft-1 step 2 — Teach `export` to embed those images (EPUB + HTML first; PDF best-effort / xhtml2pdf limits OK)
- [ ] Draft-1 step 3 — Smoke `export --force`; open EPUB (and HTML) as the product check
- [ ] Draft-1 step 4 — Human iterate from the draft (placement, captions, missing bits) — small follow-ups only

## Later

- [ ] After Alice draft-1 export — **multi-book foundation** (book-id–scoped `data/` / `state/` / `output/`; migrate Alice off flat paths)
  - Spec: `idea/pipeline_ui_and_multi_book.md` · decision: `docs/decisions.md`
- [ ] Next title: **Asimov — *The Naked Sun*** — PDF ingest + chapter split (not Gutenberg `CHAPTER` rules)
- [ ] **Pipeline control UI** (grow `web/` past handoff): pick book, run CLI steps, show artifact status + progress
  - Prefer after multi-book scoping; CLI stays source of truth
- [ ] PDF image/layout polish (or alternate PDF path) if EPUB/HTML isn’t enough
- [ ] Vision-LLM (or hybrid) art consistency review vs resolved bible — optional; human pass is enough for current Alice set
- [ ] Decide billing / model quality strategy (paid Flash? Pro/Sonnet mix? per-agent hybrid?)
  - Parked for now: local Qwen (`LLM_PROVIDER=lmstudio`) for feature work
  - Counter: full-book latency + upcoming agents make mix a design choice, not just a bill
  - Context: `docs/decisions.md` + `idea/model_comparison_and_context_enrichment.md`
- [ ] RAG / embeddings over chapters
- [ ] Full illustrated book packaging (Gutenberg text + images) — beyond companion report

## Done

- [x] Project skeleton (venv, deps, `.env.example`, gitignore, folders)
- [x] Place Alice text under `data/books/` and exclude via `.cursorignore`
- [x] Book loader + chapter splitter (`book.py`, `main.py chapters`)
- [x] Stage-1 single-agent summarizer (OpenAI, temporary)
- [x] Initial git commit
- [x] Knowledge base: `docs/`, `AGENTS.md`, `.cursor/rules/knowledge-base.mdc`
- [x] Switch LLM provider from OpenAI to Gemini
- [x] Skip existing chapter summaries unless `--force`
- [x] Summarize all chapters (map) and merge into one Markdown report
- [x] Split roles: Reader agent → Editor agent
- [x] Persist per-chapter structured analysis in `state/`
- [x] Dual LLM providers: Gemini + LM Studio (`LLM_PROVIDER`)
- [x] Critic loop (critique → revise → final, one pass)
- [x] Persist Editor draft + `summarize --from` stage restart / soft resume
- [x] Book-level structured rollup in `state/` (cross-chapter characters/themes)
- [x] Fuzzy / LLM character–theme alias merge (`aliases` → `state/book-rollup-merged.json`)
- [x] Export HTML / PDF / EPUB (`export` → `output/book-report.{html,pdf,epub}`)
- [x] Footnote / research agent (`footnotes` → footnotes JSON + enriched MD; report prefers enriched)
- [x] Bare `footnotes` resumes at first chapter missing footnotes JSON
- [x] LLM reduce / book-level synthesis (`reduce` → `book-synthesis.md`; weave into report)
- [x] Split Visual into bible-first steps (identity → characters → places → scenes → handoff; gen later)
- [x] Visual Bible step 1 — book-level visual identity (`visual-identity` → `state/book-visual-identity.json`)
- [x] Visual Bible step 2 — character visual sheets (`visual-characters` → `state/book-visual-characters.json`)
- [x] Visual Bible step 3 — key places / settings (`visual-places` → `state/book-visual-places.json`)
- [x] Visual Bible step 4 — scene briefs (`visual-scenes` → `state/book-visual-scenes.json`)
- [x] Visual Bible step 5 — open questions + consistency pass (`visual-handoff` → `state/book-visual-handoff.json`)
- [x] Visual handoff local viewer (`web/handoff.html` + `view-handoff` / VS Code task)
- [x] Handoff open questions carry `options` (+ optional `suggested`); viewer renders them
- [x] Handoff viewer → answers JSON (`web/handoff.html` download → `state/book-visual-handoff-answers.json`)
- [x] Handoff answers → resolve/apply CLI (`visual-resolve` → `state/book-visual-resolved.json`)
- [x] Scene image generation (manual Bing → `output/illustrations/scene-NN-chNN-*.jpg`, mapped to resolved scene briefs)
- [x] Art consistency review vs resolved bible — human pass for now; current 8 images accepted (Vision LLM parked)
- [x] Agent-first playbook checklist (`docs/agent-playbook.md`) for next repos
