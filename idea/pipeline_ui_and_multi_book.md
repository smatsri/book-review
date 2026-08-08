# Pipeline UI + multi-book (vision)

> Aspirational. Current path layout (scoped trees) is in [`docs/architecture.md`](../docs/architecture.md).  
> Handoff viewer today: `web/handoff.html` + `view-handoff` (Alice DEFAULT_URL hardcoded; MB5 will book-scope).

## Why

Two product pressures after Alice draft-1:

1. **Web works** — the handoff viewer proved a thin local UI is better than JSON-in-chat for human-in-the-loop steps. Next: control the pipeline and **see progress**, not only answer art questions.
2. **Next book** — after Alice export, move to **Asimov — *The Naked Sun*** (source is a **PDF**). That forces **multi-book** layout and a non-Gutenberg ingest path. Flat `state/` / `output/` cannot host two books without collisions.

Do not build the full UI or multi-book plumbing until Alice draft-1 (weave → export) is done — see `todo.md` Now/Next.

## Multi-book (foundation)

### Intent

- One repo, many books; each book has its own source + artifacts.
- CLI stays the real engine; UI (when built) selects a book and calls the same steps.
- Alice remains the first completed product path; Naked Sun is the first multi-book / PDF stress test.

### Sketch (not committed layout)

```
data/books/<book-id>/     # source: .txt and/or .pdf (+ optional meta)
state/<book-id>/          # chapters, analyses, bible, handoff, …
output/<book-id>/         # summaries, report, exports, illustrations/
```

`<book-id>` examples: `alice-wonderland`, `asimov-naked-sun` (stable slug, not display title).

### Book registry (light)

A small manifest (e.g. `data/books/catalog.json` or per-book `meta.json`) should eventually hold:

- `id`, display title, author
- source kind: `gutenberg_txt` | `pdf` (more later)
- chapter-split strategy / notes
- optional default LLM / language hints

Until that exists, treat “active book” as an explicit CLI flag / env — avoid silent global defaults that mix Alice and Naked Sun.

### PDF ingest (*The Naked Sun*)

- Extract text from PDF → normalized plain text (or chapter files) under that book’s data dir.
- Chapter split will **not** match Alice’s `CHAPTER …` Gutenberg rules; expect a book-specific splitter or config.
- Rights / source: keep PDFs Cursor-ignored like other book full text; do not invent licensing assumptions in code.

### What stays single-book until migration

Alice migration (MB3) scoped `data/` / `state/` / `output/` under `<book-id>`. Light catalog (MB4) ships per-book `meta.json` + derived `catalog.json` + CLI `books`. Remaining foundation: book-scoped handoff viewer (MB5).

### Foundation slices (implementation order)

One PR/chat per slice; keep migrate (MB3) alone. Backlog ids in `todo.md`.

1. **MB1 — Path contract** — `BookPaths` + `--book <id>`; flat Alice compat; no file moves.
2. **MB2 — Wire CLI** — every command resolves artifacts via `BookPaths`.
3. **MB3 — Migrate Alice** — scoped `data/` / `state/` / `output/`; drop flat fallback; update architecture/runbook smoke.
4. **MB4 — Light catalog** — per-book `meta.json` and/or `catalog.json`.
5. **MB5 — Book-scope handoff viewer** — `view-handoff --book` + HTML fetch under `state/<book-id>/`.

Out of this foundation: PDF ingest, Naked Sun, pipeline control UI (see sequencing below).

## Pipeline control UI

### Intent

Grow `web/` from a **one-page handoff questionnaire** into a **local operator console**:

- Pick active book
- See pipeline stages and artifact status (done / missing / stale)
- Trigger steps (or copy the exact CLI) with skip/force/`--from` semantics preserved
- Show progress while long runs execute (chapter N of M, current stage)
- Keep handoff answers / resolve as one stage in that flow

### Constraints (keep it honest)

- **CLI remains source of truth** — UI wraps `main.py` (or thin Python HTTP that shells the same commands). Do not fork business logic into JS.
- **Local-first** — same spirit as `view-handoff` (serve repo / localhost). No cloud dashboard requirement for v1.
- **Progress = filesystem truth** — prefer scanning `state/<book-id>/` + `output/<book-id>/` (and optional `run-status.json` written by CLI) over inventing a second job DB.
- **Handoff pattern** — static or lightly dynamic pages under `web/`; human downloads or POSTs answers only where needed; answers still land under that book’s `state/`.

### Suggested slices (when implementing)

1. **Read-only status board** — per book, which artifacts exist (chapters → summarize → … → export).
2. **Run controls** — start one CLI step; stream or poll logs/progress.
3. **Handoff integrated** — book-scoped path to existing handoff UI.
4. **Catalog** — add/select books (including PDF import entry point).

## Sequencing vs Alice

```
Alice draft-1 (weave → export smoke)
        |
   Multi-book paths + catalog (migrate Alice)
        |
   PDF ingest + Naked Sun chapters
        |
   Pipeline UI (status → run → progress)
```

UI can prototype against Alice earlier **only** as a thin status viewer; full control + progress is more valuable once book scoping exists.

## Out of scope here

- RAG / embeddings (separate Later in `todo.md`)
- Full illustrated novel packaging
- Paid model mix (parked in decisions)
- Automated image gen / Vision-LLM art QA
