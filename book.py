"""Load a Gutenberg plain-text book and split it into chapters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BOOK_ID = "alice-wonderland"

ROOT = Path(__file__).resolve().parent
DEFAULT_BOOK = (
    ROOT / "data" / "books" / DEFAULT_BOOK_ID / f"{DEFAULT_BOOK_ID}.txt"
)

START_MARKER = "*** START OF THE PROJECT GUTENBERG EBOOK"
END_MARKER = "*** END OF THE PROJECT GUTENBERG EBOOK"
CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLCDM]+)\.\s*$", re.MULTILINE)


@dataclass(frozen=True)
class BookPaths:
    """Resolve state/output/source paths under book-id–scoped trees."""

    book_id: str
    root: Path = ROOT

    @property
    def state_dir(self) -> Path:
        return self.root / "state" / self.book_id

    @property
    def output_dir(self) -> Path:
        return self.root / "output" / self.book_id

    @property
    def illustrations_dir(self) -> Path:
        return self.output_dir / "illustrations"

    @property
    def source_path(self) -> Path:
        return (
            self.root / "data" / "books" / self.book_id / f"{self.book_id}.txt"
        )

    def chapter_summary_path(self, number: int) -> Path:
        return self.output_dir / f"chapter-{number:02d}-summary.md"

    def chapter_analysis_path(self, number: int) -> Path:
        return self.state_dir / f"chapter-{number:02d}-analysis.json"

    def chapter_draft_path(self, number: int) -> Path:
        return self.state_dir / f"chapter-{number:02d}-draft.md"

    def chapter_critique_path(self, number: int) -> Path:
        return self.state_dir / f"chapter-{number:02d}-critique.json"

    def chapter_footnotes_path(self, number: int) -> Path:
        return self.state_dir / f"chapter-{number:02d}-footnotes.json"

    def chapter_enriched_path(self, number: int) -> Path:
        return self.output_dir / f"chapter-{number:02d}-enriched.md"

    def chapters_json_path(self) -> Path:
        return self.state_dir / "chapters.json"

    def book_report_path(self) -> Path:
        return self.output_dir / "book-report.md"

    def book_enriched_path(self) -> Path:
        return self.output_dir / "book-enriched.md"

    def book_synthesis_path(self) -> Path:
        return self.output_dir / "book-synthesis.md"

    def book_rollup_path(self) -> Path:
        return self.state_dir / "book-rollup.json"

    def book_rollup_merged_path(self) -> Path:
        return self.state_dir / "book-rollup-merged.json"

    def book_visual_identity_path(self) -> Path:
        return self.state_dir / "book-visual-identity.json"

    def book_visual_characters_path(self) -> Path:
        return self.state_dir / "book-visual-characters.json"

    def book_visual_places_path(self) -> Path:
        return self.state_dir / "book-visual-places.json"

    def book_visual_scenes_path(self) -> Path:
        return self.state_dir / "book-visual-scenes.json"

    def book_visual_handoff_path(self) -> Path:
        return self.state_dir / "book-visual-handoff.json"

    def book_visual_answers_path(self) -> Path:
        return self.state_dir / "book-visual-handoff-answers.json"

    def book_visual_resolved_path(self) -> Path:
        return self.state_dir / "book-visual-resolved.json"


@dataclass(frozen=True)
class Chapter:
    number: int
    roman: str
    title: str
    text: str

    @property
    def heading(self) -> str:
        return f"CHAPTER {self.roman}. {self.title}"


def _strip_gutenberg_wrapper(raw: str) -> str:
    start = raw.find(START_MARKER)
    if start != -1:
        start = raw.find("\n", start)
        raw = raw[start + 1 :] if start != -1 else raw

    end = raw.find(END_MARKER)
    if end != -1:
        raw = raw[:end]

    return raw.strip()


def _roman_to_int(roman: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(roman.upper()):
        value = values[ch]
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return total


def load_book(path: Path | None = None) -> str:
    book_path = path or DEFAULT_BOOK
    raw = book_path.read_text(encoding="utf-8")
    return _strip_gutenberg_wrapper(raw)


def split_chapters(book_text: str) -> list[Chapter]:
    matches = list(CHAPTER_RE.finditer(book_text))
    if not matches:
        raise ValueError("No CHAPTER headings found in book text")

    chapters: list[Chapter] = []
    for i, match in enumerate(matches):
        roman = match.group(1)
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(book_text)
        body = book_text[body_start:body_end].strip()

        lines = body.splitlines()
        title = ""
        content_start = 0
        for idx, line in enumerate(lines):
            if line.strip():
                title = line.strip()
                content_start = idx + 1
                break

        text = "\n".join(lines[content_start:]).strip()
        chapters.append(
            Chapter(
                number=_roman_to_int(roman),
                roman=roman,
                title=title,
                text=text,
            )
        )

    return chapters


def load_chapters(path: Path | None = None) -> list[Chapter]:
    return split_chapters(load_book(path))
