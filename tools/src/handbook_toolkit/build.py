"""Build a handbook release payload set without publishing it.

The build is deliberately conservative:

* the source repository must be clean at the exact requested commit;
* only tracked files from that commit are staged, via ``git archive``;
* Quarto renders HTML, Typst/PDF, DOCX and a single-file GitHub-flavoured Markdown edition;
* all five payloads are inspected before identity files are written;
* the five payloads plus manifest/checksums are assembled in a private staging directory;
* the verified staging directory is atomically renamed to the final output.

This module does not publish, upload, deploy, approve or release anything.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import platform
import posixpath
from html import escape
import html
import re
import xml.etree.ElementTree as ET
import shutil
import subprocess
import tempfile
from typing import Any
import zipfile
from zipfile import ZIP_DEFLATED, ZipFile
import zlib

import yaml

from . import __version__
from . import design
from .artifacts import archive_tree, inspect_payload
from .publication import verify_publication, write_manifest
from .profiles import validate_profile
from .profile_resources import load_profile
from .books import validate_book
from .manuscript import validate_manuscript
from .references import validate_references
from .render_resources import stage_render_resources
from .validation import (
    DocumentError,
    load_document,
    load_packaged_schema,
)
from .print_layout import (
    DEFAULT_RUNNING_HEADER,
    document_control_table,
    edition_date,
    edition_fields,
    inject_document_control,
    license_label,
    toc_depth,
    typst_book_data,
    typst_front,
)

QUARTO_VERSION = "1.11.9"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?\Z")
ROLES = ("html", "pdf", "docx", "markdown", "source")
PAYLOADS = {
    "html": "book-html.zip",
    "pdf": "book.pdf",
    "docx": "book.docx",
    "markdown": "book.md",
    "source": "book-source.zip",
}
MARKDOWN_ENTRY = "book-markdown.qmd"
MARKDOWN_DIR = "_markdown"
FRONT_MATTER_BLOCK = re.compile(r"\A---[ \t]*\n.*?\n---[ \t]*\n", re.DOTALL)
INCLUDE_SHORTCODE = re.compile(r"\{\{<[ \t]*include[ \t]+([^>\s]+)[ \t]*>\}\}")
XREF_LINK = re.compile(r'<a href="[^"]*" class="quarto-xref">(.*?)</a>', re.DOTALL)
FIGURE_BLOCK = re.compile(r'<div id="fig-[^"]*">\s*(.*?)\s*</div>', re.DOTALL)
TABLE_BLOCK = re.compile(r'<div id="tbl-[^"]*">\s*(.*?)\s*</div>', re.DOTALL)
IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
# CommonMark: a backslash before ASCII punctuation is an escape and renders as that character.
BACKSLASH_ESCAPE = re.compile(r"\\(?=[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")
OMITTED_FIGURE = "*(figure image not included in the Markdown edition)*"
MARKDOWN_NOTE = (
    "> Markdown edition: the whole book in reading order, generated from the same source commit as "
    "the other payloads. Figures appear as their captions only; use the HTML, PDF or DOCX payload "
    "for the images. Table and figure counters run sequentially in this file."
)


class BuildError(ValueError):
    """Raised when a build cannot produce a verified release directory."""


@dataclass(frozen=True)
class BuildResult:
    output: Path
    commit: str
    version: str
    epoch: int
    tool_versions: dict[str, str]


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildError(f"cannot run {command[0]}: {exc}") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise BuildError(f"{' '.join(command)} failed: {detail}")
    return (result.stdout.strip() or result.stderr.strip())


def _git(repo: Path, *args: str) -> str:
    return _run(["git", "-C", str(repo), *args])


def _require_clean_commit(repo: Path, commit: str) -> None:
    if not COMMIT.fullmatch(commit):
        raise BuildError("commit must be a full 40-character lowercase SHA")
    if not repo.is_dir():
        raise BuildError(f"repository does not exist: {repo}")
    head = _git(repo, "rev-parse", "HEAD")
    if head != commit:
        raise BuildError(f"requested commit {commit} is not HEAD ({head})")
    if _git(repo, "status", "--porcelain"):
        raise BuildError("source repository must be clean before building")


def _reading_groups(book: dict[str, Any], repo: Path) -> dict[str, list[str]]:
    manuscript = book["manuscript"]
    root = repo / manuscript["root"]
    path = repo / manuscript["reading_order"]
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BuildError(f"cannot read reading order {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise BuildError("reading order must be a YAML mapping")
    groups: dict[str, list[str]] = {}
    for group in ("front", "chapters", "back", "appendices", "references"):
        values = document.get(group, []) or []
        if not isinstance(values, list):
            raise BuildError(f"reading order group {group} must be a list")
        checked: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value.endswith(".qmd"):
                raise BuildError(f"reading order entry is not a .qmd path: {value!r}")
            candidate = (root / value).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError as exc:
                raise BuildError(f"reading order entry escapes manuscript root: {value}") from exc
            if not candidate.is_file():
                raise BuildError(f"reading order entry does not exist: {value}")
            checked.append(f"{manuscript['root']}/{value}")
        groups[group] = checked
    if not groups["chapters"]:
        raise BuildError("reading order contains no chapters")
    return groups


def _validate_manuscripts(
    workspace: Path,
    book: dict[str, Any],
    profile: dict[str, Any],
    mode: str,
) -> None:
    groups = _reading_groups(book, workspace)
    chapters = groups["chapters"]
    appendices = groups["appendices"]
    if mode == "section-pilot":
        if len(chapters) != 1 or appendices:
            raise BuildError(
                "section-pilot mode requires exactly one chapter and no appendices in the reading order"
            )
        targets = chapters
    else:
        # Front matter, back matter and references are separate special groups.
        targets = [*chapters, *appendices]
    for entry in targets:
        path = workspace / entry
        result = validate_manuscript(path, profile, mode)
        if not result.ok:
            raise BuildError(
                f"manuscript validation failed for {entry}: "
                + "; ".join(map(str, result.issues))
            )


def _book_version(repo: Path, requested: str | None) -> str:
    if requested is not None:
        version = requested
    else:
        path = repo / "publishing/metadata.yaml"
        try:
            metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise BuildError(f"cannot read publishing/metadata.yaml: {exc}") from exc
        version = metadata.get("version") if isinstance(metadata, dict) else None
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise BuildError("book version must be an exact semantic version such as 1.0.0")
    return version


def _require_prerelease_version(version: str, mode: str, preview: bool) -> None:
    if (mode == "section-pilot" or preview) and "-" not in version:
        raise BuildError(
            "section-pilot and --preview builds require a prerelease book version "
            "such as 0.1.0-preview, not a stable release version"
        )


def _epoch(repo: Path, commit: str, requested: int | None) -> int:
    if requested is not None:
        epoch = requested
    elif os.environ.get("SOURCE_DATE_EPOCH"):
        try:
            epoch = int(os.environ["SOURCE_DATE_EPOCH"])
        except ValueError as exc:
            raise BuildError("SOURCE_DATE_EPOCH must be an integer") from exc
    else:
        epoch = int(_git(repo, "show", "-s", "--format=%ct", commit))
    if epoch < 0:
        raise BuildError("source epoch must be nonnegative")
    return epoch


def _tool_versions(quarto: str) -> dict[str, str]:
    quarto_version = _run([quarto, "--version"]).splitlines()[-1].strip()
    if quarto_version != QUARTO_VERSION:
        raise BuildError(
            f"Quarto {QUARTO_VERSION} is required; found {quarto_version or 'unknown'}"
        )
    pandoc = _run([quarto, "pandoc", "--version"]).splitlines()[0].split()[-1]
    typst = _run([quarto, "typst", "--version"]).splitlines()[0].split()[1]
    return {
        "quarto": quarto_version,
        "pandoc": pandoc,
        "typst": typst,
        "python": platform.python_version(),
        "zlib": zlib.ZLIB_RUNTIME_VERSION,
    }


def _strip_heading_number(title: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*[ .]+", "", title).strip()


def _transform_chapter(text: str, chapter_number: int) -> str:
    """Stage a chapter wrapper and explicit table captions without changing source."""

    front: dict[str, Any] = {}
    body = text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if match:
        try:
            loaded = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise BuildError(f"cannot parse staged chapter front matter: {exc}") from exc
        if isinstance(loaded, dict):
            front = loaded
        body = match.group(2)
    front.pop("title", None)

    lines = body.splitlines()
    first = next(
        (index for index, line in enumerate(lines) if re.match(r"^#{1,3}\s+", line)),
        None,
    )
    if first is None:
        raise BuildError("staged chapter has no heading to use as the rendered chapter title")
    heading = lines[first]
    title = _strip_heading_number(re.sub(r"^#{1,3}\s+", "", heading))
    if len(re.findall(r"[A-Za-z]", title)) < 3:
        raise BuildError("staged chapter heading is not meaningful")
    remaining = lines[:first] + lines[first + 1 :]

    output: list[str] = [f"# {title}", ""]
    if front:
        output = ["---", *yaml.safe_dump(front, sort_keys=False).splitlines(), "---", "", *output]
    table_number = 0
    previous = ""
    for line in remaining:
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            line = f"{heading_match.group(1)} {_strip_heading_number(heading_match.group(2))}"
        caption = re.match(r"^:\s+(.*\S)\s*$", line)
        if caption and previous.lstrip().startswith("|"):
            table_number += 1
            if not re.search(r"\{#tbl-[^}]+\}\s*$", caption.group(1)):
                caption_text = re.sub(r"\s*\{[^}]*\}\s*$", "", caption.group(1)).strip()
                line = f": {caption_text} {{#tbl-{chapter_number}-{table_number}}}"
            output.extend(["", line, ""])
            previous = ""
            continue
        output.append(line)
        if line.strip():
            previous = line
    return "\n".join(output).rstrip() + "\n"


def _prepare_render(workspace: Path, entries: list[str]) -> list[str]:
    """Create root index and transformed chapter files for Quarto.

    The first reading-order file becomes ``index.qmd`` so Quarto has a home page without a
    separate generated chapter. Other chapter/appendix files are transformed in place in the
    private staging workspace. Canonical source in the commit is untouched.
    """

    if not entries:
        raise BuildError("no manuscript entries to render")
    first = entries[0]
    first_path = workspace / first
    try:
        first_text = first_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"cannot read staged chapter {first}: {exc}") from exc
    index_text = _transform_chapter(first_text, 1)
    (workspace / "index.qmd").write_text(index_text, encoding="utf-8")

    rendered: list[str] = ["index.qmd"]
    chapter_number = 1
    for entry in entries[1:]:
        path = workspace / entry
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise BuildError(f"cannot read staged chapter {entry}: {exc}") from exc
        chapter_number += 1
        path.write_text(_transform_chapter(text, chapter_number), encoding="utf-8")
        rendered.append(entry)
    return rendered


def _render_config(
    book: dict[str, Any],
    config: dict[str, Any],
    entries: list[str],
    resources: dict[str, Path],
    workspace: Path,
    *,
    toc_depth: int | None = None,
    edition_date: str | None = None,
) -> dict[str, Any]:
    project = config.setdefault("project", {})
    if not isinstance(project, dict) or project.get("type", "book") != "book":
        raise BuildError("publishing/_quarto.yml must declare a Quarto book project")
    project["type"] = "book"
    project["output-dir"] = "_output"
    config["number-sections"] = True

    book_config = config.setdefault("book", {})
    if not isinstance(book_config, dict):
        raise BuildError("publishing/_quarto.yml book section must be a mapping")
    book_config["title"] = book["title"]
    book_config["chapters"] = entries
    if edition_date is not None:
        # The edition date comes from the source commit, never a hand-kept value.
        book_config["date"] = edition_date
        config.setdefault("date-format", "MMMM YYYY")

    config.setdefault("tbl-cap-location", "bottom")
    config.setdefault("number-sections", True)
    crossref = config.setdefault("crossref", {})
    if isinstance(crossref, dict):
        crossref.setdefault("chapters", True)
    formats = config.get("format", {})
    if not isinstance(formats, dict):
        raise BuildError("publishing/_quarto.yml format section must be a mapping")
    config["format"] = {name: formats.get(name, {}) for name in ("html", "typst", "docx")}
    config["filters"] = [
        {"at": "pre-ast", "path": (resources["filters/table-layout.lua"]).relative_to(workspace).as_posix()},
        {"at": "pre-ast", "path": (resources["filters/task-checkbox.lua"]).relative_to(workspace).as_posix()},
        {"at": "pre-ast", "path": (resources["filters/docx-callouts.lua"]).relative_to(workspace).as_posix()},
    ]

    def staged(name: str) -> str:
        return resources[name].relative_to(workspace).as_posix()

    typst_format = config["format"]["typst"]
    typst_format["mainfont"] = design.load_tokens()["type"]["brand"]["text_family"]
    typst_format["monofont"] = "JetBrains Mono"
    typst_format["font-paths"] = [
        resources["fonts/source-sans3/HandbookSans-Regular.ttf"].parent.relative_to(workspace).as_posix(),
        resources["fonts/source-serif4/HandbookSerif-Regular.ttf"].parent.relative_to(workspace).as_posix(),
        resources["fonts/jetbrains-mono/JetBrainsMono-Regular.ttf"].parent.relative_to(workspace).as_posix(),
    ]
    # Design constants are generated from the packaged tokens; the hand-written
    # theme reads them and never carries its own palette.
    typst_tokens = resources["typst/handbook-typst.typ"].parent / "design-tokens.typ"
    typst_tokens.write_text(design.typst_preamble(), encoding="utf-8")
    # Styles and page furniture are header includes so they apply before the
    # cover is laid out; the generated cover and Contents open the body.
    header_includes = [
        typst_tokens.relative_to(workspace).as_posix(),
        staged("typst/handbook-typst.typ"),
    ]
    if "typst/book-data.typ" in resources:
        header_includes.append(staged("typst/book-data.typ"))
    typst_format["include-in-header"] = header_includes
    if "typst/front.typ" in resources:
        typst_format["include-before-body"] = staged("typst/front.typ")
    elif "typst/handbook-typst.typ" in resources:
        typst_format["include-before-body"] = staged("typst/handbook-typst.typ")
    # The generated front places the Contents after the cover page.
    typst_format["toc"] = False
    if "template-partials" not in typst_format:
        typst_format["template-partials"] = [staged("typst/typst-show.typ")]
    if "margin" not in typst_format:
        typst_format["margin"] = {"x": "2.2cm", "y": "2.4cm"}

    docx_format = config["format"]["docx"]
    if "reference-doc" not in docx_format:
        docx_format["reference-doc"] = staged("docx/reference.docx")
    if toc_depth is not None:
        for name in ("typst", "docx"):
            config["format"][name].setdefault("toc-depth", toc_depth)
    config["format"]["docx"].setdefault("toc-title", "Contents")
    for name in ("typst", "docx"):
        config["format"][name].setdefault("lot", True)

    html_format = config["format"]["html"]
    html_format.setdefault("toc-title", "Contents")
    html_tokens = resources["html/handbook.css"].parent / "design-tokens.css"
    html_tokens.write_text(design.book_theme_css(), encoding="utf-8")
    tokens_css = html_tokens.relative_to(workspace).as_posix()
    existing_css = html_format.get("css")
    if existing_css is None:
        stylesheets = [resources["html/handbook.css"].relative_to(workspace).as_posix()]
    elif isinstance(existing_css, str):
        stylesheets = [existing_css]
    else:
        stylesheets = list(existing_css)
    html_format["css"] = [tokens_css] + [sheet for sheet in stylesheets if sheet != tokens_css]
    execute = config.setdefault("execute", {})
    if not isinstance(execute, dict):
        raise BuildError("publishing/_quarto.yml execute section must be a mapping")
    execute["enabled"] = False
    return config


def _extract_source(source_zip: Path, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(source_zip) as archive:
            for info in archive.infolist():
                name = info.filename
                path = Path(name)
                if path.is_absolute() or ".." in path.parts or info.is_dir():
                    if info.is_dir():
                        continue
                    raise BuildError(f"unsafe source archive member: {name}")
            archive.extractall(workspace)
    except (OSError, zipfile.BadZipFile) as exc:
        raise BuildError(f"cannot extract source archive: {exc}") from exc


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


def _docx_table_entries(root: ET.Element, word: str) -> list[tuple[str, str]]:
    """Return ``(caption, bookmark)`` pairs in document order."""

    entries: list[tuple[str, str]] = []
    for wrapper in root.iter(f"{word}tbl"):
        if not any(node is not wrapper and node.tag == f"{word}tbl" for node in wrapper.iter()):
            continue
        caption = ""
        for paragraph in wrapper.iter(f"{word}p"):
            if _paragraph_style(paragraph, word) not in {"ImageCaption", "TableCaption", "Caption"}:
                continue
            value = "".join(node.text or "" for node in paragraph.iter(f"{word}t")).strip()
            if value.startswith("Table"):
                caption = value
                break
        bookmark = ""
        for mark in wrapper.iter(f"{word}bookmarkStart"):
            name = mark.get(f"{word}name", "")
            if name.startswith("tbl-"):
                bookmark = name
                break
        if caption and bookmark:
            entries.append((caption, bookmark))
    return entries


def _list_of_tables_paragraph(word: str, caption: str, bookmark: str) -> ET.Element:
    paragraph = ET.Element(f"{word}p")
    properties = ET.SubElement(paragraph, f"{word}pPr")
    style = ET.SubElement(properties, f"{word}pStyle")
    style.set(f"{word}val", "TOC1")
    link = ET.SubElement(paragraph, f"{word}hyperlink")
    link.set(f"{word}anchor", bookmark)
    run = ET.SubElement(link, f"{word}r")
    run_properties = ET.SubElement(run, f"{word}rPr")
    colour = ET.SubElement(run_properties, f"{word}color")
    colour.set(f"{word}val", "0B5D5F")
    underline = ET.SubElement(run_properties, f"{word}u")
    underline.set(f"{word}val", "single")
    ET.SubElement(run, f"{word}t").text = caption
    return paragraph


def _replace_docx_list_of_tables(root: ET.Element, word: str) -> None:
    """Replace Word's empty List of Tables field with a static, linked list.

    Word may update the TOC field on open, but a static list is deterministic
    and visible in every viewer. Each caption links to the ``tbl-`` bookmark
    anchored at its table, so the list behaves like a real index.
    """

    body = root.find(f".//{word}body")
    if body is None:
        return
    target = None
    target_index = None
    for index, child in enumerate(list(body)):
        if child.tag != f"{word}sdt":
            continue
        text = "".join(node.text or "" for node in child.iter(f"{word}t"))
        if "List of Tables" in text:
            target = child
            target_index = index
            break
    if target is None or target_index is None:
        return
    entries = _docx_table_entries(root, word)
    if not entries:
        return
    body.remove(target)
    title = ET.Element(f"{word}p")
    properties = ET.SubElement(title, f"{word}pPr")
    style = ET.SubElement(properties, f"{word}pStyle")
    style.set(f"{word}val", "TOCHeading")
    run = ET.SubElement(title, f"{word}r")
    ET.SubElement(run, f"{word}t").text = "List of Tables"
    body.insert(target_index, title)
    for offset, (caption, bookmark) in enumerate(entries, start=1):
        body.insert(
            target_index + offset,
            _list_of_tables_paragraph(word, caption, bookmark),
        )


def _paragraph_style(paragraph: ET.Element, word: str) -> str:
    style = paragraph.find(f"./{word}pPr/{word}pStyle")
    return style.get(f"{word}val", "") if style is not None else ""


def _page_text_width(root: ET.Element, word: str) -> int:
    size = root.find(f".//{word}sectPr/{word}pgSz")
    margins = root.find(f".//{word}sectPr/{word}pgMar")
    if size is None or margins is None:
        return 9360
    width = int(size.get(f"{word}w", "11906"))
    left = int(margins.get(f"{word}left", "1247"))
    right = int(margins.get(f"{word}right", "1247"))
    return max(4000, width - left - right)


def _spacer(word: str) -> ET.Element:
    paragraph = ET.Element(f"{word}p")
    properties = ET.SubElement(paragraph, f"{word}pPr")
    spacing = ET.SubElement(properties, f"{word}spacing")
    spacing.set(f"{word}before", "0")
    spacing.set(f"{word}after", "0")
    spacing.set(f"{word}line", "120")
    spacing.set(f"{word}lineRule", "exact")
    run = ET.SubElement(paragraph, f"{word}r")
    run_properties = ET.SubElement(run, f"{word}rPr")
    size = ET.SubElement(run_properties, f"{word}sz")
    size.set(f"{word}val", "8")
    return paragraph


def _clear_paragraph_box(paragraph: ET.Element, word: str) -> None:
    properties = paragraph.find(f"./{word}pPr")
    if properties is None:
        return
    for tag in ("pBdr", "shd"):
        existing = properties.find(f"./{word}{tag}")
        if existing is not None:
            properties.remove(existing)


def _clear_table_stripes(table: ET.Element, word: str) -> None:
    for item in table.iter(f"{word}tbl"):
        for row in item.findall(f"{word}tr"):
            properties = row.find(f"./{word}trPr")
            if properties is not None:
                shade = properties.find(f"./{word}shd")
                if shade is not None:
                    properties.remove(shade)
        look = item.find(f"./{word}tblPr/{word}tblLook")
        if look is not None:
            look.set(f"{word}noHBand", "1")
        style = item.find(f"./{word}tblPr/{word}tblStyle")
        if style is not None:
            style.set(f"{word}val", "TablePlain")


def _colour_callout_title(paragraph: ET.Element, word: str, accent: str) -> None:
    for run in paragraph.iter(f"{word}r"):
        properties = run.find(f"./{word}rPr")
        if properties is None:
            properties = ET.Element(f"{word}rPr")
            run.insert(0, properties)
        colour = properties.find(f"./{word}color")
        if colour is None:
            colour = ET.SubElement(properties, f"{word}color")
        colour.set(f"{word}val", accent)


def _wrap_callout_box(
    root: ET.Element,
    body: ET.Element,
    children: list[ET.Element],
    position: int,
    group: list[ET.Element],
    word: str,
    accent: str,
    tint: str,
) -> None:
    width = _page_text_width(root, word)
    table = ET.Element(f"{word}tbl")
    properties = ET.SubElement(table, f"{word}tblPr")
    table_style = ET.SubElement(properties, f"{word}tblStyle")
    table_style.set(f"{word}val", "CalloutBox")
    table_width = ET.SubElement(properties, f"{word}tblW")
    table_width.set(f"{word}w", str(width))
    table_width.set(f"{word}type", "dxa")
    layout = ET.SubElement(properties, f"{word}tblLayout")
    layout.set(f"{word}type", "fixed")
    look = ET.SubElement(properties, f"{word}tblLook")
    look.set(f"{word}val", "0000")
    look.set(f"{word}firstRow", "0")
    look.set(f"{word}noHBand", "1")
    borders = ET.SubElement(properties, f"{word}tblBorders")
    for side, colour, size in (
        ("top", "D9E2EC", 4), ("left", accent, 24),
        ("bottom", "D9E2EC", 4), ("right", "D9E2EC", 4),
    ):
        border = ET.SubElement(borders, f"{word}{side}")
        border.set(f"{word}val", "single")
        border.set(f"{word}sz", str(size))
        border.set(f"{word}space", "0")
        border.set(f"{word}color", colour)
    margins = ET.SubElement(properties, f"{word}tblCellMar")
    for side, value in (("top", 80), ("left", 120), ("bottom", 80), ("right", 120)):
        margin = ET.SubElement(margins, f"{word}{side}")
        margin.set(f"{word}w", str(value))
        margin.set(f"{word}type", "dxa")
    grid = ET.SubElement(table, f"{word}tblGrid")
    column = ET.SubElement(grid, f"{word}gridCol")
    column.set(f"{word}w", str(width))
    row = ET.SubElement(table, f"{word}tr")
    row_properties = ET.SubElement(row, f"{word}trPr")
    ET.SubElement(row_properties, f"{word}cantSplit")
    cell = ET.SubElement(row, f"{word}tc")
    cell_properties = ET.SubElement(cell, f"{word}tcPr")
    cell_width = ET.SubElement(cell_properties, f"{word}tcW")
    cell_width.set(f"{word}w", str(width))
    cell_width.set(f"{word}type", "dxa")
    shade = ET.SubElement(cell_properties, f"{word}shd")
    shade.set(f"{word}val", "clear")
    shade.set(f"{word}color", "auto")
    shade.set(f"{word}fill", tint)
    for block in group:
        body.remove(block)
        cell.append(block)
    body.insert(position, table)
    body.insert(position, _spacer(word))
    body.insert(position + 2, _spacer(word))
    children.clear()
    children.extend(list(body))


def _style_docx_callouts(root: ET.Element, word: str) -> None:
    """Wrap each callout in a single-cell table.

    Paragraph borders cannot align across body paragraphs and list items: Word
    draws them at each paragraph's indent, so the left rule and the box edges
    drift. A one-cell table owns the edge, keeps the group together with
    ``cantSplit`` and lets the cell shading carry the palette tint.
    """

    tokens = design.load_tokens()["callout"]
    names = {
        "CalloutNoteTitle": "note", "CalloutTipTitle": "tip",
        "CalloutWarningTitle": "warning", "CalloutImportantTitle": "important",
        "CalloutReviewTitle": "review",
    }
    body = root.find(f".//{word}body")
    if body is None:
        return
    children = list(body)
    index = 0
    while index < len(children):
        child = children[index]
        if child.tag != f"{word}p":
            index += 1
            continue
        style = _paragraph_style(child, word)
        kind = names.get(style)
        if kind is None:
            index += 1
            continue
        group = [child]
        cursor = index + 1
        end_marker = None
        while cursor < len(children):
            candidate = children[cursor]
            if candidate.tag == f"{word}tbl":
                group.append(candidate)
                cursor += 1
                continue
            if candidate.tag != f"{word}p":
                cursor += 1
                continue
            candidate_style = _paragraph_style(candidate, word)
            if candidate_style == "CalloutEnd":
                end_marker = candidate
                break
            if candidate_style.startswith("Heading") or candidate_style in names:
                break
            group.append(candidate)
            cursor += 1
        accent = tokens[kind]["accent"]["print"].lstrip("#")
        tint = tokens[kind]["tint"]["print"].lstrip("#")
        for block in group:
            if block.tag == f"{word}p":
                _clear_paragraph_box(block, word)
            else:
                _clear_table_stripes(block, word)
        _colour_callout_title(child, word, accent)
        _wrap_callout_box(root, body, children, index, group, word, accent, tint)
        if end_marker is not None:
            body.remove(end_marker)
        children.clear()
        children.extend(list(body))
        index += 3


def _style_docx_stripes(root: ET.Element, word: str) -> None:
    fill = design.load_tokens()["color"]["table_stripe"]["print"].lstrip("#")
    for table in root.iter(f"{word}tbl"):
        if any(node is not table and node.tag == f"{word}tbl" for node in table.iter()):
            continue
        for row_index, row in enumerate(table.findall(f"{word}tr")[1:]):
            if row_index % 2 == 0:
                continue
            properties = row.find(f"./{word}trPr")
            if properties is None:
                properties = ET.Element(f"{word}trPr")
                row.insert(0, properties)
            shade = properties.find(f"./{word}shd")
            if shade is None:
                shade = ET.SubElement(properties, f"{word}shd")
            shade.set(f"{word}val", "clear")
            shade.set(f"{word}color", "auto")
            shade.set(f"{word}fill", fill)


def _normalise_cell_paragraph(paragraph: ET.Element, word: str) -> None:
    if _paragraph_style(paragraph, word) in {"ImageCaption", "TableCaption", "Caption"}:
        return
    properties = paragraph.findall(f"./{word}pPr")
    if not properties:
        properties = [ET.Element(f"{word}pPr")]
        paragraph.insert(0, properties[0])
    canonical = next(
        (value for value in properties if value.find(f"./{word}pStyle") is not None),
        properties[0],
    )
    for value in properties:
        if value is not canonical:
            paragraph.remove(value)
    for existing in canonical.findall(f"./{word}jc"):
        canonical.remove(existing)
    align = ET.SubElement(canonical, f"{word}jc")
    align.set(f"{word}val", "left")


def _left_align_docx_tables(root: ET.Element, word: str) -> None:
    """Keep table body text left-aligned; only captions are centred."""

    for table in root.iter(f"{word}tbl"):
        for cell in table.iter(f"{word}tc"):
            for paragraph in cell.findall(f"./{word}p"):
                _normalise_cell_paragraph(paragraph, word)


def _reflow_license_paragraph(paragraph: ET.Element, word: str) -> None:
    """Turn hard-wrapped licence lines into flowing text.

    A licensed text is stored as one code paragraph with a line break per
    source line. Short upstream lines leave half of the Word text column empty.
    Line breaks inside a paragraph become spaces; blank lines separate
    paragraphs inside the same shaded block.
    """

    lines: list[str] = []
    current = ""
    for run in paragraph.findall(f"./{word}r"):
        for node in run:
            if node.tag == f"{word}t":
                current += node.text or ""
            elif node.tag == f"{word}br":
                lines.append(current)
                current = ""
    lines.append(current)
    segments: list[str] = []
    text = ""
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if text:
                segments.append(text.strip())
                text = ""
        else:
            text = f"{text} {stripped}".strip()
    if text:
        segments.append(text.strip())
    if not segments:
        return
    for child in list(paragraph):
        if child.tag != f"{word}pPr":
            paragraph.remove(child)
    for offset, value in enumerate(segments):
        run = ET.SubElement(paragraph, f"{word}r")
        properties = ET.SubElement(run, f"{word}rPr")
        style = ET.SubElement(properties, f"{word}rStyle")
        style.set(f"{word}val", "VerbatimChar")
        if offset:
            ET.SubElement(run, f"{word}br")
            ET.SubElement(run, f"{word}br")
        ET.SubElement(run, f"{word}t").text = value


def _reflow_docx_licenses(root: ET.Element, word: str) -> None:
    body = root.find(f".//{word}body")
    if body is None:
        return
    heading = ""
    for child in list(body):
        if child.tag == f"{word}p":
            style = _paragraph_style(child, word)
            text = "".join(node.text or "" for node in child.iter(f"{word}t")).strip()
            if style.startswith("Heading"):
                heading = text
            elif "License" in heading and style == "SourceCode":
                _reflow_license_paragraph(child, word)


def _style_docx_table_headers(path: Path) -> None:
    """Apply direct header formatting to every DOCX table.

    Word and LibreOffice treat table-style ``firstRow`` conditionals
    differently. Direct run colour plus cell shading makes the header reliable
    in both, and ``tblHeader`` repeats it across a page break.
    """

    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    word = "{%s}" % namespace
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(members["word/document.xml"])
    for table in root.iter(f"{word}tbl"):
        # Quarto wraps a captioned float in an outer one-cell table. Styling
        # that wrapper would paint the caption and, through the recursive run
        # walk, the nested content too. Leave wrappers alone; style the table
        # that actually holds the data.
        if any(node is not table and node.tag == f"{word}tbl" for node in table.iter()):
            continue
        rows = table.findall(f"{word}tr")
        if not rows:
            continue
        header = rows[0]
        properties = header.find(f"./{word}trPr")
        if properties is None:
            properties = ET.Element(f"{word}trPr")
            header.insert(0, properties)
        if properties.find(f"./{word}tblHeader") is None:
            ET.SubElement(properties, f"{word}tblHeader")
        for cell in header.findall(f"{word}tc"):
            cell_properties = cell.find(f"./{word}tcPr")
            if cell_properties is None:
                cell_properties = ET.Element(f"{word}tcPr")
                cell.insert(0, cell_properties)
            shade = cell_properties.find(f"./{word}shd")
            if shade is None:
                shade = ET.SubElement(cell_properties, f"{word}shd")
            shade.set(f"{word}val", "clear")
            shade.set(f"{word}color", "auto")
            shade.set(f"{word}fill", "0B5D5F")
            for run in cell.iter(f"{word}r"):
                run_properties = run.find(f"./{word}rPr")
                if run_properties is None:
                    run_properties = ET.Element(f"{word}rPr")
                    run.insert(0, run_properties)
                if run_properties.find(f"./{word}b") is None:
                    ET.SubElement(run_properties, f"{word}b")
                if run_properties.find(f"./{word}bCs") is None:
                    ET.SubElement(run_properties, f"{word}bCs")
                colour = run_properties.find(f"./{word}color")
                if colour is None:
                    colour = ET.SubElement(run_properties, f"{word}color")
                colour.set(f"{word}val", "FFFFFF")
    _style_docx_stripes(root, word)
    _style_docx_callouts(root, word)
    _left_align_docx_tables(root, word)
    _reflow_docx_licenses(root, word)
    _replace_docx_list_of_tables(root, word)
    for paragraph in root.iter(f"{word}p"):
        style = _paragraph_style(paragraph, word)
        if style not in {"ImageCaption", "TableCaption", "Caption"}:
            continue
        text = "".join(node.text or "" for node in paragraph.iter(f"{word}t")).strip()
        if not text.startswith("Table"):
            continue
        properties = paragraph.findall(f"./{word}pPr")
        if not properties:
            properties = [ET.Element(f"{word}pPr")]
            paragraph.insert(0, properties[0])
        canonical = next(
            (value for value in properties if value.find(f"./{word}pStyle") is not None),
            properties[0],
        )
        for value in properties:
            if value is not canonical:
                paragraph.remove(value)
        for existing in canonical.findall(f"./{word}jc"):
            canonical.remove(existing)
        align = ET.SubElement(canonical, f"{word}jc")
        align.set(f"{word}val", "center")
    background = ET.Element(f"{word}background")
    background.set(f"{word}color", "F6F1E7")
    root.insert(0, background)
    settings = ET.fromstring(members["word/settings.xml"]) if "word/settings.xml" in members else None
    if settings is not None:
        for tag in ("updateFields", "displayBackgroundShape"):
            if settings.find(f"{word}{tag}") is None:
                ET.SubElement(settings, f"{word}{tag}")
        members["word/settings.xml"] = ET.tostring(
            settings, encoding="utf-8", xml_declaration=True
        )
    ET.register_namespace("w", namespace)
    members["word/document.xml"] = ET.tostring(
        root, encoding="utf-8", xml_declaration=True
    )
    temporary = path.with_suffix(".tmp.docx")
    with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    temporary.replace(path)


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
    _style_docx_table_headers(dist / PAYLOADS["docx"])
    return {
        "html": dist / PAYLOADS["html"],
        "pdf": dist / PAYLOADS["pdf"],
        "docx": dist / PAYLOADS["docx"],
        "source": dist / PAYLOADS["source"],
    }


def _markdown_sources(workspace: Path, entries: list[str]) -> str:
    """Concatenate the canonical reading order into one GitHub-flavoured Markdown source.

    The Markdown edition is one file, so the per-file front matter of the reading order is
    dropped and include shortcodes are resolved against the combined document at the project
    root. The canonical sources are read before the render staging rewrites their headings.
    """

    parts: list[str] = []
    for entry in entries:
        try:
            text = (workspace / entry).read_text(encoding="utf-8")
        except OSError as exc:
            raise BuildError(f"cannot read staged chapter {entry}: {exc}") from exc
        match = FRONT_MATTER_BLOCK.match(text)
        body = (text[match.end():] if match else text).strip()
        if not body:
            continue
        parts.append(_rewrite_includes(body, entry))
    if not parts:
        raise BuildError("the reading order contains no manuscript content for the Markdown edition")
    return "\n\n".join(parts) + "\n"


def _rewrite_includes(text: str, entry: str) -> str:
    """Resolve include shortcodes relative to the combined document at the project root."""

    directory = posixpath.dirname(entry)
    if not directory:
        return text

    def resolve(match: re.Match[str]) -> str:
        target = posixpath.normpath(posixpath.join(directory, match.group(1)))
        return f"{{{{< include {target} >}}}}"

    return INCLUDE_SHORTCODE.sub(resolve, text)


def _markdown_header(book: dict[str, Any], fields: list[tuple[str, str]], commit: str) -> str:
    """Open the edition with the document-control fields of the print editions plus the commit."""

    title = str(book.get("title", "")).strip()
    if not title:
        raise BuildError("the book descriptor has no title for the Markdown edition")
    table = document_control_table([*fields, ("Commit", commit)])
    return f"# {title}\n\n{table}\n\n{MARKDOWN_NOTE}\n\n"


def _figure_caption(body: str) -> str:
    """Replace a rendered figure by its caption or alternative text."""

    caption = ""
    alternative = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("!["):
            image = IMAGE.search(stripped)
            if image is not None and image.group(1).strip():
                alternative = image.group(1).strip()
            continue
        caption = stripped
    text = caption or alternative
    return f"*{text}*" if text else OMITTED_FIGURE


def _clean_markdown(text: str) -> str:
    """Turn the Quarto gfm output into plain GitHub-flavoured Markdown.

    Quarto resolves cross-references to raw HTML anchors and wraps tables and cross-referenced
    figures in ``<div>`` containers. Markdown links and plain text keep the same information
    without raw HTML, and figure images become their captions because one file cannot carry them.
    """

    text = text.replace("\r\n", "\n")
    text = XREF_LINK.sub(r"\1", text)
    text = FIGURE_BLOCK.sub(lambda match: f"\n\n{_figure_caption(match.group(1))}\n\n", text)
    text = TABLE_BLOCK.sub(lambda match: f"\n\n{match.group(1).strip()}\n\n", text)
    text = IMAGE.sub(
        lambda match: f"*{match.group(1).strip()}*" if match.group(1).strip() else OMITTED_FIGURE,
        text,
    )
    lines = [line.rstrip() for line in text.splitlines()]
    collapsed: list[str] = []
    for line in lines:
        if not line and collapsed and not collapsed[-1]:
            continue
        collapsed.append(line)
    return "\n".join(collapsed).strip() + "\n"


def _unescape_markdown(text: str) -> str:
    """Remove CommonMark backslash escapes so an escaped path compares as written.

    The gfm writer escapes ASCII punctuation in prose, for example ``/tmp/build_dir``
    becomes ``/tmp/build\\_dir``. The escaped form is the same path to a reader, so the
    leak check must look at both the raw and the unescaped text.
    """

    return BACKSLASH_ESCAPE.sub("", text)


def _reject_local_paths(text: str, paths: list[Path]) -> None:
    """Fail the build when the Markdown edition leaks one of this build's absolute paths.

    Book content may legitimately mention a path such as ``/tmp/demo`` or ``file://``.
    The leak that matters is the private staging workspace, the output directory or the
    source repository of this build, including the home directory. A path with fewer than
    three components, such as ``/tmp`` or ``/home``, is a shared system directory and is
    never used as a needle: an output directly under it would otherwise reject ordinary
    content.
    """

    leaked = sorted({str(path) for path in paths if len(path.parts) >= 3})
    unescaped = _unescape_markdown(text)
    for value in leaked:
        if value in text or value in unescaped:
            raise BuildError(f"the Markdown edition leaks the local path {value}")


def _render_markdown(
    workspace: Path,
    source: str,
    resources: dict[str, Path],
    quarto: str,
    environment: dict[str, str],
) -> str:
    """Render one gfm document from the prepared source and return its raw Markdown."""

    (workspace / MARKDOWN_ENTRY).write_text(source, encoding="utf-8")
    config = {
        "project": {"type": "default", "output-dir": MARKDOWN_DIR, "render": [MARKDOWN_ENTRY]},
        "format": {"gfm": {"wrap": "none"}},
        "filters": [
            {"at": "pre-ast", "path": resources["filters/table-layout.lua"].relative_to(workspace).as_posix()},
            {"at": "pre-ast", "path": resources["filters/task-checkbox.lua"].relative_to(workspace).as_posix()},
        ],
        "execute": {"enabled": False},
    }
    (workspace / "_quarto.yml").write_text(
        yaml.safe_dump(config, sort_keys=True, allow_unicode=True), encoding="utf-8"
    )
    _run([quarto, "render", ".", "--no-execute"], cwd=workspace, env=environment)
    rendered = workspace / MARKDOWN_DIR / "book-markdown.md"
    if not rendered.is_file():
        raise BuildError("Quarto did not produce the Markdown edition")
    try:
        return rendered.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"cannot read the rendered Markdown edition: {exc}") from exc


def build_book(
    repo: Path,
    commit: str,
    output: Path,
    *,
    profile: Path | None = None,
    version: str | None = None,
    epoch: int | None = None,
    quarto: str = "quarto",
    mode: str = "chapter",
    preview: bool = False,
) -> BuildResult:
    """Build a verified seven-file publication directory at *output*.

    ``output`` must not exist and must be outside the source repository. All work
    happens in a private sibling staging directory; only a complete, inspected
    and identity-verified directory is atomically renamed into place.
    """

    repo = Path(repo).resolve()
    raw_output = Path(output)
    profile_path = Path(profile).resolve() if profile is not None else None
    if mode not in {"chapter", "section-pilot"}:
        raise BuildError('mode must be "chapter" or "section-pilot"')

    _require_clean_commit(repo, commit)
    if raw_output.is_symlink() or raw_output.exists():
        raise BuildError(f"output already exists: {raw_output}")
    output = raw_output.resolve()
    if output.exists() or output.is_symlink():
        raise BuildError(f"output already exists: {output}")
    try:
        output.relative_to(repo)
    except ValueError:
        pass
    else:
        raise BuildError("output must be outside the source repository")
    output.parent.mkdir(parents=True, exist_ok=True)

    source_epoch = _epoch(repo, commit, epoch)
    tool_versions = _tool_versions(quarto)

    staging = Path(tempfile.mkdtemp(prefix=".handbook-build-", dir=output.parent))
    dist = staging / "dist"
    workspace = staging / "work"
    dist.mkdir()
    try:
        source_zip = dist / PAYLOADS["source"]
        _git(repo, "archive", "--format=zip", f"--output={source_zip}", commit)
        with zipfile.ZipFile(source_zip) as archive:
            if archive.comment.decode("ascii", errors="replace") != commit:
                raise BuildError("git archive did not record the exact source commit")
        source_issues = inspect_payload(source_zip, "source", source_commit=commit)
        if source_issues:
            raise BuildError(
                "source inspection failed: " + "; ".join(map(str, source_issues))
            )
        _extract_source(source_zip, workspace)

        book_path = workspace / "book.yaml"
        book_result = validate_book(book_path, load_packaged_schema("book.schema.json"))
        if not book_result.ok:
            raise BuildError("invalid book descriptor: " + "; ".join(map(str, book_result.issues)))
        book = load_document(book_path)
        if profile_path is not None:
            profile_result = validate_profile(
                profile_path, load_packaged_schema("profile.schema.json")
            )
            if not profile_result.ok:
                raise BuildError(
                    "invalid profile: " + "; ".join(map(str, profile_result.issues))
                )
            profile_document = load_document(profile_path)
        else:
            try:
                profile_document = load_profile(
                    book["profile"]["id"], book["profile"]["version"]
                )
            except DocumentError as exc:
                raise BuildError(
                    "cannot resolve the book profile from the installed package: " + str(exc)
                ) from exc
        if book["profile"]["id"] != profile_document["id"] or book["profile"]["version"] != profile_document["version"]:
            raise BuildError("book.yaml profile pin does not match the resolved profile")
        if book["toolkit"] != __version__ and not preview:
            raise BuildError(
                f"book.yaml toolkit pin {book['toolkit']} does not match builder {__version__}; "
                "use an explicit --preview build only for a non-release preview"
            )
        reference_result = validate_references(
            workspace / "book.yaml", load_packaged_schema("book.schema.json")
        )
        if not reference_result.ok:
            raise BuildError(
                "reference validation failed: "
                + "; ".join(map(str, reference_result.issues))
            )
        groups = _reading_groups(book, workspace)
        entries = [entry for group in ("front", "chapters", "back", "appendices", "references") for entry in groups[group]]
        _validate_manuscripts(workspace, book, profile_document, mode)
        book_version = _book_version(workspace, version)
        _require_prerelease_version(book_version, mode, preview)
        resources = stage_render_resources(workspace / ".handbook-render")
        brand = design.load_tokens()
        brand_colours = {
            role: values["light"] for role, values in brand["color"].items()
        }
        (workspace / "_brand.yml").write_text(
            "color:\n"
            f"  palette:\n    canvas: \"{brand_colours['canvas']}\"\n"
            f"    ink: \"{brand_colours['text']}\"\n"
            f"    accent: \"{brand_colours['accent']}\"\n"
            "  background: canvas\n  foreground: ink\n  primary: accent\n",
            encoding="utf-8",
        )
        metadata_path = workspace / "publishing/metadata.yaml"
        metadata: dict[str, Any] = {}
        if metadata_path.is_file():
            try:
                loaded_meta = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
                if isinstance(loaded_meta, dict):
                    metadata = loaded_meta
            except (OSError, yaml.YAMLError) as exc:
                raise BuildError(f"cannot read publishing/metadata.yaml: {exc}") from exc

        config_path = workspace / "publishing/_quarto.yml"
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise BuildError(f"cannot read publishing/_quarto.yml: {exc}") from exc
        if not isinstance(config, dict):
            raise BuildError("publishing/_quarto.yml must be a YAML mapping")

        author = str(metadata.get("author") or config.get("book", {}).get("author") or "")
        language = str(metadata.get("language") or config.get("lang") or "en")
        fields = edition_fields(
            book,
            metadata,
            version=book_version,
            preview=preview,
            epoch=source_epoch,
            profile=profile_document,
            author=author,
            language=language,
        )
        control_table = document_control_table(fields)
        # The Markdown edition carries its own document-control header, so it is captured
        # before the print editions inject the table into the front matter.
        markdown_source = _markdown_sources(workspace, entries)
        for entry in entries:
            entry_path = workspace / entry
            content = entry_path.read_text(encoding="utf-8")
            injected = inject_document_control(content, control_table)
            if injected is not None:
                entry_path.write_text(injected, encoding="utf-8")
                break

        entry_texts = [(workspace / entry).read_text(encoding="utf-8") for entry in entries]
        depth = toc_depth(entry_texts)

        title = str(book.get("title", ""))
        licenses = book.get("license", {})
        license_text = license_label(str(licenses.get("content", "")))
        running_header = str(metadata.get("series_label") or DEFAULT_RUNNING_HEADER)
        book_data_file = resources["typst/handbook-typst.typ"].parent / "book-data.typ"
        book_data_file.write_text(
            typst_book_data(
                title=title,
                license_text=license_text,
                running_header=running_header,
            ),
            encoding="utf-8",
        )
        resources["typst/book-data.typ"] = book_data_file

        front_file = resources["typst/handbook-typst.typ"].parent / "front.typ"
        edition_dt = edition_date(source_epoch)
        date_str = edition_dt.strftime("%B %Y")
        version_line = f"Version {book_version}, {date_str}"
        scope_line = str(metadata.get("scope_banner") or "")
        series_label = str(metadata.get("series_label") or "")
        disclaimer = str(metadata.get("disclaimer") or "")
        front_file.write_text(
            typst_front(
                series_label=series_label,
                version_line=version_line,
                scope_line=scope_line,
                author=author,
                license_text=license_text,
                disclaimer=disclaimer,
                depth=depth,
            ),
            encoding="utf-8",
        )
        resources["typst/front.typ"] = front_file

        rendered_entries = _prepare_render(workspace, entries)

        (workspace / "_quarto.yml").write_text(
            yaml.safe_dump(
                _render_config(
                    book,
                    config,
                    rendered_entries,
                    resources,
                    workspace,
                    toc_depth=depth,
                    edition_date=date_str,
                ),
                sort_keys=True,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["SOURCE_DATE_EPOCH"] = str(source_epoch)
        _run(
            [quarto, "render", ".", "--no-execute"],
            cwd=workspace,
            env=environment,
        )

        payloads = _payload_paths(workspace, dist, source_epoch)
        markdown_text = _markdown_header(book, fields, commit) + _clean_markdown(
            _render_markdown(workspace, markdown_source, resources, quarto, environment)
        )
        _reject_local_paths(
            markdown_text,
            [repo, workspace, staging, output, Path.home()],
        )
        markdown_path = dist / PAYLOADS["markdown"]
        markdown_path.write_text(markdown_text, encoding="utf-8")
        payloads["markdown"] = markdown_path
        for role in ROLES:
            issues = inspect_payload(
                payloads[role],
                role,
                source_commit=commit if role == "source" else None,
                version=book_version if role == "markdown" else None,
            )
            if issues:
                raise BuildError(
                    f"{role} inspection failed: " + "; ".join(map(str, issues))
                )

        metadata = {
            "book": {"id": book["id"], "version": book_version, "commit": commit},
            "toolkit": __version__,
            "profile": {
                "id": profile_document["id"],
                "version": profile_document["version"],
            },
            "build": {
                "command": "handbook-toolkit build-book --commit "
                + commit
                + f" --mode {mode}"
                + (" --preview" if preview else ""),
                "source_date_epoch": source_epoch,
                "tool_versions": tool_versions,
            },
        }
        write_manifest(dist, metadata, {role: payloads[role].name for role in ROLES})
        verification = verify_publication(dist)
        if not verification.ok:
            raise BuildError(
                "publication identity verification failed: "
                + "; ".join(map(str, verification.issues))
            )
        if output.exists() or output.is_symlink():
            raise BuildError(f"output appeared during build; refusing to replace: {output}")

        os.replace(dist, output)
        return BuildResult(output, commit, book_version, source_epoch, tool_versions)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
