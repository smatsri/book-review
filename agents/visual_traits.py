"""Shared Visual Bible trait-row normalization."""

from __future__ import annotations

from typing import Any

KINDS = frozenset({"fact", "interpretation", "art_decision"})


def normalize_trait_list(raw: Any, *, label: str) -> list[dict[str, Any]]:
    """Keep well-formed trait rows; drop bad entries (fail closed per row)."""
    if not isinstance(raw, list):
        raise RuntimeError(f"Visual Bible JSON '{label}' must be an array")

    items: list[dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if not isinstance(value, str) or not value.strip():
            continue
        kind = entry.get("kind")
        if not isinstance(kind, str) or kind.strip() not in KINDS:
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


__all__ = ["KINDS", "normalize_trait_list"]
