"""Editorial profile validation: schema plus structural invariants."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .validation import (
    CheckResult,
    DocumentError,
    Issue,
    load_document,
    schema_issues,
)


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return sorted(repeated)


def validate_profile(path: Path, schema: dict[str, Any]) -> CheckResult:
    """Validate an editorial profile against its schema and ordering rules."""

    label = str(path)
    try:
        data = load_document(path)
    except DocumentError as exc:
        return CheckResult(label, (Issue(label, str(exc)),))

    issues = schema_issues(data, schema, label)
    if issues:
        return CheckResult(label, tuple(issues))

    chapter_elements = data["chapter"]["required_elements"]
    section_elements = data["section"]["required_elements"]

    chapter_ids = [element["id"] for element in chapter_elements]
    section_ids = [element["id"] for element in section_elements]
    for value in _duplicates(chapter_ids):
        issues.append(Issue(f"{label}:chapter.required_elements", f"duplicate element id {value!r}"))
    for value in _duplicates(section_ids):
        issues.append(Issue(f"{label}:section.required_elements", f"duplicate element id {value!r}"))

    chapter_titles = [element["title"] for element in chapter_elements]
    for value in _duplicates(chapter_titles):
        issues.append(
            Issue(f"{label}:chapter.required_elements", f"duplicate element title {value!r}")
        )

    closing_order = data["section"]["closing_order"]
    closing_ids = [
        element["id"] for element in section_elements if element["placement"] == "section-closing"
    ]
    if set(closing_order) != set(closing_ids):
        missing = sorted(set(closing_ids) - set(closing_order))
        unknown = sorted(set(closing_order) - set(closing_ids))
        detail = []
        if missing:
            detail.append(f"missing closing elements {missing}")
        if unknown:
            detail.append(f"unknown closing elements {unknown}")
        issues.append(
            Issue(
                f"{label}:section.closing_order",
                "closing_order: " + ("; ".join(detail) or "does not match the section-closing elements"),
            )
        )

    unit = data["unit"]
    if unit["min_words"] > unit["max_words"]:
        issues.append(
            Issue(
                f"{label}:unit",
                f"min_words {unit['min_words']} exceeds max_words {unit['max_words']}",
            )
        )
    for text in unit["required_labels"]:
        if not text.endswith("."):
            issues.append(
                Issue(
                    f"{label}:unit.required_labels",
                    f"label {text!r} must end with a period because label_style is bold-period",
                )
            )
        if text != text.strip():
            issues.append(
                Issue(f"{label}:unit.required_labels", f"label {text!r} has leading or trailing space")
            )

    for name in ("figure", "table"):
        rule = data[name]
        if rule["required"] and rule["min_per_section"] < 1:
            issues.append(
                Issue(
                    f"{label}:{name}",
                    f"{name} is required but min_per_section is {rule['min_per_section']}",
                )
            )
        if not rule["required"] and rule["min_per_section"] > 0:
            issues.append(
                Issue(
                    f"{label}:{name}",
                    f"{name} is optional but min_per_section is {rule['min_per_section']}; "
                    "set it to 0 or mark the element required",
                )
            )

    if data["figure"]["upscale"]:
        issues.append(
            Issue(
                f"{label}:figure.upscale",
                "upscaling is incompatible with the readable proportional-figure rule",
            )
        )

    validation = data.get("validation")
    if data["version"] == "1.0.0" and validation is None:
        issues.append(Issue(f"{label}:validation", "profile 1.0.0 requires rule classifications"))
    if validation is not None:
        rules = validation["rules"]
        rule_ids = [rule["id"] for rule in rules]
        for value in _duplicates(rule_ids):
            issues.append(Issue(f"{label}:validation.rules", f"duplicate rule id {value!r}"))
        if not rules:
            issues.append(Issue(f"{label}:validation.rules", "at least one classified rule is required"))

    return CheckResult(label, tuple(issues))
