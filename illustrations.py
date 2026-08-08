"""Deterministic scene-illustration weave for the book report (no LLM)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_resolved_scenes(resolved_path: Path) -> list[dict[str, Any]]:
    """Return the ordered scene list from book-visual-resolved.json."""
    if not resolved_path.exists():
        return []
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    scenes_obj = payload.get("scenes")
    if not isinstance(scenes_obj, dict):
        return []
    scenes = scenes_obj.get("scenes")
    if not isinstance(scenes, list):
        return []
    return [s for s in scenes if isinstance(s, dict)]


def find_scene_image(
    illustrations_dir: Path, index_1based: int, chapter: int
) -> Path | None:
    """Resolve ``scene-NN-chCC-*.jpg`` for a 1-based scene index and chapter."""
    if not illustrations_dir.is_dir():
        return None
    pattern = f"scene-{index_1based:02d}-ch{chapter:02d}-*.jpg"
    matches = sorted(illustrations_dir.glob(pattern))
    return matches[0] if matches else None


def markdown_for_scene(title: str, rel_path: str) -> str:
    """Markdown image + italic caption for one scene."""
    safe_title = title.strip() or "Scene"
    return f"![{safe_title}]({rel_path})\n\n*{safe_title}*"


def inject_illustrations(chapter_md: str, blocks: list[str]) -> str:
    """Insert illustration blocks after the first ``#`` heading line."""
    if not blocks:
        return chapter_md
    text = chapter_md.strip()
    lines = text.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("#"):
            insert_at = i + 1
            break
    illustration = "\n\n".join(blocks)
    before = "\n".join(lines[:insert_at]).rstrip()
    after = "\n".join(lines[insert_at:]).lstrip()
    if after:
        return f"{before}\n\n{illustration}\n\n{after}"
    return f"{before}\n\n{illustration}"


def illustrations_by_chapter(
    resolved_path: Path, illustrations_dir: Path
) -> dict[int, list[str]]:
    """Map chapter number → markdown blocks (resolved-list order)."""
    by_chapter: dict[int, list[str]] = defaultdict(list)
    scenes = load_resolved_scenes(resolved_path)
    for i, scene in enumerate(scenes):
        chapter = scene.get("chapter")
        title = scene.get("title")
        if not isinstance(chapter, int) or chapter < 1:
            continue
        if not isinstance(title, str) or not title.strip():
            continue
        image = find_scene_image(illustrations_dir, i + 1, chapter)
        if image is None:
            continue
        rel = f"illustrations/{image.name}"
        by_chapter[chapter].append(markdown_for_scene(title, rel))
    return dict(by_chapter)
