# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Switching Now to Visual image prompts (prompt pack); Naked Sun sheets still not re-run.
- **Last success:** Illustration-cast selection + smaller batches; Naked Sun aliases restored Elijah Baley; prompt-pack idea parked then promoted to Now.
- **Do not redo:** Alias merge harden; full-cast experiment (superseded); MB1–MB5; EPUB; UI; Critic harden; Alice visual/images.
- **Parked / reminders:** Naked Sun `visual-characters --force` (illustration cast) → scenes → handoff → resolve; optional reduce/identity/places; Enriched v1 polish.

## Now

- [ ] Visual image prompts (prompt pack) — after resolve: compile Bing (~480) + full-model prompts from locked bible; see `idea/visual_image_prompts.md`

## Next

After multi-book foundation:

- [ ] Optional: small report placement/caption follow-ups
- [ ] Enriched v2+ (inline footnotes, mid-chapter scenes, character plates) — see spec
- [ ] Enriched v1.1 polish — parked Known issues in `idea/enriched_book_export.md` (PDF width, EPUB line breaks, empty footnote lists)

## Later

After multi-book foundation.

- [ ] Character companion sketch — idea note saved in `idea/character_companion_sketch.md`
- [ ] Split `main.py` into smaller, focused modules for readability and token management; keep entrypoint thin and move shared CLI helpers/command groups into dedicated files
- [ ] Pipeline UI polish — `web/pipeline.html` layout / run panel UX (after UI-2 works; not blocking UI-3)
- [ ] PDF image/layout polish if EPUB/HTML isn’t enough (see also enriched Known issues)
- [ ] Vision-LLM (or hybrid) art consistency review — optional; human pass enough for current Alice set
- [ ] Billing / model quality strategy — local Gemma 4 12B for now; see `docs/decisions.md` + `idea/model_comparison_and_context_enrichment.md`
- [ ] RAG / embeddings over chapters
- [ ] Agent policy / configurable characteristics — shared mechanism, per-agent taste knobs; see `idea/agent_policy_config.md`

## Done

Recent:

- [x] **Visual characters illustration cast** — ≥3 ch / fill 8 / cap 12 / keep #1; batch 3 + JSON retry; supersedes full-cast
- [x] **Visual characters full cast (batched)** — superseded (too slow / truncated JSON on robot-heavy cast)
- [x] **Alias merge harden** — notes + chapter counts in prompt; identity-conflict split validators; display by chapter count; docs + `test_alias_refine.py`
- [x] **Handoff Save to state** — `POST /api/handoff-answers` + **Save to state** in `handoff.html`; Download kept; validates vs handoff
- [x] **Pipeline UI-3 — handoff in operator console** — same-origin **Open handoff** from `view-pipeline` (8766); `view-handoff` 8765 kept as dedicated entry
- [x] **Local model → Gemma 4 12B** — `LMSTUDIO_MODEL` / code default / runbook + architecture + decisions; supersedes Qwen-as-dev-default
- [x] **Critic ~8k prompt fit** — head+tail chapter truncate + compact notes; Naked Sun ch18 `--from critic` smoke
- [x] **Critic JSON resilience** — `agents/json_util.py`; Critic max tokens + one retry; Naked Sun ch15 `--from critic` smoke
- [x] **Pipeline UI-2 — Run one CLI step** — `pipeline_run.py` + `POST/GET /api/run`; allowlist; one job; poll log + status; Run button in `web/pipeline.html`
- [x] **Pipeline UI-1 — Status board** — `pipeline_status.py` + `view-pipeline` (port 8766) + `web/pipeline.html`; pick book, show done/partial/missing, copy CLI (no run)
- [x] **EPUB ingest** — `source_kind: epub` via ebooklib numbered TOC → `Chapter` list; smoke `chapters --book asimov-naked-sun` (18 chapters)
- [x] **MB5 — Book-scope handoff viewer** — `view-handoff --book` + `?book=` fetch `state/<id>/book-visual-handoff.json`
- [x] **MB4 — Light catalog** — `meta.json` / `catalog.json` (id, title, author, source kind); list/validate ids
- [x] **MB3 — Migrate Alice** — scoped `data/` / `state/` / `output/`; drop flat fallback; smoke + architecture/runbook
- [x] **MB2 — Wire CLI** — all commands + enriched/export use `BookPaths` (Alice still flat)
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
