"""CLI for the book-review MVP pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from book import Chapter, load_chapters

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
STATE_DIR = ROOT / "state"
BOOK_REPORT_PATH = OUTPUT_DIR / "book-report.md"


def chapter_summary_path(number: int) -> Path:
    return OUTPUT_DIR / f"chapter-{number:02d}-summary.md"


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


def summarize_one(chapter: Chapter, *, force: bool) -> str:
    """Summarize one chapter to disk. Returns 'wrote', 'skip', or raises."""
    from agents.summarizer import summarize_chapter

    out_path = chapter_summary_path(chapter.number)
    if out_path.exists() and not force:
        print(
            f"Skip {chapter.heading}: {out_path.relative_to(ROOT)} already exists "
            "(use --force to regenerate)"
        )
        return "skip"

    print(f"Summarizing {chapter.heading} ...")
    markdown = summarize_chapter(chapter)
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
        result = summarize_one(chapter, force=args.force)
        if result == "wrote":
            wrote += 1
        else:
            skipped += 1

    if args.all:
        print(f"\nMap done: {wrote} written, {skipped} skipped")
        report_path = write_book_report(chapters)
        print(f"Wrote {report_path.relative_to(ROOT)}")


def cmd_report(_: argparse.Namespace) -> None:
    report_path = write_book_report(load_chapters())
    print(f"Wrote {report_path.relative_to(ROOT)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Book review MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    chapters_parser = sub.add_parser("chapters", help="List chapters (no LLM)")
    chapters_parser.set_defaults(func=cmd_chapters)

    summarize_parser = sub.add_parser(
        "summarize",
        help="Summarize chapter(s) with the LLM; --all also writes book-report.md",
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
        help="Summarize every chapter, then merge into output/book-report.md",
    )
    summarize_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if output/chapter-NN-summary.md already exists",
    )
    summarize_parser.set_defaults(func=cmd_summarize)

    report_parser = sub.add_parser(
        "report",
        help="Merge existing chapter summaries into output/book-report.md (no LLM)",
    )
    report_parser.set_defaults(func=cmd_report)

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
