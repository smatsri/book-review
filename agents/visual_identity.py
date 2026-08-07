"""Visual Identity agent: book-level style / palette / atmosphere / motifs."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text

SYSTEM_PROMPT = """You are a careful Visual Identity agent for illustrated books.
You receive compact per-chapter Reader notes and a book-level character/theme index.
Propose a coherent book-level visual identity (style, palette, atmosphere, period, motifs).
Separate three kinds of information for every trait:
- fact: explicitly grounded in the provided notes/index
- interpretation: reasonable inference from the material
- art_decision: stylistic choice not required by the text
Do not invent plot events, characters, or quotes absent from the inputs.
Art decisions are allowed but must use kind art_decision and low confidence.
Return valid JSON only."""

# Keep payloads small enough for ~8k local contexts (Alice-sized books).
_MAX_PLOT_CHARS = 450
_MAX_THEMES_PER_CHAPTER = 5
_MAX_ROLLUP_CHARACTERS = 20
_MAX_ROLLUP_THEMES = 15

_TRAIT_KEYS = (
    "artistic_style",
    "color_palette",
    "atmosphere",
    "period",
    "motifs",
)
_KINDS = frozenset({"fact", "interpretation", "art_decision"})


def _compact_chapters(
    chapter_analyses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for analysis in chapter_analyses:
        plot = analysis.get("plot")
        if not isinstance(plot, str):
            plot = ""
        plot = " ".join(plot.strip().split())
        if len(plot) > _MAX_PLOT_CHARS:
            plot = plot[: _MAX_PLOT_CHARS - 3].rstrip() + "..."

        themes_raw = analysis.get("themes") or []
        themes: list[str] = []
        if isinstance(themes_raw, list):
            for item in themes_raw:
                if isinstance(item, str) and item.strip():
                    themes.append(item.strip())
                if len(themes) >= _MAX_THEMES_PER_CHAPTER:
                    break

        compact.append(
            {
                "chapter": analysis.get("chapter"),
                "heading": analysis.get("heading"),
                "plot": plot,
                "themes": themes,
            }
        )
    return compact


def _slim_rollup(rollup: dict[str, Any]) -> dict[str, list[str]]:
    characters = rollup.get("characters") or []
    themes = rollup.get("themes") or []

    char_rows = [
        c
        for c in characters
        if isinstance(c, dict) and isinstance(c.get("name"), str) and c["name"].strip()
    ]
    char_rows.sort(key=lambda c: (-len(c.get("chapters") or []), c["name"]))
    char_names = [c["name"].strip() for c in char_rows[:_MAX_ROLLUP_CHARACTERS]]

    theme_rows = [
        t
        for t in themes
        if isinstance(t, dict)
        and isinstance(t.get("theme"), str)
        and t["theme"].strip()
    ]
    theme_rows.sort(key=lambda t: (-len(t.get("chapters") or []), t["theme"]))
    theme_labels = [t["theme"].strip() for t in theme_rows[:_MAX_ROLLUP_THEMES]]

    return {"characters": char_names, "themes": theme_labels}


def _normalize_trait_list(raw: Any, *, label: str) -> list[dict[str, Any]]:
    """Keep well-formed trait rows; drop bad entries (fail closed per row)."""
    if not isinstance(raw, list):
        raise RuntimeError(f"Visual identity JSON '{label}' must be an array")

    items: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if not isinstance(value, str) or not value.strip():
            continue
        kind = entry.get("kind")
        if not isinstance(kind, str) or kind.strip() not in _KINDS:
            continue
        confidence = entry.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            continue
        conf = float(confidence)
        if conf < 0.0:
            conf = 0.0
        elif conf > 1.0:
            conf = 1.0
        note = entry.get("note")
        if not isinstance(note, str):
            note = ""
        items.append(
            {
                "value": value.strip(),
                "kind": kind.strip(),
                "confidence": conf,
                "note": note.strip(),
            }
        )
    return items


def build_visual_identity(
    chapter_analyses: list[dict[str, Any]],
    rollup: dict[str, Any],
    *,
    source_rollup: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Build book-level visual identity JSON from analyses and a rollup dict."""
    if not chapter_analyses:
        raise ValueError("chapter_analyses must not be empty")

    chapters_included: list[int] = []
    for analysis in chapter_analyses:
        num = analysis.get("chapter")
        if isinstance(num, int):
            chapters_included.append(num)

    chapters_json = json.dumps(
        _compact_chapters(chapter_analyses),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    rollup_json = json.dumps(
        _slim_rollup(rollup),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    user_prompt = f"""Book-level character/theme index (JSON names only):
{rollup_json}

Per-chapter notes (compact JSON: plot + themes):
{chapters_json}

Return a JSON object with exactly these keys (each an array of trait objects):
- "artistic_style"
- "color_palette"
- "atmosphere"
- "period"
- "motifs"

Each trait object must have:
- "value": short string (e.g. "pencil illustration", "dreamlike", "playing cards")
- "kind": one of "fact", "interpretation", "art_decision"
- "confidence": number from 0.0 to 1.0
  - 1.0 explicit in the notes/index
  - 0.7 strong inference
  - 0.4 soft interpretation
  - 0.1 pure art decision
- "note": brief rationale (may be empty string)

Prefer a small coherent set (roughly 2–6 items per key). Do not add other top-level keys.
"""

    raw = generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        model=model,
        temperature=0.3,
        json_mode=True,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Visual identity returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Visual identity JSON must be an object")

    payload: dict[str, Any] = {
        "source_rollup": source_rollup,
        "chapters_included": chapters_included,
    }
    for key in _TRAIT_KEYS:
        if key not in data:
            raise RuntimeError(f"Visual identity JSON missing required key '{key}'")
        payload[key] = _normalize_trait_list(data[key], label=key)

    return payload


__all__ = ["build_visual_identity"]
