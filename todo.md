# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Draft-1 export smoke passed (EPUB images OK); next is human iterate on the draft.
- **Last success:** Opened `output/book-report.epub` — scene images present and fine for now.
- **Do not redo:** Full-book footnotes; visual bible through `visual-resolve` + handoff; Bing JPGs + human art pass; report scene weave; export image packing + smoke. Older work → Done / `docs/decisions.md`.
- **Parked:** See Later (billing/model mix, Vision-LLM review, multi-book / UI / PDF ingest — Alice draft-1 export smoke done; gate open).

## Now

- [ ] Draft-1 step 4 — Human iterate from the draft (placement, captions, missing bits) — small follow-ups only

## Next

- [ ] After step 4: open Later — multi-book foundation first

## Later

Gate open: Alice draft-1 weave → export smoke done.

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

- [x] Draft-1 step 3 — Smoke `export --force`; EPUB (and HTML) product check — images OK
- [x] Draft-1 step 2 — Teach `export` to embed scene images (EPUB pack + HTML relative + PDF link_callback)
- [x] Draft-1 step 1 — Weave scene illustrations into `book-report.md` (`illustrations.py` + `write_book_report`)
- [x] Footnotes for all Alice chapters 1–12 (`footnotes --all`)
- [x] Visual bible → handoff → resolve; Bing scene JPGs + human art consistency pass
- [x] Handoff viewer + answers JSON + `visual-resolve`
- [x] Agent-first playbook (`docs/agent-playbook.md`)
- [x] Export HTML / PDF / EPUB; LLM reduce; alias merge; rollup; Reader/Editor/Critic pipeline

Archive (milestones; details in git + `docs/decisions.md`):

- [x] Project skeleton, Alice under `data/books/`, knowledge base (`docs/`, `AGENTS.md`)
- [x] Book loader/splitter; map/merge summarize; skip/force; dual providers (Gemini + LM Studio)
- [x] Critic one-pass; draft persist + `--from`; footnote agent + resume; bible-first visual steps 1–5
