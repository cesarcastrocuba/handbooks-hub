#!/usr/bin/env python3
"""Point an existing catalog entry at a newer published release of its book.

The core (:func:`plan_update` and :func:`published_date`) is deterministic and performs no network
access. The caller fetches the GitHub release object and passes it in as a file. Only
``latest_release`` is ever rewritten: adding a book or changing its metadata is a human change.

Usage:
  python3 tools/scripts/update_catalog.py source-repo --catalog FILE --slug SLUG --tag TAG
  python3 tools/scripts/update_catalog.py apply --catalog FILE --slug SLUG --tag TAG \
      --source-repo OWNER/REPO --release-json FILE
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
from urllib.parse import urlsplit

from handbook_toolkit.catalog import ASSET_FILES, validate_catalog
from handbook_toolkit.publication import CHECKSUMS, MANIFEST
from handbook_toolkit.validation import load_packaged_schema

TAG_PATTERN = re.compile(r"v(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})")
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
TIMESTAMP_PATTERN = re.compile(r"([0-9]{4}-[0-9]{2}-[0-9]{2})T[0-9:.]+(?:Z|[+-][0-9:]+)")
REPO_PART = re.compile(r"[A-Za-z0-9_.-]+")


class CatalogUpdateError(ValueError):
    """The requested update is not allowed; the catalog must stay as it is."""


@dataclass(frozen=True)
class UpdatePlan:
    """The outcome of one requested update."""

    document: dict[str, Any]
    changed: bool
    message: str


def parse_tag(tag: str) -> tuple[int, int, int]:
    """Return the numeric version of an exact ``vMAJOR.MINOR.PATCH`` tag."""

    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise CatalogUpdateError(f"malformed tag {tag!r}: expected exact vMAJOR.MINOR.PATCH")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def _check_source_repo(source_repo: str) -> None:
    parts = source_repo.split("/")
    if len(parts) != 2 or not all(REPO_PART.fullmatch(part) and part not in {".", ".."} for part in parts):
        raise CatalogUpdateError(f"malformed source repository {source_repo!r}: expected OWNER/REPO")


def _check_published_at(published_at: str) -> None:
    try:
        if DATE_PATTERN.fullmatch(published_at) is None:
            raise ValueError
        date.fromisoformat(published_at)
    except ValueError:
        raise CatalogUpdateError(f"malformed published date {published_at!r}: expected YYYY-MM-DD") from None


def _check_catalog(document: dict[str, Any], label: str) -> None:
    """Run the toolkit validator, which reads from a path, on an in-memory document."""

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "catalog.json"
        path.write_text(serialize(document), encoding="utf-8")
        result = validate_catalog(path, load_packaged_schema("catalog.schema.json"))
    if not result.ok:
        details = "; ".join(sorted(f"{issue.location.replace(str(path), 'catalog')}: {issue.message}" for issue in result.issues))
        raise CatalogUpdateError(f"{label} catalog is invalid: {details}")


def _find_book(document: dict[str, Any], slug: str) -> dict[str, Any]:
    for book in document["books"]:
        if book["slug"] == slug:
            return book
    raise CatalogUpdateError(f"unknown book {slug!r}: adding a book to the catalog is a human change")


def source_repo_of(book: dict[str, Any]) -> str:
    """Return the ``OWNER/REPO`` that a catalog entry's current release belongs to."""

    release_url = book["latest_release"]["url"]
    parsed = urlsplit(release_url)
    parts = parsed.path.strip("/").split("/")
    if parsed.hostname != "github.com" or len(parts) != 5 or parts[2:4] != ["releases", "tag"]:
        raise CatalogUpdateError(f"automation supports GitHub Releases URLs only, not {release_url!r}")
    return "/".join(parts[:2])


def release_entry(source_repo: str, tag: str, published_at: str, roles: tuple[str, ...] = ()) -> dict[str, Any]:
    """Build the ``latest_release`` object that the catalog contract requires.

    ``roles`` lists the artifact roles whose canonical file is attached to the release; each one
    becomes a direct download link under ``assets`` (catalog schema 1.1).
    """

    site = f"https://github.com/{source_repo}/releases"
    entry: dict[str, Any] = {
        "version": tag[1:],
        "tag": tag,
        "url": f"{site}/tag/{tag}",
        "published_at": published_at,
        "manifest_url": f"{site}/download/{tag}/{MANIFEST}",
        "checksums_url": f"{site}/download/{tag}/{CHECKSUMS}",
    }
    if roles:
        entry["assets"] = {role: f"{site}/download/{tag}/{ASSET_FILES[role]}" for role in ASSET_FILES if role in roles}
    return entry


def release_roles(release: Any, source_repo: str, tag: str) -> tuple[str, ...]:
    """Return the artifact roles whose canonical file is an uploaded asset of this release.

    A release object without an ``assets`` list yields no roles, so the catalog entry carries no
    direct download links. Online verification later checks every link against the manifest.
    """

    assets = release.get("assets") if isinstance(release, dict) else None
    if not isinstance(assets, list):
        return ()
    prefix = f"https://github.com/{source_repo}/releases/download/{tag}/"
    uploaded = {
        asset.get("name")
        for asset in assets
        if isinstance(asset, dict)
        and asset.get("state") == "uploaded"
        and asset.get("browser_download_url") == prefix + str(asset.get("name"))
    }
    return tuple(role for role, name in ASSET_FILES.items() if name in uploaded)


def published_date(release: Any, tag: str) -> str:
    """Return the publication date of a GitHub release object, rejecting unstable releases."""

    if not isinstance(release, dict):
        raise CatalogUpdateError("release data must be a JSON object")
    if release.get("tag_name") != tag:
        raise CatalogUpdateError(f"release data is for {release.get('tag_name')!r}, not {tag!r}")
    if release.get("draft") is not False:
        raise CatalogUpdateError(f"release {tag} is a draft or does not state that it is not one")
    if release.get("prerelease") is not False:
        raise CatalogUpdateError(f"release {tag} is a prerelease or does not state that it is not one")
    published_at = release.get("published_at")
    match = TIMESTAMP_PATTERN.fullmatch(published_at) if isinstance(published_at, str) else None
    if match is None:
        raise CatalogUpdateError(f"release {tag} has no usable published_at timestamp: {published_at!r}")
    return match.group(1)


def _without_assets(release: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in release.items() if key != "assets"}


def plan_update(
    document: dict[str, Any], slug: str, source_repo: str, tag: str, published_at: str, roles: tuple[str, ...] = ()
) -> UpdatePlan:
    """Return the catalog with ``slug`` listing ``tag``; the input document is not modified.

    A listed release never changes: asking again for the listed tag is a no-op and does not add
    download links to an entry that was listed without them.
    """

    version = parse_tag(tag)
    _check_source_repo(source_repo)
    _check_published_at(published_at)
    _check_catalog(document, "input")

    updated = copy.deepcopy(document)
    book = _find_book(updated, slug)
    if book["status"] != "published":
        raise CatalogUpdateError(f"book {slug!r} is {book['status']}: changing its status is a human change")
    catalog_repo = source_repo_of(book)
    if source_repo != catalog_repo:
        raise CatalogUpdateError(f"book {slug!r} is released from {catalog_repo}, not {source_repo}: moving it is a human change")

    current = book["latest_release"]
    entry = release_entry(source_repo, tag, published_at, roles)
    current_version = parse_tag(current["tag"])
    if version < current_version:
        raise CatalogUpdateError(f"version downgrade rejected: {slug} lists {current['tag']}, requested {tag}")
    if version == current_version:
        if _without_assets(current) != _without_assets(entry) or ("assets" in current and current != entry):
            raise CatalogUpdateError(f"{slug} already lists {tag} with different release data: a published release must not change")
        return UpdatePlan(updated, False, f"no-op: {slug} already lists {tag}")

    book["latest_release"] = entry
    if "assets" in entry:
        updated["schema_version"] = "1.1"
    _check_catalog(updated, "updated")
    return UpdatePlan(updated, True, f"updated: {slug} {current['tag']} -> {tag} (published {published_at})")


def serialize(document: dict[str, Any]) -> str:
    """Render a catalog in the repository's canonical JSON form."""

    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CatalogUpdateError(f"cannot read {path}: {error}") from error


def _source_repo_command(args: argparse.Namespace) -> None:
    parse_tag(args.tag)
    document = _read_json(args.catalog)
    _check_catalog(document, "input")
    print(source_repo_of(_find_book(document, args.slug)))


def _apply_command(args: argparse.Namespace) -> None:
    release = _read_json(args.release_json)
    published_at = published_date(release, args.tag)
    roles = release_roles(release, args.source_repo, args.tag)
    plan = plan_update(_read_json(args.catalog), args.slug, args.source_repo, args.tag, published_at, roles)
    if plan.changed:
        args.catalog.write_text(serialize(plan.document), encoding="utf-8", newline="\n")
    print(plan.message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update an existing catalog entry to a newer published release")
    commands = parser.add_subparsers(dest="command", required=True)

    source_repo = commands.add_parser("source-repo", help="validate the request and print the book's OWNER/REPO")
    apply = commands.add_parser("apply", help="list the release in the catalog")
    for command in (source_repo, apply):
        command.add_argument("--catalog", type=Path, required=True)
        command.add_argument("--slug", required=True)
        command.add_argument("--tag", required=True)
    apply.add_argument("--source-repo", required=True)
    apply.add_argument("--release-json", type=Path, required=True, help="GitHub release object for the tag")
    source_repo.set_defaults(handler=_source_repo_command)
    apply.set_defaults(handler=_apply_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.handler(args)
    except CatalogUpdateError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
