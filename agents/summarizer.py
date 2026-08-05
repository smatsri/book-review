"""Stage-1 single agent: summarize one chapter into Markdown."""

from __future__ import annotations

import os

from openai import OpenAI

from book import Chapter

DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are a careful literary analyst.
Summarize the given chapter of a public-domain book.
Write clear Markdown for a human reader.
Be faithful to the text; do not invent events.
Keep the summary concise but complete enough to follow the plot."""


def summarize_chapter(chapter: Chapter, *, model: str | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    client = OpenAI(api_key=api_key)
    chosen_model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    user_prompt = f"""Chapter: {chapter.heading}

---
{chapter.text}
---

Produce Markdown with these sections:
1. Brief plot summary (a few paragraphs)
2. Characters who appear or are mentioned
3. Themes / motifs in this chapter
4. Notable quotes (1-3 short quotes, if any stand out)
"""

    response = client.chat.completions.create(
        model=chosen_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from the model")

    return f"# {chapter.heading}\n\n{content.strip()}\n"


# Keep a simple package-style import path for later agents/
__all__ = ["summarize_chapter"]
