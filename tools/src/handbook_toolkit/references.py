"""Validate explicit cross-references, duplicate labels and local image paths.

This is a structural gate across the canonical reading order. It does not render
Quarto, resolve automatic heading anchors, fetch external URLs or judge prose.
"""

from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from .books import READING_KEYS, validate_book
from .validation import CheckResult, DocumentError, Issue, load_document

LABEL = re.compile(r"\{#([A-Za-z][A-Za-z0-9:_-]*)(?=[\s}])")
XREF = re.compile(r"(?<![A-Za-z0-9_@])@((?:sec|fig|tbl|eq|lst)-[A-Za-z0-9][A-Za-z0-9_-]*)")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
IMAGE = re.compile(r"!\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
CROSSREF_PREFIXES = ("sec-", "fig-", "tbl-", "eq-", "lst-")


def _strip_inline_code(line: str) -> str:
    """Remove backtick-delimited spans using the exact opening delimiter."""
    output: list[str] = []
    index = 0
    while index < len(line):
        if line[index] != "`":
            output.append(line[index])
            index += 1
            continue
        end = index
        while end < len(line) and line[end] == "`":
            end += 1
        delimiter = line[index:end]
        close = line.find(delimiter, end)
        if close < 0:
            break
        output.append(" ")
        index = close + len(delimiter)
    return "".join(output)


def _visible_lines(text: str):
    """Yield lines outside fenced code, multiline comments and inline code."""
    in_fence = False
    fence_char = ""
    fence_length = 0
    in_comment = False
    for number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_length = len(marker)
                continue
            if marker[0] == fence_char and len(marker) >= fence_length:
                in_fence = False
                fence_char = ""
                fence_length = 0
                continue
        if in_fence:
            continue

        cleaned: list[str] = []
        index = 0
        while index < len(line):
            if in_comment:
                close = line.find("-->", index)
                if close < 0:
                    break
                index = close + 3
                in_comment = False
                continue
            start = line.find("<!--", index)
            if start < 0:
                cleaned.append(line[index:])
                break
            cleaned.append(line[index:start])
            close = line.find("-->", start + 4)
            if close < 0:
                in_comment = True
                break
            index = close + 3
        yield number, _strip_inline_code("".join(cleaned))


def _symlink_component(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _image_path(path: Path, line: int, target: str, book_root: Path, issues: list[Issue]) -> None:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target:
        return
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return  # external/data links are deliberately preserved and not fetched
    relative = unquote(parsed.path)
    if not relative:
        return
    candidate = Path(relative)
    if candidate.is_absolute():
        issues.append(Issue(f"{path}:{line}", f"image path must be relative: {target}"))
        return
    candidate_path = path.parent / candidate
    resolved = candidate_path.resolve()
    try:
        resolved.relative_to(book_root)
    except ValueError:
        issues.append(Issue(f"{path}:{line}", f"image path escapes the book repository: {target}"))
        return
    if _symlink_component(candidate_path, book_root):
        issues.append(Issue(f"{path}:{line}", f"referenced image uses a symlink: {target}"))
    elif not resolved.is_file():
        issues.append(Issue(f"{path}:{line}", f"referenced image is missing: {target}"))


def _local_target(path: Path, line: int, target: str, book_root: Path, files: set[Path], labels: dict[Path, set[str]], issues: list[Issue]) -> None:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return
    fragment = unquote(parsed.fragment)
    if not fragment.startswith(CROSSREF_PREFIXES):
        return  # auto heading anchors and ordinary links are outside this gate
    relative = unquote(parsed.path)
    destination = path if not relative else (path.parent / relative)
    if not relative:
        destination = path
    resolved = destination.resolve()
    try:
        resolved.relative_to(book_root)
    except ValueError:
        issues.append(Issue(f"{path}:{line}", f"local cross-reference escapes the book repository: {target}"))
        return
    if resolved not in files:
        issues.append(Issue(f"{path}:{line}", f"local cross-reference target is not canonical: {target}"))
        return
    if fragment not in labels.get(resolved, set()):
        issues.append(Issue(f"{path}:{line}", f"unresolved local cross-reference {target}"))


def validate_references(book_path: Path, book_schema: dict) -> CheckResult:
    """Validate labels, unresolved @-crossrefs and local images across the reading order."""
    book_result = validate_book(book_path, book_schema, full=True)
    if not book_result.ok:
        return book_result

    root = book_path.parent.resolve()
    try:
        book = load_document(book_path)
        reading_path = (root / book["manuscript"]["reading_order"]).resolve()
        reading = load_document(reading_path)
    except (DocumentError, OSError, KeyError, TypeError) as error:
        return CheckResult(str(book_path), (Issue(str(book_path), str(error)),))

    manuscript_root = (root / book["manuscript"]["root"]).resolve()
    files: list[Path] = []
    for group in READING_KEYS:
        entries = reading.get(group, []) or []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str) and entry.endswith(".qmd"):
                files.append((manuscript_root / entry).resolve())
    canonical = set(files)

    issues: list[Issue] = []
    labels: dict[str, tuple[Path, int]] = {}
    labels_by_file: dict[Path, set[str]] = {}
    parsed: list[tuple[Path, list[tuple[int, str]]]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            issues.append(Issue(str(path), f"cannot read manuscript: {error}"))
            continue
        lines = list(_visible_lines(text))
        parsed.append((path, lines))
        for line_number, line in lines:
            for match in LABEL.finditer(line):
                label = match.group(1)
                labels_by_file.setdefault(path, set()).add(label)
                if label in labels:
                    first_path, first_line = labels[label]
                    issues.append(
                        Issue(
                            f"{path}:{line_number}",
                            f"duplicate explicit label #{label}; first declared at "
                            f"{first_path}:{first_line}",
                        )
                    )
                else:
                    labels[label] = (path, line_number)

    for path, lines in parsed:
        for line_number, line in lines:
            for match in XREF.finditer(line):
                target = match.group(1)
                if target not in labels:
                    issues.append(
                        Issue(f"{path}:{line_number}", f"unresolved explicit cross-reference @{target}")
                    )
            for match in LINK.finditer(line):
                _local_target(
                    path, line_number, match.group(1), root, canonical, labels_by_file, issues
                )
            for match in IMAGE.finditer(line):
                _image_path(path, line_number, match.group(1), root, issues)

    return CheckResult(str(book_path), tuple(issues))
