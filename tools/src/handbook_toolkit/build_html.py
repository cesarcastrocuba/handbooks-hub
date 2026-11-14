"""Build html."""

from __future__ import annotations
import os
from pathlib import Path, PurePosixPath
from html import escape
import html
import re
import shutil
from . import design
from .docx_post import (
    prepare_docx,
)
from .artifacts import archive_tree

from .build_types import BuildError, PAYLOADS

def _one_file(directory: Path, suffix: str) -> Path:
    matches = sorted(directory.rglob(f"*{suffix}"))
    if len(matches) != 1:
        raise BuildError(
            f"expected exactly one {suffix} output under {directory}, found {len(matches)}"
        )
    return matches[0]

def _sidebar_item(href: str, label: str, active: bool = False) -> str:
    classes = "sidebar-item-text sidebar-link" + (" active" if active else "")
    return (
        '<li class="sidebar-item">\n'
        '  <div class="sidebar-item-container"> \n'
        f'  <a href="{escape(href, quote=True)}" class="{classes}">\n'
        f' <span class="menu-text">{escape(label)}</span></a>\n'
        "  </div>\n"
        "</li>\n"
    )

SIDEBAR_DOCUMENT_CONTROL = re.compile(
    r'<li class="sidebar-item">\s*<div class="sidebar-item-container">\s*'
    r'<a href="([^"]*)"[^>]*>\s*<span class="menu-text">Document Control</span>'
    r"</a>\s*</div>\s*</li>",
    re.DOTALL,
)

def _add_tables_navigation(site: Path) -> None:
    """Put the List of Tables in the book sidebar, below Document Control.

    The page is generated after Quarto renders the book, so the navigation is
    injected into every rendered page instead of living in ``_quarto.yml``.
    """

    for path in sorted(site.rglob("*.html")):
        if path.name == "tables.html":
            continue
        text = path.read_text(encoding="utf-8")
        href = PurePosixPath(os.path.relpath(site / "tables.html", path.parent)).as_posix()
        if 'menu-text">Tables</span>' in text:
            continue

        def replace(match: re.Match[str]) -> str:
            return match.group(0) + _sidebar_item(href, "Tables")

        updated = SIDEBAR_DOCUMENT_CONTROL.sub(replace, text, count=1)
        if updated == text:
            item = _sidebar_item(href, "Tables")
            updated = re.sub(
                r'(<ul class="list-unstyled[^"]*">)',
                lambda match: match.group(1) + item,
                text,
                count=1,
            )
        if updated != text:
            path.write_text(updated, encoding="utf-8")

def _inject_table_index(site: Path) -> None:
    """Create the web List of Tables page and link it from the sidebar."""

    index = site / "index.html"
    if not index.is_file():
        return
    entries: list[tuple[int, str, str, str]] = []

    def order(path: Path) -> int:
        relative = path.relative_to(site).as_posix()
        if relative == "index.html" or "/front-matter/" in relative:
            return 0
        if "/chapters/" in relative:
            return 1
        if "/appendices/" in relative:
            return 2
        return 3

    pattern = re.compile(
        r'<div id="(tbl-[^"]+)"[^>]*>.*?<figcaption[^>]*>(.*?)</figcaption>',
        re.DOTALL,
    )
    for path in sorted(site.rglob("*.html"), key=lambda item: (order(item), item.as_posix())):
        if path.name == "tables.html":
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            caption = html.unescape(re.sub(r"<[^>]+>", "", match.group(2))).strip()
            if caption:
                relative = path.relative_to(site).as_posix()
                entries.append((order(path), relative, match.group(1), caption))
    if not entries:
        items = "<li>This edition has no tables.</li>"
    else:
        items = "".join(
            f'<li><a href="{escape(relative)}#{escape(identifier, quote=True)}">'
            f"{escape(caption)}</a></li>"
            for _position, relative, identifier, caption in entries
        )
    section = (
        '<section class="list-of-tables" aria-labelledby="list-of-tables-title">'
        f"<ul>{items}</ul></section>"
    )
    _add_tables_navigation(site)
    text = index.read_text(encoding="utf-8")
    book_title = "Handbook"
    title_match = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
    if title_match:
        book_title = html.unescape(title_match.group(1)).strip()
    main = re.search(r"<main\b[^>]*>", text)
    closing = text.rfind("</main>")
    if main is None or closing < 0:
        page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>List of Tables — {escape(book_title)}</title>
<link rel="stylesheet" href=".handbook-render/html/design-tokens.css">
<link rel="stylesheet" href=".handbook-render/html/handbook.css">
</head><body class="quarto-light">
<main id="quarto-document-content" class="content">
<h1 class="title">List of Tables</h1>{section}</main></body></html>"""
        (site / "tables.html").write_text(page, encoding="utf-8")
        return
    header = (
        '<header id="title-block-header">'
        '<h1 class="title" id="list-of-tables-title">List of Tables</h1></header>'
    )
    page = (
        text[: main.end()]
        + header
        + section
        + text[closing:]
    )
    page = re.sub(
        r"<title>.*?</title>",
        lambda match: f"<title>List of Tables — {escape(book_title)}</title>",
        page,
        count=1,
        flags=re.DOTALL,
    )
    page = re.sub(
        r'<nav id="TOC"[^>]*>.*?</nav>',
        '<nav id="TOC" role="doc-toc" class="toc-active">'
        '<h2 id="toc-title">Contents</h2>'
        '<ul><li><a href="#list-of-tables-title" class="nav-link active">'
        "List of Tables</a></li></ul></nav>",
        page,
        count=1,
        flags=re.DOTALL,
    )
    page = page.replace(
        "sidebar-item-text sidebar-link active",
        "sidebar-item-text sidebar-link",
    )
    page = re.sub(
        r'class="sidebar-item-text sidebar-link"(>\s*<span class="menu-text">Tables</span>)',
        r'class="sidebar-item-text sidebar-link active"\1',
        page,
        count=1,
    )
    page = re.sub(
        r'<nav class="quarto-page-breadcrumbs"[^>]*>.*?</nav>',
        '<nav class="quarto-page-breadcrumbs" aria-label="Breadcrumbs">'
        '<ol class="breadcrumb"><li class="breadcrumb-item">List of Tables</li></ol></nav>',
        page,
        count=1,
        flags=re.DOTALL,
    )
    page = re.sub(
        r'<nav class="page-navigation"[^>]*>.*?</nav>',
        "",
        page,
        count=1,
        flags=re.DOTALL,
    )
    (site / "tables.html").write_text(page, encoding="utf-8")

def _payload_paths(workspace: Path, dist: Path, epoch: int) -> dict[str, Path]:
    output = workspace / "_output"
    if not (output / "index.html").is_file():
        raise BuildError("Quarto did not produce _output/index.html")
    site = dist.parent / "site"
    shutil.copytree(
        output,
        site,
        ignore=shutil.ignore_patterns("*.pdf", "*.docx", "*.typst"),
    )
    # Quarto copies only the font files referenced by the stylesheet. The OFL
    # notices must travel with them, so they are added explicitly before the
    # exact tree is archived and deployed.
    for relative, data in design.font_licenses().items():
        target = site / ".handbook-render" / "fonts" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    _inject_table_index(site)
    archive_tree(site, dist / PAYLOADS["html"], epoch)
    pdf = _one_file(output, ".pdf")
    docx = _one_file(output, ".docx")
    shutil.copy2(pdf, dist / PAYLOADS["pdf"])
    shutil.copy2(docx, dist / PAYLOADS["docx"])
    prepare_docx(dist / PAYLOADS["docx"])
    return {
        "html": dist / PAYLOADS["html"],
        "pdf": dist / PAYLOADS["pdf"],
        "docx": dist / PAYLOADS["docx"],
        "source": dist / PAYLOADS["source"],
    }
