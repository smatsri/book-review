"""CLI for the book-review MVP pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from book import load_chapters

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
STATE_DIR = ROOT / "state"


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
    from agents.summarizer import summarize_chapter

    chapters = load_chapters()
    chapter = next((c for c in chapters if c.number == args.chapter), None)
    if chapter is None:
        available = ", ".join(str(c.number) for c in chapters)
        raise SystemExit(f"Chapter {args.chapter} not found. Available: {available}")

    out_path = OUTPUT_DIR / f"chapter-{chapter.number:02d}-summary.md"
    if out_path.exists() and not args.force:
        print(
            f"Skip {chapter.heading}: {out_path.relative_to(ROOT)} already exists "
            "(use --force to regenerate)"
        )
        return

    print(f"Summarizing {chapter.heading} ...")
    markdown = summarize_chapter(chapter)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {out_path.relative_to(ROOT)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Book review MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    chapters_parser = sub.add_parser("chapters", help="List chapters (no LLM)")
    chapters_parser.set_defaults(func=cmd_chapters)

    summarize_parser = sub.add_parser(
        "summarize", help="Summarize one chapter with the LLM"
    )
    summarize_parser.add_argument(
        "--chapter",
        type=int,
        default=1,
        help="Chapter number to summarize (default: 1)",
    )
    summarize_parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if output/chapter-NN-summary.md already exists",
    )
    summarize_parser.set_defaults(func=cmd_summarize)

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
