"""Repository-level checks and relative documentation-link verification."""

from __future__ import annotations

import re
from pathlib import Path

from .books import validate_book
from .catalog import validate_catalog
from .profiles import validate_profile
from .validation import CheckResult, DocumentError, Issue, load_schema_source

SCHEMA_NAMES = ("book.schema.json", "catalog.schema.json", "profile.schema.json")

REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "STATUS.md",
    "NOTICE.md",
    "LICENSE",
    "LICENSE-CODE",
    "docs/architecture.md",
    "docs/editorial-contract.md",
    "docs/publication-contract.md",
    "docs/catalog-contract.md",
    "docs/decisions.md",
    "docs/assumptions.md",
    "docs/implementation-plan.md",
    "profiles/standard/profile.yaml",
    "tools/src/handbook_toolkit/schemas/book.schema.json",
    "tools/src/handbook_toolkit/schemas/catalog.schema.json",
    "tools/src/handbook_toolkit/schemas/profile.schema.json",
    "catalog/catalog.json",
    "template/book/book.yaml",
)

DOC_FILES = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "STATUS.md",
    "NOTICE.md",
    "CHANGELOG.md",
)

LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _required_files(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            issues.append(Issue(str(root / relative), "required file is missing"))
    return issues


def _documentation_files(root: Path) -> list[Path]:
    files = [root / name for name in DOC_FILES]
    for directory in ("docs", "sdd"):
        base = root / directory
        if base.is_dir():
            files.extend(sorted(base.rglob("*.md")))
    return [path for path in files if path.is_file()]


def check_documentation_links(root: Path) -> CheckResult:
    """Check relative Markdown links and images; skip URLs, anchors and fenced code."""

    issues: list[Issue] = []
    for path in _documentation_files(root):
        in_fence = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for match in LINK.finditer(line):
                target = match.group(1).strip()
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1].strip()
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    issues.append(
                        Issue(f"{path}:{number}", f"link target {target!r} escapes the repository")
                    )
                    continue
                if not resolved.exists():
                    issues.append(Issue(f"{path}:{number}", f"link target {target!r} does not exist"))
    return CheckResult("documentation links", tuple(issues))


def verify_repository(
    root: Path, full: bool = False, schemas: Path | None = None
) -> list[CheckResult]:
    """Run the hub's deterministic checks.

    Schemas come from the installed toolkit package unless *schemas* overrides the directory.
    Full mode adds documentation links and manuscript completeness.
    """

    root = root.resolve()
    results: list[CheckResult] = [CheckResult("repository files", tuple(_required_files(root)))]

    catalog_path = root / "catalog/catalog.json"
    profile_path = root / "profiles/standard/profile.yaml"
    book_path = root / "template/book/book.yaml"

    try:
        loaded = {name: load_schema_source(name, schemas) for name in SCHEMA_NAMES}
    except DocumentError as exc:
        results.append(CheckResult("packaged schemas", (Issue("packaged schemas", str(exc)),)))
        return results

    results.append(CheckResult("packaged schemas", ()))

    if catalog_path.is_file():
        results.append(validate_catalog(catalog_path, loaded["catalog.schema.json"]))
    if profile_path.is_file():
        results.append(validate_profile(profile_path, loaded["profile.schema.json"]))
    if book_path.is_file():
        results.append(validate_book(book_path, loaded["book.schema.json"], full=full))

    if full:
        results.append(check_documentation_links(root))

    return results
