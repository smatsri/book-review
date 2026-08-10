"""Alias merger agent: cluster character/theme aliases from a book rollup."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text


SYSTEM_PROMPT = """You are a careful literary Alias Merger agent.
You receive book-level character entries (name, chapter count, notes) and theme strings.
Cluster labels that refer to the same character or the same theme (true aliases only).
Do not invent names or themes that are not in the input lists.
When unsure whether two labels are the same entity, keep them separate.
Shared surnames do not mean the same person (spouses, relatives, distinct people).
Different given names usually mean different people.
Return valid JSON only."""

_MAX_NOTES_PER_CHARACTER = 2
_MAX_NOTE_CHARS = 72


def _truncate(text: str, max_chars: int) -> str:
    text = " ".join(text.strip().split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _compact_characters_for_prompt(rollup: dict[str, Any]) -> list[dict[str, Any]]:
    """Name + chapter count + short notes so the model can tell people apart."""
    out: list[dict[str, Any]] = []
    for row in rollup.get("characters") or []:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        chapters = row.get("chapters") or []
        chapter_count = (
            len([c for c in chapters if isinstance(c, int)])
            if isinstance(chapters, list)
            else 0
        )
        notes: list[str] = []
        notes_raw = row.get("notes") or []
        if isinstance(notes_raw, list):
            for note in notes_raw:
                if isinstance(note, str) and note.strip():
                    notes.append(_truncate(note, _MAX_NOTE_CHARS))
                if len(notes) >= _MAX_NOTES_PER_CHARACTER:
                    break
        entry: dict[str, Any] = {
            "name": name.strip(),
            "chapters": chapter_count,
        }
        if notes:
            entry["notes"] = notes
        out.append(entry)
    return out


def _normalize_cluster_list(
    raw: Any,
    *,
    known: set[str],
    label: str,
) -> list[list[str]]:
    """Parse LLM clusters: keep only known strings; drop overlaps and empties."""
    if not isinstance(raw, list):
        raise RuntimeError(f"Alias merger JSON '{label}' must be an array")

    used: set[str] = set()
    clusters: list[list[str]] = []

    for item in raw:
        if not isinstance(item, list):
            continue
        cluster: list[str] = []
        for entry in item:
            if not isinstance(entry, str):
                continue
            name = entry.strip()
            if not name or name not in known or name in used:
                continue
            used.add(name)
            cluster.append(name)
        if cluster:
            clusters.append(cluster)

    return clusters


def propose_alias_clusters(
    rollup: dict[str, Any],
    *,
    model: str | None = None,
) -> dict[str, list[list[str]]]:
    """Ask the LLM to cluster character/theme aliases from a rollup dict.

    Returns ``{"characters": [[...], ...], "themes": [[...], ...]}`` with only
    names/themes that appear in the rollup. Overlaps and unknown labels dropped.
    """
    char_entries = _compact_characters_for_prompt(rollup)
    char_names = [c["name"] for c in char_entries]
    theme_labels = [
        t["theme"]
        for t in rollup.get("themes") or []
        if isinstance(t, dict) and isinstance(t.get("theme"), str) and t["theme"].strip()
    ]

    known_chars = set(char_names)
    known_themes = set(theme_labels)

    chars_json = json.dumps(char_entries, ensure_ascii=False, indent=2)
    themes_json = json.dumps(theme_labels, ensure_ascii=False, indent=2)

    user_prompt = f"""Character entries from the book rollup (use the "name" strings exactly):
{chars_json}

Theme labels from the book rollup (use these exact strings only):
{themes_json}

Return a JSON object with exactly these keys:
- "characters": array of clusters; each cluster is an array of "name" strings from the character list that refer to the same person/creature. Singletons may be omitted (the code will add them).
- "themes": array of clusters; each cluster is an array of strings from the theme list that refer to the same theme/motif. Singletons may be omitted.

Rules:
- Every string in a cluster must appear exactly in the corresponding input list (character "name" or theme label).
- A name or theme may appear in at most one cluster.
- Prefer not merging when unsure.
- Do not merge people who share only a surname (e.g. spouses or relatives with different given names).
- Do not merge labels whose notes describe different roles/identities (e.g. undersecretary vs detective).
- Short forms (surname-only) may merge with the matching full name when notes agree.
- Parenthetical qualifiers like "(mentioned)" or "(imposter)" on the same core name may cluster together when notes agree; do not pull unrelated robots or codes into that cluster.
"""

    raw = generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        model=model,
        temperature=0.1,
        json_mode=True,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Alias merger returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Alias merger JSON must be an object")

    return {
        "characters": _normalize_cluster_list(
            data.get("characters"),
            known=known_chars,
            label="characters",
        ),
        "themes": _normalize_cluster_list(
            data.get("themes"),
            known=known_themes,
            label="themes",
        ),
    }


__all__ = ["propose_alias_clusters"]
