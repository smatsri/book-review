# Visual image prompts (prompt pack)

Vision only — not implemented. Extends the Visual Bible after `visual-resolve`.

Current truth: bible steps → locked `state/<book-id>/book-visual-resolved.json`; scene JPGs are still produced **manually** (e.g. Bing) and stored under `output/<book-id>/illustrations/`. See `docs/decisions.md` (“Scene images manual…”) and `docs/architecture.md`.

## Problem

Resolved sheets are structured art direction (identity / characters / places / scenes). They are **not** paste-ready prompts for image models.

Today’s free Bing path has a hard ~**480 character** limit. A proper image model (Flux / SD / Ideogram / Midjourney-class) wants a longer consistency payload. One prompt cannot serve both well.

## Goal

Add a **prompt compiler** step after resolve:

```text
visual-resolve → visual-prompts → (human / Bing / API later) → illustrations/
```

- Input: `book-visual-resolved.json` only (no chapter re-read).
- Output: a prompt-pack artifact (e.g. `state/<book-id>/book-visual-prompts.json`, optional MD for copy/paste).
- Still **no** required image API — prompts are the product of this step; gen stays external until a later slice.

## Design

### One brief, two (or more) renders

Per scene (optionally per character plate later):

1. **Canonical brief** — medium, model-agnostic: style lock + cast looks + place + shot + mood + “don’t invent cast.”
2. **`prompt_bing`** — hard-capped (~480). Aggressive triage; drop secondary detail.
3. **`prompt_full`** — longer target for a proper model: identity palette, per-character physical + visual_language, place architecture, composition, optional negatives / avoid list.

Same scene id → both strings. Operator picks which to paste. Later: `prompt_<provider>` without redoing the bible.

### Bing budget policy (lossy on purpose)

Priority order when compressing:

1. Style lock (from identity / art decisions)
2. Protagonist / hero look
3. Action + composition
4. Place
5. Extras / secondary cast

Drop from the bottom. Negatives usually waste Bing budget — prefer them on `prompt_full` only.

### Consistency anchors

Reusable short **character lock** snippets (from character sheets) reused across scenes. Helps both Bing and paid models stay on-model without re-deriving looks each time.

### LLM rewrite vs pure template

Prefer a small LLM pass with a hard char budget for Bing over naive trait concatenation. Templates alone glue traits awkwardly; the bible stays source of truth, the compiler is a renderer for a target.

## What this is not

- Not a change to `visual-scenes` / handoff / resolve (wrong concern; art choices already locked).
- Not automatic image generation in the same step (couple later if desired).
- Not Vision-LLM art QA (stays Later / human pass for now).

## Placement vs existing pipeline

| Step | Role |
|------|------|
| identity → characters → places → scenes | Structured bible |
| handoff → answers → resolve | Lock open art questions |
| **visual-prompts (new)** | Compile locked sheets → target-specific prompts |
| illustrations (manual today) | Produce JPGs named for weave/export |

## Open choices (when implementing)

- Exact JSON schema + CLI name (`visual-prompts` vs `image-prompts`).
- Whether character-only prompt packs ship in v1 or scenes-only first.
- Whether Bing cap is configurable (default 480).
- When/if to add an API image-gen step that consumes `prompt_full`.

## Related

- Visual Bible vision: [`visual_bible_for_books.md`](visual_bible_for_books.md)
- Enriched book weave of scene art: [`enriched_book_export.md`](enriched_book_export.md)
