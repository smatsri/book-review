"""Deterministic Markdown Extra footnote weave (no LLM)."""

from __future__ import annotations

import re
from typing import Any


def _escape_regex(text: str) -> str:
    return re.escape(text)


def weave_footnotes(summary_md: str, payload: dict[str, Any]) -> str:
    """Insert Markdown Extra footnote markers into summary text.

    For each footnote, finds the first case-insensitive whole-phrase match of
    ``anchor`` and inserts ``[^id]`` after it. Definitions are appended at the
    end. Anchors that cannot be placed go under an "Unplaced notes" list.
    """
    body = summary_md.rstrip()
    footnotes = payload.get("footnotes") or []
    if not isinstance(footnotes, list) or not footnotes:
        return body + "\n"

    placed: list[dict[str, str]] = []
    unplaced: list[dict[str, str]] = []

    for item in footnotes:
        if not isinstance(item, dict):
            continue
        note_id = item.get("id")
        anchor = item.get("anchor")
        note = item.get("note")
        kind = item.get("kind") or "concept"
        confidence = item.get("confidence") or "low"
        if (
            not isinstance(note_id, str)
            or not note_id.strip()
            or not isinstance(anchor, str)
            or not anchor.strip()
            or not isinstance(note, str)
            or not note.strip()
        ):
            continue

        note_id = note_id.strip()
        anchor = anchor.strip()
        pattern = re.compile(
            rf"(?<!\w)({_escape_regex(anchor)})(?!\w)",
            re.IGNORECASE,
        )
        match = pattern.search(body)
        if match is None:
            unplaced.append(
                {
                    "id": note_id,
                    "anchor": anchor,
                    "note": note.strip(),
                    "kind": str(kind),
                    "confidence": str(confidence),
                }
            )
            continue

        insert_at = match.end(1)
        marker = f"[^{note_id}]"
        # Avoid double-inserting the same marker at the same spot.
        if body[insert_at : insert_at + len(marker)] == marker:
            placed.append(
                {
                    "id": note_id,
                    "note": note.strip(),
                    "kind": str(kind),
                    "confidence": str(confidence),
                }
            )
            continue

        body = body[:insert_at] + marker + body[insert_at:]
        placed.append(
            {
                "id": note_id,
                "note": note.strip(),
                "kind": str(kind),
                "confidence": str(confidence),
            }
        )

    parts = [body.rstrip(), ""]

    if unplaced:
        parts.append("### Unplaced notes")
        parts.append("")
        for item in unplaced:
            parts.append(
                f"- **{item['anchor']}** ({item['kind']}, {item['confidence']}): "
                f"{item['note']}"
            )
        parts.append("")

    if placed:
        parts.append("")
        for item in placed:
            parts.append(
                f"[^{item['id']}]: ({item['kind']}; {item['confidence']}) {item['note']}"
            )
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def endnotes_markdown(payload: dict[str, Any]) -> str:
    """Format footnote JSON as a chapter-end ``### Notes`` bullet list.

    Does not place mid-body markers (anchors often target Editor summaries,
    not Gutenberg prose). Returns empty string when there are no usable notes.
    """
    footnotes = payload.get("footnotes") or []
    if not isinstance(footnotes, list) or not footnotes:
        return ""

    lines: list[str] = []
    for item in footnotes:
        if not isinstance(item, dict):
            continue
        anchor = item.get("anchor")
        note = item.get("note")
        if (
            not isinstance(anchor, str)
            or not anchor.strip()
            or not isinstance(note, str)
            or not note.strip()
        ):
            continue
        kind = item.get("kind") or "concept"
        confidence = item.get("confidence") or "low"
        lines.append(
            f"- **{anchor.strip()}** ({kind}; {confidence}): {note.strip()}"
        )

    if not lines:
        return ""
    return "### Notes\n\n" + "\n".join(lines) + "\n"


__all__ = ["weave_footnotes", "endnotes_markdown"]
