"""Filesystem pipeline status for the local operator UI (no LLM)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from book import BookMeta, BookPaths, ROOT, load_catalog, require_book_id


def _cli(command: str, book_id: str) -> str:
    return f"python main.py {command} --book {book_id}"


def _presence(path: Path) -> str:
    return "done" if path.is_file() else "missing"


def _count_state(present: int, total: int) -> str:
    if total <= 0 or present <= 0:
        return "missing"
    if present >= total:
        return "done"
    return "partial"


def _export_state(paths: list[Path]) -> tuple[str, dict[str, bool]]:
    flags = {p.name: p.is_file() for p in paths}
    n = sum(1 for ok in flags.values() if ok)
    if n == 0:
        return "missing", flags
    if n == len(paths):
        return "done", flags
    return "partial", flags


def _chapter_numbers(paths: BookPaths) -> list[int] | None:
    path = paths.chapters_json_path()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, list):
        return None
    numbers: list[int] = []
    for row in raw:
        if isinstance(row, dict) and isinstance(row.get("number"), int):
            numbers.append(row["number"])
    return numbers


def _stage(
    stage_id: str,
    label: str,
    status: str,
    *,
    cli: str,
    detail: str | None = None,
    counts: dict[str, Any] | None = None,
    files: dict[str, bool] | None = None,
    links: dict[str, str] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": stage_id,
        "label": label,
        "status": status,
        "cli": cli,
    }
    if detail is not None:
        row["detail"] = detail
    if counts is not None:
        row["counts"] = counts
    if files is not None:
        row["files"] = files
    if links is not None:
        row["links"] = links
    return row


def build_pipeline_status(book_id: str, root: Path = ROOT) -> dict[str, Any]:
    """Scan state/output for one catalog book; return JSON-serializable status."""
    meta: BookMeta = require_book_id(book_id, root=root)
    paths = BookPaths(book_id=meta.id, root=root)
    numbers = _chapter_numbers(paths)
    chapter_count = len(numbers) if numbers is not None else 0
    chapter_nums = numbers or []

    stages: list[dict[str, Any]] = []

    chapters_path = paths.chapters_json_path()
    stages.append(
        _stage(
            "chapters",
            "Chapters",
            _presence(chapters_path),
            cli=_cli("chapters", meta.id),
            detail=(
                f"{chapter_count} chapter(s) in chapters.json"
                if chapters_path.is_file()
                else "Missing chapters.json"
            ),
            counts={"chapters": chapter_count} if chapters_path.is_file() else None,
        )
    )

    def _count_existing(path_fn) -> int:
        return sum(1 for n in chapter_nums if path_fn(n).is_file())

    if chapter_nums:
        analysis_n = _count_existing(paths.chapter_analysis_path)
        draft_n = _count_existing(paths.chapter_draft_path)
        critique_n = _count_existing(paths.chapter_critique_path)
        summary_n = _count_existing(paths.chapter_summary_path)
        # Summarize is done when every chapter has a summary (pipeline end product).
        summarize_status = _count_state(summary_n, chapter_count)
        stages.append(
            _stage(
                "summarize",
                "Summarize",
                summarize_status,
                cli=_cli("summarize --all", meta.id),
                detail=(
                    f"{summary_n}/{chapter_count} summaries "
                    f"(analysis {analysis_n}, draft {draft_n}, critique {critique_n})"
                ),
                counts={
                    "total": chapter_count,
                    "analysis": analysis_n,
                    "draft": draft_n,
                    "critique": critique_n,
                    "summary": summary_n,
                },
            )
        )
    else:
        stages.append(
            _stage(
                "summarize",
                "Summarize",
                "missing",
                cli=_cli("summarize --all", meta.id),
                detail="Needs chapters.json first",
            )
        )

    report_path = paths.book_report_path()
    stages.append(
        _stage(
            "report",
            "Report",
            _presence(report_path),
            cli=_cli("report", meta.id),
            detail=report_path.name if report_path.is_file() else "Missing book-report.md",
        )
    )

    rollup_path = paths.book_rollup_path()
    stages.append(
        _stage(
            "rollup",
            "Rollup",
            _presence(rollup_path),
            cli=_cli("rollup", meta.id),
            detail=rollup_path.name if rollup_path.is_file() else "Missing book-rollup.json",
        )
    )

    merged_path = paths.book_rollup_merged_path()
    stages.append(
        _stage(
            "aliases",
            "Aliases",
            _presence(merged_path),
            cli=_cli("aliases", meta.id),
            detail=(
                merged_path.name
                if merged_path.is_file()
                else "Missing book-rollup-merged.json"
            ),
        )
    )

    if chapter_nums:
        footnotes_n = _count_existing(paths.chapter_footnotes_path)
        enriched_ch_n = _count_existing(paths.chapter_enriched_path)
        stages.append(
            _stage(
                "footnotes",
                "Footnotes",
                _count_state(footnotes_n, chapter_count),
                cli=_cli("footnotes --all", meta.id),
                detail=(
                    f"{footnotes_n}/{chapter_count} footnotes JSON "
                    f"({enriched_ch_n} enriched MD)"
                ),
                counts={
                    "total": chapter_count,
                    "footnotes": footnotes_n,
                    "enriched_md": enriched_ch_n,
                },
            )
        )
    else:
        stages.append(
            _stage(
                "footnotes",
                "Footnotes",
                "missing",
                cli=_cli("footnotes --all", meta.id),
                detail="Needs chapters.json first",
            )
        )

    synthesis_path = paths.book_synthesis_path()
    stages.append(
        _stage(
            "reduce",
            "Reduce",
            _presence(synthesis_path),
            cli=_cli("reduce", meta.id),
            detail=(
                synthesis_path.name
                if synthesis_path.is_file()
                else "Missing book-synthesis.md"
            ),
        )
    )

    visual_steps = [
        ("visual_identity", "Visual identity", paths.book_visual_identity_path(), "visual-identity"),
        (
            "visual_characters",
            "Visual characters",
            paths.book_visual_characters_path(),
            "visual-characters",
        ),
        ("visual_places", "Visual places", paths.book_visual_places_path(), "visual-places"),
        ("visual_scenes", "Visual scenes", paths.book_visual_scenes_path(), "visual-scenes"),
        ("visual_handoff", "Visual handoff", paths.book_visual_handoff_path(), "visual-handoff"),
        (
            "visual_answers",
            "Handoff answers",
            paths.book_visual_answers_path(),
            "view-handoff",
        ),
        ("visual_resolved", "Visual resolve", paths.book_visual_resolved_path(), "visual-resolve"),
    ]
    for stage_id, label, path, command in visual_steps:
        links = None
        if stage_id in ("visual_handoff", "visual_answers") and paths.book_visual_handoff_path().is_file():
            links = {
                "handoff": f"/web/handoff.html?book={meta.id}",
                "handoff_note": "Handoff viewer is on port 8765 (python main.py view-handoff)",
            }
        stages.append(
            _stage(
                stage_id,
                label,
                _presence(path),
                cli=_cli(command, meta.id),
                detail=path.name if path.is_file() else f"Missing {path.name}",
                links=links,
            )
        )

    illus_dir = paths.illustrations_dir
    jpg_count = 0
    if illus_dir.is_dir():
        jpg_count = sum(1 for p in illus_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg"))
    stages.append(
        _stage(
            "illustrations",
            "Illustrations",
            "done" if jpg_count > 0 else "missing",
            cli=(
                f"# place scene JPGs under output/{meta.id}/illustrations/"
            ),
            detail=f"{jpg_count} JPG(s) in illustrations/",
            counts={"jpgs": jpg_count},
        )
    )

    enriched_path = paths.book_enriched_path()
    stages.append(
        _stage(
            "enriched",
            "Enriched binder",
            _presence(enriched_path),
            cli=_cli("enriched", meta.id),
            detail=(
                enriched_path.name
                if enriched_path.is_file()
                else "Missing book-enriched.md"
            ),
        )
    )

    report_exports = [
        paths.output_dir / "book-report.html",
        paths.output_dir / "book-report.pdf",
        paths.output_dir / "book-report.epub",
    ]
    export_report_status, export_report_files = _export_state(report_exports)
    stages.append(
        _stage(
            "export_report",
            "Export report",
            export_report_status,
            cli=_cli("export --mode report", meta.id),
            detail=f"{sum(export_report_files.values())}/3 formats",
            files=export_report_files,
        )
    )

    enriched_exports = [
        paths.output_dir / "book-enriched.html",
        paths.output_dir / "book-enriched.pdf",
        paths.output_dir / "book-enriched.epub",
    ]
    export_enriched_status, export_enriched_files = _export_state(enriched_exports)
    stages.append(
        _stage(
            "export_enriched",
            "Export enriched",
            export_enriched_status,
            cli=_cli("export --mode enriched", meta.id),
            detail=f"{sum(export_enriched_files.values())}/3 formats",
            files=export_enriched_files,
        )
    )

    return {
        "book": asdict(meta),
        "chapter_count": chapter_count,
        "chapters_json": chapters_path.is_file(),
        "stages": stages,
    }


def catalog_books_payload(root: Path = ROOT) -> dict[str, Any]:
    """JSON payload for GET /api/books."""
    books = load_catalog(root)
    return {"books": [asdict(b) for b in books]}
