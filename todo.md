# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Footnotes complete for all 12 chapters; next is Draft-1 weave → export embed → smoke.
- **Last success:** `footnotes --all` (ch.1–12 enriched MD + report rebuild). Prior: Bing scene JPGs accepted; agent-playbook docs.
- **Do not redo:** Full-book footnotes; visual bible through `visual-resolve` + handoff viewer/answers; Bing JPGs + human art pass. Older work → Done / `docs/decisions.md`.
- **Parked:** See Later (billing/model mix, Vision-LLM review, multi-book / UI / PDF ingest — after Alice draft-1 export).

## Now

- [ ] Draft-1 step 1 — Weave scene illustrations into `book-report.md`
  - Depends: `state/book-visual-resolved.json` + `output/illustrations/scene-NN-chNN-*.jpg`
  - Deterministic: map `scenes[]` → JPGs; insert under matching chapter (caption = scene title); no LLM
  - Prefer `report` (or thin weave helper) so regen stays skip/force-friendly
  - **Done when:** each resolved scene with a JPG appears under its chapter in `output/book-report.md`

## Next

Draft-1 (remaining):

- [ ] Step 2 — Teach `export` to embed those images (EPUB + HTML first; PDF best-effort / xhtml2pdf OK)
- [ ] Step 3 — Smoke `export --force`; open EPUB (and HTML) as the product check
- [ ] Step 4 — Human iterate from the draft (placement, captions, missing bits) — small follow-ups only

## Later

Gate: after Alice draft-1 export (weave → export smoke).

- [ ] **Multi-book foundation** (book-id–scoped `data/` / `state/` / `output/`; migrate Alice off flat paths)
  - Spec: `idea/pipeline_ui_and_multi_book.md` · decision: `docs/decisions.md`
- [ ] Next title: **Asimov — *The Naked Sun*** — PDF ingest + chapter split (not Gutenberg `CHAPTER` rules)
- [ ] **Pipeline control UI** (grow `web/` past handoff): pick book, run CLI steps, show artifact status + progress (after multi-book; CLI stays source of truth)
- [ ] PDF image/layout polish if EPUB/HTML isn’t enough
- [ ] Vision-LLM (or hybrid) art consistency review — optional; human pass enough for current Alice set
- [ ] Billing / model quality strategy — local Qwen for now; see `docs/decisions.md` + `idea/model_comparison_and_context_enrichment.md`
- [ ] RAG / embeddings over chapters
- [ ] Full illustrated book packaging (Gutenberg text + images) — beyond companion report

## Done

Recent:

- [x] Footnotes for all Alice chapters 1–12 (`footnotes --all`)
- [x] Visual bible → handoff → resolve; Bing scene JPGs + human art consistency pass
- [x] Handoff viewer + answers JSON + `visual-resolve`
- [x] Agent-first playbook (`docs/agent-playbook.md`)
- [x] Export HTML / PDF / EPUB; LLM reduce; alias merge; rollup; Reader/Editor/Critic pipeline

Archive (milestones; details in git + `docs/decisions.md`):

- [x] Project skeleton, Alice under `data/books/`, knowledge base (`docs/`, `AGENTS.md`)
- [x] Book loader/splitter; map/merge summarize; skip/force; dual providers (Gemini + LM Studio)
- [x] Critic one-pass; draft persist + `--from`; footnote agent + resume; bible-first visual steps 1–5
