#!/usr/bin/env python3
"""Replace the template identifiers with the identity of a new book.

This is book-owned bootstrap code. It lives in the book, not in the shared toolkit, and it uses
only PyYAML, which the pinned toolkit installs. Every input arrives as an argument, so no value is
ever interpolated into a shell script.

The rewrites are textual: only the changed values are replaced, so comments, quoting, key order,
blank lines and every other byte of the template files survive. Before writing, the script parses
the result and refuses to continue unless every requested value round-trips exactly and no
unrelated key changed. The script refuses to run once ``book.yaml`` no longer has the template
identifier, so a second run cannot overwrite a real book.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
from typing import NoReturn

import yaml

TEMPLATE_ID = "template-book"
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{1,63}")
REPOSITORY_URL = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
CATEGORIES = (
    "architecture",
    "authoring",
    "cloud",
    "data",
    "engineering",
    "governance",
    "publishing",
    "security",
)
MAX_SUMMARY = 280
DEFAULT_VERSION = "0.1.0"
DEFAULT_STATUS = "Draft"

FILES = {
    "book": Path("book.yaml"),
    "quarto": Path("publishing/_quarto.yml"),
    "metadata": Path("publishing/metadata.yaml"),
    "notice": Path("NOTICE.md"),
    "license": Path("LICENSE-CODE"),
    "readme": Path("README.md"),
}

KEY_LINE = re.compile(r"^(\s*)([A-Za-z0-9_.-]+):(?:\s|$)")


def fail(message: str) -> NoReturn:
    print(f"initialize-book: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot read {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path} must contain a mapping")
    return data


def validate(args: argparse.Namespace) -> str:
    """Validate every input before touching the book. Return the summary as provided."""

    if not IDENTIFIER.fullmatch(args.identifier):
        fail("id must match ^[a-z][a-z0-9-]{1,63}$")
    if not args.title.strip():
        fail("title must not be empty")
    if not args.author.strip():
        fail("author must not be empty")
    if args.category not in CATEGORIES:
        fail(f"category must be one of {', '.join(CATEGORIES)}")
    if not REPOSITORY_URL.fullmatch(args.repository_url):
        fail("repository URL must look like https://github.com/OWNER/REPOSITORY")
    if not args.summary.strip():
        fail("summary must not be empty")
    if len(args.summary) > MAX_SUMMARY:
        fail(f"summary must be at most {MAX_SUMMARY} characters")
    return args.summary


def yaml_scalar(value: object) -> str:
    """Return a single-line, safely quoted YAML scalar for *value*.

    A JSON string is a valid YAML double-quoted scalar. Using it guarantees one physical line and
    exact round-tripping for colons, quotes, ``#``, leading or trailing spaces, control characters
    and non-ASCII text.
    """

    return json.dumps(value, ensure_ascii=False)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _find_key(lines: list[str], path: tuple[str, ...], label: str) -> int:
    """Return the line index of a nested key, following indentation and skipping comments."""

    start = 0
    parent_indent = -1
    index = -1
    for depth, key in enumerate(path):
        found = None
        for position in range(start, len(lines)):
            stripped = lines[position].strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = KEY_LINE.match(lines[position])
            if match is None:
                continue
            indent = len(match.group(1))
            if depth == 0 and indent != 0:
                continue
            if depth > 0 and indent <= parent_indent:
                break
            if match.group(2) == key:
                found = position
                break
        if found is None:
            fail(f"{label} has no {'.'.join(path)} key")
        index = found
        parent_indent = len(KEY_LINE.match(lines[found]).group(1))
        start = found + 1
    return index


def set_scalar(text: str, path: tuple[str, ...], value: object, label: str) -> str:
    """Replace one scalar value in place, keeping indentation, separator and line ending."""

    lines = text.splitlines(keepends=True)
    index = _find_key(lines, path, label)
    match = re.match(
        rf"^(\s*{re.escape(path[-1])}\s*:)([ \t]*)([^\r\n]*)(\r?\n)?$", lines[index]
    )
    if match is None:
        fail(f"{label} has an unexpected shape for {'.'.join(path)}")
    separator = match.group(2) or " "
    newline = match.group(4) or ""
    lines[index] = f"{match.group(1)}{separator}{yaml_scalar(value)}{newline}"
    return "".join(lines)


def set_sequence(text: str, path: tuple[str, ...], values: list[object], label: str) -> str:
    """Replace a block sequence in place, keeping the item indentation and line ending."""

    lines = text.splitlines(keepends=True)
    index = _find_key(lines, path, label)
    key_indent = _indent(lines[index])
    item_indent = None
    end = index + 1
    position = index + 1
    while position < len(lines):
        stripped = lines[position].strip()
        if not stripped or stripped.startswith("#"):
            break
        indent = _indent(lines[position])
        if indent <= key_indent:
            break
        if not stripped.startswith("- "):
            break
        if item_indent is None:
            item_indent = indent
        if indent != item_indent:
            break
        end = position + 1
        position += 1
    if item_indent is None:
        item_indent = key_indent + 2
    newline = "\n" if lines[index].endswith("\n") else ""
    replacement = [" " * item_indent + "- " + yaml_scalar(value) + newline for value in values]
    lines[index + 1 : end] = replacement
    return "".join(lines)


def parsed(path: Path, text: str) -> object:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        fail(f"{path} does not parse after the rewrite: {exc}")


def commit(changes: dict[Path, str], expectations: dict[Path, object]) -> None:
    """Write every change, verify it, and restore the originals on any failure."""

    originals = {path: path.read_text(encoding="utf-8") for path in changes}
    try:
        for path, text in changes.items():
            path.write_text(text, encoding="utf-8")
        for path, expected in expectations.items():
            actual = yaml.safe_load(path.read_text(encoding="utf-8"))
            if actual != expected:
                raise ValueError(f"{path.name} does not round-trip the requested values")
        for path, text in changes.items():
            if path.read_text(encoding="utf-8") != text:
                raise ValueError(f"{path.name} was not written exactly")
    except (OSError, yaml.YAMLError, ValueError) as exc:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        fail(f"cannot write the initialized book: {exc}")


def replace_once(text: str, old: str, new: str, path: Path) -> str:
    if old not in text:
        fail(f"{path} no longer contains the expected text: {old!r}")
    return text.replace(old, new, 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replace the template identifiers with the identity of a new book."
    )
    parser.add_argument("--root", default=".", help="book repository root (default: current directory)")
    parser.add_argument("--id", dest="identifier", required=True, help="book identifier slug")
    parser.add_argument("--title", required=True, help="book title")
    parser.add_argument("--author", required=True, help="author or copyright holder")
    parser.add_argument("--summary", required=True, help="catalog summary")
    parser.add_argument("--category", required=True, help="primary catalog category")
    parser.add_argument("--repository-url", required=True, help="public repository URL")
    args = parser.parse_args(argv)

    summary = validate(args)
    root = Path(args.root).resolve()
    paths = {name: root / relative for name, relative in FILES.items()}
    for path in paths.values():
        if not path.is_file():
            fail(f"required file is missing: {path}")

    book = load_yaml(paths["book"])
    if book.get("id") != TEMPLATE_ID:
        fail(f"book.yaml id is {book.get('id')!r}; this book is already initialized")

    quarto = load_yaml(paths["quarto"])
    metadata = load_yaml(paths["metadata"])

    expected_book = deepcopy(book)
    expected_book["id"] = args.identifier
    expected_book["title"] = args.title
    expected_book["catalog"]["slug"] = args.identifier
    expected_book["catalog"]["summary"] = summary
    expected_book["catalog"]["categories"] = [args.category]
    expected_book["repository"]["url"] = args.repository_url

    expected_quarto = deepcopy(quarto)
    expected_quarto["book"]["title"] = args.title
    expected_quarto["book"]["author"] = args.author

    expected_metadata = deepcopy(metadata)
    expected_metadata["version"] = DEFAULT_VERSION
    expected_metadata["status"] = DEFAULT_STATUS

    book_text = paths["book"].read_text(encoding="utf-8")
    book_text = set_scalar(book_text, ("id",), args.identifier, "book.yaml")
    book_text = set_scalar(book_text, ("title",), args.title, "book.yaml")
    book_text = set_scalar(book_text, ("catalog", "slug"), args.identifier, "book.yaml")
    book_text = set_scalar(book_text, ("catalog", "summary"), summary, "book.yaml")
    book_text = set_sequence(book_text, ("catalog", "categories"), [args.category], "book.yaml")
    book_text = set_scalar(book_text, ("repository", "url"), args.repository_url, "book.yaml")

    quarto_text = paths["quarto"].read_text(encoding="utf-8")
    quarto_text = set_scalar(quarto_text, ("book", "title"), args.title, "_quarto.yml")
    quarto_text = set_scalar(quarto_text, ("book", "author"), args.author, "_quarto.yml")

    metadata_text = paths["metadata"].read_text(encoding="utf-8")
    metadata_text = set_scalar(metadata_text, ("version",), DEFAULT_VERSION, "metadata.yaml")
    metadata_text = set_scalar(metadata_text, ("status",), DEFAULT_STATUS, "metadata.yaml")

    if parsed(paths["book"], book_text) != expected_book:
        fail("book.yaml would not round-trip the requested values")
    if parsed(paths["quarto"], quarto_text) != expected_quarto:
        fail("_quarto.yml would not round-trip the requested values")
    if parsed(paths["metadata"], metadata_text) != expected_metadata:
        fail("metadata.yaml would not round-trip the requested values")

    notice = paths["notice"].read_text(encoding="utf-8")
    notice = replace_once(
        notice,
        "# Licensing and attribution — handbook template",
        f"# Licensing and attribution — {args.title}",
        paths["notice"],
    )
    notice = replace_once(
        notice,
        "Copyright © 2026 Franz César Castro Cuba.",
        f"Copyright © 2026 {args.author}.",
        paths["notice"],
    )

    license_code = paths["license"].read_text(encoding="utf-8")
    license_code = replace_once(
        license_code,
        "Copyright (c) 2026 Franz César Castro Cuba",
        f"Copyright (c) 2026 {args.author}",
        paths["license"],
    )

    readme = paths["readme"].read_text(encoding="utf-8")
    heading = re.compile(r"^# Book template \d+\.\d+\.\d+\s*$", re.MULTILINE)
    if not heading.search(readme):
        fail(f"{paths['readme']} no longer starts with the template heading")
    readme = heading.sub(f"# {args.title}", readme, count=1)

    commit(
        {
            paths["book"]: book_text,
            paths["quarto"]: quarto_text,
            paths["metadata"]: metadata_text,
            paths["notice"]: notice,
            paths["license"]: license_code,
            paths["readme"]: readme,
        },
        {
            paths["book"]: expected_book,
            paths["quarto"]: expected_quarto,
            paths["metadata"]: expected_metadata,
        },
    )

    print(f"initialized {args.identifier}: {args.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
