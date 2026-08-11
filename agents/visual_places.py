"""Visual Places agent: stable location / setting sheets for key places."""

from __future__ import annotations

import json
from typing import Any

from agents.json_util import parse_json_object
from agents.llm import generate_text
from agents.visual_traits import normalize_trait_list


SYSTEM_PROMPT = """You are a careful Visual Places agent for illustrated books.
You receive a book-level visual identity and compact chapter plot/event notes.
Select a small set of key places / settings worth keeping visually consistent.
Separate three kinds of information for every trait:
- fact: explicitly grounded in the provided notes
- interpretation: reasonable inference from the material
- art_decision: stylistic choice not required by the text
Do not invent plot events or places absent from the inputs.
Art decisions are allowed but must use kind art_decision and low confidence.
Keep looks consistent with the visual identity when making art decisions.
Return valid JSON only."""

# Sized for ~8k local contexts (LM Studio / Gemma) with room for JSON output.
_MAX_PLOT_CHARS = 350
_MAX_EVENTS_PER_CHAPTER = 4
_MAX_EVENT_CHARS = 80
_MAX_PLACES = 8
_MAX_OUTPUT_TOKENS = 4096
_IDENTITY_TRAIT_KEYS = (
    "artistic_style",
    "color_palette",
    "atmosphere",
    "period",
    "motifs",
)
_SHEET_KEYS = ("architecture", "climate", "atmosphere", "symbols")


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


def _compact_chapters(
    chapter_analyses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Chapter evidence for places: plot + events (no characters; saves context)."""
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

        compact.append(
            {
                "chapter": analysis.get("chapter"),
                "heading": analysis.get("heading"),
                "plot": plot,
                "events": events,
            }
        )
    return compact


def _normalize_place(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    for key in _SHEET_KEYS:
        if key not in raw:
            return None
        if not isinstance(raw[key], list):
            return None

    sheet: dict[str, Any] = {"name": name.strip()}
    for key in _SHEET_KEYS:
        sheet[key] = normalize_trait_list(raw[key], label=f"{name.strip()}.{key}")
    return sheet


def _parse_places_payload(raw: str) -> list[Any]:
    data = parse_json_object(raw)
    if "places" not in data:
        raise RuntimeError("Visual places JSON missing required key 'places'")
    if not isinstance(data["places"], list):
        raise RuntimeError("Visual places JSON 'places' must be an array")
    return data["places"]


def build_visual_places(
    chapter_analyses: list[dict[str, Any]],
    identity: dict[str, Any],
    *,
    source_identity: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Build place / setting visual sheets JSON from analyses and identity.

    One LLM call with compact prompt; one JSON parse retry on truncation /
    invalid output (same damage-control pattern as visual-characters).
    """
    if not chapter_analyses:
        raise ValueError("chapter_analyses must not be empty")

    chapters_included: list[int] = []
    for analysis in chapter_analyses:
        num = analysis.get("chapter")
        if isinstance(num, int):
            chapters_included.append(num)

    identity_json = json.dumps(
        _slim_identity(identity),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    chapters_json = json.dumps(
        _compact_chapters(chapter_analyses),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    user_prompt = f"""Book visual identity (trait values only):
{identity_json}

Per-chapter notes (compact JSON: chapter + plot + events):
{chapters_json}

Return a JSON object with exactly one top-level key:
- "places": array of place / setting sheet objects

Each place sheet must have:
- "name": short stable place label grounded in the notes
- "architecture": array of trait objects (built form, interiors, materials, layout)
- "climate": array of trait objects (weather, light, season, outdoor conditions)
- "atmosphere": array of trait objects (mood / feel of the place)
- "symbols": array of trait objects (recurring visual motifs tied to this place)

Each trait object must have:
- "value": short string (under ~6 words)
- "kind": one of "fact", "interpretation", "art_decision"
- "confidence": number from 0.0 to 1.0
- "note": empty string or under ~6 words

Prefer recurring or illustration-worthy settings. Cap at {_MAX_PLACES} places.
Use exactly 2 traits per array. Keep JSON compact — no trailing commentary.
Do not add other top-level keys. Do not invent places not supported by the notes.
"""

    raw = generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        model=model,
        temperature=0.3,
        json_mode=True,
        max_output_tokens=_MAX_OUTPUT_TOKENS,
    )
    try:
        entries = _parse_places_payload(raw)
    except (json.JSONDecodeError, ValueError, RuntimeError) as first_exc:
        print("  visual-places JSON parse failed; retrying once ...")
        raw = generate_text(
            system=SYSTEM_PROMPT,
            user=user_prompt
            + "\n\nPrevious output was invalid or truncated JSON. "
            "Reply with a complete compact JSON object only.",
            model=model,
            temperature=0.1,
            json_mode=True,
            max_output_tokens=_MAX_OUTPUT_TOKENS,
        )
        try:
            entries = _parse_places_payload(raw)
        except (json.JSONDecodeError, ValueError, RuntimeError) as exc:
            raise RuntimeError(
                f"Visual places returned invalid JSON: {exc}"
            ) from first_exc

    places: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        sheet = _normalize_place(entry)
        if sheet is None:
            continue
        key = sheet["name"].casefold()
        if key in seen:
            continue
        seen.add(key)
        places.append(sheet)
        if len(places) >= _MAX_PLACES:
            break

    return {
        "source_identity": source_identity,
        "chapters_included": chapters_included,
        "places": places,
    }


__all__ = ["build_visual_places"]
