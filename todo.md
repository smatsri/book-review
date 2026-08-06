# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Alias merge shipped (`aliases` → `state/book-rollup-merged.json`). Promote Next from Later when ready.
- **Last success:** LLM character/theme alias merge on book rollup (baseline `book-rollup.json` unchanged).
- **Do not redo:** Project skeleton, Alice loader/splitter, knowledge base, OpenAI→Gemini, skip/force, map/merge CLI, Reader/Editor split, dual providers, Gemini vs Qwen chapter-1 comparison, Critic one-pass loop, draft persist + `--from`, book rollup normalize rules, billing decision for now, alias merge CLI/agent (see `docs/decisions.md`).
- **Parked:** Paid Flash / Pro-Sonnet mix / per-agent hybrid — revisit when quota or quality blocks local-only dev. See Later + `docs/decisions.md`.

## Now

_(empty — promote from Later when ready)_

## Next

_(empty — promote from Later when ready)_

## Later

- [ ] Decide billing / model quality strategy (paid Flash? Pro/Sonnet mix? per-agent hybrid?)
  - Parked: local Qwen (`LLM_PROVIDER=lmstudio`) is enough for current dev
  - Trigger: free-tier/quota pain returns, or quality needs beyond local 9B
  - Context / lean notes: `docs/decisions.md` + `idea/model_comparison_and_context_enrichment.md`
- [ ] Multi-round Critic (loop until ok / max N) — only if one-pass is insufficient
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
- [x] Fuzzy / LLM character–theme alias merge (`aliases` → `state/book-rollup-merged.json`)
