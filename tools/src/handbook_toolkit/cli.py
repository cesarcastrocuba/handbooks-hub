"""Command-line interface for the handbook toolkit."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

from . import __version__
from .books import validate_book
from .build import BuildError, build_book
from .catalog import validate_catalog
from .manuscript import validate_manuscript
from .profiles import validate_profile
from .references import validate_references
from .repository import verify_repository
from .validation import (
    CheckResult,
    DocumentError,
    Issue,
    load_document,
    load_schema_source,
    resolve_document,
)

DEFAULT_CATALOG = "catalog/catalog.json"
DEFAULT_PROFILE = "profiles/standard/profile.yaml"
DEFAULT_BOOK = "book.yaml"


def _print_result(result: CheckResult) -> None:
    status = "OK" if result.ok else f"{len(result.issues)} problem(s)"
    print(f"{result.label}: {status}")
    for issue in result.issues:
        print(f"  {issue}", file=sys.stderr)


def _summary(name: str, results: list[CheckResult]) -> int:
    problems = sum(len(result.issues) for result in results)
    print(f"{name}: {len(results)} check(s), {problems} problem(s)")
    return 0 if problems == 0 else 1


def _schema_override(args: argparse.Namespace) -> Path | None:
    return Path(args.schemas).resolve() if args.schemas else None


def _load_schema(args: argparse.Namespace, name: str) -> dict[str, Any] | None:
    try:
        return load_schema_source(name, _schema_override(args))
    except DocumentError as exc:
        _print_result(CheckResult(name, (Issue(name, str(exc)),)))
        return None


def command_verify(args: argparse.Namespace) -> int:
    results = verify_repository(
        Path(args.root), full=args.full, schemas=_schema_override(args)
    )
    for result in results:
        _print_result(result)
    return _summary("VERIFY (full)" if args.full else "VERIFY", results)


def command_catalog(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = resolve_document(root, args.path, DEFAULT_CATALOG)
    schema = _load_schema(args, "catalog.schema.json")
    if schema is None:
        return 1
    result = validate_catalog(path, schema)
    _print_result(result)
    return 0 if result.ok else 1


def command_profile(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = resolve_document(root, args.path, DEFAULT_PROFILE)
    schema = _load_schema(args, "profile.schema.json")
    if schema is None:
        return 1
    result = validate_profile(path, schema)
    _print_result(result)
    return 0 if result.ok else 1


def command_book(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = resolve_document(root, args.path, DEFAULT_BOOK)
    schema = _load_schema(args, "book.schema.json")
    if schema is None:
        return 1
    result = validate_book(path, schema, full=args.full)
    _print_result(result)
    return 0 if result.ok else 1


def command_manuscript(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = resolve_document(root, args.path, args.path)
    profile_path = resolve_document(root, args.profile, args.profile)

    schema = _load_schema(args, "profile.schema.json")
    if schema is None:
        return 1

    profile_result = validate_profile(profile_path, schema)
    if not profile_result.ok:
        _print_result(profile_result)
        return 1

    try:
        profile = load_document(profile_path)
    except DocumentError as exc:
        _print_result(CheckResult(str(profile_path), (Issue(str(profile_path), str(exc)),)))
        return 1

    result = validate_manuscript(path, profile, args.mode)
    _print_result(result)
    return 0 if result.ok else 1


def command_build(args: argparse.Namespace) -> int:
    try:
        result = build_book(
            Path(args.repo),
            args.commit,
            Path(args.output),
            profile=Path(args.profile) if args.profile else None,
            version=args.version,
            epoch=args.epoch,
            quarto=args.quarto,
            mode=args.mode,
            preview=args.preview,
        )
    except (BuildError, DocumentError, OSError, ValueError) as exc:
        print(f"BUILD: FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"{result.output}: OK")
    print(f"commit: {result.commit}")
    print(f"version: {result.version}")
    print(f"epoch: {result.epoch}")
    print("tool_versions: " + ", ".join(f"{key}={value}" for key, value in sorted(result.tool_versions.items())))
    return 0


def command_references(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = resolve_document(root, args.path, DEFAULT_BOOK)
    schema = _load_schema(args, "book.schema.json")
    if schema is None:
        return 1
    result = validate_references(path, schema)
    _print_result(result)
    return 0 if result.ok else 1


def command_version(_args: argparse.Namespace) -> int:
    print(f"handbook-toolkit {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="handbook-toolkit",
        description="Deterministic validators and shared tooling for handbook repositories.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="repository root (default: current directory)",
    )
    parser.add_argument(
        "--schemas",
        help="optional schema directory override (default: schemas bundled with the installed toolkit)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="run all repository validations")
    verify.add_argument(
        "--full",
        action="store_true",
        help="add documentation-link and template completeness checks",
    )
    verify.set_defaults(func=command_verify)

    catalog = subparsers.add_parser("validate-catalog", help="validate a catalog document")
    catalog.add_argument("path", nargs="?", help=f"default: {DEFAULT_CATALOG}")
    catalog.set_defaults(func=command_catalog)

    profile = subparsers.add_parser("validate-profile", help="validate an editorial profile")
    profile.add_argument("path", nargs="?", help=f"default: {DEFAULT_PROFILE}")
    profile.set_defaults(func=command_profile)

    book = subparsers.add_parser("validate-book", help="validate a book descriptor")
    book.add_argument("path", nargs="?", help=f"default: {DEFAULT_BOOK}")
    book.add_argument("--full", action="store_true", help="also check every manuscript file is listed")
    book.set_defaults(func=command_book)

    manuscript = subparsers.add_parser(
        "validate-manuscript",
        help="validate a section pilot or chapter against an explicit profile",
    )
    manuscript.add_argument("path", help="Markdown/Quarto file to validate")
    manuscript.add_argument(
        "--mode",
        required=True,
        choices=("section-pilot", "chapter"),
        help="structural mode: one section pilot or a full chapter",
    )
    manuscript.add_argument(
        "--profile",
        required=True,
        help="profile YAML to validate against; explicit until packaged profile resolution exists",
    )
    manuscript.set_defaults(func=command_manuscript)

    build = subparsers.add_parser(
        "build-book",
        help="build a local six-file publication payload set without publishing",
    )
    build.add_argument("--repo", required=True, help="book repository path")
    build.add_argument("--commit", required=True, help="exact clean 40-character source commit")
    build.add_argument("--output", required=True, help="new external output directory; must not exist")
    build.add_argument(
        "--profile",
        help="optional explicit reviewed profile YAML; default resolves the exact book pin from the installed package",
    )
    build.add_argument("--version", help="book version; defaults to publishing/metadata.yaml")
    build.add_argument("--epoch", type=int, help="SOURCE_DATE_EPOCH; defaults to commit timestamp")
    build.add_argument("--quarto", default="quarto", help="Quarto executable (default: quarto)")
    build.add_argument(
        "--mode",
        default="chapter",
        choices=("chapter", "section-pilot"),
        help="structural manuscript gate; section-pilot is for a partial pilot build (default: chapter)",
    )
    build.add_argument(
        "--preview",
        action="store_true",
        help="explicit non-release preview: allow a book.yaml toolkit pin that differs from the builder",
    )
    build.set_defaults(func=command_build)

    references = subparsers.add_parser(
        "validate-references",
        help="validate explicit labels, cross-references and local images across the reading order",
    )
    references.add_argument("path", nargs="?", help=f"default: {DEFAULT_BOOK}")
    references.set_defaults(func=command_references)

    version = subparsers.add_parser("version", help="print the toolkit version")
    version.set_defaults(func=command_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
