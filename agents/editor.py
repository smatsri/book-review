"""Editor agent: turn Reader analysis into human-facing Markdown."""

from __future__ import annotations

import json
from typing import Any

from agents.llm import generate_text

SYSTEM_PROMPT = """You are a careful literary Editor agent.
You receive structured analysis from a Reader agent (not the raw chapter).
Write clear Markdown for a human reader.
Be faithful to the provided analysis; do not invent events, characters, or quotes.
Keep the summary concise but complete enough to follow the plot."""


def edit_analysis(analysis: dict[str, Any], *, model: str | None = None) -> str:
    """Turn Reader JSON into a chapter Markdown document."""
    heading = analysis.get("heading") or f"Chapter {analysis.get('chapter', '?')}"
    payload = json.dumps(
        {
            "plot": analysis.get("plot", ""),
            "characters": analysis.get("characters", []),
            "themes": analysis.get("themes", []),
            "quotes": analysis.get("quotes", []),
            "events": analysis.get("events", []),
        },
        indent=2,
        ensure_ascii=False,
    )

    user_prompt = f"""Chapter: {heading}

Reader analysis (JSON):
{payload}

Produce Markdown with these sections:
1. Brief plot summary (a few paragraphs)
2. Characters who appear or are mentioned
3. Themes / motifs in this chapter
4. Notable quotes (1-3 short quotes, if any stand out)

Do not include a top-level title; the caller adds the chapter heading.
"""

    body = generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        model=model,
        temperature=0.3,
    )
    return f"# {heading}\n\n{body}\n"


__all__ = ["edit_analysis"]
