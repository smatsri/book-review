"""Visual Scenes agent: illustration-worthy scene briefs with composition focus."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text
from agents.visual_traits import normalize_trait_list


SYSTEM_PROMPT = """You are a careful Visual Scenes agent for illustrated books.
You receive a book-level visual identity, character and place name lists, and compact chapter notes.
Select a small set of illustration-worthy moments as scene briefs.
Separate three kinds of information for every trait:
- fact: explicitly grounded in the provided notes
- interpretation: reasonable inference from the material
- art_decision: stylistic choice not required by the text
Do not invent plot events absent from the inputs.
Art decisions are allowed but must use kind art_decision and low confidence.
Prefer character and place names from the provided lists when they fit.
Keep looks consistent with the visual identity when making art decisions.
Return valid JSON only."""

# Sized for ~8k local contexts (LM Studio / Qwen) with room for JSON output.
_MAX_PLOT_CHARS = 350
_MAX_EVENTS_PER_CHAPTER = 4
_MAX_EVENT_CHARS = 80
_MAX_CHARS_PER_CHAPTER = 4
_MAX_SCENES = 8
_MAX_SHEET_NAMES = 8
_IDENTITY_TRAIT_KEYS = (
    "artistic_style",
    "color_palette",
    "atmosphere",
    "period",
    "motifs",
)
_TRAIT_KEYS = ("emotional_focus", "composition")


def _trait_values(raw: Any, *, limit: int = 4) -> list[str]:
    if not isinstance(raw, list):
        return []
    values: list[str] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
        if len(values) >= limit:
            break
    return values


def _slim_identity(identity: dict[str, Any]) -> dict[str, list[str]]:
    return {
        key: _trait_values(identity.get(key))
        for key in _IDENTITY_TRAIT_KEYS
    }


def _truncate(text: str, max_chars: int) -> str:
    text = " ".join(text.strip().split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _sheet_names(payload: dict[str, Any], *, key: str) -> list[str]:
    rows = payload.get(key) or []
    if not isinstance(rows, list):
        return []
    names: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
        if len(names) >= _MAX_SHEET_NAMES:
            break
    return names


def _compact_chapters(
    chapter_analyses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Chapter evidence for scenes: plot + events + light cast names."""
    compact: list[dict[str, Any]] = []
    for analysis in chapter_analyses:
        plot = analysis.get("plot")
        if not isinstance(plot, str):
            plot = ""
        plot = _truncate(plot, _MAX_PLOT_CHARS) if plot else ""

        events_raw = analysis.get("events") or []
        events: list[str] = []
        if isinstance(events_raw, list):
            for item in events_raw:
                if isinstance(item, str) and item.strip():
                    events.append(_truncate(item, _MAX_EVENT_CHARS))
                if len(events) >= _MAX_EVENTS_PER_CHAPTER:
                    break

        characters_raw = analysis.get("characters") or []
        character_names: list[str] = []
        if isinstance(characters_raw, list):
            for item in characters_raw:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        character_names.append(name.strip())
                elif isinstance(item, str) and item.strip():
                    character_names.append(item.strip())
                if len(character_names) >= _MAX_CHARS_PER_CHAPTER:
                    break

        compact.append(
            {
                "chapter": analysis.get("chapter"),
                "heading": analysis.get("heading"),
                "plot": plot,
                "events": events,
                "characters": character_names,
            }
        )
    return compact


def _normalize_string_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            continue
        value = item.strip()
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _normalize_scene(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    chapter = raw.get("chapter")
    if not isinstance(chapter, int):
        return None
    for key in _TRAIT_KEYS:
        if key not in raw:
            return None
        if not isinstance(raw[key], list):
            return None

    title_clean = title.strip()
    sheet: dict[str, Any] = {
        "title": title_clean,
        "chapter": chapter,
        "characters": _normalize_string_list(raw.get("characters")),
        "location": _normalize_string_list(raw.get("location")),
    }
    for key in _TRAIT_KEYS:
        sheet[key] = normalize_trait_list(raw[key], label=f"{title_clean}.{key}")
    return sheet


def build_visual_scenes(
    chapter_analyses: list[dict[str, Any]],
    identity: dict[str, Any],
    characters_payload: dict[str, Any],
    places_payload: dict[str, Any],
    *,
    source_identity: str,
    source_characters: str,
    source_places: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Build scene-brief JSON from analyses + identity + character/place sheets."""
    if not chapter_analyses:
        raise ValueError("chapter_analyses must not be empty")

    chapters_included: list[int] = []
    for analysis in chapter_analyses:
        num = analysis.get("chapter")
        if isinstance(num, int):
            chapters_included.append(num)

    character_names = _sheet_names(characters_payload, key="characters")
    place_names = _sheet_names(places_payload, key="places")

    identity_json = json.dumps(
        _slim_identity(identity),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    cast_json = json.dumps(character_names, ensure_ascii=False, separators=(",", ":"))
    places_json = json.dumps(place_names, ensure_ascii=False, separators=(",", ":"))
    chapters_json = json.dumps(
        _compact_chapters(chapter_analyses),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    user_prompt = f"""Book visual identity (trait values only):
{identity_json}

Character sheet names (prefer these when they fit):
{cast_json}

Place sheet names (prefer these when they fit):
{places_json}

Per-chapter notes (compact JSON: chapter + plot + events + character names):
{chapters_json}

Return a JSON object with exactly one top-level key:
- "scenes": array of scene brief objects

Each scene brief must have:
- "title": short label for the illustration-worthy moment
- "chapter": integer chapter number from the notes
- "characters": array of short character name strings present in the moment
- "location": array of short place / setting name strings for the moment
- "emotional_focus": array of trait objects (mood / feeling to emphasize)
- "composition": array of trait objects (camera, framing, visual focus; flatten camera/focus into this list)

Each trait object must have:
- "value": short string
- "kind": one of "fact", "interpretation", "art_decision"
- "confidence": number from 0.0 to 1.0
  - 1.0 explicit in the notes
  - 0.7 strong inference
  - 0.4 soft interpretation
  - 0.1 pure art decision
- "note": brief rationale (may be empty string)

Prefer striking, illustration-worthy moments across the book. Cap at {_MAX_SCENES} scenes.
Prefer names from the character/place lists when they fit; other grounded labels are allowed.
Prefer 2–3 short traits per emotional_focus / composition array.
Keep each "value" brief and each "note" under ~8 words (or empty).
Keep total JSON compact.
Do not add other top-level keys. Do not invent moments not supported by the notes.
"""

    raw = generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        model=model,
        temperature=0.3,
        json_mode=True,
        max_output_tokens=4096,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Visual scenes returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Visual scenes JSON must be an object")
    if "scenes" not in data:
        raise RuntimeError("Visual scenes JSON missing required key 'scenes'")
    if not isinstance(data["scenes"], list):
        raise RuntimeError("Visual scenes JSON 'scenes' must be an array")

    scenes: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for entry in data["scenes"]:
        sheet = _normalize_scene(entry)
        if sheet is None:
            continue
        key = (sheet["chapter"], sheet["title"].casefold())
        if key in seen:
            continue
        seen.add(key)
        scenes.append(sheet)
        if len(scenes) >= _MAX_SCENES:
            break

    return {
        "source_identity": source_identity,
        "source_characters": source_characters,
        "source_places": source_places,
        "chapters_included": chapters_included,
        "scenes": scenes,
    }


__all__ = ["build_visual_scenes"]
