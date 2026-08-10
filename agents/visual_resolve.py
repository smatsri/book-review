"""Apply handoff answers into a locked Visual Bible (deterministic, no LLM)."""

from __future__ import annotations

import copy
from typing import Any

_QUESTION_TOPICS = frozenset({"style", "character", "place", "scene", "other"})


def _require_object(payload: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return payload


def _require_list(payload: Any, *, label: str) -> list[Any]:
    if not isinstance(payload, list):
        raise RuntimeError(f"{label} must be an array")
    return payload


def _trait_row(value: str, note: str) -> dict[str, Any]:
    return {
        "value": value.strip(),
        "kind": "art_decision",
        "confidence": 1.0,
        "note": note.strip() if isinstance(note, str) else "",
    }


def _append_trait(
    traits: list[Any],
    *,
    value: str,
    note: str,
) -> str:
    """Append art_decision trait unless identical value already present.

    Returns '' on append, or 'already_present' when skipped as duplicate.
    """
    value = value.strip()
    for entry in traits:
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("value"), str)
            and entry["value"].strip() == value
        ):
            return "already_present"
    traits.append(_trait_row(value, note))
    return ""


def _match_rows(
    rows: list[dict[str, Any]],
    *,
    key: str,
    related: list[str],
) -> list[dict[str, Any]]:
    """Match related names to rows by exact then casefold string equality."""
    if not related:
        return []
    by_exact: dict[str, dict[str, Any]] = {}
    by_fold: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = row.get(key)
        if not isinstance(name, str) or not name.strip():
            continue
        stripped = name.strip()
        by_exact.setdefault(stripped, row)
        by_fold.setdefault(stripped.casefold(), row)

    matched: list[dict[str, Any]] = []
    seen: set[int] = set()
    for label in related:
        if not isinstance(label, str) or not label.strip():
            continue
        needle = label.strip()
        row = by_exact.get(needle) or by_fold.get(needle.casefold())
        if row is None:
            continue
        row_id = id(row)
        if row_id in seen:
            continue
        seen.add(row_id)
        matched.append(row)
    return matched


def _related_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _validate_and_pair(
    handoff: dict[str, Any],
    answers: dict[str, Any],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    questions = _require_list(
        handoff.get("open_questions"),
        label="Visual handoff 'open_questions'",
    )
    answer_rows = _require_list(
        answers.get("answers"),
        label="Handoff answers 'answers'",
    )
    if len(answer_rows) != len(questions):
        raise RuntimeError(
            "Handoff answers length "
            f"({len(answer_rows)}) does not match open_questions "
            f"({len(questions)})"
        )

    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for i, (question, answer) in enumerate(zip(questions, answer_rows)):
        if not isinstance(question, dict):
            raise RuntimeError(f"open_questions[{i}] must be an object")
        if not isinstance(answer, dict):
            raise RuntimeError(f"answers[{i}] must be an object")

        q_text = question.get("question")
        if not isinstance(q_text, str):
            q_text = ""
        a_text = answer.get("question")
        if not isinstance(a_text, str):
            a_text = ""
        if q_text != a_text:
            raise RuntimeError(
                f"answers[{i}].question does not match "
                f"open_questions[{i}].question"
            )

        idx = answer.get("index")
        if idx != i:
            raise RuntimeError(
                f"answers[{i}].index must be {i}, got {idx!r}"
            )

        topic = question.get("topic")
        if not isinstance(topic, str) or topic.strip() not in _QUESTION_TOPICS:
            raise RuntimeError(
                f"open_questions[{i}].topic must be one of "
                f"{sorted(_QUESTION_TOPICS)}"
            )

        options = question.get("options")
        if options is None:
            options = []
        if not isinstance(options, list):
            raise RuntimeError(
                f"open_questions[{i}].options must be an array"
            )

        chosen = answer.get("chosen")
        if chosen is not None:
            if isinstance(chosen, bool) or not isinstance(chosen, int):
                raise RuntimeError(
                    f"answers[{i}].chosen must be an int or null"
                )
            if chosen < 0 or chosen >= len(options):
                raise RuntimeError(
                    f"answers[{i}].chosen {chosen} out of range for "
                    f"open_questions[{i}].options "
                    f"(len={len(options)})"
                )
            opt = options[chosen]
            if not isinstance(opt, str) or not opt.strip():
                raise RuntimeError(
                    f"open_questions[{i}].options[{chosen}] must be "
                    "a non-empty string"
                )

        pairs.append((question, answer))
    return pairs


def _apply_choice(
    *,
    topic: str,
    related: list[str],
    chosen_text: str,
    note: str,
    identity: dict[str, Any],
    characters: dict[str, Any],
    places: dict[str, Any],
    scenes: dict[str, Any],
) -> tuple[bool, list[str], str]:
    """Patch sheets for one answered question.

    Returns (applied, targets, reason).
    """
    targets: list[str] = []
    reasons: list[str] = []

    if topic in ("style", "other"):
        field = "artistic_style" if topic == "style" else "motifs"
        traits = identity.get(field)
        if not isinstance(traits, list):
            traits = []
            identity[field] = traits
        reason = _append_trait(traits, value=chosen_text, note=note)
        targets.append(f"identity.{field}")
        if reason:
            reasons.append(reason)
        return True, targets, reasons[0] if reasons else ""

    if topic == "character":
        rows = [
            r
            for r in (characters.get("characters") or [])
            if isinstance(r, dict)
        ]
        matched = _match_rows(rows, key="name", related=related)
        if not related:
            return False, [], "empty_related"
        if not matched:
            return False, [], "no_matching_character"
        for row in matched:
            name = str(row.get("name") or "").strip()
            traits = row.get("visual_language")
            if not isinstance(traits, list):
                traits = []
                row["visual_language"] = traits
            reason = _append_trait(traits, value=chosen_text, note=note)
            targets.append(f"characters.{name}.visual_language")
            if reason:
                reasons.append(reason)
        uniq = sorted(set(reasons))
        return True, targets, uniq[0] if len(uniq) == 1 else (
            ",".join(uniq) if uniq else ""
        )

    if topic == "place":
        rows = [
            r for r in (places.get("places") or []) if isinstance(r, dict)
        ]
        matched = _match_rows(rows, key="name", related=related)
        if not related:
            return False, [], "empty_related"
        if not matched:
            return False, [], "no_matching_place"
        for row in matched:
            name = str(row.get("name") or "").strip()
            traits = row.get("atmosphere")
            if not isinstance(traits, list):
                traits = []
                row["atmosphere"] = traits
            reason = _append_trait(traits, value=chosen_text, note=note)
            targets.append(f"places.{name}.atmosphere")
            if reason:
                reasons.append(reason)
        uniq = sorted(set(reasons))
        return True, targets, uniq[0] if len(uniq) == 1 else (
            ",".join(uniq) if uniq else ""
        )

    if topic == "scene":
        rows = [
            r for r in (scenes.get("scenes") or []) if isinstance(r, dict)
        ]
        matched = _match_rows(rows, key="title", related=related)
        if not related:
            return False, [], "empty_related"
        if not matched:
            return False, [], "no_matching_scene"
        for row in matched:
            title = str(row.get("title") or "").strip()
            traits = row.get("composition")
            if not isinstance(traits, list):
                traits = []
                row["composition"] = traits
            reason = _append_trait(traits, value=chosen_text, note=note)
            targets.append(f"scenes.{title}.composition")
            if reason:
                reasons.append(reason)
        uniq = sorted(set(reasons))
        return True, targets, uniq[0] if len(uniq) == 1 else (
            ",".join(uniq) if uniq else ""
        )

    return False, [], f"unknown_topic:{topic}"


def build_visual_resolved(
    identity: dict[str, Any],
    characters: dict[str, Any],
    places: dict[str, Any],
    scenes: dict[str, Any],
    handoff: dict[str, Any],
    answers: dict[str, Any],
    *,
    source_identity: str,
    source_characters: str,
    source_places: str,
    source_scenes: str,
    source_handoff: str,
    source_answers: str,
) -> dict[str, Any]:
    """Deep-copy bible sheets and apply answered handoff options as art_decisions."""
    identity_in = _require_object(identity, label="Visual identity")
    characters_in = _require_object(characters, label="Visual characters")
    places_in = _require_object(places, label="Visual places")
    scenes_in = _require_object(scenes, label="Visual scenes")
    handoff_in = _require_object(handoff, label="Visual handoff")
    answers_in = _require_object(answers, label="Handoff answers")

    pairs = _validate_and_pair(handoff_in, answers_in)

    identity_out = copy.deepcopy(identity_in)
    characters_out = copy.deepcopy(characters_in)
    places_out = copy.deepcopy(places_in)
    scenes_out = copy.deepcopy(scenes_in)

    resolutions: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    for i, (question, answer) in enumerate(pairs):
        q_text = question.get("question")
        if not isinstance(q_text, str):
            q_text = ""
        topic = str(question.get("topic") or "").strip()
        related = _related_list(question.get("related"))
        note = answer.get("note")
        if not isinstance(note, str):
            note = ""

        options_raw = question.get("options") or []
        if not isinstance(options_raw, list):
            options_raw = []

        chosen = answer.get("chosen")
        if chosen is None:
            unresolved.append(
                {
                    "index": i,
                    "question": q_text,
                    "reason": "unanswered",
                }
            )
            continue

        chosen_text = str(options_raw[chosen]).strip()
        applied, targets, reason = _apply_choice(
            topic=topic,
            related=related,
            chosen_text=chosen_text,
            note=note,
            identity=identity_out,
            characters=characters_out,
            places=places_out,
            scenes=scenes_out,
        )
        resolutions.append(
            {
                "index": i,
                "topic": topic,
                "related": related,
                "question": q_text,
                "chosen": chosen,
                "chosen_text": chosen_text,
                "note": note.strip(),
                "applied": applied,
                "targets": targets,
                "reason": reason,
            }
        )
        if not applied:
            unresolved.append(
                {
                    "index": i,
                    "question": q_text,
                    "reason": reason or "not_applied",
                }
            )

    return {
        "source_identity": source_identity,
        "source_characters": source_characters,
        "source_places": source_places,
        "source_scenes": source_scenes,
        "source_handoff": source_handoff,
        "source_answers": source_answers,
        "identity": identity_out,
        "characters": characters_out,
        "places": places_out,
        "scenes": scenes_out,
        "resolutions": resolutions,
        "unresolved": unresolved,
    }


def validate_answers_against_handoff(
    handoff: dict[str, Any],
    answers: dict[str, Any],
) -> None:
    """Raise RuntimeError if answers JSON does not pair with handoff questions."""
    _validate_and_pair(handoff, answers)


__all__ = ["build_visual_resolved", "validate_answers_against_handoff"]
