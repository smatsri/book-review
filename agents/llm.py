"""Shared LLM helpers for agents (Gemini or LM Studio)."""

from __future__ import annotations

import os

from google import genai
from google.genai import types
from openai import OpenAI

DEFAULT_PROVIDER = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_LMSTUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
DEFAULT_LMSTUDIO_MODEL = "google/gemma-4-12b"
DEFAULT_LMSTUDIO_API_KEY = "lm-studio"


def resolve_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if provider not in {"gemini", "lmstudio"}:
        raise RuntimeError(
            f"Unknown LLM_PROVIDER={provider!r}. Use 'gemini' or 'lmstudio'."
        )
    return provider


def require_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return api_key


def resolve_gemini_model(model: str | None = None) -> str:
    return model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def resolve_lmstudio_model(model: str | None = None) -> str:
    return model or os.getenv("LMSTUDIO_MODEL", DEFAULT_LMSTUDIO_MODEL)


def _generate_gemini(
    *,
    system: str,
    user: str,
    model: str | None,
    temperature: float,
    json_mode: bool,
    max_output_tokens: int | None,
) -> str:
    client = genai.Client(api_key=require_gemini_api_key())
    config_kwargs: dict = {
        "system_instruction": system,
        "temperature": temperature,
    }
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if max_output_tokens is not None:
        config_kwargs["max_output_tokens"] = max_output_tokens

    response = client.models.generate_content(
        model=resolve_gemini_model(model),
        contents=user,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    content = response.text
    if not content:
        raise RuntimeError("Empty response from the model")
    return content.strip()


def _generate_lmstudio(
    *,
    system: str,
    user: str,
    model: str | None,
    temperature: float,
    json_mode: bool,
    max_output_tokens: int | None,
) -> str:
    base_url = os.getenv("LMSTUDIO_BASE_URL", DEFAULT_LMSTUDIO_BASE_URL)
    api_key = os.getenv("LMSTUDIO_API_KEY", DEFAULT_LMSTUDIO_API_KEY)
    client = OpenAI(base_url=base_url, api_key=api_key)

    kwargs: dict = {
        "model": resolve_lmstudio_model(model),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if max_output_tokens is not None:
        kwargs["max_tokens"] = max_output_tokens
    if json_mode:
        # LM Studio accepts json_schema / text, not OpenAI's json_object.
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "schema": {"type": "object", "additionalProperties": True},
            },
        }

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise RuntimeError("Empty response from the model")
    return content.strip()


def generate_text(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.3,
    json_mode: bool = False,
    max_output_tokens: int | None = None,
) -> str:
    provider = resolve_provider()
    if provider == "gemini":
        return _generate_gemini(
            system=system,
            user=user,
            model=model,
            temperature=temperature,
            json_mode=json_mode,
            max_output_tokens=max_output_tokens,
        )
    return _generate_lmstudio(
        system=system,
        user=user,
        model=model,
        temperature=temperature,
        json_mode=json_mode,
        max_output_tokens=max_output_tokens,
    )
