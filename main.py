"""CLI for the book-review MVP pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from book import DEFAULT_BOOK_ID, BookPaths, Chapter, load_chapters
from enriched_book import write_book_enriched
from export_book import EXPORT_MODES, export_report
from footnotes import weave_footnotes
from illustrations import illustrations_by_chapter, inject_illustrations
from rollup import apply_alias_clusters, build_book_rollup

ROOT = Path(__file__).resolve().parent
WEB_HANDOFF_HTML_PATH = ROOT / "web" / "handoff.html"
VIEW_HANDOFF_PORT = 8765

# Pipeline stages in order. `--from STAGE` regenerates that stage and everything after.
STAGES = ("reader", "draft", "critic", "revise")


def _chapters(paths: BookPaths) -> list[Chapter]:
    return load_chapters(paths.source_path)


def write_book_report(chapters: list[Chapter], paths: BookPaths) -> Path:
    """Merge chapter Markdown into one report (prefer enriched over summary)."""
    report_path = paths.book_report_path()
    synthesis_path = paths.book_synthesis_path()
    scene_blocks = illustrations_by_chapter(
        paths.book_visual_resolved_path(), paths.illustrations_dir
    )
    parts: list[str] = []
    missing: list[int] = []
    for ch in chapters:
        enriched = paths.chapter_enriched_path(ch.number)
        summary = paths.chapter_summary_path(ch.number)
        if enriched.exists():
            path = enriched
        elif summary.exists():
            path = summary
        else:
            missing.append(ch.number)
            continue
        body = path.read_text(encoding="utf-8").strip()
        parts.append(inject_illustrations(body, scene_blocks.get(ch.number, [])))

    if missing:
        available = ", ".join(str(n) for n in missing)
        raise SystemExit(
            f"Missing chapter summaries: {available}. "
            "Run `python main.py summarize --all` first."
        )

    header = (
        f"# Book report\n\n"
        f"Merged chapter summaries ({len(parts)} chapters).\n"
    )
    chunks: list[str] = [header.rstrip()]
    if synthesis_path.exists():
        synthesis = synthesis_path.read_text(encoding="utf-8").strip()
        if synthesis:
            chunks.append(synthesis)
    body = "\n\n---\n\n".join(parts)
    chunks.append(body)
    report_path.write_text("\n\n---\n\n".join(chunks) + "\n", encoding="utf-8")
    return report_path


def write_book_rollup(chapters: list[Chapter], paths: BookPaths) -> Path:
    """Merge Reader analyses into state/book-rollup.json (no LLM)."""
    rollup_path = paths.book_rollup_path()
    analyses: list[dict] = []
    missing: list[int] = []
    for ch in chapters:
        path = paths.chapter_analysis_path(ch.number)
        if not path.exists():
            missing.append(ch.number)
            continue
        analyses.append(json.loads(path.read_text(encoding="utf-8")))

    if missing:
        available = ", ".join(str(n) for n in missing)
        raise SystemExit(
            f"Missing chapter analyses: {available}. "
            "Run `python main.py summarize --all` first."
        )

    payload = build_book_rollup(analyses)
    rollup_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return rollup_path


def _require_artifact(path: Path, *, stage: str, hint: str) -> None:
    if not path.exists():
        raise SystemExit(
            f"Cannot --from {stage}: missing {path.relative_to(ROOT)}. {hint}"
        )


def _resolve_start(
    *,
    force: bool,
    from_stage: str | None,
    out_path: Path,
    notes_path: Path,
    draft_path: Path,
    critique_path: Path,
) -> str | None:
    """Return pipeline start stage, or None to skip the chapter."""
    if force and from_stage:
        raise SystemExit("Use either --force or --from, not both")

    if from_stage:
        if from_stage == "draft":
            _require_artifact(
                notes_path,
                stage=from_stage,
                hint="Run Reader first (summarize without --from, or --from reader).",
            )
        elif from_stage == "critic":
            _require_artifact(
                notes_path,
                stage=from_stage,
                hint="Need Reader analysis first.",
            )
            _require_artifact(
                draft_path,
                stage=from_stage,
                hint="Need Editor draft first (--from draft).",
            )
        elif from_stage == "revise":
            _require_artifact(
                notes_path,
                stage=from_stage,
                hint="Need Reader analysis first.",
            )
            _require_artifact(
                draft_path,
                stage=from_stage,
                hint="Need Editor draft first.",
            )
            _require_artifact(
                critique_path,
                stage=from_stage,
                hint="Need Critic JSON first (--from critic).",
            )
        return from_stage

    if force:
        return "reader"

    if out_path.exists():
        return None

    # Soft resume: continue from the first missing artifact in the chain.
    if not notes_path.exists():
        return "reader"
    if not draft_path.exists():
        return "draft"
    if not critique_path.exists():
        return "critic"
    return "revise"


def summarize_one(
    chapter: Chapter,
    paths: BookPaths,
    *,
    force: bool,
    from_stage: str | None,
) -> str:
    """Reader → Editor draft → Critic → revise for one chapter.

    Returns 'wrote', 'skip', or raises.
    """
    from agents.critic import critique_draft
    from agents.editor import edit_analysis, revise_summary
    from agents.reader import read_chapter

    out_path = paths.chapter_summary_path(chapter.number)
    notes_path = paths.chapter_analysis_path(chapter.number)
    draft_path = paths.chapter_draft_path(chapter.number)
    critique_path = paths.chapter_critique_path(chapter.number)

    start = _resolve_start(
        force=force,
        from_stage=from_stage,
        out_path=out_path,
        notes_path=notes_path,
        draft_path=draft_path,
        critique_path=critique_path,
    )
    if start is None:
        print(
            f"Skip {chapter.heading}: {out_path.relative_to(ROOT)} already exists "
            "(use --force or --from STAGE to regenerate)"
        )
        return "skip"

    start_idx = STAGES.index(start)

    if start_idx <= STAGES.index("reader"):
        print(f"Reading {chapter.heading} ...")
        analysis = read_chapter(chapter)
        notes_path.write_text(
            json.dumps(analysis, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {notes_path.relative_to(ROOT)}")
    else:
        print(f"Reusing Reader notes {notes_path.relative_to(ROOT)}")
        analysis = json.loads(notes_path.read_text(encoding="utf-8"))

    if start_idx <= STAGES.index("draft"):
        print(f"Editing draft {chapter.heading} ...")
        draft = edit_analysis(analysis)
        draft_path.write_text(draft, encoding="utf-8")
        print(f"Wrote {draft_path.relative_to(ROOT)}")
    else:
        print(f"Reusing Editor draft {draft_path.relative_to(ROOT)}")
        draft = draft_path.read_text(encoding="utf-8")

    if start_idx <= STAGES.index("critic"):
        print(f"Critiquing {chapter.heading} ...")
        critique = critique_draft(chapter, analysis, draft)
        critique_path.write_text(
            json.dumps(critique, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(
            f"Wrote {critique_path.relative_to(ROOT)} "
            f"(verdict={critique.get('verdict', '?')})"
        )
    else:
        print(f"Reusing Critic notes {critique_path.relative_to(ROOT)}")
        critique = json.loads(critique_path.read_text(encoding="utf-8"))

    print(f"Revising {chapter.heading} ...")
    markdown = revise_summary(analysis, draft, critique)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {out_path.relative_to(ROOT)}")
    return "wrote"


def cmd_chapters(args: argparse.Namespace) -> None:
    paths: BookPaths = args.paths
    chapters = _chapters(paths)
    print(f"Found {len(chapters)} chapters:\n")
    for ch in chapters:
        words = len(ch.text.split())
        print(f"  {ch.number:2d}. {ch.heading}  ({words} words)")

    state_path = paths.chapters_json_path()
    payload = [
        {
            "number": ch.number,
            "roman": ch.roman,
            "title": ch.title,
            "word_count": len(ch.text.split()),
        }
        for ch in chapters
    ]
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote metadata to {state_path.relative_to(ROOT)}")


def cmd_summarize(args: argparse.Namespace) -> None:
    paths: BookPaths = args.paths
    chapters = _chapters(paths)

    if args.all:
        if args.chapter != 1:
            print("Note: --all ignores --chapter")
        targets = chapters
    else:
        chapter = next((c for c in chapters if c.number == args.chapter), None)
        if chapter is None:
            available = ", ".join(str(c.number) for c in chapters)
            raise SystemExit(f"Chapter {args.chapter} not found. Available: {available}")
        targets = [chapter]

    wrote = skipped = 0
    for chapter in targets:
        result = summarize_one(
            chapter,
            paths,
            force=args.force,
            from_stage=args.from_stage,
        )
        if result == "wrote":
            wrote += 1
        else:
            skipped += 1

    if args.all:
        print(f"\nMap done: {wrote} written, {skipped} skipped")
        report_path = write_book_report(chapters, paths)
        print(f"Wrote {report_path.relative_to(ROOT)}")
        rollup_path = write_book_rollup(chapters, paths)
        print(f"Wrote {rollup_path.relative_to(ROOT)}")


def cmd_report(args: argparse.Namespace) -> None:
    paths: BookPaths = args.paths
    report_path = write_book_report(_chapters(paths), paths)
    print(f"Wrote {report_path.relative_to(ROOT)}")


def cmd_enriched(args: argparse.Namespace) -> None:
    paths: BookPaths = args.paths
    path = write_book_enriched(_chapters(paths), paths)
    print(f"Wrote {path.relative_to(ROOT)}")


def cmd_rollup(args: argparse.Namespace) -> None:
    paths: BookPaths = args.paths
    rollup_path = write_book_rollup(_chapters(paths), paths)
    payload = json.loads(rollup_path.read_text(encoding="utf-8"))
    print(f"Wrote {rollup_path.relative_to(ROOT)}")
    print(
        f"  {len(payload['chapters_included'])} chapters, "
        f"{len(payload['characters'])} characters, "
        f"{len(payload['themes'])} themes"
    )


def write_book_rollup_merged(paths: BookPaths, *, force: bool) -> Path | None:
    """LLM alias merge of book-rollup.json → book-rollup-merged.json.

    Returns the path written, or None if skipped.
    """
    rollup_path = paths.book_rollup_path()
    merged_path = paths.book_rollup_merged_path()
    if not rollup_path.exists():
        raise SystemExit(
            f"Missing {rollup_path.relative_to(ROOT)}. "
            "Run `python main.py rollup` first."
        )

    if merged_path.exists() and not force:
        print(
            f"Skip aliases: {merged_path.relative_to(ROOT)} already exists "
            "(use --force to regenerate)"
        )
        return None

    from agents.alias_merger import propose_alias_clusters

    rollup = json.loads(rollup_path.read_text(encoding="utf-8"))
    print("Proposing character/theme alias clusters ...")
    clusters = propose_alias_clusters(rollup)
    payload = apply_alias_clusters(rollup, clusters)
    merged_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return merged_path


def cmd_aliases(args: argparse.Namespace) -> None:
    merged_path = write_book_rollup_merged(args.paths, force=args.force)
    if merged_path is None:
        return
    payload = json.loads(merged_path.read_text(encoding="utf-8"))
    multi_chars = sum(1 for c in payload["characters"] if len(c.get("aliases") or []) > 1)
    multi_themes = sum(1 for t in payload["themes"] if len(t.get("aliases") or []) > 1)
    print(f"Wrote {merged_path.relative_to(ROOT)}")
    print(
        f"  {len(payload['chapters_included'])} chapters, "
        f"{len(payload['characters'])} characters ({multi_chars} multi-alias), "
        f"{len(payload['themes'])} themes ({multi_themes} multi-alias)"
    )


def write_book_synthesis(paths: BookPaths, *, force: bool) -> Path | None:
    """LLM reduce: compact analyses + rollup → output/book-synthesis.md.

    Requires chapter summaries too so the rebuilt report can include them.
    Returns the path written, or None if skipped.
    """
    rollup_base = paths.book_rollup_path()
    rollup_merged = paths.book_rollup_merged_path()
    synthesis_path = paths.book_synthesis_path()
    if not rollup_base.exists() and not rollup_merged.exists():
        raise SystemExit(
            f"Missing {rollup_base.relative_to(ROOT)}. "
            "Run `python main.py rollup` first."
        )

    if synthesis_path.exists() and not force:
        print(
            f"Skip reduce: {synthesis_path.relative_to(ROOT)} already exists "
            "(use --force to regenerate)"
        )
        return None

    chapters = _chapters(paths)
    analyses: list[dict] = []
    missing_analysis: list[int] = []
    missing_summary: list[int] = []
    for ch in chapters:
        analysis_path = paths.chapter_analysis_path(ch.number)
        summary_path = paths.chapter_summary_path(ch.number)
        if not analysis_path.exists():
            missing_analysis.append(ch.number)
            continue
        if not summary_path.exists():
            missing_summary.append(ch.number)
            continue
        analyses.append(json.loads(analysis_path.read_text(encoding="utf-8")))

    if missing_analysis:
        available = ", ".join(str(n) for n in missing_analysis)
        raise SystemExit(
            f"Missing chapter analyses: {available}. "
            "Run `python main.py summarize --all` first."
        )
    if missing_summary:
        available = ", ".join(str(n) for n in missing_summary)
        raise SystemExit(
            f"Missing chapter summaries: {available}. "
            "Run `python main.py summarize --all` first."
        )

    rollup_path = rollup_merged if rollup_merged.exists() else rollup_base
    rollup = json.loads(rollup_path.read_text(encoding="utf-8"))

    from agents.reducer import synthesize_book

    print(
        f"Synthesizing book overview from {len(analyses)} compact analyses "
        f"+ {rollup_path.relative_to(ROOT)} ..."
    )
    markdown = synthesize_book(analyses, rollup)
    synthesis_path.write_text(markdown, encoding="utf-8")
    return synthesis_path


def cmd_reduce(args: argparse.Namespace) -> None:
    paths: BookPaths = args.paths
    synth_path = write_book_synthesis(paths, force=args.force)
    if synth_path is None:
        return
    print(f"Wrote {synth_path.relative_to(ROOT)}")
    report_path = write_book_report(_chapters(paths), paths)
    print(f"Wrote {report_path.relative_to(ROOT)}")


def write_book_visual_identity(paths: BookPaths, *, force: bool) -> Path | None:
    """LLM visual identity from compact analyses + rollup → state JSON.

    Returns the path written, or None if skipped.
    """
    rollup_base = paths.book_rollup_path()
    rollup_merged = paths.book_rollup_merged_path()
    identity_path = paths.book_visual_identity_path()
    if not rollup_base.exists() and not rollup_merged.exists():
        raise SystemExit(
            f"Missing {rollup_base.relative_to(ROOT)}. "
            "Run `python main.py rollup` first."
        )

    if identity_path.exists() and not force:
        print(
            f"Skip visual-identity: {identity_path.relative_to(ROOT)} "
            "already exists (use --force to regenerate)"
        )
        return None

    chapters = _chapters(paths)
    analyses: list[dict] = []
    missing_analysis: list[int] = []
    for ch in chapters:
        analysis_path = paths.chapter_analysis_path(ch.number)
        if not analysis_path.exists():
            missing_analysis.append(ch.number)
            continue
        analyses.append(json.loads(analysis_path.read_text(encoding="utf-8")))

    if missing_analysis:
        available = ", ".join(str(n) for n in missing_analysis)
        raise SystemExit(
            f"Missing chapter analyses: {available}. "
            "Run `python main.py summarize --all` first."
        )

    rollup_path = rollup_merged if rollup_merged.exists() else rollup_base
    rollup = json.loads(rollup_path.read_text(encoding="utf-8"))

    from agents.visual_identity import build_visual_identity

    print(
        f"Building visual identity from {len(analyses)} compact analyses "
        f"+ {rollup_path.relative_to(ROOT)} ..."
    )
    payload = build_visual_identity(
        analyses,
        rollup,
        source_rollup=rollup_path.name,
    )
    identity_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return identity_path


def cmd_visual_identity(args: argparse.Namespace) -> None:
    path = write_book_visual_identity(args.paths, force=args.force)
    if path is None:
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(f"Wrote {path.relative_to(ROOT)}")
    print(
        f"  {len(payload.get('chapters_included') or [])} chapters, "
        f"{len(payload.get('artistic_style') or [])} style, "
        f"{len(payload.get('color_palette') or [])} palette, "
        f"{len(payload.get('atmosphere') or [])} atmosphere, "
        f"{len(payload.get('period') or [])} period, "
        f"{len(payload.get('motifs') or [])} motifs"
    )


def write_book_visual_characters(paths: BookPaths, *, force: bool) -> Path | None:
    """LLM character visual sheets from analyses + rollup + identity → state JSON.

    Returns the path written, or None if skipped.
    """
    rollup_base = paths.book_rollup_path()
    rollup_merged = paths.book_rollup_merged_path()
    identity_path = paths.book_visual_identity_path()
    characters_path = paths.book_visual_characters_path()
    if not rollup_base.exists() and not rollup_merged.exists():
        raise SystemExit(
            f"Missing {rollup_base.relative_to(ROOT)}. "
            "Run `python main.py rollup` first."
        )
    if not identity_path.exists():
        raise SystemExit(
            f"Missing {identity_path.relative_to(ROOT)}. "
            "Run `python main.py visual-identity` first."
        )

    if characters_path.exists() and not force:
        print(
            f"Skip visual-characters: {characters_path.relative_to(ROOT)} "
            "already exists (use --force to regenerate)"
        )
        return None

    chapters = _chapters(paths)
    analyses: list[dict] = []
    missing_analysis: list[int] = []
    for ch in chapters:
        analysis_path = paths.chapter_analysis_path(ch.number)
        if not analysis_path.exists():
            missing_analysis.append(ch.number)
            continue
        analyses.append(json.loads(analysis_path.read_text(encoding="utf-8")))

    if missing_analysis:
        available = ", ".join(str(n) for n in missing_analysis)
        raise SystemExit(
            f"Missing chapter analyses: {available}. "
            "Run `python main.py summarize --all` first."
        )

    rollup_path = rollup_merged if rollup_merged.exists() else rollup_base
    rollup = json.loads(rollup_path.read_text(encoding="utf-8"))
    identity = json.loads(identity_path.read_text(encoding="utf-8"))

    from agents.visual_characters import build_visual_characters

    print(
        f"Building visual characters from {len(analyses)} compact analyses "
        f"+ {rollup_path.relative_to(ROOT)} "
        f"+ {identity_path.relative_to(ROOT)} ..."
    )
    payload = build_visual_characters(
        analyses,
        rollup,
        identity,
        source_rollup=rollup_path.name,
        source_identity=identity_path.name,
    )
    characters_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return characters_path


def cmd_visual_characters(args: argparse.Namespace) -> None:
    path = write_book_visual_characters(args.paths, force=args.force)
    if path is None:
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    characters = payload.get("characters") or []
    physical = sum(len(c.get("physical") or []) for c in characters)
    personality = sum(len(c.get("personality") or []) for c in characters)
    visual_language = sum(len(c.get("visual_language") or []) for c in characters)
    print(f"Wrote {path.relative_to(ROOT)}")
    print(
        f"  {len(payload.get('chapters_included') or [])} chapters, "
        f"{len(characters)} characters, "
        f"{physical} physical, "
        f"{personality} personality, "
        f"{visual_language} visual_language"
    )


def write_book_visual_places(paths: BookPaths, *, force: bool) -> Path | None:
    """LLM place / setting sheets from analyses + identity → state JSON.

    Returns the path written, or None if skipped.
    """
    identity_path = paths.book_visual_identity_path()
    places_path = paths.book_visual_places_path()
    if not identity_path.exists():
        raise SystemExit(
            f"Missing {identity_path.relative_to(ROOT)}. "
            "Run `python main.py visual-identity` first."
        )

    if places_path.exists() and not force:
        print(
            f"Skip visual-places: {places_path.relative_to(ROOT)} "
            "already exists (use --force to regenerate)"
        )
        return None

    chapters = _chapters(paths)
    analyses: list[dict] = []
    missing_analysis: list[int] = []
    for ch in chapters:
        analysis_path = paths.chapter_analysis_path(ch.number)
        if not analysis_path.exists():
            missing_analysis.append(ch.number)
            continue
        analyses.append(json.loads(analysis_path.read_text(encoding="utf-8")))

    if missing_analysis:
        available = ", ".join(str(n) for n in missing_analysis)
        raise SystemExit(
            f"Missing chapter analyses: {available}. "
            "Run `python main.py summarize --all` first."
        )

    identity = json.loads(identity_path.read_text(encoding="utf-8"))

    from agents.visual_places import build_visual_places

    print(
        f"Building visual places from {len(analyses)} compact analyses "
        f"+ {identity_path.relative_to(ROOT)} ..."
    )
    payload = build_visual_places(
        analyses,
        identity,
        source_identity=identity_path.name,
    )
    places_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return places_path


def cmd_visual_places(args: argparse.Namespace) -> None:
    path = write_book_visual_places(args.paths, force=args.force)
    if path is None:
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    places = payload.get("places") or []
    architecture = sum(len(p.get("architecture") or []) for p in places)
    climate = sum(len(p.get("climate") or []) for p in places)
    atmosphere = sum(len(p.get("atmosphere") or []) for p in places)
    symbols = sum(len(p.get("symbols") or []) for p in places)
    print(f"Wrote {path.relative_to(ROOT)}")
    print(
        f"  {len(payload.get('chapters_included') or [])} chapters, "
        f"{len(places)} places, "
        f"{architecture} architecture, "
        f"{climate} climate, "
        f"{atmosphere} atmosphere, "
        f"{symbols} symbols"
    )


def write_book_visual_scenes(paths: BookPaths, *, force: bool) -> Path | None:
    """LLM scene briefs from analyses + identity + characters + places → state JSON.

    Returns the path written, or None if skipped.
    """
    identity_path = paths.book_visual_identity_path()
    characters_path = paths.book_visual_characters_path()
    places_path = paths.book_visual_places_path()
    scenes_path = paths.book_visual_scenes_path()
    if not identity_path.exists():
        raise SystemExit(
            f"Missing {identity_path.relative_to(ROOT)}. "
            "Run `python main.py visual-identity` first."
        )
    if not characters_path.exists():
        raise SystemExit(
            f"Missing {characters_path.relative_to(ROOT)}. "
            "Run `python main.py visual-characters` first."
        )
    if not places_path.exists():
        raise SystemExit(
            f"Missing {places_path.relative_to(ROOT)}. "
            "Run `python main.py visual-places` first."
        )

    if scenes_path.exists() and not force:
        print(
            f"Skip visual-scenes: {scenes_path.relative_to(ROOT)} "
            "already exists (use --force to regenerate)"
        )
        return None

    chapters = _chapters(paths)
    analyses: list[dict] = []
    missing_analysis: list[int] = []
    for ch in chapters:
        analysis_path = paths.chapter_analysis_path(ch.number)
        if not analysis_path.exists():
            missing_analysis.append(ch.number)
            continue
        analyses.append(json.loads(analysis_path.read_text(encoding="utf-8")))

    if missing_analysis:
        available = ", ".join(str(n) for n in missing_analysis)
        raise SystemExit(
            f"Missing chapter analyses: {available}. "
            "Run `python main.py summarize --all` first."
        )

    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    characters_payload = json.loads(characters_path.read_text(encoding="utf-8"))
    places_payload = json.loads(places_path.read_text(encoding="utf-8"))

    from agents.visual_scenes import build_visual_scenes

    print(
        f"Building visual scenes from {len(analyses)} compact analyses "
        f"+ {identity_path.relative_to(ROOT)} "
        f"+ {characters_path.relative_to(ROOT)} "
        f"+ {places_path.relative_to(ROOT)} ..."
    )
    payload = build_visual_scenes(
        analyses,
        identity,
        characters_payload,
        places_payload,
        source_identity=identity_path.name,
        source_characters=characters_path.name,
        source_places=places_path.name,
    )
    scenes_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return scenes_path


def cmd_visual_scenes(args: argparse.Namespace) -> None:
    path = write_book_visual_scenes(args.paths, force=args.force)
    if path is None:
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    scenes = payload.get("scenes") or []
    emotional_focus = sum(len(s.get("emotional_focus") or []) for s in scenes)
    composition = sum(len(s.get("composition") or []) for s in scenes)
    print(f"Wrote {path.relative_to(ROOT)}")
    print(
        f"  {len(payload.get('chapters_included') or [])} chapters, "
        f"{len(scenes)} scenes, "
        f"{emotional_focus} emotional_focus, "
        f"{composition} composition"
    )


def write_book_visual_handoff(paths: BookPaths, *, force: bool) -> Path | None:
    """LLM handoff: open questions + consistency over bible sheets → state JSON.

    Returns the path written, or None if skipped.
    """
    identity_path = paths.book_visual_identity_path()
    characters_path = paths.book_visual_characters_path()
    places_path = paths.book_visual_places_path()
    scenes_path = paths.book_visual_scenes_path()
    handoff_path = paths.book_visual_handoff_path()
    if not identity_path.exists():
        raise SystemExit(
            f"Missing {identity_path.relative_to(ROOT)}. "
            "Run `python main.py visual-identity` first."
        )
    if not characters_path.exists():
        raise SystemExit(
            f"Missing {characters_path.relative_to(ROOT)}. "
            "Run `python main.py visual-characters` first."
        )
    if not places_path.exists():
        raise SystemExit(
            f"Missing {places_path.relative_to(ROOT)}. "
            "Run `python main.py visual-places` first."
        )
    if not scenes_path.exists():
        raise SystemExit(
            f"Missing {scenes_path.relative_to(ROOT)}. "
            "Run `python main.py visual-scenes` first."
        )

    if handoff_path.exists() and not force:
        print(
            f"Skip visual-handoff: {handoff_path.relative_to(ROOT)} "
            "already exists (use --force to regenerate)"
        )
        return None

    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    characters_payload = json.loads(characters_path.read_text(encoding="utf-8"))
    places_payload = json.loads(places_path.read_text(encoding="utf-8"))
    scenes_payload = json.loads(scenes_path.read_text(encoding="utf-8"))

    from agents.visual_handoff import build_visual_handoff

    print(
        f"Building visual handoff from "
        f"{identity_path.relative_to(ROOT)} "
        f"+ {characters_path.relative_to(ROOT)} "
        f"+ {places_path.relative_to(ROOT)} "
        f"+ {scenes_path.relative_to(ROOT)} ..."
    )
    payload = build_visual_handoff(
        identity,
        characters_payload,
        places_payload,
        scenes_payload,
        source_identity=identity_path.name,
        source_characters=characters_path.name,
        source_places=places_path.name,
        source_scenes=scenes_path.name,
    )
    handoff_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return handoff_path


def cmd_visual_handoff(args: argparse.Namespace) -> None:
    path = write_book_visual_handoff(args.paths, force=args.force)
    if path is None:
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions = payload.get("open_questions") or []
    issues = payload.get("consistency_issues") or []
    print(f"Wrote {path.relative_to(ROOT)}")
    print(f"  {len(questions)} open_questions, {len(issues)} consistency_issues")


def write_book_visual_resolved(paths: BookPaths, *, force: bool) -> Path | None:
    """Apply handoff answers into a locked resolved bible → state JSON.

    Returns the path written, or None if skipped.
    """
    identity_path = paths.book_visual_identity_path()
    characters_path = paths.book_visual_characters_path()
    places_path = paths.book_visual_places_path()
    scenes_path = paths.book_visual_scenes_path()
    handoff_path = paths.book_visual_handoff_path()
    answers_path = paths.book_visual_answers_path()
    resolved_path = paths.book_visual_resolved_path()
    if not identity_path.exists():
        raise SystemExit(
            f"Missing {identity_path.relative_to(ROOT)}. "
            "Run `python main.py visual-identity` first."
        )
    if not characters_path.exists():
        raise SystemExit(
            f"Missing {characters_path.relative_to(ROOT)}. "
            "Run `python main.py visual-characters` first."
        )
    if not places_path.exists():
        raise SystemExit(
            f"Missing {places_path.relative_to(ROOT)}. "
            "Run `python main.py visual-places` first."
        )
    if not scenes_path.exists():
        raise SystemExit(
            f"Missing {scenes_path.relative_to(ROOT)}. "
            "Run `python main.py visual-scenes` first."
        )
    if not handoff_path.exists():
        raise SystemExit(
            f"Missing {handoff_path.relative_to(ROOT)}. "
            "Run `python main.py visual-handoff` first."
        )
    if not answers_path.exists():
        raise SystemExit(
            f"Missing {answers_path.relative_to(ROOT)}. "
            "Download answers from `python main.py view-handoff` and place "
            "the file under state/."
        )

    if resolved_path.exists() and not force:
        print(
            f"Skip visual-resolve: {resolved_path.relative_to(ROOT)} "
            "already exists (use --force to regenerate)"
        )
        return None

    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    characters_payload = json.loads(characters_path.read_text(encoding="utf-8"))
    places_payload = json.loads(places_path.read_text(encoding="utf-8"))
    scenes_payload = json.loads(scenes_path.read_text(encoding="utf-8"))
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    answers = json.loads(answers_path.read_text(encoding="utf-8"))

    from agents.visual_resolve import build_visual_resolved

    print(
        f"Resolving visual bible from "
        f"{answers_path.relative_to(ROOT)} "
        f"+ {handoff_path.relative_to(ROOT)} "
        f"+ bible sheets ..."
    )
    try:
        payload = build_visual_resolved(
            identity,
            characters_payload,
            places_payload,
            scenes_payload,
            handoff,
            answers,
            source_identity=identity_path.name,
            source_characters=characters_path.name,
            source_places=places_path.name,
            source_scenes=scenes_path.name,
            source_handoff=handoff_path.name,
            source_answers=answers_path.name,
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    resolved_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return resolved_path


def cmd_visual_resolve(args: argparse.Namespace) -> None:
    path = write_book_visual_resolved(args.paths, force=args.force)
    if path is None:
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    resolutions = payload.get("resolutions") or []
    unresolved = payload.get("unresolved") or []
    applied = sum(1 for r in resolutions if r.get("applied"))
    print(f"Wrote {path.relative_to(ROOT)}")
    print(
        f"  {applied}/{len(resolutions)} resolutions applied, "
        f"{len(unresolved)} unresolved"
    )


def cmd_view_handoff(args: argparse.Namespace) -> None:
    """Serve web/handoff.html against state JSON and open a browser (no LLM)."""
    import functools
    import http.server
    import socketserver
    import webbrowser

    paths: BookPaths = args.paths
    handoff_path = paths.book_visual_handoff_path()
    if not handoff_path.exists():
        raise SystemExit(
            f"Missing {handoff_path.relative_to(ROOT)}. "
            "Run `python main.py visual-handoff` first."
        )
    if not WEB_HANDOFF_HTML_PATH.exists():
        raise SystemExit(f"Missing {WEB_HANDOFF_HTML_PATH.relative_to(ROOT)}.")

    port = VIEW_HANDOFF_PORT
    url = f"http://127.0.0.1:{port}/web/handoff.html"
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(ROOT),
    )
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    except OSError as exc:
        raise SystemExit(
            f"Could not bind 127.0.0.1:{port} ({exc}). "
            "Stop whatever is using that port, then retry."
        ) from exc

    with httpd:
        print(f"Serving {url}")
        print("Press Ctrl+C to stop.")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def footnotes_one(chapter: Chapter, paths: BookPaths, *, force: bool) -> str:
    """Research footnotes + weave enriched Markdown for one chapter.

    Returns 'wrote' or 'skip'.
    """
    from agents.footnote import research_footnotes

    notes_path = paths.chapter_analysis_path(chapter.number)
    summary_path = paths.chapter_summary_path(chapter.number)
    footnotes_path = paths.chapter_footnotes_path(chapter.number)
    enriched_path = paths.chapter_enriched_path(chapter.number)

    if not notes_path.exists():
        raise SystemExit(
            f"Missing {notes_path.relative_to(ROOT)}. "
            "Run `python main.py summarize` for this chapter first."
        )
    if not summary_path.exists():
        raise SystemExit(
            f"Missing {summary_path.relative_to(ROOT)}. "
            "Run `python main.py summarize` for this chapter first."
        )

    if footnotes_path.exists() and not force:
        print(
            f"Skip {chapter.heading}: {footnotes_path.relative_to(ROOT)} already exists "
            "(use --force to regenerate)"
        )
        return "skip"

    analysis = json.loads(notes_path.read_text(encoding="utf-8"))
    print(f"Researching footnotes for {chapter.heading} ...")
    payload = research_footnotes(chapter, analysis)
    footnotes_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {footnotes_path.relative_to(ROOT)} "
        f"({len(payload.get('footnotes') or [])} notes)"
    )

    summary_md = summary_path.read_text(encoding="utf-8")
    enriched = weave_footnotes(summary_md, payload)
    enriched_path.write_text(enriched, encoding="utf-8")
    print(f"Wrote {enriched_path.relative_to(ROOT)}")
    return "wrote"


def cmd_footnotes(args: argparse.Namespace) -> None:
    paths: BookPaths = args.paths
    chapters = _chapters(paths)

    if args.all:
        if args.chapter is not None:
            print("Note: --all ignores --chapter")
        targets = chapters
    elif args.chapter is None:
        chapter = next(
            (c for c in chapters if not paths.chapter_footnotes_path(c.number).exists()),
            None,
        )
        if chapter is None:
            raise SystemExit(
                "All chapters already have footnotes "
                "(use --chapter N --force to regenerate, or --all)"
            )
        print(f"Resuming at {chapter.heading} (no footnotes JSON yet)")
        targets = [chapter]
    else:
        chapter = next((c for c in chapters if c.number == args.chapter), None)
        if chapter is None:
            available = ", ".join(str(c.number) for c in chapters)
            raise SystemExit(f"Chapter {args.chapter} not found. Available: {available}")
        targets = [chapter]

    wrote = skipped = 0
    for chapter in targets:
        result = footnotes_one(chapter, paths, force=args.force)
        if result == "wrote":
            wrote += 1
        else:
            skipped += 1

    if args.all:
        print(f"\nFootnotes done: {wrote} written, {skipped} skipped")
        report_path = write_book_report(chapters, paths)
        print(f"Wrote {report_path.relative_to(ROOT)}")


def cmd_export(args: argparse.Namespace) -> None:
    written = export_report(
        args.format, force=args.force, mode=args.mode, paths=args.paths
    )
    for path in written:
        print(f"Wrote {path.relative_to(ROOT)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Book review MVP")
    book_parent = argparse.ArgumentParser(add_help=False)
    book_parent.add_argument(
        "--book",
        default=DEFAULT_BOOK_ID,
        metavar="ID",
        help=f"Book id (default: {DEFAULT_BOOK_ID}; Alice still uses flat paths)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    chapters_parser = sub.add_parser(
        "chapters",
        parents=[book_parent],
        help="List chapters (no LLM)",
    )
    chapters_parser.set_defaults(func=cmd_chapters)

    summarize_parser = sub.add_parser(
        "summarize",
        parents=[book_parent],
        help=(
            "Reader→Editor→Critic→revise for chapter(s); writes state analysis + "
            "draft + critique + output summary; --all also writes book-report.md "
            "and state/book-rollup.json"
        ),
    )
    summarize_parser.add_argument(
        "--chapter",
        type=int,
        default=1,
        help="Chapter number to summarize (default: 1; ignored with --all)",
    )
    summarize_parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Summarize every chapter, then merge into output/book-report.md "
            "and state/book-rollup.json"
        ),
    )
    summarize_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Regenerate from Reader through summary even if output already exists "
            "(mutually exclusive with --from)"
        ),
    )
    summarize_parser.add_argument(
        "--from",
        dest="from_stage",
        choices=STAGES,
        metavar="STAGE",
        help=(
            "Restart at STAGE (reader|draft|critic|revise), reusing earlier "
            "artifacts; overrides skip when summary exists"
        ),
    )
    summarize_parser.set_defaults(func=cmd_summarize)

    report_parser = sub.add_parser(
        "report",
        parents=[book_parent],
        help="Merge existing chapter summaries into output/book-report.md (no LLM)",
    )
    report_parser.set_defaults(func=cmd_report)

    enriched_parser = sub.add_parser(
        "enriched",
        parents=[book_parent],
        help=(
            "Bind Gutenberg chapters + scene images + footnote endnotes into "
            "output/book-enriched.md (no LLM)"
        ),
    )
    enriched_parser.set_defaults(func=cmd_enriched)

    rollup_parser = sub.add_parser(
        "rollup",
        parents=[book_parent],
        help=(
            "Merge chapter analyses into state/book-rollup.json "
            "(characters + themes; no LLM)"
        ),
    )
    rollup_parser.set_defaults(func=cmd_rollup)

    aliases_parser = sub.add_parser(
        "aliases",
        parents=[book_parent],
        help=(
            "LLM alias merge of state/book-rollup.json into "
            "state/book-rollup-merged.json"
        ),
    )
    aliases_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/book-rollup-merged.json already exists",
    )
    aliases_parser.set_defaults(func=cmd_aliases)

    reduce_parser = sub.add_parser(
        "reduce",
        parents=[book_parent],
        help=(
            "LLM book-level synthesis from compact analyses + rollup into "
            "output/book-synthesis.md; rebuilds book-report.md"
        ),
    )
    reduce_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if output/book-synthesis.md already exists",
    )
    reduce_parser.set_defaults(func=cmd_reduce)

    visual_identity_parser = sub.add_parser(
        "visual-identity",
        parents=[book_parent],
        help=(
            "LLM book-level visual identity (style / palette / atmosphere / "
            "period / motifs) into state/book-visual-identity.json"
        ),
    )
    visual_identity_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/book-visual-identity.json already exists",
    )
    visual_identity_parser.set_defaults(func=cmd_visual_identity)

    visual_characters_parser = sub.add_parser(
        "visual-characters",
        parents=[book_parent],
        help=(
            "LLM character visual sheets (physical / personality / "
            "visual_language) into state/book-visual-characters.json"
        ),
    )
    visual_characters_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/book-visual-characters.json already exists",
    )
    visual_characters_parser.set_defaults(func=cmd_visual_characters)

    visual_places_parser = sub.add_parser(
        "visual-places",
        parents=[book_parent],
        help=(
            "LLM place / setting sheets (architecture / climate / "
            "atmosphere / symbols) into state/book-visual-places.json"
        ),
    )
    visual_places_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/book-visual-places.json already exists",
    )
    visual_places_parser.set_defaults(func=cmd_visual_places)

    visual_scenes_parser = sub.add_parser(
        "visual-scenes",
        parents=[book_parent],
        help=(
            "LLM scene briefs (illustration moments + emotional_focus / "
            "composition) into state/book-visual-scenes.json"
        ),
    )
    visual_scenes_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/book-visual-scenes.json already exists",
    )
    visual_scenes_parser.set_defaults(func=cmd_visual_scenes)

    visual_handoff_parser = sub.add_parser(
        "visual-handoff",
        parents=[book_parent],
        help=(
            "LLM Visual Bible handoff (open questions + consistency issues) "
            "into state/book-visual-handoff.json"
        ),
    )
    visual_handoff_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/book-visual-handoff.json already exists",
    )
    visual_handoff_parser.set_defaults(func=cmd_visual_handoff)

    visual_resolve_parser = sub.add_parser(
        "visual-resolve",
        parents=[book_parent],
        help=(
            "Apply state/book-visual-handoff-answers.json into a locked "
            "resolved bible (state/book-visual-resolved.json; no LLM)"
        ),
    )
    visual_resolve_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/book-visual-resolved.json already exists",
    )
    visual_resolve_parser.set_defaults(func=cmd_visual_resolve)

    view_handoff_parser = sub.add_parser(
        "view-handoff",
        parents=[book_parent],
        help=(
            "Open web/handoff.html for state/book-visual-handoff.json "
            "(local HTTP server; no LLM)"
        ),
    )
    view_handoff_parser.set_defaults(func=cmd_view_handoff)

    footnotes_parser = sub.add_parser(
        "footnotes",
        parents=[book_parent],
        help=(
            "Footnote/Research agent: write state footnotes JSON + enriched "
            "chapter Markdown (keeps summaries pristine); --all also rebuilds "
            "book-report.md"
        ),
    )
    footnotes_parser.add_argument(
        "--chapter",
        type=int,
        default=None,
        help=(
            "Chapter number; omit to resume at the first chapter without "
            "footnotes JSON (ignored with --all)"
        ),
    )
    footnotes_parser.add_argument(
        "--all",
        action="store_true",
        help="Research every chapter, then rebuild output/book-report.md",
    )
    footnotes_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if state/chapter-NN-footnotes.json already exists",
    )
    footnotes_parser.set_defaults(func=cmd_footnotes)

    export_parser = sub.add_parser(
        "export",
        parents=[book_parent],
        help=(
            "Export binder Markdown to HTML, PDF, and/or EPUB "
            "(no LLM; skips existing files unless --force)"
        ),
    )
    export_parser.add_argument(
        "--mode",
        choices=list(EXPORT_MODES),
        default="report",
        help=(
            "Which binder to export: report → book-report.*; "
            "enriched → book-enriched.* (default: report)"
        ),
    )
    export_parser.add_argument(
        "--format",
        choices=("html", "pdf", "epub", "all"),
        default="all",
        help="Output format (default: all)",
    )
    export_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if export files already exist",
    )
    export_parser.set_defaults(func=cmd_export)

    return parser


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = build_parser()
    args = parser.parse_args()
    paths = BookPaths(book_id=args.book, root=ROOT)
    args.paths = paths
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()
