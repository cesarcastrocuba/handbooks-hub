"""Build markdown."""

from __future__ import annotations
from pathlib import Path
from html.parser import HTMLParser
import posixpath
import re
from typing import Any
import yaml
from .print_layout import (
    document_control_table,
)

from .build_types import BuildError, _run

MARKDOWN_ENTRY = "book-markdown.qmd"

MARKDOWN_DIR = "_markdown"

FRONT_MATTER_BLOCK = re.compile(r"\A---[ \t]*\n.*?\n---[ \t]*\n", re.DOTALL)

INCLUDE_SHORTCODE = re.compile(r"\{\{<[ \t]*include[ \t]+([^>\s]+)[ \t]*>\}\}")

IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")

BACKSLASH_ESCAPE = re.compile(r"\\(?=[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")

OMITTED_FIGURE = "*(figure image not included in the Markdown edition)*"

MARKDOWN_NOTE = (
    "> Markdown edition: the whole book in reading order, generated from the same source commit as "
    "the other payloads. Figures appear as their captions only; use the HTML, PDF or DOCX payload "
    "for the images. Table and figure counters run sequentially in this file."
)

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

class _MarkdownHTML(HTMLParser):
    """Unwrap Quarto structural HTML without matching markup with regexes."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []
        self.divs: list[str] = []
        self.anchors: list[bool] = []
        self.figure: list[str] | None = None

    def append(self, text: str) -> None:
        (self.figure if self.figure is not None else self.output).append(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a":
            unwrap = "quarto-xref" in (attributes.get("class") or "").split()
            self.anchors.append(unwrap)
            if unwrap:
                return
        if tag == "div":
            identity = attributes.get("id") or ""
            kind = "figure" if identity.startswith("fig-") else "table" if identity.startswith(("tbl-", "lst-")) else ""
            self.divs.append(kind)
            if kind == "figure" and self.figure is None:
                self.figure = []
                return
            if kind == "table":
                self.append("\n\n")
                return
        self.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchors and self.anchors.pop():
            return
        if tag == "div" and self.divs:
            kind = self.divs.pop()
            if kind == "figure" and self.figure is not None:
                body = "".join(self.figure)
                self.figure = None
                self.output.append("\n\n" + _figure_caption(body) + "\n\n")
                return
            if kind == "table":
                self.append("\n\n")
                return
        self.append(f"</{tag}>")

    def handle_comment(self, data: str) -> None:
        self.append("<!--" + data + "-->")

    def handle_decl(self, decl: str) -> None:
        self.append("<!" + decl + ">")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.append(self.get_starttag_text())

    def handle_data(self, data: str) -> None:
        self.append(data)

    def handle_entityref(self, name: str) -> None:
        self.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.append(f"&#{name};")


def _clean_markdown(text: str) -> str:
    """Turn the Quarto gfm output into plain GitHub-flavoured Markdown.

    Quarto resolves cross-references to raw HTML anchors and wraps tables and cross-referenced
    figures in ``<div>`` containers. Markdown links and plain text keep the same information
    without raw HTML, and figure images become their captions because one file cannot carry them.
    """

    text = text.replace("\r\n", "\n")
    parser = _MarkdownHTML()
    parser.feed(text)
    parser.close()
    text = "".join(parser.output)
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
