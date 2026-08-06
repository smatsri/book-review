"""Reducer agent: book-level synthesis from chapter analyses + rollup."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text

SYSTEM_PROMPT = """You are a careful literary Reducer agent.
You receive compact per-chapter Reader notes and a book-level character/theme index.
Write a short whole-book overview in Markdown for a human reader.
Be faithful to the provided material; do not invent plot events, characters, or quotes.
Do not invent author biography, publication history, or outside-book facts.
Ground every claim in the chapter notes or rollup index."""

# Keep payloads small enough for ~8k local contexts (Alice-sized books).
_MAX_PLOT_CHARS = 450
_MAX_THEMES_PER_CHAPTER = 5
_MAX_ROLLUP_CHARACTERS = 20
_MAX_ROLLUP_THEMES = 15


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


def synthesize_book(
    chapter_analyses: list[dict[str, Any]],
    rollup: dict[str, Any],
    *,
    model: str | None = None,
) -> str:
    """Synthesize book-level Markdown from Reader analyses and a rollup dict."""
    if not chapter_analyses:
        raise ValueError("chapter_analyses must not be empty")

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

Produce Markdown with exactly these sections and headings:
# Book overview
(2–4 short paragraphs introducing the book as a whole)

## Plot arc
(coherent arc across chapters; no chapter-by-chapter dump)

## Characters
(main cast across the book; use index names when helpful)

## Themes / motifs
(cross-chapter themes; use index themes when helpful)

## Closing note
(one short paragraph)

Do not add other top-level sections. Do not invent material absent from the inputs.
"""

    body = generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        model=model,
        temperature=0.3,
    )
    return body.strip() + "\n"


__all__ = ["synthesize_book"]
