"""Generated print-layout inputs: cover, Contents, Document Control and TOC depth.

These helpers produce presentation-only inputs for the staged render workspace.
They never read or write canonical manuscript files in the source repository;
the build calls them on the private staged copy.

* The cover, running furniture and Contents of the Typst edition are generated
  from the book descriptor, the optional ``publishing/metadata.yaml`` keys and
  the build version, so they can never drift from the released edition.
* The edition fields of the Document Control page are generated for the same
  reason and inserted directly after the book's ``# Document Control`` heading.
* The Contents depth follows the heading depth the book actually uses.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Iterable

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+\S")
DOCUMENT_CONTROL = re.compile(r"^#\s+Document Control\b[^\n]*$", re.MULTILINE)
LICENSE_LABELS = {
    "CC-BY-SA-4.0": "CC BY-SA 4.0",
    "CC-BY-4.0": "CC BY 4.0",
    "CC-BY-NC-SA-4.0": "CC BY-NC-SA 4.0",
    "CC0-1.0": "CC0 1.0",
    "MIT": "MIT",
    "Apache-2.0": "Apache 2.0",
}
LANGUAGES = {"en": "English", "es": "Spanish", "pt": "Portuguese", "fr": "French", "de": "German"}
# Contents entries that fit comfortably on two or three A4 pages at 10 pt.
THREE_LEVEL_LIMIT = 90
DEFAULT_RUNNING_HEADER = "Practitioner reference"


def license_label(identifier: str) -> str:
    """Return the human label of an SPDX license identifier."""

    return LICENSE_LABELS.get(identifier, identifier)


def edition_date(epoch: int) -> datetime:
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


def heading_levels(text: str) -> list[int]:
    """Return Markdown heading levels outside fenced code blocks."""

    levels: list[int] = []
    fence: str | None = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token[0] * len(token)
            elif token.startswith(fence):
                fence = None
            continue
        if fence is None:
            match = HEADING.match(line)
            if match:
                levels.append(len(match.group(1)))
    return levels


def toc_depth(texts: Iterable[str]) -> int:
    """Choose the Contents depth from the headings a book actually uses.

    One level shows one level; two levels show two. A book with three or more
    levels shows three when the third level keeps the Contents short, and two
    otherwise, which is how the reference handbook keeps its Contents usable.
    """

    levels = [level for text in texts for level in heading_levels(text)]
    deepest = max(levels, default=1)
    if deepest <= 1:
        return 1
    if deepest == 2:
        return 2
    return 3 if sum(1 for level in levels if level <= 3) <= THREE_LEVEL_LIMIT else 2


def _cell(value: str) -> str:
    return value.replace("|", "\\|").strip()


def document_control_table(fields: list[tuple[str, str]]) -> str:
    rows = ["| Field | Value |", "| :--- | :--- |"]
    rows.extend(f"| {_cell(name)} | {_cell(value)} |" for name, value in fields if value)
    return "\n".join(rows)


def edition_fields(
    book: dict[str, Any],
    metadata: dict[str, Any],
    *,
    version: str,
    preview: bool,
    epoch: int,
    profile: dict[str, Any],
    author: str,
    language: str,
) -> list[tuple[str, str]]:
    """Fields that change with every edition and are therefore generated."""

    status = "Preview build — not a released edition" if preview else "Released edition"
    if "-" in version and not preview:
        status = "Pre-release edition"
    licenses = book.get("license", {})
    return [
        ("Title", str(book.get("title", ""))),
        ("Subtitle", str(metadata.get("subtitle", "") or "")),
        ("Author", author),
        ("Version", version),
        ("Status", status),
        ("Date", edition_date(epoch).strftime("%B %Y")),
        ("Profile", f"{profile.get('id', '')} {profile.get('version', '')}".strip()),
        ("Language", LANGUAGES.get(language, language)),
        ("Content license", license_label(str(licenses.get("content", "")))),
        ("Code license", license_label(str(licenses.get("code", "")))),
    ]


def inject_document_control(text: str, table: str) -> str | None:
    """Insert *table* after the first ``# Document Control`` heading, if any."""

    match = DOCUMENT_CONTROL.search(text)
    if match is None:
        return None
    return text[: match.end()] + "\n\n" + table + "\n" + text[match.end() :]


def _typst_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{escaped}"'


def typst_book_data(*, title: str, license_text: str, running_header: str) -> str:
    """Variables read by the shared Typst style for the running header and footer."""

    return "\n".join(
        [
            "// Generated by handbook-toolkit for this build. Do not edit.",
            f"#let handbook-title = {_typst_string(title)}",
            f"#let handbook-license = {_typst_string(license_text)}",
            f"#let handbook-running-header = {_typst_string(running_header)}",
            "",
        ]
    )


def typst_front(
    *,
    series_label: str,
    version_line: str,
    scope_line: str,
    author: str,
    license_text: str,
    disclaimer: str,
    depth: int,
) -> str:
    """Cover lines below the title block, then the Contents on its own page."""

    lines = ["// Generated by handbook-toolkit for this build. Do not edit."]
    if series_label:
        lines += [f"#text(weight: \"bold\")[#{_typst_string(series_label.upper())}]", ""]
    banner = [part for part in (version_line, scope_line) if part]
    if banner:
        lines += [" \\\n".join(f"#{_typst_string(part)}" for part in banner), ""]
    if author:
        suffix = f"#{_typst_string(' · ' + license_text)}" if license_text else ""
        lines += [f"#text(weight: \"bold\")[#{_typst_string(author)}]{suffix}", ""]
    elif license_text:
        lines += [f"#{_typst_string(license_text)}", ""]
    if disclaimer:
        lines += [
            "#block(inset: (left: 12pt, y: 4pt), stroke: (left: 2pt + hb-border))["
            f"#text(fill: hb-muted)[#{_typst_string(disclaimer)}]]",
            "",
        ]
    lines += [
        "#pagebreak()",
        f"#outline(title: [Contents], depth: {depth})",

        "",
    ]
    from .indexes import LISTS

    for prefix, title, _letter in LISTS:
        target = f'figure.where(kind: "quarto-float-{prefix}")'
        lines += [
            f"#context {{ if query({target}).len() > 0 {{",
            "  pagebreak()",
            f"  outline(title: [{title}], target: {target})",
            "} }",
        ]
    return "\n".join(lines)
