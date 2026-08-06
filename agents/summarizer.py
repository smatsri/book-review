"""Stage-1 single agent: summarize one chapter into Markdown."""

from __future__ import annotations

import os

from google import genai
from google.genai import types

from book import Chapter

DEFAULT_MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = """You are a careful literary analyst.
Summarize the given chapter of a public-domain book.
Write clear Markdown for a human reader.
Be faithful to the text; do not invent events.
Keep the summary concise but complete enough to follow the plot."""


def summarize_chapter(chapter: Chapter, *, model: str | None = None) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    client = genai.Client(api_key=api_key)
    chosen_model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

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

    response = client.models.generate_content(
        model=chosen_model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
        ),
    )

    content = response.text
    if not content:
        raise RuntimeError("Empty response from the model")

    return f"# {chapter.heading}\n\n{content.strip()}\n"


# Keep a simple package-style import path for later agents/
__all__ = ["summarize_chapter"]
