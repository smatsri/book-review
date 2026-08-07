"""Visual Handoff agent: open questions + consistency pass over the Visual Bible."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text


SYSTEM_PROMPT = """You are a careful Visual Handoff agent for illustrated books.
You receive a book-level visual identity plus character sheets, place sheets, and scene briefs.
Your job is to prepare a handoff artifact for an illustrator or image system:
- List open questions the bible has not settled (do not invent fake certainty).
- For each open question, offer 2–3 concrete mutually exclusive art options so a human can pick.
- Optionally mark one option as suggested (preferred default), still as a proposal only.
- Flag soft consistency issues (style clashes, ambiguous looks, conflicting traits).
Do not rewrite the bible sheets. Do not invent plot or characters absent from the inputs.
Return valid JSON only."""

_MAX_QUESTIONS = 12
_MAX_ISSUES = 12
_MAX_RELATED = 6
_MAX_OPTIONS = 3
_MAX_TRAITS_PER_KEY = 4
_IDENTITY_TRAIT_KEYS = (
    "artistic_style",
    "color_palette",
    "atmosphere",
    "period",
    "motifs",
)
_CHARACTER_TRAIT_KEYS = ("physical", "personality", "visual_language")
_PLACE_TRAIT_KEYS = ("architecture", "climate", "atmosphere", "symbols")
_SCENE_TRAIT_KEYS = ("emotional_focus", "composition")
_QUESTION_TOPICS = frozenset({"style", "character", "place", "scene", "other"})
_ISSUE_SEVERITIES = frozenset(
    {"conflict", "gap", "name_mismatch", "ambiguity"}
)


def _trait_values(raw: Any, *, limit: int = _MAX_TRAITS_PER_KEY) -> list[str]:
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


def _sheet_rows(payload: dict[str, Any], *, key: str) -> list[dict[str, Any]]:
    rows = payload.get(key) or []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _sheet_name_set(payload: dict[str, Any], *, key: str) -> set[str]:
    names: set[str] = set()
    for row in _sheet_rows(payload, key=key):
        name = row.get("name")
        if isinstance(name, str) and name.strip():
            names.add(name.strip().casefold())
    return names


def _slim_characters(payload: dict[str, Any]) -> list[dict[str, Any]]:
    slim: list[dict[str, Any]] = []
    for row in _sheet_rows(payload, key="characters"):
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        entry: dict[str, Any] = {"name": name.strip()}
        for key in _CHARACTER_TRAIT_KEYS:
            entry[key] = _trait_values(row.get(key))
        slim.append(entry)
    return slim


def _slim_places(payload: dict[str, Any]) -> list[dict[str, Any]]:
    slim: list[dict[str, Any]] = []
    for row in _sheet_rows(payload, key="places"):
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        entry: dict[str, Any] = {"name": name.strip()}
        for key in _PLACE_TRAIT_KEYS:
            entry[key] = _trait_values(row.get(key))
        slim.append(entry)
    return slim


def _slim_scenes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    slim: list[dict[str, Any]] = []
    for row in _sheet_rows(payload, key="scenes"):
        title = row.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        chapter = row.get("chapter")
        characters = row.get("characters") or []
        location = row.get("location") or []
        entry: dict[str, Any] = {
            "title": title.strip(),
            "chapter": chapter if isinstance(chapter, int) else None,
            "characters": [
                c.strip()
                for c in characters
                if isinstance(c, str) and c.strip()
            ]
            if isinstance(characters, list)
            else [],
            "location": [
                loc.strip()
                for loc in location
                if isinstance(loc, str) and loc.strip()
            ]
            if isinstance(location, list)
            else [],
        }
        for key in _SCENE_TRAIT_KEYS:
            entry[key] = _trait_values(row.get(key))
        slim.append(entry)
    return slim


def _normalize_related(raw: Any) -> list[str]:
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
        if len(out) >= _MAX_RELATED:
            break
    return out


def _normalize_options(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, str):
            continue
        text = entry.strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= _MAX_OPTIONS:
            break
    return out


def _normalize_suggested(raw: Any, *, option_count: int) -> int | None:
    if option_count <= 0:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int):
        return None
    if raw < 0 or raw >= option_count:
        return None
    return raw


def _normalize_question(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    question = raw.get("question")
    if not isinstance(question, str) or not question.strip():
        return None
    topic = raw.get("topic")
    if not isinstance(topic, str) or topic.strip().casefold() not in _QUESTION_TOPICS:
        return None
    note = raw.get("note")
    if note is None:
        note = ""
    if not isinstance(note, str):
        return None
    options = _normalize_options(raw.get("options"))
    item: dict[str, Any] = {
        "question": question.strip(),
        "topic": topic.strip().casefold(),
        "related": _normalize_related(raw.get("related")),
        "note": note.strip(),
        "options": options,
    }
    suggested = _normalize_suggested(raw.get("suggested"), option_count=len(options))
    if suggested is not None:
        item["suggested"] = suggested
    return item


def _normalize_issue(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    summary = raw.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return None
    severity = raw.get("severity")
    if (
        not isinstance(severity, str)
        or severity.strip().casefold() not in _ISSUE_SEVERITIES
    ):
        return None
    suggestion = raw.get("suggestion")
    if suggestion is None:
        suggestion = ""
    if not isinstance(suggestion, str):
        return None
    return {
        "summary": summary.strip(),
        "severity": severity.strip().casefold(),
        "related": _normalize_related(raw.get("related")),
        "suggestion": suggestion.strip(),
    }


def _dedupe_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for issue in issues:
        key = issue["summary"].casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(issue)
        if len(out) >= _MAX_ISSUES:
            break
    return out


def _trait_lists_empty(row: dict[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        values = _trait_values(row.get(key), limit=1)
        if values:
            return False
    return True


def _deterministic_issues(
    characters_payload: dict[str, Any],
    places_payload: dict[str, Any],
    scenes_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    character_names = _sheet_name_set(characters_payload, key="characters")
    place_names = _sheet_name_set(places_payload, key="places")

    for row in _sheet_rows(characters_payload, key="characters"):
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        if _trait_lists_empty(row, _CHARACTER_TRAIT_KEYS):
            issues.append(
                {
                    "summary": f"Character sheet '{name.strip()}' has no traits",
                    "severity": "gap",
                    "related": [name.strip()],
                    "suggestion": "Re-run visual-characters or fill physical/personality/visual_language",
                }
            )

    for row in _sheet_rows(places_payload, key="places"):
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        if _trait_lists_empty(row, _PLACE_TRAIT_KEYS):
            issues.append(
                {
                    "summary": f"Place sheet '{name.strip()}' has no traits",
                    "severity": "gap",
                    "related": [name.strip()],
                    "suggestion": "Re-run visual-places or fill architecture/climate/atmosphere/symbols",
                }
            )

    seen_titles: set[str] = set()
    for row in _sheet_rows(scenes_payload, key="scenes"):
        title = row.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        title_clean = title.strip()
        title_key = title_clean.casefold()
        if title_key in seen_titles:
            issues.append(
                {
                    "summary": f"Duplicate scene title '{title_clean}'",
                    "severity": "conflict",
                    "related": [title_clean],
                    "suggestion": "Rename or drop the duplicate scene brief",
                }
            )
        else:
            seen_titles.add(title_key)

        characters = row.get("characters") or []
        if isinstance(characters, list):
            for name in characters:
                if not isinstance(name, str) or not name.strip():
                    continue
                if name.strip().casefold() not in character_names:
                    issues.append(
                        {
                            "summary": (
                                f"Scene '{title_clean}' character "
                                f"'{name.strip()}' missing from character sheets"
                            ),
                            "severity": "name_mismatch",
                            "related": [title_clean, name.strip()],
                            "suggestion": "Align scene cast with visual-characters names",
                        }
                    )

        locations = row.get("location") or []
        if isinstance(locations, list):
            for loc in locations:
                if not isinstance(loc, str) or not loc.strip():
                    continue
                if loc.strip().casefold() not in place_names:
                    issues.append(
                        {
                            "summary": (
                                f"Scene '{title_clean}' location "
                                f"'{loc.strip()}' missing from place sheets"
                            ),
                            "severity": "name_mismatch",
                            "related": [title_clean, loc.strip()],
                            "suggestion": "Align scene locations with visual-places names",
                        }
                    )

        if _trait_lists_empty(row, _SCENE_TRAIT_KEYS):
            issues.append(
                {
                    "summary": f"Scene '{title_clean}' has no emotional_focus/composition traits",
                    "severity": "gap",
                    "related": [title_clean],
                    "suggestion": "Re-run visual-scenes or add composition guidance",
                }
            )

    return _dedupe_issues(issues)


def build_visual_handoff(
    identity: dict[str, Any],
    characters_payload: dict[str, Any],
    places_payload: dict[str, Any],
    scenes_payload: dict[str, Any],
    *,
    source_identity: str,
    source_characters: str,
    source_places: str,
    source_scenes: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Build handoff JSON: open questions + consistency issues over bible sheets."""
    deterministic = _deterministic_issues(
        characters_payload, places_payload, scenes_payload
    )

    identity_json = json.dumps(
        _slim_identity(identity),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    characters_json = json.dumps(
        _slim_characters(characters_payload),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    places_json = json.dumps(
        _slim_places(places_payload),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    scenes_json = json.dumps(
        _slim_scenes(scenes_payload),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    known_issues_json = json.dumps(
        deterministic,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    user_prompt = f"""Book visual identity (trait values only):
{identity_json}

Character sheets (slim):
{characters_json}

Place sheets (slim):
{places_json}

Scene briefs (slim):
{scenes_json}

Deterministic consistency issues already found (do not repeat these summaries):
{known_issues_json}

Return a JSON object with exactly these top-level keys:
- "open_questions": array of question objects
- "consistency_issues": array of additional soft issue objects (may be empty)

Each open question must have:
- "question": short unresolved question for the illustrator
- "topic": one of "style", "character", "place", "scene", "other"
- "related": array of short name/title strings (may be empty)
- "note": brief rationale (may be empty string)
- "options": array of 2–3 short mutually exclusive concrete art choices (one line each)
- "suggested": optional 0-based index into options for a preferred default (omit if unsure)

Each consistency issue must have:
- "summary": short description of the clash or ambiguity
- "severity": one of "conflict", "gap", "name_mismatch", "ambiguity"
- "related": array of short name/title strings (may be empty)
- "suggestion": brief fix hint (may be empty string)

Focus open_questions on undecided art choices and low-confidence / underspecified looks.
Options must be actionable art decisions (not restatements of the question).
Focus consistency_issues on soft clashes not already listed above.
Cap at {_MAX_QUESTIONS} open_questions and {_MAX_ISSUES} consistency_issues.
Keep each string brief. Keep total JSON compact.
Do not add other top-level keys.
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
        raise RuntimeError(f"Visual handoff returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Visual handoff JSON must be an object")
    for key in ("open_questions", "consistency_issues"):
        if key not in data:
            raise RuntimeError(f"Visual handoff JSON missing required key '{key}'")
        if not isinstance(data[key], list):
            raise RuntimeError(f"Visual handoff JSON '{key}' must be an array")

    questions: list[dict[str, Any]] = []
    seen_questions: set[str] = set()
    for entry in data["open_questions"]:
        item = _normalize_question(entry)
        if item is None:
            continue
        key = item["question"].casefold()
        if key in seen_questions:
            continue
        seen_questions.add(key)
        questions.append(item)
        if len(questions) >= _MAX_QUESTIONS:
            break

    llm_issues: list[dict[str, Any]] = []
    for entry in data["consistency_issues"]:
        item = _normalize_issue(entry)
        if item is None:
            continue
        llm_issues.append(item)

    issues = _dedupe_issues(deterministic + llm_issues)

    return {
        "source_identity": source_identity,
        "source_characters": source_characters,
        "source_places": source_places,
        "source_scenes": source_scenes,
        "open_questions": questions,
        "consistency_issues": issues,
    }


__all__ = ["build_visual_handoff"]
