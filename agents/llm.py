"""Shared Gemini client helpers for agents."""

from __future__ import annotations

import os

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-3.5-flash"


def require_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return api_key


def resolve_model(model: str | None = None) -> str:
    return model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def generate_text(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.3,
    json_mode: bool = False,
) -> str:
    client = genai.Client(api_key=require_api_key())
    config_kwargs: dict = {
        "system_instruction": system,
        "temperature": temperature,
    }
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"

    response = client.models.generate_content(
        model=resolve_model(model),
        contents=user,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    content = response.text
    if not content:
        raise RuntimeError("Empty response from the model")
    return content.strip()
