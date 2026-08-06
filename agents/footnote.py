"""Footnote agent: research historical/cultural notes for one chapter."""

from __future__ import annotations

import json
import re
from typing import Any

from agents.llm import generate_text
from book import Chapter

SYSTEM_PROMPT = """You are a careful literary Footnote / Research agent.
You add short historical, conceptual, cultural, or source notes that help a
reader understand the chapter.
Be faithful to the chapter text and Reader notes; do not invent plot events.
Prefer confidence "low" over fabricated facts. Do not invent URLs or citations.
Return valid JSON only."""

_KINDS = frozenset({"history", "concept", "culture", "source"})
_CONFIDENCE = frozenset({"high", "medium", "low"})
_MAX_FOOTNOTES = 8
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", text.strip().casefold()).strip("-")
    return slug or "note"


def _normalize_footnotes(
    raw: Any,
    *,
    chapter_number: int,
) -> list[dict[str, str]]:
    """Validate LLM footnotes; assign unique chNN-slug ids."""
    if not isinstance(raw, list):
        return []

    prefix = f"ch{chapter_number:02d}"
    used_ids: set[str] = set()
    notes: list[dict[str, str]] = []

    for item in raw:
        if not isinstance(item, dict):
            continue
        if len(notes) >= _MAX_FOOTNOTES:
            break

        anchor = item.get("anchor")
        note = item.get("note")
        kind = item.get("kind")
        confidence = item.get("confidence")
        raw_id = item.get("id")

        if not isinstance(anchor, str) or not anchor.strip():
            continue
        if not isinstance(note, str) or not note.strip():
            continue
        if not isinstance(kind, str) or kind.strip().casefold() not in _KINDS:
            continue
        if (
            not isinstance(confidence, str)
            or confidence.strip().casefold() not in _CONFIDENCE
        ):
            confidence = "low"

        anchor = " ".join(anchor.strip().split())
        note_text = " ".join(note.strip().split())
        kind_norm = kind.strip().casefold()
        conf_norm = str(confidence).strip().casefold()

        if isinstance(raw_id, str) and raw_id.strip():
            slug = _slugify(raw_id.strip())
            # Drop accidental chapter prefix from model output.
            if slug.startswith(f"{prefix}-"):
                slug = slug[len(prefix) + 1 :] or "note"
        else:
            slug = _slugify(anchor)

        note_id = f"{prefix}-{slug}"
        base = note_id
        n = 2
        while note_id in used_ids:
            note_id = f"{base}-{n}"
            n += 1
        used_ids.add(note_id)

        notes.append(
            {
                "id": note_id,
                "anchor": anchor,
                "kind": kind_norm,
                "note": note_text,
                "confidence": conf_norm,
            }
        )

    return notes


def research_footnotes(
    chapter: Chapter,
    analysis: dict[str, Any],
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """Propose footnotes for a chapter; return a JSON-serializable dict."""
    notes = json.dumps(
        {
            "plot": analysis.get("plot", ""),
            "characters": analysis.get("characters", []),
            "themes": analysis.get("themes", []),
            "quotes": analysis.get("quotes", []),
            "events": analysis.get("events", []),
        },
        indent=2,
        ensure_ascii=False,
    )

    user_prompt = f"""Chapter: {chapter.heading}

Chapter text:
---
{chapter.text}
---

Reader analysis (JSON):
{notes}

Return a JSON object with exactly these keys:
- "footnotes": array of 3–8 objects (or fewer / empty if nothing worth annotating), each with:
  - "id": string — short slug hint only (e.g. "white-rabbit"); code will prefix chNN-
  - "anchor": string — short phrase expected to appear in a chapter summary (character
    name, concept, place, or quoted fragment); used to place the marker
  - "kind": string — one of "history", "concept", "culture", "source"
  - "note": string — one or two short sentences for a human reader
  - "confidence": string — one of "high", "medium", "low"

Rules:
- Explain historical context, concepts, cultural allusions, or soft source hints only.
- Do not invent URLs, page numbers, or fake citations.
- Do not invent plot events absent from the chapter.
- Prefer fewer, high-value notes over many trivial ones.
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
        raise RuntimeError(f"Footnote agent returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Footnote agent JSON must be an object")

    return {
        "chapter": chapter.number,
        "heading": chapter.heading,
        "footnotes": _normalize_footnotes(
            data.get("footnotes"),
            chapter_number=chapter.number,
        ),
    }


__all__ = ["research_footnotes"]
