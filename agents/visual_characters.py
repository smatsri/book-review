"""Visual Characters agent: stable character look sheets for the cast."""

from __future__ import annotations

import json
from typing import Any

from agents.json_util import parse_json_object
from agents.llm import generate_text
from agents.visual_traits import normalize_trait_list


SYSTEM_PROMPT = """You are a careful Visual Characters agent for illustrated books.
You receive a book-level visual identity, a cast batch with notes, and compact chapter notes.
Produce stable visual sheets for every listed cast character (do not invent new names).
Separate three kinds of information for every trait:
- fact: explicitly grounded in the provided notes/index
- interpretation: reasonable inference from the material
- art_decision: stylistic choice not required by the text
Do not invent plot events or quotes absent from the inputs.
Art decisions are allowed but must use kind art_decision and low confidence.
Keep looks consistent with the visual identity when making art decisions.
Return valid JSON only. Keep the JSON compact."""

# Illustration cast (not full literary rollup) + small batches for local ~8k / output limits.
_MAX_CHARS_PER_CHAPTER = 4
_MAX_NOTE_CHARS = 50
_MAX_NOTES_PER_CHARACTER = 2
_MAX_NOTE_CHARS_ROLLUP = 64
_MAX_ALIASES_PER_CHARACTER = 4
_MIN_CHAPTERS_FOR_SHEET = 3
_MAX_ILLUSTRATION_CAST = 12
_MIN_ILLUSTRATION_CAST = 8
_SHEET_BATCH_SIZE = 3
_MAX_OUTPUT_TOKENS = 3072
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


def _chapter_count(row: dict[str, Any]) -> int:
    chapters = row.get("chapters") or []
    if not isinstance(chapters, list):
        return 0
    return len([n for n in chapters if isinstance(n, int)])


def select_illustration_cast(
    rollup_characters: list[dict[str, Any]],
    *,
    min_chapters: int = _MIN_CHAPTERS_FOR_SHEET,
    max_cast: int = _MAX_ILLUSTRATION_CAST,
    min_cast: int = _MIN_ILLUSTRATION_CAST,
) -> list[dict[str, Any]]:
    """Pick illustration-worthy rows from a rollup cast (already slimmed).

    - Prefer characters appearing in ``min_chapters``+ chapters.
    - Always keep the #1-by-chapter-count character.
    - If fewer than ``min_cast`` pass the threshold, fill by chapter rank.
    - Cap at ``max_cast``.
    """
    rows = [
        c
        for c in rollup_characters
        if isinstance(c, dict) and isinstance(c.get("name"), str) and c["name"].strip()
    ]
    rows.sort(key=lambda c: (-_chapter_count(c), c["name"]))
    if not rows:
        return []

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(row: dict[str, Any]) -> None:
        name = row["name"].strip()
        key = name.casefold()
        if key in seen:
            return
        seen.add(key)
        selected.append(row)

    # Threshold pass.
    for row in rows:
        if _chapter_count(row) >= min_chapters:
            _add(row)
        if len(selected) >= max_cast:
            break

    # Hard guarantee: #1 by chapters.
    _add(rows[0])

    # Floor: fill by rank if the book has few recurring names.
    if len(selected) < min_cast:
        for row in rows:
            _add(row)
            if len(selected) >= min_cast:
                break

    selected.sort(key=lambda c: (-_chapter_count(c), c["name"]))
    return selected[:max_cast]


def _slim_rollup_row(row: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {"name": row["name"].strip()}
    aliases = row.get("aliases")
    if isinstance(aliases, list):
        clean = [
            a.strip()
            for a in aliases
            if isinstance(a, str) and a.strip()
        ]
        if clean:
            entry["aliases"] = clean[:_MAX_ALIASES_PER_CHARACTER]
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
        entry["chapters"] = [n for n in chapters if isinstance(n, int)]
    return entry


def _enriched_rollup_characters(rollup: dict[str, Any]) -> list[dict[str, Any]]:
    """Illustration cast from rollup: recurring names, capped, #1 guaranteed."""
    characters = rollup.get("characters") or []
    slim = [
        _slim_rollup_row(c)
        for c in characters
        if isinstance(c, dict) and isinstance(c.get("name"), str) and c["name"].strip()
    ]
    return select_illustration_cast(slim)


def _batch_name_keys(batch: list[dict[str, Any]]) -> set[str]:
    """Casefold names + aliases for filtering chapter evidence to this batch."""
    keys: set[str] = set()
    for row in batch:
        name = row.get("name")
        if isinstance(name, str) and name.strip():
            keys.add(name.strip().casefold())
        aliases = row.get("aliases") or []
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str) and alias.strip():
                    keys.add(alias.strip().casefold())
    return keys


def _compact_chapters_for_batch(
    chapter_analyses: list[dict[str, Any]],
    *,
    batch_keys: set[str],
) -> list[dict[str, Any]]:
    """Chapter evidence for looks, filtered to names/aliases in this batch."""
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
                if name.strip().casefold() not in batch_keys:
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

        if not chars:
            continue
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


def _chunks(
    rows: list[dict[str, Any]], size: int
) -> list[list[dict[str, Any]]]:
    if size <= 0:
        raise ValueError("batch size must be positive")
    return [rows[i : i + size] for i in range(0, len(rows), size)]


def _parse_characters_payload(raw: str) -> list[Any]:
    data = parse_json_object(raw)
    if "characters" not in data:
        raise RuntimeError(
            "Visual characters JSON missing required key 'characters'"
        )
    if not isinstance(data["characters"], list):
        raise RuntimeError(
            "Visual characters JSON 'characters' must be an array"
        )
    return data["characters"]


def _generate_character_batch(
    *,
    identity: dict[str, Any],
    batch: list[dict[str, Any]],
    chapter_analyses: list[dict[str, Any]],
    allowed_names: set[str],
    model: str | None,
) -> list[dict[str, Any]]:
    batch_keys = _batch_name_keys(batch)
    identity_json = json.dumps(
        _slim_identity(identity),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    rollup_json = json.dumps(
        {"characters": batch},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    chapters_json = json.dumps(
        _compact_chapters_for_batch(chapter_analyses, batch_keys=batch_keys),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    must_names = [row["name"] for row in batch]

    user_prompt = f"""Book visual identity (trait values only):
{identity_json}

Cast batch (JSON; produce a sheet for every name below):
{rollup_json}

Required names (exact strings): {json.dumps(must_names, ensure_ascii=False)}

Per-chapter character notes for this batch (compact JSON):
{chapters_json}

Return a JSON object with exactly one top-level key:
- "characters": array of character sheet objects

Each character sheet must have:
- "name": string matching a cast batch name exactly
- "physical": array of trait objects
- "personality": array of trait objects
- "visual_language": array of trait objects

Each trait object must have:
- "value": short string (under ~6 words)
- "kind": one of "fact", "interpretation", "art_decision"
- "confidence": number from 0.0 to 1.0
- "note": empty string or under ~6 words

Use exactly 2 traits per array. Keep JSON compact — no trailing commentary.
Include a sheet for every required name.
Do not add other top-level keys. Do not invent characters not in the cast batch.
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
        entries = _parse_characters_payload(raw)
    except (json.JSONDecodeError, ValueError, RuntimeError) as first_exc:
        print(
            "  visual-characters batch JSON parse failed; retrying once ..."
        )
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
            entries = _parse_characters_payload(raw)
        except (json.JSONDecodeError, ValueError, RuntimeError) as exc:
            raise RuntimeError(
                f"Visual characters returned invalid JSON: {exc}"
            ) from first_exc

    characters: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
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
    return characters


def build_visual_characters(
    chapter_analyses: list[dict[str, Any]],
    rollup: dict[str, Any],
    identity: dict[str, Any],
    *,
    source_rollup: str,
    source_identity: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Build character visual sheets JSON from analyses, rollup, and identity.

    Selects an illustration cast (recurring names, capped; #1-by-chapters
    always kept). Generates sheets in small batches with one JSON retry and
    one missing-name retry pass.
    """
    if not chapter_analyses:
        raise ValueError("chapter_analyses must not be empty")

    chapters_included: list[int] = []
    for analysis in chapter_analyses:
        num = analysis.get("chapter")
        if isinstance(num, int):
            chapters_included.append(num)

    rollup_chars = _enriched_rollup_characters(rollup)
    if not rollup_chars:
        raise RuntimeError("Rollup has no characters to sheet")

    print(
        f"  illustration cast: {len(rollup_chars)} "
        f"(min {_MIN_CHAPTERS_FOR_SHEET}+ chapters, "
        f"cap {_MAX_ILLUSTRATION_CAST})"
    )
    for row in rollup_chars:
        print(f"    - {row['name']} ({_chapter_count(row)} ch)")

    allowed_names = {c["name"] for c in rollup_chars}
    by_name = {c["name"]: c for c in rollup_chars}
    collected: dict[str, dict[str, Any]] = {}

    batches = _chunks(rollup_chars, _SHEET_BATCH_SIZE)
    for index, batch in enumerate(batches, start=1):
        print(
            f"  visual-characters batch {index}/{len(batches)} "
            f"({len(batch)} characters) ..."
        )
        for sheet in _generate_character_batch(
            identity=identity,
            batch=batch,
            chapter_analyses=chapter_analyses,
            allowed_names=allowed_names,
            model=model,
        ):
            collected[sheet["name"]] = sheet

    missing = [name for name in allowed_names if name not in collected]
    if missing:
        print(
            f"  visual-characters retry for {len(missing)} missing "
            f"name(s) ..."
        )
        retry_rows = [by_name[name] for name in missing if name in by_name]
        for batch in _chunks(retry_rows, 2):
            for sheet in _generate_character_batch(
                identity=identity,
                batch=batch,
                chapter_analyses=chapter_analyses,
                allowed_names=allowed_names,
                model=model,
            ):
                collected[sheet["name"]] = sheet

    still_missing = sorted(
        name for name in allowed_names if name not in collected
    )
    if still_missing:
        raise RuntimeError(
            "Visual characters incomplete after retry; missing: "
            + ", ".join(still_missing)
        )

    characters = [collected[c["name"]] for c in rollup_chars]
    return {
        "source_rollup": source_rollup,
        "source_identity": source_identity,
        "chapters_included": chapters_included,
        "characters": characters,
    }


__all__ = ["build_visual_characters", "select_illustration_cast"]
