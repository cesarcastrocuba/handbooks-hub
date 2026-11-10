#!/usr/bin/env python3
"""Replace the template identifiers with the identity of a new book.

This is book-owned bootstrap code. It lives in the book, not in the shared toolkit, and it uses
only PyYAML, which the pinned toolkit installs. Every input arrives as an argument, so no value is
ever interpolated into a shell script.

The script refuses to run once ``book.yaml`` no longer has the template identifier, so a second run
cannot overwrite a real book. On any validation failure it exits with a non-zero status and writes
nothing.
"""

from __future__ import annotations

import argparse
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
    """Validate every input before touching the book. Return the trimmed summary."""

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
    summary = args.summary.strip()
    if not summary:
        fail("summary must not be empty")
    if len(summary) > MAX_SUMMARY:
        fail(f"summary must be at most {MAX_SUMMARY} characters")
    return summary


def dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


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

    book["id"] = args.identifier
    book["title"] = args.title.strip()
    catalog = book.setdefault("catalog", {})
    catalog["slug"] = args.identifier
    catalog["summary"] = summary
    catalog["categories"] = [args.category]
    repository = book.setdefault("repository", {})
    repository["url"] = args.repository_url

    quarto_book = quarto.setdefault("book", {})
    quarto_book["title"] = args.title.strip()
    quarto_book["author"] = args.author.strip()

    metadata["version"] = DEFAULT_VERSION
    metadata["status"] = DEFAULT_STATUS

    notice = paths["notice"].read_text(encoding="utf-8")
    notice = replace_once(
        notice,
        "# Licensing and attribution — handbook template",
        f"# Licensing and attribution — {args.title.strip()}",
        paths["notice"],
    )
    notice = replace_once(
        notice,
        "Copyright © 2026 Franz César Castro Cuba.",
        f"Copyright © 2026 {args.author.strip()}.",
        paths["notice"],
    )

    license_code = paths["license"].read_text(encoding="utf-8")
    license_code = replace_once(
        license_code,
        "Copyright (c) 2026 Franz César Castro Cuba",
        f"Copyright (c) 2026 {args.author.strip()}",
        paths["license"],
    )

    readme = paths["readme"].read_text(encoding="utf-8")
    heading = re.compile(r"^# Book template \d+\.\d+\.\d+\s*$", re.MULTILINE)
    if not heading.search(readme):
        fail(f"{paths['readme']} no longer starts with the template heading")
    readme = heading.sub(f"# {args.title.strip()}", readme, count=1)

    paths["book"].write_text(dump_yaml(book), encoding="utf-8")
    paths["quarto"].write_text(dump_yaml(quarto), encoding="utf-8")
    paths["metadata"].write_text(dump_yaml(metadata), encoding="utf-8")
    paths["notice"].write_text(notice, encoding="utf-8")
    paths["license"].write_text(license_code, encoding="utf-8")
    paths["readme"].write_text(readme, encoding="utf-8")

    print(f"initialized {args.identifier}: {args.title.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
