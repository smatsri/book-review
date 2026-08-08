"""Deterministic enriched reading-edition binder (no LLM)."""

from __future__ import annotations

import json
from pathlib import Path

from book import Chapter
from footnotes import endnotes_markdown
from illustrations import illustrations_by_chapter, inject_illustrations

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
STATE_DIR = ROOT / "state"
ILLUSTRATIONS_DIR = OUTPUT_DIR / "illustrations"
BOOK_ENRICHED_PATH = OUTPUT_DIR / "book-enriched.md"
BOOK_VISUAL_RESOLVED_PATH = STATE_DIR / "book-visual-resolved.json"

BOOK_TITLE = "Alice's Adventures in Wonderland"


def chapter_footnotes_path(number: int) -> Path:
    return STATE_DIR / f"chapter-{number:02d}-footnotes.json"


def _chapter_body_md(chapter: Chapter) -> str:
    """Heading + Gutenberg body for one chapter."""
    body = chapter.text.strip()
    return f"# {chapter.heading}\n\n{body}"


def _chapter_endnotes(number: int) -> str:
    path = chapter_footnotes_path(number)
    if not path.exists():
        return ""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ""
    return endnotes_markdown(payload).rstrip()


def write_book_enriched(chapters: list[Chapter]) -> Path:
    """Bind Gutenberg chapters + scene JPGs + footnote endnotes.

    Writes ``output/book-enriched.md``. Always regenerates (like ``report``).
    """
    scene_blocks = illustrations_by_chapter(
        BOOK_VISUAL_RESOLVED_PATH, ILLUSTRATIONS_DIR
    )
    parts: list[str] = []
    for ch in chapters:
        md = _chapter_body_md(ch)
        md = inject_illustrations(md, scene_blocks.get(ch.number, []))
        notes = _chapter_endnotes(ch.number)
        if notes:
            md = f"{md.rstrip()}\n\n{notes}"
        parts.append(md.strip())

    header = (
        f"# {BOOK_TITLE}\n\n"
        f"Enriched edition ({len(parts)} chapters): original text with "
        f"scene illustrations and chapter endnotes.\n"
    )
    body = "\n\n---\n\n".join(parts)
    BOOK_ENRICHED_PATH.parent.mkdir(parents=True, exist_ok=True)
    BOOK_ENRICHED_PATH.write_text(
        f"{header.rstrip()}\n\n---\n\n{body}\n", encoding="utf-8"
    )
    return BOOK_ENRICHED_PATH


__all__ = ["BOOK_ENRICHED_PATH", "BOOK_TITLE", "write_book_enriched"]
