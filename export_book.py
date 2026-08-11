"""Export book Markdown to HTML, PDF, and EPUB (no LLM)."""

from __future__ import annotations

import html
import re
from functools import partial
from pathlib import Path
from typing import Iterable

import markdown
from ebooklib import epub
from xhtml2pdf import pisa

from book import BookPaths, DEFAULT_BOOK_ID, ROOT

ILLUSTRATIONS_PREFIX = "illustrations/"

FORMATS = ("html", "pdf", "epub")
EXPORT_MODES = ("report", "enriched")
DEFAULT_TITLE = "Book Report"
ENRICHED_TITLE = "Alice's Adventures in Wonderland"

_MODE_CONFIG = {
    "report": {
        "stem": "book-report",
        "title": DEFAULT_TITLE,
        "binder_hint": "python main.py report",
        "source_attr": "book_report_path",
    },
    "enriched": {
        "stem": "book-enriched",
        "title": ENRICHED_TITLE,
        "binder_hint": "python main.py enriched",
        "source_attr": "book_enriched_path",
    },
}

_CSS = """
body {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.55;
  max-width: 42rem;
  margin: 2rem auto;
  padding: 0 1.25rem;
  color: #1a1a1a;
}
h1, h2, h3 {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.25;
  margin-top: 1.6em;
}
h1 { font-size: 1.75rem; }
h2 { font-size: 1.35rem; }
h3 { font-size: 1.15rem; }
p, li { font-size: 1rem; }
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1em 0;
}
blockquote {
  margin: 1em 0;
  padding-left: 1em;
  border-left: 3px solid #ccc;
  color: #333;
}
hr { border: none; border-top: 1px solid #ddd; margin: 2em 0; }
code { font-family: Consolas, monospace; font-size: 0.9em; }
"""

_IMG_SRC_RE = re.compile(
    r"""<img\b[^>]*\bsrc=["']([^"']+)["']""",
    re.IGNORECASE,
)


def _body_html(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )


def _illustration_srcs(body: str) -> list[str]:
    """Return unique ``illustrations/…`` src values from HTML body order."""
    seen: set[str] = set()
    out: list[str] = []
    for match in _IMG_SRC_RE.finditer(body):
        src = match.group(1).strip()
        if not src.startswith(ILLUSTRATIONS_PREFIX):
            continue
        if src in seen:
            continue
        seen.add(src)
        out.append(src)
    return out


def _resolve_illustration(src: str, *, base: Path) -> Path | None:
    """Map a relative ``illustrations/…`` src to an existing file under base."""
    if not src.startswith(ILLUSTRATIONS_PREFIX):
        return None
    # Normalize: no ``..`` escapes.
    rel = Path(src)
    if rel.is_absolute() or ".." in rel.parts:
        return None
    path = (base / rel).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def _existing_illustration_paths(body: str, *, base: Path) -> list[Path]:
    paths: list[Path] = []
    for src in _illustration_srcs(body):
        resolved = _resolve_illustration(src, base=base)
        if resolved is not None:
            paths.append(resolved)
    return paths


def md_to_html(md_text: str, title: str = DEFAULT_TITLE) -> str:
    """Full HTML document with embedded CSS."""
    body = _body_html(md_text)
    safe_title = html.escape(title)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8"/>\n'
        f"<title>{safe_title}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


def output_path(fmt: str, stem: str = "book-report", *, output_dir: Path) -> Path:
    if fmt not in FORMATS:
        raise ValueError(f"Unknown format: {fmt}")
    return output_dir / f"{stem}.{fmt}"


def resolve_formats(fmt: str) -> list[str]:
    if fmt == "all":
        return list(FORMATS)
    if fmt not in FORMATS:
        raise ValueError(f"Unknown format: {fmt}")
    return [fmt]


def write_html(md_text: str, dest: Path, *, title: str = DEFAULT_TITLE) -> Path:
    dest.write_text(md_to_html(md_text, title=title), encoding="utf-8")
    return dest


def _pdf_link_callback(uri: str, rel: str, *, output_dir: Path) -> str:
    """Resolve relative image URIs for xhtml2pdf against output_dir."""
    del rel  # unused; required by pisa signature
    if not uri:
        return uri
    # Already absolute / scheme URLs: leave alone.
    if "://" in uri or uri.startswith("data:"):
        return uri
    path = Path(uri)
    if path.is_absolute():
        return str(path) if path.is_file() else uri
    resolved = (
        _resolve_illustration(uri, base=output_dir)
        if uri.startswith(ILLUSTRATIONS_PREFIX)
        else None
    )
    if resolved is not None:
        return str(resolved)
    candidate = (output_dir / uri).resolve()
    try:
        candidate.relative_to(output_dir.resolve())
    except ValueError:
        return uri
    return str(candidate) if candidate.is_file() else uri


def write_pdf(
    md_text: str,
    dest: Path,
    *,
    title: str = DEFAULT_TITLE,
    output_dir: Path | None = None,
) -> Path:
    # xhtml2pdf prefers XHTML-ish markup; keep a simple document wrapper.
    body = _body_html(md_text)
    doc = (
        '<!DOCTYPE html>\n'
        '<html>\n'
        "<head>\n"
        '<meta charset="utf-8"/>\n'
        f"<title>{html.escape(title)}</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )
    base = output_dir if output_dir is not None else dest.parent
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        result = pisa.CreatePDF(
            src=doc,
            dest=out,
            encoding="utf-8",
            link_callback=partial(_pdf_link_callback, output_dir=base),
        )
    if result.err:
        raise RuntimeError(f"PDF export failed with {result.err} error(s)")
    return dest


def write_epub(
    md_text: str,
    dest: Path,
    *,
    title: str = DEFAULT_TITLE,
    output_dir: Path | None = None,
) -> Path:
    book = epub.EpubBook()
    book.set_identifier("book-review-report")
    book.set_title(title)
    book.set_language("en")

    body = _body_html(md_text)
    chapter = epub.EpubHtml(title=title, file_name="report.xhtml", lang="en")
    # ebooklib wraps fragments into an XHTML document; pass body markup only.
    # Keep illustrations/ src so it matches packaged EpubItem paths.
    chapter.content = f'<style type="text/css">{_CSS}</style>\n{body}'
    book.add_item(chapter)

    base = output_dir if output_dir is not None else dest.parent
    for path in _existing_illustration_paths(body, base=base):
        item = epub.EpubItem(
            uid=f"ill-{path.name}",
            file_name=f"{ILLUSTRATIONS_PREFIX}{path.name}",
            media_type="image/jpeg",
            content=path.read_bytes(),
        )
        book.add_item(item)

    book.toc = (epub.Link("report.xhtml", title, "report"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

    dest.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(dest), book)
    if dest.stat().st_size < 100:
        raise RuntimeError(f"EPUB export produced a suspiciously small file: {dest}")
    return dest


def export_report(
    formats: Iterable[str] | str = "all",
    *,
    force: bool = False,
    mode: str = "report",
    paths: BookPaths | None = None,
    source: Path | None = None,
    title: str | None = None,
) -> list[Path]:
    """Export binder Markdown to the requested formats.

    ``mode`` selects source stem/title (``report`` or ``enriched``). Explicit
    ``source`` / ``title`` override the mode defaults. Artifact dirs come from
    ``paths`` (default ``BookPaths`` for ``kafka-penal-colony``).

    Returns paths written. Skips existing targets unless ``force``.
    Raises SystemExit if the Markdown source is missing.

    Scene images referenced as ``illustrations/…`` are left as relative links
    for HTML (beside ``output/``), packed into the EPUB, and resolved via
    xhtml2pdf ``link_callback`` for PDF (best-effort).
    """
    if mode not in _MODE_CONFIG:
        raise ValueError(f"Unknown export mode: {mode}")
    if paths is None:
        paths = BookPaths(book_id=DEFAULT_BOOK_ID, root=ROOT)
    cfg = _MODE_CONFIG[mode]
    source_attr = cfg["source_attr"]
    assert isinstance(source_attr, str)
    src = source or getattr(paths, source_attr)()
    stem = cfg["stem"]
    export_title = title if title is not None else cfg["title"]
    assert isinstance(src, Path)
    assert isinstance(stem, str)
    assert isinstance(export_title, str)

    if not src.exists():
        rel = src.relative_to(ROOT) if src.is_relative_to(ROOT) else src
        raise SystemExit(
            f"Missing {rel}. Run `{cfg['binder_hint']}` first."
        )

    if isinstance(formats, str):
        fmt_list = resolve_formats(formats)
    else:
        fmt_list = list(formats)

    md_text = src.read_text(encoding="utf-8")
    written: list[Path] = []
    output_dir = paths.output_dir
    for fmt in fmt_list:
        dest = output_path(fmt, stem=stem, output_dir=output_dir)
        if dest.exists() and not force:
            print(
                f"Skip export {fmt}: {dest.relative_to(ROOT)} already exists "
                "(use --force to regenerate)"
            )
            continue
        if fmt == "html":
            path = write_html(md_text, dest, title=export_title)
        elif fmt == "pdf":
            path = write_pdf(
                md_text, dest, title=export_title, output_dir=output_dir
            )
        else:
            path = write_epub(
                md_text, dest, title=export_title, output_dir=output_dir
            )
        written.append(path)
    return written
