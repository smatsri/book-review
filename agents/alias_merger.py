"""Alias merger agent: cluster character/theme aliases from a book rollup."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text

SYSTEM_PROMPT = """You are a careful literary Alias Merger agent.
You receive book-level character names and theme strings extracted from chapter analyses.
Cluster labels that refer to the same character or the same theme (true aliases only).
Do not invent names or themes that are not in the input lists.
When unsure whether two labels are the same entity, keep them separate.
Return valid JSON only."""


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
    char_names = [
        c["name"]
        for c in rollup.get("characters") or []
        if isinstance(c, dict) and isinstance(c.get("name"), str) and c["name"].strip()
    ]
    theme_labels = [
        t["theme"]
        for t in rollup.get("themes") or []
        if isinstance(t, dict) and isinstance(t.get("theme"), str) and t["theme"].strip()
    ]

    known_chars = set(char_names)
    known_themes = set(theme_labels)

    user_prompt = f"""Character names from the book rollup (use these exact strings only):
{json.dumps(char_names, ensure_ascii=False, indent=2)}

Theme labels from the book rollup (use these exact strings only):
{json.dumps(theme_labels, ensure_ascii=False, indent=2)}

Return a JSON object with exactly these keys:
- "characters": array of clusters; each cluster is an array of strings from the character list that refer to the same person/creature. Singletons may be omitted (the code will add them).
- "themes": array of clusters; each cluster is an array of strings from the theme list that refer to the same theme/motif. Singletons may be omitted.

Rules:
- Every string in a cluster must appear exactly in the corresponding input list.
- A name or theme may appear in at most one cluster.
- Prefer not merging when unsure.
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
