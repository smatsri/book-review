"""Export book-report.md to HTML, PDF, and EPUB (no LLM)."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Iterable

import markdown
from ebooklib import epub
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"
BOOK_REPORT_PATH = OUTPUT_DIR / "book-report.md"

FORMATS = ("html", "pdf", "epub")
DEFAULT_TITLE = "Book Report"

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
blockquote {
  margin: 1em 0;
  padding-left: 1em;
  border-left: 3px solid #ccc;
  color: #333;
}
hr { border: none; border-top: 1px solid #ddd; margin: 2em 0; }
code { font-family: Consolas, monospace; font-size: 0.9em; }
"""


def _body_html(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )


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


def output_path(fmt: str) -> Path:
    if fmt not in FORMATS:
        raise ValueError(f"Unknown format: {fmt}")
    return OUTPUT_DIR / f"book-report.{fmt}"


def resolve_formats(fmt: str) -> list[str]:
    if fmt == "all":
        return list(FORMATS)
    if fmt not in FORMATS:
        raise ValueError(f"Unknown format: {fmt}")
    return [fmt]


def write_html(md_text: str, dest: Path, *, title: str = DEFAULT_TITLE) -> Path:
    dest.write_text(md_to_html(md_text, title=title), encoding="utf-8")
    return dest


def write_pdf(md_text: str, dest: Path, *, title: str = DEFAULT_TITLE) -> Path:
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
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        result = pisa.CreatePDF(src=doc, dest=out, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"PDF export failed with {result.err} error(s)")
    return dest


def write_epub(md_text: str, dest: Path, *, title: str = DEFAULT_TITLE) -> Path:
    book = epub.EpubBook()
    book.set_identifier("book-review-report")
    book.set_title(title)
    book.set_language("en")

    chapter = epub.EpubHtml(title=title, file_name="report.xhtml", lang="en")
    # ebooklib wraps fragments into an XHTML document; pass body markup only.
    chapter.content = (
        f"<style type=\"text/css\">{_CSS}</style>\n{_body_html(md_text)}"
    )
    book.add_item(chapter)
    book.toc = (epub.Link("report.xhtml", title, "report"),)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

    dest.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(dest), book)
    if dest.stat().st_size < 100:
        raise RuntimeError(f"EPUB export produced a suspiciously small file: {dest}")
    return dest


_WRITERS = {
    "html": write_html,
    "pdf": write_pdf,
    "epub": write_epub,
}


def export_report(
    formats: Iterable[str] | str = "all",
    *,
    force: bool = False,
    source: Path | None = None,
    title: str = DEFAULT_TITLE,
) -> list[Path]:
    """Export book-report.md to the requested formats.

    Returns paths written. Skips existing targets unless ``force``.
    Raises SystemExit if the Markdown source is missing.
    """
    src = source or BOOK_REPORT_PATH
    if not src.exists():
        raise SystemExit(
            f"Missing {src.relative_to(ROOT) if src.is_relative_to(ROOT) else src}. "
            "Run `python main.py report` first."
        )

    if isinstance(formats, str):
        fmt_list = resolve_formats(formats)
    else:
        fmt_list = list(formats)

    md_text = src.read_text(encoding="utf-8")
    written: list[Path] = []
    for fmt in fmt_list:
        dest = output_path(fmt)
        if dest.exists() and not force:
            print(
                f"Skip export {fmt}: {dest.relative_to(ROOT)} already exists "
                "(use --force to regenerate)"
            )
            continue
        writer = _WRITERS[fmt]
        path = writer(md_text, dest, title=title)
        written.append(path)
    return written
