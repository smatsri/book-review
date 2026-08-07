# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Split handoff answers work into two slices. Next: viewer → answers JSON, then resolve/apply CLI.
- **Last success:** `visual-handoff --force` wrote `state/book-visual-handoff.json` with options on all open questions; viewer renders options + suggested.
- **Do not redo:** Project skeleton, Alice loader/splitter, knowledge base, OpenAI→Gemini, skip/force, map/merge CLI, Reader/Editor split, dual providers, Gemini vs Qwen chapter-1 comparison, Critic one-pass loop (no multi-round), draft persist + `--from`, book rollup normalize rules, alias merge CLI/agent, export CLI, footnote enriched weave, LLM reduce synthesis, footnotes resume, visual-identity book identity, visual-characters sheets, visual-places sheets, visual-scenes briefs, visual-handoff, handoff HTML viewer + `view-handoff`, handoff question options (see `docs/decisions.md`).
- **Parked:** Paid Flash / Pro-Sonnet mix / per-agent hybrid — see Later + `docs/decisions.md`. Gutenberg/external book context (not needed this stage). Image generation until handoff answers are applied into a resolved bible.

## Now

- [ ] Handoff viewer → answers JSON: pick options in `web/handoff.html`, download `state/book-visual-handoff-answers.json` (chosen option index per open question ± notes)

## Next

- [ ] Handoff answers → resolve/apply CLI: accept answers JSON and fold into bible state (new resolved artifact and/or patched sheets) — see `docs/decisions.md`
- [ ] Image generation from resolved bible + scene briefs

## Later

- [ ] Consistency review of generated art vs bible
- [ ] Wire / weave illustrations into enriched MD / report / export
- [ ] Decide billing / model quality strategy (paid Flash? Pro/Sonnet mix? per-agent hybrid?)
  - Parked for now: local Qwen (`LLM_PROVIDER=lmstudio`) for feature work
  - Counter: full-book latency + upcoming agents make mix a design choice, not just a bill
  - Context: `docs/decisions.md` + `idea/model_comparison_and_context_enrichment.md`
- [ ] RAG / embeddings over chapters

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
