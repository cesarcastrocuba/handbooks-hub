"""The packaged semantic design tokens that every renderer must consume.

Colour, type, spacing and contrast rules live in ``design/tokens.json`` so the portal, the book
HTML, the Typst/PDF edition and the DOCX edition cannot drift into separate visual systems. The
module only reads and validates data: it renders nothing, so a caller can adopt the contract
without changing any output.
"""

from __future__ import annotations

from importlib.resources import files as resource_files
import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from .validation import Issue, load_packaged_schema

SCHEMES: tuple[str, ...] = ("light", "dark", "print")
"""Every surface family a colour role must serve."""

MINIMUM_TEXT_CONTRAST = 4.5
"""WCAG 2.2 AA floor for normal text; token pairs may not declare a lower bound."""

TOKENS_SCHEMA = "design-tokens.schema.json"


def load_tokens(path: Path | None = None) -> dict[str, Any]:
    """Load the packaged tokens, or an explicit file for tests and tooling."""

    if path is None:
        resource = resource_files("handbook_toolkit").joinpath("design", "tokens.json")
        try:
            text = resource.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"packaged design tokens are unreadable: {exc}") from exc
        label = "packaged design tokens"
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read design tokens {path}: {exc}") from exc
        label = str(path)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} are not a JSON object")
    return data


def validate_tokens(
    tokens: dict[str, Any], schema: dict[str, Any] | None = None
) -> list[Issue]:
    """Return deterministic issues for a token document; an empty list means valid.

    Validation covers shape, colour syntax, role references and the declared contrast floors. It
    does not inspect rendered output: phase 1 conformance tests compare generated resources with
    these values.
    """

    schema = schema if schema is not None else load_packaged_schema(TOKENS_SCHEMA)
    validator = Draft202012Validator(schema)
    issues = [
        Issue(_pointer(error.absolute_path), error.message)
        for error in sorted(
            validator.iter_errors(tokens),
            key=lambda error: (list(error.absolute_path), error.message),
        )
    ]
    if issues:
        return sorted(issues)
    issues.extend(_reference_issues(tokens))
    issues.extend(_contrast_issues(tokens))
    return sorted(issues)


def relative_luminance(value: str) -> float:
    """Return the WCAG relative luminance of a ``#RRGGBB`` colour."""

    digits = value.strip().lstrip("#")
    if len(digits) != 6:
        raise ValueError(f"expected a #RRGGBB colour, got {value!r}")
    try:
        channels = [int(digits[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    except ValueError as exc:
        raise ValueError(f"expected a #RRGGBB colour, got {value!r}") from exc
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    """Return the WCAG contrast ratio between two ``#RRGGBB`` colours."""

    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def _pointer(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _reference_issues(tokens: dict[str, Any]) -> list[Issue]:
    roles = set(tokens["color"])
    issues = []
    for index, pair in enumerate(tokens["contrast"]):
        for field in ("foreground", "background"):
            if pair[field] not in roles:
                issues.append(
                    Issue(
                        f"$.contrast[{index}].{field}",
                        f"unknown colour role: {pair[field]}",
                    )
                )
    return issues


def _contrast_issues(tokens: dict[str, Any]) -> list[Issue]:
    issues = []
    colours = tokens["color"]
    for index, pair in enumerate(tokens["contrast"]):
        minimum = pair["minimum"]
        if minimum < MINIMUM_TEXT_CONTRAST:
            issues.append(
                Issue(
                    f"$.contrast[{index}].minimum",
                    f"{minimum}:1 is below the {MINIMUM_TEXT_CONTRAST}:1 text floor",
                )
            )
        foreground = colours.get(pair["foreground"], {})
        background = colours.get(pair["background"], {})
        for scheme in pair["schemes"]:
            if scheme not in foreground or scheme not in background:
                continue
            ratio = contrast_ratio(foreground[scheme], background[scheme])
            if ratio + 1e-9 < minimum:
                issues.append(
                    Issue(
                        f"$.contrast[{index}].{scheme}",
                        f"{pair['name']} is {ratio:.2f}:1, below the required {minimum}:1",
                    )
                )
    return issues
