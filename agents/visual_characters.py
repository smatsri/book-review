"""Visual Characters agent: stable character look sheets for the cast."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text
from agents.visual_traits import normalize_trait_list


SYSTEM_PROMPT = """You are a careful Visual Characters agent for illustrated books.
You receive a book-level visual identity, a cast index with notes, and compact chapter notes.
Produce stable visual sheets for the listed characters only (do not invent new names).
Separate three kinds of information for every trait:
- fact: explicitly grounded in the provided notes/index
- interpretation: reasonable inference from the material
- art_decision: stylistic choice not required by the text
Do not invent plot events or quotes absent from the inputs.
Art decisions are allowed but must use kind art_decision and low confidence.
Keep looks consistent with the visual identity when making art decisions.
Return valid JSON only."""

# Sized for ~8k local contexts (LM Studio / Qwen) with room for JSON output.
_MAX_CHARS_PER_CHAPTER = 4
_MAX_NOTE_CHARS = 60
_MAX_ROLLUP_CHARACTERS = 8
_MAX_NOTES_PER_CHARACTER = 3
_MAX_NOTE_CHARS_ROLLUP = 80
_IDENTITY_TRAIT_KEYS = (
    "artistic_style",
    "color_palette",
    "atmosphere",
    "period",
    "motifs",
)
_SHEET_KEYS = ("physical", "personality", "visual_language")


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


def _enriched_rollup_characters(rollup: dict[str, Any]) -> list[dict[str, Any]]:
    characters = rollup.get("characters") or []
    char_rows = [
        c
        for c in characters
        if isinstance(c, dict) and isinstance(c.get("name"), str) and c["name"].strip()
    ]
    char_rows.sort(key=lambda c: (-len(c.get("chapters") or []), c["name"]))

    out: list[dict[str, Any]] = []
    for row in char_rows[:_MAX_ROLLUP_CHARACTERS]:
        entry: dict[str, Any] = {"name": row["name"].strip()}
        aliases = row.get("aliases")
        if isinstance(aliases, list):
            clean = [
                a.strip()
                for a in aliases
                if isinstance(a, str) and a.strip()
            ]
            if clean:
                entry["aliases"] = clean[:5]
        notes_raw = row.get("notes") or []
        notes: list[str] = []
        if isinstance(notes_raw, list):
            for note in notes_raw:
                if isinstance(note, str) and note.strip():
                    notes.append(_truncate(note, _MAX_NOTE_CHARS_ROLLUP))
                if len(notes) >= _MAX_NOTES_PER_CHARACTER:
                    break
        entry["notes"] = notes
        chapters = row.get("chapters") or []
        if isinstance(chapters, list):
            entry["chapters"] = [
                n for n in chapters if isinstance(n, int)
            ]
        out.append(entry)
    return out


def _compact_chapters(
    chapter_analyses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Chapter evidence for looks: character name/note only (no plot; saves context)."""
    compact: list[dict[str, Any]] = []
    for analysis in chapter_analyses:
        chars_raw = analysis.get("characters") or []
        chars: list[dict[str, str]] = []
        if isinstance(chars_raw, list):
            for item in chars_raw:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue
                note = item.get("note")
                if not isinstance(note, str):
                    note = ""
                chars.append(
                    {
                        "name": name.strip(),
                        "note": _truncate(note, _MAX_NOTE_CHARS) if note else "",
                    }
                )
                if len(chars) >= _MAX_CHARS_PER_CHAPTER:
                    break

        compact.append(
            {
                "chapter": analysis.get("chapter"),
                "heading": analysis.get("heading"),
                "characters": chars,
            }
        )
    return compact

def _normalize_character(raw: Any) -> dict[str, Any] | None:
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


def build_visual_characters(
    chapter_analyses: list[dict[str, Any]],
    rollup: dict[str, Any],
    identity: dict[str, Any],
    *,
    source_rollup: str,
    source_identity: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Build character visual sheets JSON from analyses, rollup, and identity."""
    if not chapter_analyses:
        raise ValueError("chapter_analyses must not be empty")

    chapters_included: list[int] = []
    for analysis in chapter_analyses:
        num = analysis.get("chapter")
        if isinstance(num, int):
            chapters_included.append(num)

    rollup_chars = _enriched_rollup_characters(rollup)
    allowed_names = {c["name"] for c in rollup_chars}

    identity_json = json.dumps(
        _slim_identity(identity),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    rollup_json = json.dumps(
        {"characters": rollup_chars},
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

Cast index (JSON; only these characters):
{rollup_json}

Per-chapter character notes (compact JSON: chapter + character name/note only):
{chapters_json}

Return a JSON object with exactly one top-level key:
- "characters": array of character sheet objects

Each character sheet must have:
- "name": string matching a cast index name exactly
- "physical": array of trait objects (age, height, build, hair, distinctive features, etc.)
- "personality": array of trait objects (stable temperament cues useful for illustration)
- "visual_language": array of trait objects (posture, gaze, clothing, silhouette, etc.)

Each trait object must have:
- "value": short string
- "kind": one of "fact", "interpretation", "art_decision"
- "confidence": number from 0.0 to 1.0
  - 1.0 explicit in the notes/index
  - 0.7 strong inference
  - 0.4 soft interpretation
  - 0.1 pure art decision
- "note": brief rationale (may be empty string)

Prefer 2–3 short traits per array. Keep each "value" brief and each "note" under ~8 words (or empty).
Include a sheet for every cast-index character. Keep total JSON compact.
Do not add other top-level keys. Do not invent characters not in the cast index.
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
        raise RuntimeError(f"Visual characters returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Visual characters JSON must be an object")
    if "characters" not in data:
        raise RuntimeError("Visual characters JSON missing required key 'characters'")
    if not isinstance(data["characters"], list):
        raise RuntimeError("Visual characters JSON 'characters' must be an array")

    characters: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in data["characters"]:
        sheet = _normalize_character(entry)
        if sheet is None:
            continue
        if sheet["name"] not in allowed_names:
            continue
        key = sheet["name"].casefold()
        if key in seen:
            continue
        seen.add(key)
        characters.append(sheet)

    return {
        "source_rollup": source_rollup,
        "source_identity": source_identity,
        "chapters_included": chapters_included,
        "characters": characters,
    }


__all__ = ["build_visual_characters"]
