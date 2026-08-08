"""Deterministic enriched reading-edition binder (no LLM)."""

from __future__ import annotations

import json
from pathlib import Path

from book import BookPaths, Chapter, DEFAULT_BOOK_ID, ROOT
from footnotes import endnotes_markdown
from illustrations import illustrations_by_chapter, inject_illustrations

BOOK_TITLE = "Alice's Adventures in Wonderland"


def _chapter_body_md(chapter: Chapter) -> str:
    """Heading + Gutenberg body for one chapter."""
    body = chapter.text.strip()
    return f"# {chapter.heading}\n\n{body}"


def _chapter_endnotes(number: int, paths: BookPaths) -> str:
    path = paths.chapter_footnotes_path(number)
    if not path.exists():
        return ""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return ""
    return endnotes_markdown(payload).rstrip()


def write_book_enriched(
    chapters: list[Chapter],
    paths: BookPaths | None = None,
) -> Path:
    """Bind Gutenberg chapters + scene JPGs + footnote endnotes.

    Writes ``book-enriched.md`` under ``paths.output_dir``. Always regenerates
    (like ``report``).
    """
    if paths is None:
        paths = BookPaths(book_id=DEFAULT_BOOK_ID, root=ROOT)
    out_path = paths.book_enriched_path()
    scene_blocks = illustrations_by_chapter(
        paths.book_visual_resolved_path(), paths.illustrations_dir
    )
    parts: list[str] = []
    for ch in chapters:
        md = _chapter_body_md(ch)
        md = inject_illustrations(md, scene_blocks.get(ch.number, []))
        notes = _chapter_endnotes(ch.number, paths)
        if notes:
            md = f"{md.rstrip()}\n\n{notes}"
        parts.append(md.strip())

    header = (
        f"# {BOOK_TITLE}\n\n"
        f"Enriched edition ({len(parts)} chapters): original text with "
        f"scene illustrations and chapter endnotes.\n"
    )
    body = "\n\n---\n\n".join(parts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        f"{header.rstrip()}\n\n---\n\n{body}\n", encoding="utf-8"
    )
    return out_path


__all__ = ["BOOK_TITLE", "write_book_enriched"]
