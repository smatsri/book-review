# Todo

Short-term memory and backlog. Durable design lives in `docs/` and `idea.md`.  
Agents: read **Session** + **Now** first. See `AGENTS.md`.

## Session

- **Stopped at:** Knowledge base scaffolded (`docs/`, `AGENTS.md`, cursor rule). Next product work is still the Gemini switch.
- **Last success:** MVP OpenAI summarizer + `python main.py chapters` / `summarize --chapter 1` (prior sessions).
- **Do not redo:** Project skeleton, Alice loader/splitter, stage-1 OpenAI summarizer, initial git commit.

## Now

- [ ] Switch LLM provider from OpenAI to Gemini
  - Update `requirements.txt` (`google-genai` or equivalent)
  - Update `.env.example` (`GEMINI_API_KEY`, model name)
  - Rewrite `agents/summarizer.py` to call Gemini
  - Update `docs/architecture.md`, `docs/runbook.md`, and supersede the OpenAI decision in `docs/decisions.md`
  - Smoke-test: `python main.py summarize --chapter 1`

## Next

- [ ] Summarize all chapters (map) and merge into one Markdown report
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
