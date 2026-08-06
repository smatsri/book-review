"""CLI for the book-review MVP pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from book import Chapter, load_chapters
from rollup import apply_alias_clusters, build_book_rollup

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
STATE_DIR = ROOT / "state"
BOOK_REPORT_PATH = OUTPUT_DIR / "book-report.md"
BOOK_ROLLUP_PATH = STATE_DIR / "book-rollup.json"
BOOK_ROLLUP_MERGED_PATH = STATE_DIR / "book-rollup-merged.json"

# Pipeline stages in order. `--from STAGE` regenerates that stage and everything after.
STAGES = ("reader", "draft", "critic", "revise")


def chapter_summary_path(number: int) -> Path:
    return OUTPUT_DIR / f"chapter-{number:02d}-summary.md"


def chapter_analysis_path(number: int) -> Path:
    return STATE_DIR / f"chapter-{number:02d}-analysis.json"


def chapter_draft_path(number: int) -> Path:
    return STATE_DIR / f"chapter-{number:02d}-draft.md"


def chapter_critique_path(number: int) -> Path:
    return STATE_DIR / f"chapter-{number:02d}-critique.json"


def write_book_report(chapters: list[Chapter]) -> Path:
    """Merge existing chapter summaries into one Markdown report (no LLM)."""
    parts: list[str] = []
    missing: list[int] = []
    for ch in chapters:
        path = chapter_summary_path(ch.number)
        if not path.exists():
            missing.append(ch.number)
            continue
        parts.append(path.read_text(encoding="utf-8").strip())

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
    body = "\n\n---\n\n".join(parts)
    BOOK_REPORT_PATH.write_text(f"{header}\n---\n\n{body}\n", encoding="utf-8")
    return BOOK_REPORT_PATH


def write_book_rollup(chapters: list[Chapter]) -> Path:
    """Merge Reader analyses into state/book-rollup.json (no LLM)."""
    analyses: list[dict] = []
    missing: list[int] = []
    for ch in chapters:
        path = chapter_analysis_path(ch.number)
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
    BOOK_ROLLUP_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return BOOK_ROLLUP_PATH


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

    out_path = chapter_summary_path(chapter.number)
    notes_path = chapter_analysis_path(chapter.number)
    draft_path = chapter_draft_path(chapter.number)
    critique_path = chapter_critique_path(chapter.number)

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


def cmd_chapters(_: argparse.Namespace) -> None:
    chapters = load_chapters()
    print(f"Found {len(chapters)} chapters:\n")
    for ch in chapters:
        words = len(ch.text.split())
        print(f"  {ch.number:2d}. {ch.heading}  ({words} words)")

    state_path = STATE_DIR / "chapters.json"
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
    chapters = load_chapters()

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
            force=args.force,
            from_stage=args.from_stage,
        )
        if result == "wrote":
            wrote += 1
        else:
            skipped += 1

    if args.all:
        print(f"\nMap done: {wrote} written, {skipped} skipped")
        report_path = write_book_report(chapters)
        print(f"Wrote {report_path.relative_to(ROOT)}")
        rollup_path = write_book_rollup(chapters)
        print(f"Wrote {rollup_path.relative_to(ROOT)}")


def cmd_report(_: argparse.Namespace) -> None:
    report_path = write_book_report(load_chapters())
    print(f"Wrote {report_path.relative_to(ROOT)}")


def cmd_rollup(_: argparse.Namespace) -> None:
    rollup_path = write_book_rollup(load_chapters())
    payload = json.loads(rollup_path.read_text(encoding="utf-8"))
    print(f"Wrote {rollup_path.relative_to(ROOT)}")
    print(
        f"  {len(payload['chapters_included'])} chapters, "
        f"{len(payload['characters'])} characters, "
        f"{len(payload['themes'])} themes"
    )


def write_book_rollup_merged(*, force: bool) -> Path | None:
    """LLM alias merge of book-rollup.json → book-rollup-merged.json.

    Returns the path written, or None if skipped.
    """
    if not BOOK_ROLLUP_PATH.exists():
        raise SystemExit(
            f"Missing {BOOK_ROLLUP_PATH.relative_to(ROOT)}. "
            "Run `python main.py rollup` first."
        )

    if BOOK_ROLLUP_MERGED_PATH.exists() and not force:
        print(
            f"Skip aliases: {BOOK_ROLLUP_MERGED_PATH.relative_to(ROOT)} already exists "
            "(use --force to regenerate)"
        )
        return None

    from agents.alias_merger import propose_alias_clusters

    rollup = json.loads(BOOK_ROLLUP_PATH.read_text(encoding="utf-8"))
    print("Proposing character/theme alias clusters ...")
    clusters = propose_alias_clusters(rollup)
    payload = apply_alias_clusters(rollup, clusters)
    BOOK_ROLLUP_MERGED_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return BOOK_ROLLUP_MERGED_PATH


def cmd_aliases(args: argparse.Namespace) -> None:
    merged_path = write_book_rollup_merged(force=args.force)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Book review MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    chapters_parser = sub.add_parser("chapters", help="List chapters (no LLM)")
    chapters_parser.set_defaults(func=cmd_chapters)

    summarize_parser = sub.add_parser(
        "summarize",
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
        help="Merge existing chapter summaries into output/book-report.md (no LLM)",
    )
    report_parser.set_defaults(func=cmd_report)

    rollup_parser = sub.add_parser(
        "rollup",
        help=(
            "Merge chapter analyses into state/book-rollup.json "
            "(characters + themes; no LLM)"
        ),
    )
    rollup_parser.set_defaults(func=cmd_rollup)

    aliases_parser = sub.add_parser(
        "aliases",
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

    return parser


def main() -> None:
    load_dotenv(ROOT / ".env")
    OUTPUT_DIR.mkdir(exist_ok=True)
    STATE_DIR.mkdir(exist_ok=True)

    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
