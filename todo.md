# Todo

## Now

- [ ] Switch LLM provider from OpenAI to Gemini
  - Update `requirements.txt` (`google-genai` or equivalent)
  - Update `.env.example` (`GEMINI_API_KEY`, model name)
  - Rewrite `agents/summarizer.py` to call Gemini
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
