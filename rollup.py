"""Book-level structured rollup from per-chapter Reader analyses (no LLM)."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def normalize_character_key(name: str) -> str:
    """Casefold, collapse space, strip a leading 'the '."""
    key = " ".join(name.strip().split()).casefold()
    if key.startswith("the "):
        key = key[4:]
    return key


def normalize_theme_key(theme: str) -> str:
    return " ".join(theme.strip().split()).casefold()


def _pick_display_name(name_counts: Counter[str]) -> str:
    """Most frequent raw name; ties → longer, then alphabetical."""
    return max(
        name_counts.keys(),
        key=lambda n: (name_counts[n], len(n), n.casefold()),
    )


def _pick_display_theme(theme_counts: Counter[str]) -> str:
    return max(
        theme_counts.keys(),
        key=lambda t: (theme_counts[t], len(t), t.casefold()),
    )


def build_book_rollup(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge characters and themes across chapter analysis dicts.

    Characters match on normalized name (case-insensitive, optional leading
    "The "). Themes match on case-insensitive exact string. No fuzzy alias
    merge (Queen vs Queen of Hearts stay separate).
    """
    char_raw_names: dict[str, Counter[str]] = defaultdict(Counter)
    char_chapters: dict[str, set[int]] = defaultdict(set)
    char_notes: dict[str, list[str]] = defaultdict(list)
    char_notes_seen: dict[str, set[str]] = defaultdict(set)

    theme_raw: dict[str, Counter[str]] = defaultdict(Counter)
    theme_chapters: dict[str, set[int]] = defaultdict(set)

    chapters_included: list[int] = []

    for analysis in sorted(analyses, key=lambda a: int(a.get("chapter", 0))):
        chapter = int(analysis["chapter"])
        chapters_included.append(chapter)

        for entry in analysis.get("characters") or []:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not name or not isinstance(name, str):
                continue
            key = normalize_character_key(name)
            if not key:
                continue
            char_raw_names[key][name.strip()] += 1
            char_chapters[key].add(chapter)
            note = entry.get("note")
            if isinstance(note, str):
                note = note.strip()
                if note and note not in char_notes_seen[key]:
                    char_notes_seen[key].add(note)
                    char_notes[key].append(note)

        for theme in analysis.get("themes") or []:
            if not isinstance(theme, str):
                continue
            theme = theme.strip()
            if not theme:
                continue
            key = normalize_theme_key(theme)
            theme_raw[key][theme] += 1
            theme_chapters[key].add(chapter)

    characters = []
    for key in sorted(char_raw_names.keys(), key=lambda k: _pick_display_name(char_raw_names[k]).casefold()):
        characters.append(
            {
                "name": _pick_display_name(char_raw_names[key]),
                "notes": char_notes[key],
                "chapters": sorted(char_chapters[key]),
            }
        )

    themes = []
    for key in sorted(theme_raw.keys(), key=lambda k: _pick_display_theme(theme_raw[k]).casefold()):
        themes.append(
            {
                "theme": _pick_display_theme(theme_raw[key]),
                "chapters": sorted(theme_chapters[key]),
            }
        )

    return {
        "chapters_included": chapters_included,
        "characters": characters,
        "themes": themes,
    }
