"""Book descriptor and reading-order validation."""

from __future__ import annotations

from pathlib import Path

from .validation import (
    CheckResult,
    DocumentError,
    Issue,
    load_document,
    load_schema,
    schema_issues,
)

READING_KEYS = ("front", "chapters", "back", "appendices", "references")
REQUIRED_FORMATS = {"html", "pdf", "docx"}


def _resolve_inside(base: Path, relative: str) -> Path | None:
    """Resolve a relative path, rejecting absolute paths, traversal and escapes."""

    if not relative or relative.startswith(("/", "\\")) or "\\" in relative:
        return None
    parts = Path(relative).parts
    if ".." in parts:
        return None
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError:
        return None
    return resolved


def _reading_order_issues(
    reading_order: Path, manuscript_root: Path, full: bool, label: str
) -> list[Issue]:
    issues: list[Issue] = []
    try:
        data = load_document(reading_order)
    except DocumentError as exc:
        return [Issue(label, str(exc))]

    if not isinstance(data, dict):
        return [Issue(f"{label}:reading_order", "reading order must be a mapping of groups")]

    unknown = sorted(set(data) - set(READING_KEYS))
    if unknown:
        issues.append(
            Issue(
                f"{label}:reading_order",
                f"unknown reading-order groups {unknown}; expected {list(READING_KEYS)}",
            )
        )

    entries: list[str] = []
    for key in READING_KEYS:
        value = data.get(key, [])
        if value is None:
            continue
        if not isinstance(value, list):
            issues.append(
                Issue(f"{label}:reading_order.{key}", f"{key} must be a list of manuscript paths")
            )
            continue
        for index, entry in enumerate(value):
            location = f"{label}:reading_order.{key}[{index}]"
            if not isinstance(entry, str):
                issues.append(Issue(location, "reading-order entry must be a string path"))
                continue
            if not entry.endswith(".qmd"):
                issues.append(Issue(location, f"reading-order entry {entry!r} must end with .qmd"))
            resolved = _resolve_inside(manuscript_root, entry)
            if resolved is None:
                issues.append(
                    Issue(location, f"reading-order entry {entry!r} escapes the manuscript root")
                )
                continue
            if not resolved.is_file():
                issues.append(Issue(location, f"reading-order entry {entry!r} does not exist"))
            entries.append(entry)

    seen: set[str] = set()
    for entry in entries:
        if entry in seen:
            issues.append(Issue(f"{label}:reading_order", f"duplicate reading-order entry {entry!r}"))
        seen.add(entry)

    if full:
        chapters = data.get("chapters", []) or []
        if not chapters:
            issues.append(Issue(f"{label}:reading_order.chapters", "at least one chapter is required"))
        discovered = sorted(
            path.relative_to(manuscript_root).as_posix()
            for path in manuscript_root.rglob("*.qmd")
            if path.is_file()
        )
        listed = sorted(set(entries))
        for entry in sorted(set(discovered) - set(listed)):
            issues.append(Issue(f"{label}:reading_order", f"manuscript file {entry!r} is not listed"))
        for entry in sorted(set(listed) - set(discovered)):
            issues.append(
                Issue(f"{label}:reading_order", f"listed manuscript file {entry!r} was not found")
            )

    return issues


def validate_book(path: Path, schema_path: Path, full: bool = False) -> CheckResult:
    """Validate a book descriptor, its reading order and, in full mode, every manuscript file."""

    label = str(path)
    try:
        data = load_document(path)
        schema = load_schema(schema_path)
    except DocumentError as exc:
        return CheckResult(label, (Issue(label, str(exc)),))

    issues = schema_issues(data, schema, label)
    if issues:
        return CheckResult(label, tuple(issues))

    book_root = path.parent.resolve()
    manuscript = data["manuscript"]
    manuscript_root = _resolve_inside(book_root, manuscript["root"])
    if manuscript_root is None or not manuscript_root.is_dir():
        issues.append(
            Issue(
                f"{label}:manuscript.root",
                f"manuscript root {manuscript['root']!r} is missing or outside the book root",
            )
        )
    else:
        reading_order = _resolve_inside(book_root, manuscript["reading_order"])
        if reading_order is None or not reading_order.is_file():
            issues.append(
                Issue(
                    f"{label}:manuscript.reading_order",
                    f"reading order {manuscript['reading_order']!r} is missing or outside the book root",
                )
            )
        else:
            issues.extend(_reading_order_issues(reading_order, manuscript_root, full, label))

    if full and data["status"] in {"active", "pilot"}:
        formats = set(data["publication"]["formats"])
        missing = sorted(REQUIRED_FORMATS - formats)
        if missing:
            issues.append(
                Issue(
                    f"{label}:publication.formats",
                    f"an {data['status']} book must publish {missing}",
                )
            )

    return CheckResult(label, tuple(issues))
