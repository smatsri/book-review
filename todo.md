# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Reader → Editor split done; next is Critic loop. LLM billing/model choice parked (deferred).
- **Last success:** `summarize --chapter 1 --force` → `state/chapter-01-analysis.json` + `output/chapter-01-summary.md` (smoke).
- **Do not redo:** Project skeleton, Alice loader/splitter, knowledge base, OpenAI→Gemini, skip/force, map/merge CLI, Reader/Editor split.
- **Parked:** Free-tier Gemini 429 / paid vs stronger models / local or hybrid — see Later + `docs/decisions.md`.

## Now

- [ ] Add Critic loop (critique → revise → final)

## Next

- [ ] Book-level structured rollup in `state/` (cross-chapter characters, themes)

## Later

- [ ] Decide LLM provider / billing / model strategy (paid Flash? Pro/Sonnet mix? local? hybrid?)
  - Context: deferred note in `docs/decisions.md` (“LLM cost / model choice — deferred”)
  - Trigger: free-tier 429s blocking map/Critic work; no decision yet
  - Local is an open option (MacBook / Ollama-style) alongside paid cloud — not decided
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
