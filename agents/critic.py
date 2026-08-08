"""Critic agent: review draft summary against chapter and Reader notes."""

from __future__ import annotations

import json
from typing import Any

from agents.json_util import parse_json_object
from agents.llm import generate_text
from book import Chapter

SYSTEM_PROMPT = """You are a careful literary Critic agent.
You review a draft chapter summary against the chapter text and Reader notes.
Find gaps, unsupported claims, wrong order, weak or invented quotes/themes.
Be concrete and evidence-based. Do not rewrite the summary — that is the Editor's job.
Return valid JSON only.
Keep detail, must_fix, and optional_improve strings short (one sentence each, single line).
Do not nest quotes, markdown fences, or multi-line strings inside JSON values."""

_MAX_OUTPUT_TOKENS = 4096
_RAW_SNIPPET = 400


def critique_draft(
    chapter: Chapter,
    analysis: dict[str, Any],
    draft_markdown: str,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """Critique a draft; return a JSON-serializable dict."""
    notes = json.dumps(
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

    user_prompt = f"""Chapter: {chapter.heading}

Chapter text:
---
{chapter.text}
---

Reader analysis (JSON):
{notes}

Draft summary (Markdown):
---
{draft_markdown}
---

Return a JSON object with exactly these keys:
- "verdict": string — one of "ok", "needs_fixes" (use needs_fixes if any must_fix item exists)
- "issues": array of objects, each with:
  - "severity": string — one of "plot", "characters", "themes", "quotes", "events", "other"
  - "severity": string — one of "missing", "unsupported", "wrong_order", "weak", "other"
  - "detail": string — what is wrong and where evidence is in the chapter (one short sentence)
- "must_fix": array of strings — concrete changes required before publishing (short single-line strings)
- "optional_improve": array of strings — nice-to-have improvements (short single-line strings)
"""

    data: dict[str, Any] | None = None
    last_raw = ""
    last_exc: Exception | None = None
    for _attempt in range(2):
        last_raw = generate_text(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            model=model,
            temperature=0.2,
            json_mode=True,
            max_output_tokens=_MAX_OUTPUT_TOKENS,
        )
        try:
            data = parse_json_object(last_raw)
            break
        except (json.JSONDecodeError, ValueError) as exc:
            last_exc = exc

    if data is None:
        snippet = last_raw[:_RAW_SNIPPET].replace("\n", "\\n")
        raise RuntimeError(
            f"Critic returned invalid JSON: {last_exc}; "
            f"raw snippet: {snippet!r}"
        ) from last_exc

    must_fix = data.get("must_fix") or []
    if not isinstance(must_fix, list):
        must_fix = []
    verdict = data.get("verdict") or ("needs_fixes" if must_fix else "ok")
    if must_fix and verdict == "ok":
        verdict = "needs_fixes"

    return {
        "chapter": chapter.number,
        "heading": chapter.heading,
        "verdict": verdict,
        "issues": data.get("issues") or [],
        "must_fix": must_fix,
        "optional_improve": data.get("optional_improve") or [],
    }


__all__ = ["critique_draft"]
