"""Reader agent: extract structured analysis from one chapter."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text
from book import Chapter

SYSTEM_PROMPT = """You are a careful literary Reader agent.
Read the chapter and extract structured analysis only.
Be faithful to the text; do not invent events, characters, or quotes.
Do not write polished prose for a human audience — that is the Editor's job.
Return valid JSON only."""


def read_chapter(chapter: Chapter, *, model: str | None = None) -> dict[str, Any]:
    """Analyze a chapter; return a JSON-serializable dict."""
    user_prompt = f"""Chapter: {chapter.heading}

---
{chapter.text}
---

Return a JSON object with exactly these keys:
- "plot": string — concise plot summary (a few paragraphs as one string)
- "characters": array of objects, each with "name" (string) and "note" (string: role/appearance)
- "themes": array of strings — themes or motifs in this chapter
- "quotes": array of strings — 1-3 short notable quotes, or empty if none stand out
- "events": array of strings — key events in order
"""

    raw = generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        model=model,
        temperature=0.2,
        json_mode=True,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Reader returned invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Reader JSON must be an object")

    return {
        "chapter": chapter.number,
        "heading": chapter.heading,
        "plot": data.get("plot", ""),
        "characters": data.get("characters", []),
        "themes": data.get("themes", []),
        "quotes": data.get("quotes", []),
        "events": data.get("events", []),
    }


__all__ = ["read_chapter"]
