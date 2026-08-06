# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Gemini provider switch done; smoke-tested `summarize --chapter 1`.
- **Last success:** Stage-1 summarizer on Gemini (`google-genai`, `GEMINI_API_KEY`).
- **Do not redo:** Project skeleton, Alice loader/splitter, knowledge base, OpenAI→Gemini switch.

## Now

- [ ] Summarize all chapters (map) and merge into one Markdown report

## Next

- [ ] Split roles: Reader agent → Editor agent
- [ ] Add Critic loop (critique → revise → final)
- [ ] Persist structured analysis in `state/` (characters, themes, etc.)

## Later

- [ ] RAG / embeddings over chapters
- [ ] Footnote / research agent
- [ ] Visual / illustration agent
- [ ] Export HTML / PDF / EPUB

## Done

- [x] Project skeleton (venv, deps, `.env.example`, gitignore, folders)
- [x] Place Alice text under `data/books/` and exclude via `.cursorignore`
- [x] Book loader + chapter splitter (`book.py`, `main.py chapters`)
- [x] Stage-1 single-agent summarizer (OpenAI, temporary)
- [x] Initial git commit
- [x] Knowledge base: `docs/`, `AGENTS.md`, `.cursor/rules/knowledge-base.mdc`
- [x] Switch LLM provider from OpenAI to Gemini
