"""Deterministic structural validation for a pilot section or a chapter.

This module checks the shape declared by an editorial profile. It does not judge meaning, factual
accuracy, prose quality or visual usefulness. It never requires a diagram or table.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from .validation import CheckResult, Issue

HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
PARAGRAPH = re.compile(r"^\*\*(?P<label>[^*\n]+?)\*\*(?P<rest>.*)$")
CALLOUT_START = re.compile(r"^:::\s*\{(?P<attrs>[^}]*)\}\s*$")
CALLOUT_END = re.compile(r"^:::\s*$")
TITLE_ATTRIBUTE = re.compile(r"title\s*=\s*(?P<quote>[\"'])(?P<title>.*?)(?P=quote)")
CLASS_ATTRIBUTE = re.compile(r"\.callout-([A-Za-z0-9_-]+)")
FENCE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>`{3,}|~{3,})(?P<rest>.*)$")
NUMBER_PREFIX = re.compile(r"^(?:\d+|[A-Z])(?:\.\d+)*[ .]+")
TRAILING_ATTRIBUTES = re.compile(r"\s*\{[^}]*\}\s*$")
PLACEHOLDER_TITLES = {"section", "chapter", "untitled", "todo", "tbd", "example"}


@dataclass(frozen=True)
class Heading:
    line: int
    level: int
    title: str


@dataclass(frozen=True)
class Callout:
    line: int
    end_line: int
    title: str
    kind: str
    body: str


@dataclass(frozen=True)
class Paragraph:
    line: int
    label: str
    rest: str


@dataclass(frozen=True)
class Manuscript:
    headings: tuple[Heading, ...]
    callouts: tuple[Callout, ...]
    paragraphs: tuple[Paragraph, ...]
    plain_lines: tuple[tuple[int, str], ...]
    malformed: tuple[tuple[int, str], ...]
    line_count: int


def _slice(manuscript: Manuscript, start: int, end: int) -> Manuscript:
    """Return the elements whose start line is within [start, end)."""

    return Manuscript(
        tuple(heading for heading in manuscript.headings if start <= heading.line < end),
        tuple(callout for callout in manuscript.callouts if start <= callout.line < end),
        tuple(paragraph for paragraph in manuscript.paragraphs if start <= paragraph.line < end),
        tuple(item for item in manuscript.plain_lines if start <= item[0] < end),
        (),
        manuscript.line_count,
    )


def _clean_title(title: str) -> str:
    return TRAILING_ATTRIBUTES.sub("", title).strip()


def _base_title(title: str) -> str:
    return NUMBER_PREFIX.sub("", _clean_title(title)).strip()


def _meaningful_title(title: str) -> bool:
    base = _base_title(title)
    if len(re.findall(r"[A-Za-z]", base)) < 3:
        return False
    return base.strip(" .:-_").casefold() not in PLACEHOLDER_TITLES


def _matches_title(actual: str, expected: str) -> bool:
    actual_base = _base_title(actual).casefold()
    expected_base = _clean_title(expected).casefold()
    if actual_base == expected_base:
        return True
    return any(
        actual_base.startswith(expected_base + separator)
        for separator in (" —", " –", " -", ":")
    )


def _matches_label(actual: str, expected: str) -> bool:
    return actual.strip().casefold() == expected.strip().casefold()


def _label_base(label: str) -> str:
    return label.strip().rstrip(".").casefold()


def _inside_callout(line: int, callouts: tuple[Callout, ...]) -> bool:
    return any(callout.line < line < callout.end_line for callout in callouts)


def scan(text: str) -> Manuscript:
    """Parse headings, callouts and bold-label paragraphs outside fenced code."""

    headings: list[Heading] = []
    callouts: list[Callout] = []
    paragraphs: list[Paragraph] = []
    plain_lines: list[tuple[int, str]] = []
    malformed: list[tuple[int, str]] = []
    stack: list[tuple[int, str, str, list[str]]] = []
    in_fence = False
    fence_char = ""
    fence_length = 0
    lines = text.splitlines()

    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        fence = FENCE.match(line)
        if fence:
            marker = fence.group("marker")
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_length = len(marker)
                continue
            if (
                marker[0] == fence_char
                and len(marker) >= fence_length
                and not fence.group("rest").strip()
            ):
                in_fence = False
                fence_char = ""
                fence_length = 0
                continue
        if in_fence:
            continue

        callout = CALLOUT_START.match(stripped)
        if callout:
            attributes = callout.group("attrs")
            title = TITLE_ATTRIBUTE.search(attributes)
            kind = CLASS_ATTRIBUTE.search(attributes)
            stack.append(
                (
                    number,
                    _clean_title(title.group("title")) if title else "",
                    kind.group(1) if kind else "",
                    [],
                )
            )
            continue
        if CALLOUT_END.match(stripped):
            if not stack:
                malformed.append((number, "closing ::: without an open callout"))
                continue
            start, title, kind, body_lines = stack.pop()
            if kind:
                callouts.append(
                    Callout(start, number, title, kind, "\n".join(body_lines).strip())
                )
            else:
                malformed.append(
                    (start, f'callout "{title or "untitled"}" has no callout-* class')
                )
            continue

        if stack:
            stack[-1][3].append(line)

        heading = HEADING.match(line)
        if heading:
            headings.append(
                Heading(number, len(heading.group(1)), _clean_title(heading.group(2)))
            )
            continue

        paragraph = PARAGRAPH.match(stripped)
        if paragraph:
            paragraphs.append(
                Paragraph(number, paragraph.group("label").strip(), paragraph.group("rest").strip())
            )
            continue

        if stripped:
            plain_lines.append((number, stripped))

    for start, title, kind, body_lines in stack:
        malformed.append(
            (start, f'unclosed callout "{title or "untitled"}" starting at line {start}')
        )
    if in_fence:
        malformed.append((len(lines), "unclosed fenced code block"))

    return Manuscript(
        tuple(headings),
        tuple(callouts),
        tuple(paragraphs),
        tuple(plain_lines),
        tuple(malformed),
        len(lines),
    )


def _occurrence_issue(
    path: str,
    issues: list[Issue],
    element: str,
    expected: str,
    correct: list[int],
    wrong: list[tuple[int, str]],
) -> None:
    if not correct:
        if wrong:
            line, detail = wrong[0]
            issues.append(Issue(f"{path}:{line}", f"{element} must be {expected}; {detail}"))
        else:
            issues.append(Issue(path, f"missing {element}: expected {expected}"))
        return
    if len(correct) > 1:
        issues.append(
            Issue(
                f"{path}:{correct[0]}",
                f"duplicate {element}: expected exactly one {expected}; found lines "
                + ", ".join(str(line) for line in correct),
            )
        )
    if wrong:
        line, detail = wrong[0]
        issues.append(
            Issue(f"{path}:{line}", f"{element} has an additional wrong-form occurrence; {detail}")
        )


def _require_paragraph_body(
    path: str,
    manuscript: Manuscript,
    issues: list[Issue],
    lines: list[int],
    label: str,
) -> None:
    by_line = {paragraph.line: paragraph for paragraph in manuscript.paragraphs}
    for line in lines:
        if not by_line[line].rest.strip():
            issues.append(
                Issue(f"{path}:{line}", f'{label} must include non-empty body text')
            )


def _require_callout_body(
    path: str,
    manuscript: Manuscript,
    issues: list[Issue],
    lines: list[int],
    label: str,
) -> None:
    by_line = {callout.line: callout for callout in manuscript.callouts}
    for line in lines:
        if not by_line[line].body.strip():
            issues.append(
                Issue(f"{path}:{line}", f'{label} must include non-empty body text')
            )


def _wrong_forms(
    title: str, manuscript: Manuscript, expected: str
) -> list[tuple[int, str]]:
    """Return occurrences of the element title in a form other than *expected*."""

    wrong: list[tuple[int, str]] = []
    if expected == "heading":
        for callout in manuscript.callouts:
            if _matches_title(callout.title, title):
                wrong.append((callout.line, "found a callout instead of the required heading"))
        for paragraph in manuscript.paragraphs:
            if _matches_label(paragraph.label, title + "."):
                wrong.append((paragraph.line, "found a bold paragraph instead of a heading"))
        for line, text in manuscript.plain_lines:
            if text.casefold().startswith(_clean_title(title).casefold()):
                wrong.append((line, "found plain text instead of a heading"))
    else:
        for heading in manuscript.headings:
            if _matches_title(heading.title, title):
                wrong.append((heading.line, "found a heading instead of the required callout"))
        for paragraph in manuscript.paragraphs:
            if _matches_label(paragraph.label, title + "."):
                wrong.append(
                    (paragraph.line, "found a bold paragraph instead of the required callout")
                )
        for line, text in manuscript.plain_lines:
            if text.casefold().startswith(_clean_title(title).casefold()):
                wrong.append((line, "found plain text instead of the required callout"))
    return wrong


def _check_heading(
    path: str,
    heading: Heading | None,
    issues: list[Issue],
    *,
    allowed_levels: tuple[int, ...],
    label: str,
) -> None:
    if heading is None:
        issues.append(Issue(path, f"missing {label} heading with a real title"))
        return
    if heading.level not in allowed_levels:
        expected = " or ".join(f"H{level}" for level in allowed_levels)
        issues.append(
            Issue(
                f"{path}:{heading.line}",
                f"{label} must start with a {expected} heading",
            )
        )
    elif not _meaningful_title(heading.title):
        issues.append(
            Issue(
                f"{path}:{heading.line}",
                f"{label} heading must contain a meaningful title, not only a number or placeholder",
            )
        )


def _check_labels(
    path: str,
    manuscript: Manuscript,
    profile: dict[str, Any],
    issues: list[Issue],
) -> None:
    labels = profile["unit"]["required_labels"]
    label_positions: list[int] = []
    for label in labels:
        correct = [
            paragraph.line
            for paragraph in manuscript.paragraphs
            if _matches_label(paragraph.label, label)
            and not _inside_callout(paragraph.line, manuscript.callouts)
        ]
        wrong: list[tuple[int, str]] = []
        for heading in manuscript.headings:
            if _label_base(heading.title) == _label_base(label):
                wrong.append((heading.line, "found a heading instead of a bold paragraph"))
        for callout in manuscript.callouts:
            if _label_base(callout.title) == _label_base(label):
                wrong.append((callout.line, "found a callout instead of a bold paragraph"))
        for paragraph in manuscript.paragraphs:
            if _matches_label(paragraph.label, label) and _inside_callout(
                paragraph.line, manuscript.callouts
            ):
                wrong.append((paragraph.line, "found the label inside a callout, not a paragraph"))
        for line, text in manuscript.plain_lines:
            if text.casefold().startswith(label.casefold()):
                wrong.append((line, "found plain text instead of a bold paragraph"))
        _occurrence_issue(
            path,
            issues,
            f'required label "{label}"',
            f'a bold paragraph starting with "**{label}**"',
            correct,
            wrong,
        )
        _require_paragraph_body(path, manuscript, issues, correct, f'required label "{label}"')
        if len(correct) == 1:
            label_positions.append(correct[0])

    if label_positions != sorted(label_positions):
        issues.append(
            Issue(
                path,
                "required labels are misordered; expected " + ", ".join(labels),
            )
        )


def _check_closing(
    path: str,
    manuscript: Manuscript,
    profile: dict[str, Any],
    issues: list[Issue],
) -> None:
    section_elements = {
        element["id"]: element for element in profile["section"]["required_elements"]
    }
    closing_positions: list[int] = []
    for element_id in profile["section"]["closing_order"]:
        element = section_elements[element_id]
        title = element["title"]
        kind = element["kind"]
        if kind == "paragraph":
            label = title + "."
            correct = [
                paragraph.line
                for paragraph in manuscript.paragraphs
                if _matches_label(paragraph.label, label)
                and not _inside_callout(paragraph.line, manuscript.callouts)
            ]
            wrong = [
                (callout.line, "found a callout instead of a bold paragraph")
                for callout in manuscript.callouts
                if _matches_title(callout.title, title)
            ]
            wrong.extend(
                (heading.line, "found a heading instead of a bold paragraph")
                for heading in manuscript.headings
                if _matches_title(heading.title, title)
            )
            wrong.extend(
                (paragraph.line, "found the label inside a callout, not a paragraph")
                for paragraph in manuscript.paragraphs
                if _matches_label(paragraph.label, label)
                and _inside_callout(paragraph.line, manuscript.callouts)
            )
            _occurrence_issue(
                path,
                issues,
                f'closing element "{title}"',
                f'a bold paragraph starting with "**{label}**"',
                correct,
                wrong,
            )
            _require_paragraph_body(
                path, manuscript, issues, correct, f'closing element "{title}"'
            )
        elif kind in {"callout", "checklist-callout"}:
            correct = [
                callout.line
                for callout in manuscript.callouts
                if _matches_title(callout.title, title)
            ]
            wrong = [
                (heading.line, "found a heading instead of the required callout")
                for heading in manuscript.headings
                if _matches_title(heading.title, title)
            ]
            wrong.extend(
                (paragraph.line, "found a bold paragraph instead of the required callout")
                for paragraph in manuscript.paragraphs
                if _matches_title(paragraph.label.rstrip("."), title)
            )
            _occurrence_issue(
                path,
                issues,
                f'closing element "{title}"',
                f'a callout titled "{title}"',
                correct,
                wrong,
            )
            _require_callout_body(
                path, manuscript, issues, correct, f'closing element "{title}"'
            )
        else:
            issues.append(
                Issue(path, f'unsupported section element kind "{kind}" for "{title}"')
            )
            continue
        if len(correct) == 1:
            closing_positions.append(correct[0])

    if closing_positions != sorted(closing_positions):
        issues.append(
            Issue(
                path,
                "section closing elements are misordered; expected "
                + ", ".join(
                    section_elements[element_id]["title"]
                    for element_id in profile["section"]["closing_order"]
                ),
            )
        )


def _check_section(
    path: str,
    manuscript: Manuscript,
    profile: dict[str, Any],
    issues: list[Issue],
) -> None:
    _check_heading(
        path,
        manuscript.headings[0] if manuscript.headings else None,
        issues,
        allowed_levels=(2, 3),
        label="section pilot",
    )
    _check_labels(path, manuscript, profile, issues)
    _check_closing(path, manuscript, profile, issues)


def _check_chapter(
    path: str,
    manuscript: Manuscript,
    profile: dict[str, Any],
    issues: list[Issue],
) -> None:
    h1 = next((heading for heading in manuscript.headings if heading.level == 1), None)
    if h1 is None:
        issues.append(Issue(path, "missing chapter heading: expected an H1 with a real title"))
    elif not _meaningful_title(h1.title):
        issues.append(
            Issue(
                f"{path}:{h1.line}",
                "chapter heading must contain a meaningful title, not only a number or placeholder",
            )
        )

    h2 = [heading for heading in manuscript.headings if heading.level == 2]
    if not h2:
        issues.append(Issue(path, "missing numbered sections: expected at least one H2"))
        return
    first_section = h2[0].line

    elements = {element["id"]: element for element in profile["chapter"]["required_elements"]}
    callout_positions: list[tuple[str, int]] = []
    worked_heading: Heading | None = None

    for element_id in ("when-to-use", "key-takeaway"):
        if element_id not in elements:
            continue
        element = elements[element_id]
        title = element["title"]
        correct = [
            callout.line
            for callout in manuscript.callouts
            if _matches_title(callout.title, title)
        ]
        wrong = _wrong_forms(title, manuscript, "callout")
        _occurrence_issue(path, issues, f'chapter element "{title}"', f'a callout titled "{title}"', correct, wrong)
        _require_callout_body(path, manuscript, issues, correct, f'chapter element "{title}"')
        if len(correct) == 1:
            callout_positions.append((element_id, correct[0]))
            if correct[0] > first_section:
                issues.append(
                    Issue(
                        f"{path}:{correct[0]}",
                        f'"{title}" must appear before the first numbered section (line {first_section})',
                    )
                )

    ordered = [position for _, position in callout_positions]
    if ordered != sorted(ordered):
        issues.append(
            Issue(path, "when-to-use and key-takeaway callouts are misordered in the chapter")
        )

    if "worked-example" in elements:
        element = elements["worked-example"]
        title = element["title"]
        correct = [heading for heading in h2 if _matches_title(heading.title, title)]
        wrong = _wrong_forms(title, manuscript, "heading")
        _occurrence_issue(
            path,
            issues,
            f'chapter element "{title}"',
            f'an H2 section titled "{title}"',
            [heading.line for heading in correct],
            wrong,
        )
        if len(correct) == 1:
            worked_heading = correct[0]
            content_sections = [
                heading for heading in h2 if not _matches_title(heading.title, "Further Reading")
            ]
            if content_sections and content_sections[-1].line != worked_heading.line:
                issues.append(
                    Issue(
                        f"{path}:{worked_heading.line}",
                        "worked-example section must be the last section before Further Reading",
                    )
                )

    if "review-checklist" in elements:
        element = elements["review-checklist"]
        title = element["title"]
        correct = [
            callout.line
            for callout in manuscript.callouts
            if _matches_title(callout.title, title)
        ]
        wrong = _wrong_forms(title, manuscript, "callout")
        _occurrence_issue(
            path,
            issues,
            f'chapter element "{title}"',
            f'a callout titled "{title}"',
            correct,
            wrong,
        )
        _require_callout_body(path, manuscript, issues, correct, f'chapter element "{title}"')
        if len(correct) == 1:
            line = correct[0]
            if worked_heading is None:
                issues.append(
                    Issue(
                        f"{path}:{line}",
                        f'"{title}" must be inside the worked-example section, but that section is missing',
                    )
                )
            else:
                next_h2 = min(
                    (heading.line for heading in h2 if heading.line > worked_heading.line),
                    default=None,
                )
                inside = (
                    line > worked_heading.line
                    if next_h2 is None
                    else worked_heading.line < line < next_h2
                )
                if not inside:
                    if next_h2 is None:
                        issues.append(
                            Issue(
                                f"{path}:{line}",
                                f'"{title}" must be inside the worked-example section starting at line {worked_heading.line}',
                            )
                        )
                    else:
                        issues.append(
                            Issue(
                                f"{path}:{line}",
                                f'"{title}" must be inside the worked-example section (lines '
                                f"{worked_heading.line + 1}–{next_h2 - 1})",
                            )
                        )

    if "further-reading" in elements:
        element = elements["further-reading"]
        title = element["title"]
        correct = [heading for heading in h2 if _matches_title(heading.title, title)]
        wrong = _wrong_forms(title, manuscript, "heading")
        _occurrence_issue(
            path,
            issues,
            f'chapter element "{title}"',
            f'a final H2 section titled "{title}"',
            [heading.line for heading in correct],
            wrong,
        )
        if len(correct) == 1 and correct[0].line != h2[-1].line:
            issues.append(
                Issue(
                    f"{path}:{correct[0].line}",
                    f'"{title}" must be the last numbered section (H2)',
                )
            )

    # Apply the section/unit rules to every ordinary content section. Worked Example and
    # Further Reading are special sections with their own chapter-level rules above.
    worked_title = elements.get("worked-example", {}).get("title", "")
    further_title = elements.get("further-reading", {}).get("title", "")
    content_sections = [
        heading
        for heading in h2
        if not (worked_title and _matches_title(heading.title, worked_title))
        and not (further_title and _matches_title(heading.title, further_title))
    ]
    for index, section in enumerate(content_sections):
        next_h2 = next(
            (heading.line for heading in h2 if heading.line > section.line),
            manuscript.line_count + 1,
        )
        section_slice = _slice(manuscript, section.line, next_h2)
        units = [heading for heading in section_slice.headings if heading.level == 3]
        if units:
            _check_heading(
                path,
                section,
                issues,
                allowed_levels=(2,),
                label="content section",
            )
            if profile["section"].get("forbid_single_unit", False) and len(units) == 1:
                issues.append(
                    Issue(
                        f"{path}:{section.line}",
                        f'content section "{section.title}" has a single subsection; add a second unit or merge it',
                    )
                )
            for unit_index, unit in enumerate(units):
                unit_end = (
                    units[unit_index + 1].line
                    if unit_index + 1 < len(units)
                    else next_h2
                )
                unit_slice = _slice(manuscript, unit.line, unit_end)
                _check_heading(
                    path,
                    unit,
                    issues,
                    allowed_levels=(3,),
                    label="unit",
                )
                _check_labels(path, unit_slice, profile, issues)
            _check_closing(path, section_slice, profile, issues)
        else:
            _check_section(path, section_slice, profile, issues)


def validate_manuscript(
    path: Path, profile: dict[str, Any], mode: str
) -> CheckResult:
    """Validate a manuscript file against the profile's structural rules."""

    label = str(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult(label, (Issue(label, f"cannot read manuscript: {exc}"),))

    if not text.strip():
        return CheckResult(label, (Issue(label, "manuscript file is empty"),))

    manuscript = scan(text)
    issues: list[Issue] = [
        Issue(f"{path}:{line}", f"malformed manuscript: {message}")
        for line, message in manuscript.malformed
    ]
    if mode == "section-pilot":
        _check_section(label, manuscript, profile, issues)
    elif mode == "chapter":
        _check_chapter(label, manuscript, profile, issues)
    else:
        issues.append(Issue(label, f'unsupported mode "{mode}"'))

    return CheckResult(label, tuple(issues))
