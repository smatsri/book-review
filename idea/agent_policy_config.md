# Agent policy / configurable characteristics

Vision only — not implemented. Current agents use fixed `SYSTEM_PROMPT` strings under `agents/`.

## Problem

Each agent has a static system prompt that mixes:

1. **Contract** — role, JSON-only output, “don’t invent plot”, trait `kind` rules
2. **Taste** — how aggressive, selective, terse, or art-free the agent should be

Taste belongs in a controllable policy; contract should stay in code so runs stay schema-safe and comparable.

## Goal

Shared mechanism for every agent; **per-agent knobs**, not one mega-config with identical fields.

```
defaults (in code)
  └─ optional book-level policy (e.g. state/<book-id>/ or thin config)
       └─ optional CLI override for one run
```

Each agent reads only its own section. Missing section = today’s behavior. Unknown keys ignored.

Do **not** expose free-form “replace the whole SYSTEM_PROMPT” as the main API.

## Split

| Keep fixed | Make configurable |
|------------|-------------------|
| Role + output shape | Selection / density bias |
| Faithfulness rules | Art freeness (`art_decision` aggressiveness) |
| Schema / allowlists | Tone, strictness, coverage preferences |
| Downstream safety (name consistency soft prefs, etc.) | Caps already hardcoded (`_MAX_SCENES`, `_MAX_FOOTNOTES`, …) if useful as named knobs |

Book *look* stays in Visual Identity output (`artistic_style`, palette, …). Agent policy is about **how the agent chooses and labels**, not redoing style.

## Suggested knobs by agent

Ship fields only where pain shows; list is a design menu, not a v1 checklist.

| Agent | Example taste knobs |
|-------|---------------------|
| Reader | Plot terseness; quote/event density |
| Critic | Strictness; `must_fix` vs `optional_improve` volume |
| Editor | Prose voice (literary vs plain) |
| Footnote | Note count bias; history vs concept lean; aggressiveness |
| Alias merger / Reducer | Few knobs; merge aggressiveness at most |
| Visual Identity | Art freeness; boldness of style proposals |
| Visual Characters / Places | Art freeness; sheet detail density |
| Visual Scenes | Climactic vs quiet; chapter spread vs iconic few; art freeness; name-match strictness |
| Visual Handoff | How picky on consistency vs open questions |

Highest value first: visual bible (esp. Scenes / Identity), then Editor / Footnote if voice matters.

## Implementation sketch (later)

1. Thin helper: load policy → render a short “Policy:” block appended to the fixed system (or user) prompt.
2. Default profile in code matching current prompts.
3. Optional book-level JSON with per-agent sections.
4. Optional CLI flags for one-off experiments (e.g. scene bias).
5. Document knobs in `docs/` only when something actually ships; keep this file as the vision note.

## Non-goals (for now)

- Per-book free-form system prompt editing
- Shared identical knob schema forced on every agent
- Changing report/export weave as part of this work
