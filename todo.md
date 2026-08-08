# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** MB1 done (`BookPaths` + `--book`); next implement **MB2** (wire CLI).
- **Last success:** `BookPaths` flat Alice compat; `python main.py chapters --book alice-wonderland` writes flat `state/chapters.json`.
- **Do not redo:** MB1 path contract; Full-book footnotes; visual bible through `visual-resolve` + handoff; Bing JPGs + human art pass; report scene weave; export image packing; enriched v1 binder. Older work → Done / `docs/decisions.md`.
- **Parked:** Enriched v1 export polish (PDF half-width; EPUB per-sentence line breaks; empty/nested footnote bullets in all formats) — list in `idea/enriched_book_export.md` § Known issues; report human-iterate (optional); billing / Vision-LLM / RAG.

## Now

- [ ] **MB2 — Wire CLI** — all commands use `BookPaths` (no scattered `ROOT / "state"`)

## Next

Multi-book foundation (after MB2; one PR/chat each; keep MB3 alone):

- [ ] **MB3 — Migrate Alice** — move source/`state`/`output` under `<book-id>`; drop flat fallback; smoke + architecture/runbook
- [ ] **MB4 — Light catalog** — `meta.json` / `catalog.json` (id, title, author, source kind); list/validate ids
- [ ] **MB5 — Book-scope handoff viewer** — `view-handoff --book` + fetch `state/<id>/book-visual-handoff.json`

After multi-book foundation:

- [ ] Next title: **Asimov — *The Naked Sun*** — PDF ingest + chapter split (not Gutenberg `CHAPTER` rules)
- [ ] **Pipeline control UI** (grow `web/` past handoff): pick book, run CLI steps, show artifact status + progress (CLI stays source of truth)
- [ ] Optional: small report placement/caption follow-ups
- [ ] Enriched v2+ (inline footnotes, mid-chapter scenes, character plates) — see spec
- [ ] Enriched v1.1 polish — parked Known issues in `idea/enriched_book_export.md` (PDF width, EPUB line breaks, empty footnote lists)

## Later

After multi-book foundation.

- [ ] PDF image/layout polish if EPUB/HTML isn’t enough (see also enriched Known issues)
- [ ] Vision-LLM (or hybrid) art consistency review — optional; human pass enough for current Alice set
- [ ] Billing / model quality strategy — local Qwen for now; see `docs/decisions.md` + `idea/model_comparison_and_context_enrichment.md`
- [ ] RAG / embeddings over chapters

## Done

Recent:

- [x] **MB1 — Path contract** — `BookPaths` + CLI `--book <id>` (default `alice-wonderland`); flat Alice compat (no file moves)
- [x] Enriched Alice v1 — binder + `export --mode enriched` → `book-enriched.*` (no new LLM); smoke HTML/EPUB
- [x] Product direction: enriched book north star; companion report kept as second export (`idea/enriched_book_export.md`)
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
