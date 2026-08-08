# Enriched book export (product north star)

Vision for packaging the **original book** with enrichment layers.  
**Current product today:** companion `book-report` → HTML/PDF/EPUB ([`docs/architecture.md`](../docs/architecture.md)).  
**Decision:** [`docs/decisions.md`](../docs/decisions.md) — “Enriched book is product north star”.

## Why

The pipeline already produces enrichment *layers* (chapter analyses, footnotes JSON, visual bible, scene JPGs). Draft-1 shipped those into a **separate report**. The distinctive product is a **readable edition of the source text** with those layers attached — not only a dossier about the book.

## Two exports (same layers)

| Mode | Spine | Job |
|------|--------|-----|
| **Companion report** (done) | Editor summaries + synthesis + footnotes weave + scene images | Human review / editorial artifact |
| **Enriched book** (target) | Gutenberg (or later PDF) chapter **body text** | Reading edition |

Keep both. Do not delete report export; add a second binder.

## Alice enriched v1 (minimal)

Goal: open an EPUB/HTML and **read Alice**, with enrichment that does not bury the prose.

**In:**

1. **Chapter body** from `book.py` (`Chapter.text` + heading) — original narrative is the main flow.
2. **Scene images** from `output/illustrations/` + resolved bible — insert at chapter (or scene) break points already mapped by `illustrations.py` (same JPG naming).
3. **Footnotes** from `state/chapter-NN-footnotes.json` — prefer **endnotes per chapter** (or book endnotes) over dense inline markers if placement in raw Gutenberg text is fragile. Reuse footnote ids/`kind`/`note`; do not invent new research.
4. Optional thin **chapter opener** (1 short paragraph from existing Editor summary or a dedicated field) — skip in v1 if it slows shipping; can be v1.1.

**Out of v1:**

- Full literary essay sections inside the reading edition (those stay in the companion report).
- Inline mid-paragraph footnote anchors requiring perfect quote matching (unless already reliable from enriched MD).
- New image gen / Vision QA.
- Multi-book paths (can still use flat Alice layout for first enriched pack).
- Fancy print layout / typography beyond what current `export_book.py` stack can do.

**Outputs (suggested names):**

- `output/book-enriched.md` (binder markdown)
- `output/book-enriched.{html,pdf,epub}` via the same export stack (or a `export --mode enriched` flag)

Reuse EPUB image packing / HTML relative / PDF `link_callback` already taught for the report.

**Status:** Alice enriched v1 binder + `export --mode enriched` shipped. Layout/footnote polish below is parked (do not block multi-book).

## Known issues (Alice v1 — parked)

Initial human pass of `book-enriched.{pdf,epub,html}` (2026-08). Fix later as enriched polish / v1.1 — not a blocker for multi-book.

| Scope | Symptom |
|-------|---------|
| **PDF** | Body text uses roughly half the page width; the rest stays white. |
| **EPUB** | Each sentence breaks onto its own line, so many rows are mostly empty whitespace instead of flowing as paragraphs. |
| **All (HTML / PDF / EPUB)** | At least one footnote renders wrong: empty list items (bullets with no text) and nested empty lists — a run of bare bullets. |

Likely homes when fixing: PDF CSS / xhtml2pdf layout; EPUB paragraph/whitespace handling in the MD→EPUB path; footnote/endnote Markdown weave (`footnotes.py` / binder Notes) so list markup is not emitted empty.

## Alice enriched v2+ (later)

- True inline footnote markers when anchors are high-confidence.
- Sidebars / “about this chapter” after each chapter (pull from summary/synthesis without replacing body).
- Character plate pages from visual character sheets.
- Per-scene mid-chapter image placement (needs stronger text anchors than chapter-head insert).
- Print-oriented PDF polish.

## Implementation sketch (when coding)

Deterministic only for v1 binder (no new LLM):

```
chapters (book.py)
  + footnotes JSON (optional weave → endnotes)
  + resolved scenes → JPG map (illustrations.py)
  → book-enriched.md
  → export (existing converters + image pack)
```

Companion `report` / `book-report.*` stay as today.

## Done when

- Human can read Alice’s chapters in EPUB/HTML with scene art appearing in the right chapters.
- Footnotes available as chapter endnotes (or equivalent) without requiring the companion report.
- `todo.md` / architecture / runbook updated; this idea stays vision until code lands.
