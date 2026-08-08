"""Load a Gutenberg plain-text book and split it into chapters."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_BOOK_ID = "alice-wonderland"

ROOT = Path(__file__).resolve().parent
DEFAULT_BOOK = (
    ROOT / "data" / "books" / DEFAULT_BOOK_ID / f"{DEFAULT_BOOK_ID}.txt"
)

START_MARKER = "*** START OF THE PROJECT GUTENBERG EBOOK"
END_MARKER = "*** END OF THE PROJECT GUTENBERG EBOOK"
CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLCDM]+)\.\s*$", re.MULTILINE)

SOURCE_KINDS = frozenset({"gutenberg_txt", "plain_txt", "pdf", "epub"})


@dataclass(frozen=True)
class BookMeta:
    """Light registry fields for one book (see data/books/<id>/meta.json)."""

    id: str
    title: str
    author: str
    source_kind: str


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
    def books_dir(self) -> Path:
        return self.root / "data" / "books"

    @property
    def meta_path(self) -> Path:
        return self.books_dir / self.book_id / "meta.json"

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


def books_dir(root: Path = ROOT) -> Path:
    return root / "data" / "books"


def catalog_path(root: Path = ROOT) -> Path:
    return books_dir(root) / "catalog.json"


def _parse_book_meta(raw: object, *, expected_id: str | None = None) -> BookMeta:
    if not isinstance(raw, dict):
        raise ValueError("Book meta must be a JSON object")
    missing = [k for k in ("id", "title", "author", "source_kind") if k not in raw]
    if missing:
        raise ValueError(f"Book meta missing fields: {', '.join(missing)}")
    book_id = raw["id"]
    title = raw["title"]
    author = raw["author"]
    source_kind = raw["source_kind"]
    if not isinstance(book_id, str) or not book_id.strip():
        raise ValueError("Book meta id must be a non-empty string")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Book meta title must be a non-empty string")
    if not isinstance(author, str) or not author.strip():
        raise ValueError("Book meta author must be a non-empty string")
    if not isinstance(source_kind, str) or source_kind not in SOURCE_KINDS:
        allowed = ", ".join(sorted(SOURCE_KINDS))
        raise ValueError(f"Book meta source_kind must be one of: {allowed}")
    if expected_id is not None and book_id != expected_id:
        raise ValueError(
            f"Book meta id {book_id!r} does not match directory {expected_id!r}"
        )
    return BookMeta(
        id=book_id,
        title=title.strip(),
        author=author.strip(),
        source_kind=source_kind,
    )


def load_book_meta(book_id: str, root: Path = ROOT) -> BookMeta:
    path = books_dir(root) / book_id / "meta.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing book meta: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    return _parse_book_meta(raw, expected_id=book_id)


def load_catalog(root: Path = ROOT) -> list[BookMeta]:
    """Discover books from data/books/*/meta.json (source of truth)."""
    base = books_dir(root)
    if not base.is_dir():
        return []
    books: list[BookMeta] = []
    for child in sorted(base.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name.startswith("."):
            continue
        meta_file = child / "meta.json"
        if not meta_file.is_file():
            continue
        books.append(load_book_meta(child.name, root=root))
    return books


def write_catalog(root: Path = ROOT, books: list[BookMeta] | None = None) -> Path:
    """Write data/books/catalog.json from per-book meta (derived snapshot)."""
    entries = books if books is not None else load_catalog(root)
    path = catalog_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"books": [asdict(b) for b in entries]}
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def require_book_id(book_id: str, root: Path = ROOT) -> BookMeta:
    """Return meta for book_id or raise ValueError with known ids."""
    catalog = load_catalog(root)
    for meta in catalog:
        if meta.id == book_id:
            return meta
    known = ", ".join(m.id for m in catalog) if catalog else "(none — add meta.json)"
    raise ValueError(
        f"Unknown book id {book_id!r}. Known: {known}. "
        f"Add data/books/{book_id}/meta.json with id, title, author, source_kind."
    )


def validate_book_meta(meta: BookMeta, root: Path = ROOT) -> list[str]:
    """Return human-readable problems for one catalog entry (empty if ok)."""
    problems: list[str] = []
    paths = BookPaths(book_id=meta.id, root=root)
    if not paths.meta_path.is_file():
        problems.append(f"missing meta.json at {paths.meta_path}")
    if meta.source_kind in ("gutenberg_txt", "plain_txt") and not paths.source_path.is_file():
        problems.append(f"missing source text at {paths.source_path}")
    elif meta.source_kind == "pdf":
        pdf = paths.books_dir / meta.id / f"{meta.id}.pdf"
        if not pdf.is_file():
            problems.append(f"missing source PDF at {pdf}")
    elif meta.source_kind == "epub":
        epub = paths.books_dir / meta.id / f"{meta.id}.epub"
        if not epub.is_file():
            problems.append(f"missing source EPUB at {epub}")
    return problems


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
