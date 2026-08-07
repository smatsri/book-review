# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Visual work split planned (bible-first). Next: book-level visual identity.
- **Last success:** `footnotes` with no `--chapter` picks first chapter without `state/chapter-NN-footnotes.json`.
- **Do not redo:** Project skeleton, Alice loader/splitter, knowledge base, OpenAI→Gemini, skip/force, map/merge CLI, Reader/Editor split, dual providers, Gemini vs Qwen chapter-1 comparison, Critic one-pass loop (no multi-round), draft persist + `--from`, book rollup normalize rules, alias merge CLI/agent, export CLI, footnote enriched weave, LLM reduce synthesis, footnotes resume (see `docs/decisions.md`).
- **Parked:** Paid Flash / Pro-Sonnet mix / per-agent hybrid — see Later + `docs/decisions.md`. Gutenberg/external book context (not needed this stage). Image generation until Visual Bible exists.

## Now

- [ ] Visual Bible step 1 — book-level visual identity (style, palette, atmosphere, motifs; fact / interpretation / art decision + confidence)
  - Vision: `idea.md` + `idea/visual_bible_for_books.md`
  - Inputs: existing rollup / analyses (no new literary pass)

## Next

- [ ] Visual Bible step 2 — character visual sheets (stable looks; source + confidence per trait)
- [ ] Visual Bible step 3 — key places / settings
- [ ] Visual Bible step 4 — scene briefs (select illustration-worthy moments + composition / emotional focus)
- [ ] Visual Bible step 5 — open questions + consistency pass (bible as handoff artifact)
- [ ] Wire bible into product (CLI + state/output; report/export later if needed)

## Later

- [ ] Image generation from bible + scene briefs
- [ ] Consistency review of generated art vs bible
- [ ] Weave illustrations into enriched MD / report / export
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
- [x] Book-level structured rollup in `state/` (cross-chapter characters, themes)
- [x] Fuzzy / LLM character–theme alias merge (`aliases` → `state/book-rollup-merged.json`)
- [x] Export HTML / PDF / EPUB (`export` → `output/book-report.{html,pdf,epub}`)
- [x] Footnote / research agent (`footnotes` → footnotes JSON + enriched MD; report prefers enriched)
- [x] Bare `footnotes` resumes at first chapter missing footnotes JSON
- [x] LLM reduce / book-level synthesis (`reduce` → `book-synthesis.md`; weave into report)
- [x] Split Visual into bible-first steps (identity → characters → places → scenes → handoff; gen later)
