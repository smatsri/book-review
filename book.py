"""Load a book (Gutenberg text or EPUB) and split it into chapters."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from ebooklib import epub

DEFAULT_BOOK_ID = "alice-wonderland"

ROOT = Path(__file__).resolve().parent
DEFAULT_BOOK = (
    ROOT / "data" / "books" / DEFAULT_BOOK_ID / f"{DEFAULT_BOOK_ID}.txt"
)

START_MARKER = "*** START OF THE PROJECT GUTENBERG EBOOK"
END_MARKER = "*** END OF THE PROJECT GUTENBERG EBOOK"
CHAPTER_RE = re.compile(r"^CHAPTER\s+([IVXLCDM]+)\.\s*$", re.MULTILINE)
# TOC titles like "1. A Question Is Asked" (numbered chapters only).
EPUB_NUMBERED_TOC_RE = re.compile(r"^(\d+)\.\s+(.+)$")

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

    @property
    def epub_path(self) -> Path:
        return (
            self.root / "data" / "books" / self.book_id / f"{self.book_id}.epub"
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
        if not paths.epub_path.is_file():
            problems.append(f"missing source EPUB at {paths.epub_path}")
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


def _int_to_roman(n: int) -> str:
    if n < 1:
        raise ValueError(f"Roman numeral requires positive int, got {n}")
    parts = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    remaining = n
    out: list[str] = []
    for value, numeral in parts:
        while remaining >= value:
            out.append(numeral)
            remaining -= value
    return "".join(out)


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


class _HTMLToText(HTMLParser):
    """Strip tags/scripts; keep paragraph-ish line breaks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        # Collapse runs of blank lines to a single blank line.
        out: list[str] = []
        blank = False
        for line in lines:
            if not line:
                if out and not blank:
                    out.append("")
                    blank = True
                continue
            out.append(line)
            blank = False
        return "\n".join(out).strip()


def _html_to_text(html: str) -> str:
    parser = _HTMLToText()
    parser.feed(html)
    parser.close()
    return parser.text()


def _flatten_epub_toc(items: list | tuple) -> list[tuple[str, str]]:
    """Return (title, href) pairs from ebooklib TOC (nested Link / tuples)."""
    flat: list[tuple[str, str]] = []
    for item in items:
        if isinstance(item, tuple) and len(item) == 2:
            link, children = item
            title = (getattr(link, "title", None) or "").strip()
            href = (getattr(link, "href", None) or "").strip()
            if title and href:
                flat.append((title, href))
            if children:
                flat.extend(_flatten_epub_toc(children))
        else:
            title = (getattr(item, "title", None) or "").strip()
            href = (getattr(item, "href", None) or "").strip()
            if title and href:
                flat.append((title, href))
    return flat


def _epub_href_path(href: str) -> str:
    """Drop fragment/query; unquote; normalize to item name path."""
    parsed = urlparse(href)
    path = unquote(parsed.path)
    return path.lstrip("/")


def _epub_item_for_href(book: epub.EpubBook, href: str):
    path = _epub_href_path(href)
    if not path:
        return None
    item = book.get_item_with_href(path)
    if item is not None:
        return item
    # Some EPUBs store names without a leading folder; try basename match.
    base = Path(path).name
    for candidate in book.get_items():
        name = candidate.get_name() or ""
        if name == path or Path(name).name == base:
            return candidate
    return None


def _strip_epub_chapter_heading(text: str, number: int, title: str) -> str:
    """Remove leading 'N' / title echo common in chapter XHTML."""
    lines = text.splitlines()
    i = 0
    # Skip blank lines at start.
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return text

    first = lines[i].strip()
    num_s = str(number)
    title_compact = re.sub(r"\s+", "", title).casefold()
    first_compact = re.sub(r"\s+", "", first).casefold()

    # Lone chapter number line.
    if first == num_s or re.fullmatch(rf"{re.escape(num_s)}\.?", first):
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i < len(lines):
            second = lines[i].strip()
            second_compact = re.sub(r"\s+", "", second).casefold()
            if second_compact == title_compact:
                i += 1
        return "\n".join(lines[i:]).strip()

    # "1TITLE" or "1. TITLE" mashed on one line.
    mashed = re.match(
        rf"^{re.escape(num_s)}\.?\s*(.*)$",
        first,
        flags=re.IGNORECASE,
    )
    if mashed:
        rest = mashed.group(1).strip()
        rest_compact = re.sub(r"\s+", "", rest).casefold()
        if not rest or rest_compact == title_compact:
            i += 1
            return "\n".join(lines[i:]).strip()

    if first_compact == title_compact:
        i += 1
        return "\n".join(lines[i:]).strip()

    return text


def load_epub_chapters(path: Path) -> list[Chapter]:
    """Load chapters from EPUB via numbered TOC entries (skip front/back matter)."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing EPUB: {path}")

    book = epub.read_epub(str(path))
    toc_entries = _flatten_epub_toc(book.toc or [])
    chapters: list[Chapter] = []

    for toc_title, href in toc_entries:
        match = EPUB_NUMBERED_TOC_RE.match(toc_title.strip())
        if not match:
            continue
        number = int(match.group(1))
        title = match.group(2).strip()
        item = _epub_item_for_href(book, href)
        if item is None:
            raise ValueError(f"EPUB TOC href not found in package: {href!r}")
        raw = item.get_content().decode("utf-8", errors="replace")
        body = _strip_epub_chapter_heading(_html_to_text(raw), number, title)
        if not body:
            raise ValueError(f"EPUB chapter {number} ({title!r}) has empty body")
        chapters.append(
            Chapter(
                number=number,
                roman=_int_to_roman(number),
                title=title,
                text=body,
            )
        )

    if not chapters:
        raise ValueError(
            f"No numbered TOC chapters (N. Title) found in EPUB: {path}"
        )
    return chapters


def load_chapters_for_book(meta: BookMeta, paths: BookPaths) -> list[Chapter]:
    """Dispatch chapter load by catalog source_kind."""
    if meta.source_kind in ("gutenberg_txt", "plain_txt"):
        return load_chapters(paths.source_path)
    if meta.source_kind == "epub":
        return load_epub_chapters(paths.epub_path)
    if meta.source_kind == "pdf":
        raise ValueError(
            f"PDF ingest is not implemented yet (book {meta.id!r})."
        )
    raise ValueError(f"Unsupported source_kind: {meta.source_kind!r}")
