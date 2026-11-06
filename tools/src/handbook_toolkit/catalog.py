"""Catalog validation: schema plus release invariants."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .validation import (
    CheckResult,
    DocumentError,
    Issue,
    load_document,
    schema_issues,
)


def validate_catalog(path: Path, schema: dict[str, Any]) -> CheckResult:
    """Validate a catalog document against its schema and release invariants."""

    label = str(path)
    try:
        data = load_document(path)
    except DocumentError as exc:
        return CheckResult(label, (Issue(label, str(exc)),))

    issues = schema_issues(data, schema, label)
    if issues:
        return CheckResult(label, tuple(issues))

    books = data["books"]
    seen_ids: dict[str, int] = {}
    seen_slugs: dict[str, int] = {}
    seen_urls: dict[str, int] = {}

    for index, book in enumerate(books):
        location = f"{label}:books[{index}]"
        book_id = book["id"]
        slug = book["slug"]

        if book_id in seen_ids:
            issues.append(
                Issue(location, f"duplicate book id {book_id!r}; first used at books[{seen_ids[book_id]}]")
            )
        else:
            seen_ids[book_id] = index

        if slug in seen_slugs:
            issues.append(
                Issue(location, f"duplicate slug {slug!r}; first used at books[{seen_slugs[slug]}]")
            )
        else:
            seen_slugs[slug] = index

        release = book["latest_release"]
        version = release["version"]
        tag = release["tag"]
        if tag != f"v{version}":
            issues.append(Issue(f"{location}.latest_release", f"tag {tag!r} must be 'v{version}'"))

        for field in ("url", "manifest_url", "checksums_url"):
            url = release[field]
            if url in seen_urls:
                issues.append(
                    Issue(
                        f"{location}.latest_release.{field}",
                        f"duplicate release URL; first used at books[{seen_urls[url]}].latest_release",
                    )
                )
            else:
                seen_urls[url] = index

        if not release["url"].rstrip("/").endswith(f"/{tag}"):
            issues.append(
                Issue(
                    f"{location}.latest_release.url",
                    f"release URL must end with the immutable tag /{tag}",
                )
            )
        for field in ("manifest_url", "checksums_url"):
            if f"/{tag}/" not in release[field]:
                issues.append(
                    Issue(
                        f"{location}.latest_release.{field}",
                        f"asset URL must contain the immutable tag segment /{tag}/",
                    )
                )

        try:
            date.fromisoformat(release["published_at"])
        except ValueError:
            issues.append(
                Issue(
                    f"{location}.latest_release.published_at",
                    "published_at must be a real ISO date (YYYY-MM-DD)",
                )
            )

    slugs = [book["slug"] for book in books]
    if slugs != sorted(slugs):
        issues.append(Issue(f"{label}:books", "books must be sorted by slug for deterministic output"))

    return CheckResult(label, tuple(issues))
