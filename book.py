"""Load a Gutenberg plain-text book and split it into chapters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BOOK = Path(__file__).resolve().parent / "data" / "books" / "alice-adventures-in-wonderland.txt"

START_MARKER = "*** START OF THE PROJECT GUTENBERG EBOOK"
END_MARKER = "*** END OF THE PROJECT GUTENBERG EBOOK"
CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLCDM]+)\.\s*$", re.MULTILINE)


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
