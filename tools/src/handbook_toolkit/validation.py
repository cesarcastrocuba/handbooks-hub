"""Shared loading and schema-validation helpers for the handbook toolkit.

The toolkit is deliberately deterministic: documents are read once, schema errors are sorted by
path and message, and no validation depends on the current time or network access.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files as resource_files
import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
import yaml


@dataclass(frozen=True, order=True)
class Issue:
    """One deterministic validation finding."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


@dataclass(frozen=True)
class CheckResult:
    """The outcome of one named check."""

    label: str
    issues: tuple[Issue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


class DocumentError(ValueError):
    """Raised when a document cannot be read or parsed."""


def load_document(path: Path) -> Any:
    """Load a JSON or YAML document, raising :class:`DocumentError` on failure."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DocumentError(f"cannot read {path}: {exc}") from exc

    try:
        if path.suffix == ".json":
            data = json.loads(text)
        elif path.suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        else:
            raise DocumentError(f"unsupported document extension: {path.suffix or '<none>'}")
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise DocumentError(f"cannot parse {path}: {exc}") from exc

    if data is None:
        raise DocumentError(f"empty document: {path}")
    return data


def load_schema(path: Path) -> dict[str, Any]:
    """Load a JSON Schema document from a filesystem path."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DocumentError(f"cannot read schema {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DocumentError(f"cannot parse schema {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise DocumentError(f"schema is not a JSON object: {path}")
    return data


def load_packaged_schema(name: str) -> dict[str, Any]:
    """Load a schema bundled inside the installed toolkit package.

    This is the default. It makes a pinned toolkit self-contained: a book needs neither a hub
    checkout nor a vendored ``schemas/`` directory. ``importlib.resources`` also works when the
    package is imported from a zip archive.
    """

    resource = resource_files("handbook_toolkit").joinpath("schemas", name)
    try:
        text = resource.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DocumentError(f"packaged schema not found or unreadable: {name}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DocumentError(f"cannot parse packaged schema {name}: {exc}") from exc
    if not isinstance(data, dict):
        raise DocumentError(f"packaged schema is not a JSON object: {name}")
    return data


def load_schema_source(name: str, override: Path | None = None) -> dict[str, Any]:
    """Load a schema from an explicit directory or, by default, from the installed package."""

    if override is not None:
        return load_schema(override / name)
    return load_packaged_schema(name)


def _pointer(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        if isinstance(part, int):
            rendered += f"[{part}]"
        else:
            rendered += f".{part}"
    return rendered


def schema_issues(data: Any, schema: dict[str, Any], location: str) -> list[Issue]:
    """Validate *data* against *schema* and return sorted, deterministic issues."""

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    return [
        Issue(f"{location}:{_pointer(error.absolute_path)}", error.message)
        for error in errors
    ]


def resolve_document(root: Path, value: str | Path | None, default: str) -> Path:
    """Resolve a CLI path argument relative to *root*."""

    candidate = Path(value) if value is not None else Path(default)
    return candidate if candidate.is_absolute() else root / candidate
