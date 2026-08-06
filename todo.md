# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Book-level structured rollup shipped (`state/book-rollup.json`); next is billing / model quality strategy.
- **Last success:** Deterministic `rollup.py` + `python main.py rollup`; characters/themes merged across chapter analyses; `summarize --all` writes report + rollup. Smoke: Alice → 12 chapters, 39 characters, 47 themes; `The White Rabbit` merges with `White Rabbit`.
- **Do not redo:** Project skeleton, Alice loader/splitter, knowledge base, OpenAI→Gemini, skip/force, map/merge CLI, Reader/Editor split, dual providers, Gemini vs Qwen chapter-1 comparison, Critic one-pass loop, draft persist + `--from`, book rollup normalize rules (see `docs/decisions.md` + `idea/model_comparison_and_context_enrichment.md`).
- **Parked:** Paid Flash vs stronger models / per-agent hybrid — see Later + `docs/decisions.md`. Fuzzy character alias merge / LLM reduce — Later.

## Now

- [ ] Decide billing / model quality strategy (paid Flash? Pro/Sonnet mix? per-agent hybrid?)
  - Context: provider switch done (`LLM_PROVIDER=gemini|lmstudio`); hybrid map-local / Critic-cloud still open — see `docs/decisions.md`
  - Trigger: quality or quota needs beyond one global provider
  - Lean: local Qwen for Reader/dev fidelity; ~5–10 min/call on M2 with thinking → single-chapter smoke, not full-book thrash; hybrid still open
  - Do not redo: chapter-1 Gemini vs Qwen comparison (notes in decisions + `idea/model_comparison_and_context_enrichment.md`)

## Next

_(empty — promote from Later when ready)_

## Later

- [ ] Multi-round Critic (loop until ok / max N) — only if one-pass is insufficient
- [ ] Fuzzy / LLM character–theme alias merge (beyond normalize rules)
- [ ] RAG / embeddings over chapters
- [ ] Footnote / research agent
- [ ] Visual / illustration agent
- [ ] Export HTML / PDF / EPUB
- [ ] LLM reduce / book-level synthesis (beyond concatenated chapter report)

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
