"""Shared helpers for parsing LLM JSON responses."""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*\n?(.*?)\n?\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)


def parse_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object from model output; strip optional markdown fences."""
    text = (raw or "").strip()
    match = _FENCE_RE.match(text)
    if match:
        text = match.group(1).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON must be an object")
    return data


__all__ = ["parse_json_object"]
