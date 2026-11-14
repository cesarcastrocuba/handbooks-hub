"""Documentation currency: release facts stated in prose must match their source of truth.

A version written into a status sentence goes stale silently at the next release. This check ties
the few statements that name a current version to the file that owns it:

- the toolkit version belongs to ``tools/pyproject.toml`` (in development) and to the template's
  pin in ``template/book/book.yaml`` (released);
- the template version belongs to the heading of ``template/book/README.md``;
- a book's current release belongs to ``catalog/catalog.json``. The catalog moves through an
  automated pull request that changes nothing else, so no other file may repeat that tag as current;
- wording that describes shipped work as future is rejected outright.

Dated records (decisions, the implementation plan, upgrade notes, change records) are history and
are not checked.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib

import yaml

from .validation import CheckResult, Issue

LABEL = "documentation currency"

VERSION_STATEMENT_FILES = ("README.md", "STATUS.md")
CATALOG_FREE_FILES = ("README.md",)
HISTORY_FILES = frozenset(
    {"docs/decisions.md", "docs/implementation-plan.md", "docs/book-upgrade.md", "CHANGELOG.md"}
)
STALE_PHRASES = ("future publication", "status: planned")

TOOLKIT_STATEMENT = re.compile(r"\btoolkit `(\d+\.\d+\.\d+)`", re.IGNORECASE)
TEMPLATE_STATEMENT = re.compile(r"\btemplate `(\d+\.\d+\.\d+)`", re.IGNORECASE)
RELEASE_STATEMENT = re.compile(r"`([a-z0-9][a-z0-9-]*)` `(v\d+\.\d+\.\d+)`")
TEMPLATE_HEADING = re.compile(r"^# Book template (\d+\.\d+\.\d+)\s*$", re.MULTILINE)


class SourceError(Exception):
    """A source of truth is missing or unreadable."""


@dataclass(frozen=True)
class ReleaseFacts:
    """The versions the repository's own files declare."""

    toolkit: frozenset[str]
    template: str
    slugs: frozenset[str]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceError(f"cannot read {path}: {exc}") from exc


def load_release_facts(root: Path) -> ReleaseFacts:
    try:
        development = tomllib.loads(_read(root / "tools/pyproject.toml"))["project"]["version"]
        released = yaml.safe_load(_read(root / "template/book/book.yaml"))["toolkit"]
        books = json.loads(_read(root / "catalog/catalog.json"))["books"]
        slugs = frozenset(book["slug"] for book in books)
    except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise SourceError(f"a source of truth has an unexpected shape: {exc!r}") from exc
    heading = TEMPLATE_HEADING.search(_read(root / "template/book/README.md"))
    if heading is None:
        raise SourceError("template/book/README.md has no '# Book template X.Y.Z' heading")
    return ReleaseFacts(frozenset({development, released}), heading.group(1), slugs)


def _lines(path: Path) -> list[tuple[int, str]]:
    return list(enumerate(path.read_text(encoding="utf-8").splitlines(), start=1))


def _version_issues(path: Path, facts: ReleaseFacts) -> list[Issue]:
    issues: list[Issue] = []
    expected_toolkit = " or ".join(sorted(facts.toolkit))
    for number, line in _lines(path):
        for match in TOOLKIT_STATEMENT.finditer(line):
            if match.group(1) not in facts.toolkit:
                issues.append(
                    Issue(
                        f"{path}:{number}",
                        f"states toolkit {match.group(1)}; tools/pyproject.toml and the template "
                        f"pin say {expected_toolkit}",
                    )
                )
        for match in TEMPLATE_STATEMENT.finditer(line):
            if match.group(1) != facts.template:
                issues.append(
                    Issue(
                        f"{path}:{number}",
                        f"states template {match.group(1)}; template/book/README.md says "
                        f"{facts.template}",
                    )
                )
    return issues


def _catalog_issues(path: Path, facts: ReleaseFacts) -> list[Issue]:
    return [
        Issue(
            f"{path}:{number}",
            f"repeats the release {match.group(2)} of {match.group(1)}; link to the catalog "
            "instead, because the catalog changes without this file",
        )
        for number, line in _lines(path)
        for match in RELEASE_STATEMENT.finditer(line)
        if match.group(1) in facts.slugs
    ]


def _stale_phrase_issues(path: Path) -> list[Issue]:
    return [
        Issue(f"{path}:{number}", f"describes shipped work as pending: {phrase!r}")
        for number, line in _lines(path)
        for phrase in STALE_PHRASES
        if phrase in line.lower()
    ]


def _current_state_documents(root: Path) -> list[Path]:
    candidates = sorted(root.glob("*.md")) + sorted((root / "docs").glob("*.md"))
    return [path for path in candidates if path.relative_to(root).as_posix() not in HISTORY_FILES]


def check_documentation_currency(root: Path) -> CheckResult:
    """Compare version statements with their sources and reject wording about a past future."""

    root = root.resolve()
    try:
        facts = load_release_facts(root)
    except SourceError as exc:
        return CheckResult(LABEL, (Issue(str(root), str(exc)),))

    issues: list[Issue] = []
    for name in VERSION_STATEMENT_FILES:
        if (root / name).is_file():
            issues += _version_issues(root / name, facts)
    for name in CATALOG_FREE_FILES:
        if (root / name).is_file():
            issues += _catalog_issues(root / name, facts)
    for path in _current_state_documents(root):
        issues += _stale_phrase_issues(path)
    return CheckResult(LABEL, tuple(issues))
