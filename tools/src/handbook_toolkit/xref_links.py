"""Opt-in, whitelist-only prose navigation in the private render workspace.

Cue rules derive from the author's MIT reference builder at frozen 13d295b;
see change 0052 for provenance. This module never auto-links glossary terms.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import posixpath
import re

from .build_types import BuildError
from .build_staging import (
    _appendix_letter,
    _count_figures,
    _count_tables,
    _is_unnumbered,
)
from .references import FENCE
from .docx_fields import bookmark_name

Targets = tuple[dict[str, str], dict[str, str], dict[str, str]]
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ATTRIBUTES = re.compile(r"\s*\{([^{}]*)\}\s*$")
IDENTIFIER = re.compile(r"(?:^|\s)#([A-Za-z][A-Za-z0-9:_-]*)(?=\s|$)")
GENERATED = re.compile(r"\[[^\]\n]*\]\(#[A-Za-z][A-Za-z0-9:_-]*\)")
GENERATED_LINK = re.compile(
    r"(\[[^\]\n]*\]\()#([A-Za-z][A-Za-z0-9:_-]*)(\)\{\.handbook-xref\})"
)
VISIBLE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}")

# Section references the staging can link. The token mirrors scripts/check_crossrefs.py.
VERSION_WORDS = {
    "tls",
    "ssl",
    "https",
    "http",
    "oauth",
    "saml",
    "oidc",
    "openid",
    "wcag",
    "iso",
    "iec",
    "iso/iec",
    "ieee",
    "nist",
    "rfc",
    "sp",
    "cvss",
    "cwe",
    "owasp",
    "asvs",
    "archimate",
    "togaf",
    "itil",
    "cobit",
    "version",
    "release",
    "python",
    "java",
    ".net",
    "angular",
    "react",
    "kubernetes",
    "postgresql",
    "mysql",
    "terraform",
    "ansible",
    "docker",
    "helm",
    "openapi",
    "json",
    "amqp",
    "mqtt",
    "kafka",
    "grpc",
    "fido2",
    "webauthn",
    "pkce",
    "totp",
    "hotp",
    "scim",
    "ldap",
    "kerberos",
    "ws-federation",
    "openssl",
    "nginx",
    "apache",
    "ubuntu",
    "debian",
    "rhel",
    "centos",
    "windows",
    "macos",
    "ios",
    "android",
    "node",
    "nodejs",
    "typescript",
    "javascript",
    "csharp",
    "dotnet",
    "go",
    "rust",
    "table",
    "figure",
    "chapter",
    "chapters",
    "appendix",
    "section",
}
UNIT_WORDS = {
    "%",
    "ms",
    "s",
    "sec",
    "secs",
    "second",
    "seconds",
    "minute",
    "minutes",
    "hour",
    "hours",
    "day",
    "days",
    "week",
    "weeks",
    "month",
    "months",
    "year",
    "years",
    "x",
    "ratio",
    "rc",
    "release",
    "specification",
    "international",
    "edition",
    "standard",
    "standards",
    "ghz",
    "mhz",
    "khz",
    "hz",
    "kb",
    "mb",
    "gb",
    "tb",
    "pb",
    "kbps",
    "mbps",
    "gbps",
    "tbps",
    "rps",
    "qps",
    "requests",
    "users",
    "records",
    "rows",
    "items",
    "bytes",
    "times",
    "fold",
    "nines",
    "percent",
    "percentile",
    "points",
}
REFERENCE_HEADERS = {
    "start with",
    "see",
    "where covered",
    "chapter",
    "chapters",
    "section",
    "sections",
    "defined in",
    "table",
    "tables",
    "figure",
    "figures",
    "appendix",
    "appendices",
}
BARE_CHAPTER_HEADERS = {
    "start with",
    "see",
    "where covered",
    "chapter",
    "chapters",
    "defined in",
}
# Words that introduce a standard's own numbering, not a handbook section. A
# bare number after one of these is a clause, not a cross-reference.
CONTEXT_WORDS = {
    "requirement",
    "clause",
    "control",
    "criterion",
    "annex",
    "article",
    "paragraph",
    "step",
    "phase",
    "stage",
    "item",
    "level",
}
MAGNITUDE_WORDS = {
    "million",
    "billion",
    "thousand",
    "trillion",
    "percentage",
    "percent",
    "fold",
}
# Handbook structure words are in VERSION_WORDS so that the number right after
# them is never read as a bare section reference ("Table 4.2" is linked as a
# table). They do not start a version list: in "Table 8.3 gives …, Section 8.1.2"
# the later number is still a location.
STRUCTURE_WORDS = {"table", "figure", "chapter", "chapters", "appendix", "section"}
VERSION_LIST = re.compile(
    r"\b("
    + "|".join(re.escape(w) for w in sorted(VERSION_WORDS - STRUCTURE_WORDS))
    + r")\s+\d+(?:\.\d+)+\b[^.;|()\[\]]*$",
    re.I,
)
SECTION_NUMBER = r"\d{1,2}(?:\.\d{1,2}){1,3}"
APPENDIX_NUMBER = r"[A-Z](?:\.\d{1,2}){1,2}"
REF_NUMBER = r"(?:[0-9A-Z]{1,2}|BM|0)\.\d{1,2}(?!\w|\.\d)"
REF_LIST = (
    rf"{REF_NUMBER}(?:\s*[–-]\s*{REF_NUMBER})?" rf"(?:\s*(?:,|and)\s*{REF_NUMBER})*"
)
REFERENCE = re.compile(
    rf"""(?P<figure>\bFigures?\s+(?P<figure_nums>{REF_LIST}))
      | (?P<fig_short>\bFig\.?\s+(?P<fig_short_nums>{REF_LIST}))
      | (?P<table>\bTables?\s+(?P<table_nums>{REF_LIST}))
      | (?P<appendix>\bAppendix\s+(?P<appendix_num>[A-Z](?:\.\d{{1,2}})?)(?!\w|\.\d))
      | (?P<appendices>\bAppendices\s+(?P<appendices_nums>[A-Z](?:\.\d{{1,2}})?(?!\w|\.\d)(?:\s*[–-]\s*[A-Z](?:\.\d{{1,2}})?(?!\w|\.\d))?(?:\s*(?:,\s*|and\s+)[A-Z](?:\.\d{{1,2}})?(?!\w|\.\d))*))
      | (?P<chapter>\bChapters?\s+(?P<chapter_nums>\d{{1,2}}(?!\w|\.\d)(?:\s*[–-]\s*\d{{1,2}})?(?:\s*(?:,|and)\s*\d{{1,2}}(?!\w|\.\d))*))
      | (?P<section_cue>\bSection\s+(?P<section_cue_num>{SECTION_NUMBER})(?!\w|\.\d))
      | (?P<appendix_section>(?<![\w.])(?P<appendix_section_num>{APPENDIX_NUMBER})(?!\w|\.\d))
      | (?P<section>(?<![\w.])(?P<section_num>{SECTION_NUMBER})(?!\w|\.\d))
    """,
    re.X,
)
BARE_NUMBER = re.compile(r"(?<![\w.])(\d{1,2})(?![\w.])")


def _section_target(number: str) -> str:
    # Appendix sections use lowercase letters in heading ids (sec_b_1); numeric
    # sections are unaffected by the lowercasing.
    return "sec_" + number.replace(".", "_").lower()


def _appendix_target(number: str) -> str:
    if "." in number:
        letter, section = number.split(".", 1)
        return f"sec_{letter.lower()}_{section.replace('.', '_')}"
    return f"sec_app_{number.lower()}"


MD_LINK_LABEL = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def _plain_before(text: str, start: int, width: int = 80) -> str:
    """Text before a match with Markdown links reduced to their labels (glossary links, earlier references)."""
    return MD_LINK_LABEL.sub(r"\1", text[max(0, start - width) : start])


def _words_around(text: str, start: int, end: int) -> tuple[str, str]:
    # A glossary link may leave its label wrapped in punctuation ("Guidelines
    # ([WCAG](#gl-wcag)) 2.2"), so ignore trailing closing brackets when looking
    # for the preceding word.
    previous = re.search(
        r'([A-Za-z][A-Za-z/.-]*)[)\]*"”]*\s*$',
        _plain_before(text, start, 32 + 64)[-40:],
    )
    following = re.match(r"\s*([A-Za-z%][A-Za-z/.-]*)", text[end : end + 24])
    return (
        (previous.group(1).rstrip(".-/").lower() if previous else ""),
        (following.group(1).rstrip(".-/").lower() if following else ""),
    )


# A number is navigational only when the surrounding text says so. These verbs
# and prepositions introduce a handbook location ("covered in 6.2", "defined in
# 3.4", "maps to 8.2.1"); they are intentionally not a list of every word that
# can precede a number, because a number after "rate of" or "about" is a value.
REFERENCE_CUES = {
    "see",
    "section",
    "sections",
    "§",
    "in",
    "by",
    "to",
    "from",
    "under",
    "of",
    "covered",
    "defined",
    "described",
    "documented",
    "explained",
    "discussed",
    "detailed",
    "listed",
    "owned",
    "introduced",
    "clarified",
    "mapped",
    "check",
    "extends",
    "extend",
    "extended",
    "using",
    "use",
}
# Value shapes that look like a section number but never are: "a rate of 14.4",
# "a total of 7.4 out of 10", "about 13.4". The noun check runs before the cue
# check so "rate of" cannot be rescued by the preposition.
VALUE_PHRASE = re.compile(
    r"\b(?:rate|total|score|value|gain|cost|growth|increase|decrease|average|"
    r"median|index|share|ratio|percentage|percent|amount|number|latency|"
    r"throughput|duration|size|capacity|budget|count|time|availability|"
    r"utilisation|utilization)\s+of\s*$",
    re.I,
)
VALUE_ADVERB = re.compile(
    r"\b(?:about|approximately|roughly|around|nearly|circa)\s*$", re.I
)
CHAPTER_LIST = re.compile(r"\bChapters?\s+\d{1,2}\s*[,;]\s*$", re.I)
APPENDIX_LIST = re.compile(
    r"\b(?:Appendix|Appendices)\s+[A-Z](?:\.\d{1,2})?\s*(?:[,;]|and)\s*$", re.I
)
PREVIOUS_REF = re.compile(
    r"([0-9A-Z]{1,2}(?:\.\d{1,2}){1,3})\s*(?:[–—-]|,|;|and|or)\s*$", re.I
)
SENTENCE_VERB = re.compile(
    r"\s*(?:provides?|covers?|defines?|describes?|explains?|documents?|lists?|shows?|"
    r"contains?|records?|owns?)\b",
    re.I,
)
GROUP_REFERENCE = re.compile(
    rf"(?:{SECTION_NUMBER}|{APPENDIX_NUMBER})"
    r"|\b(?:Chapters?|Sections?|Appendices|Appendix|Tables?|Figures?|Fig\.?|see|and|or|§)\b",
    re.I,
)


def _value_context(text: str, start: int, end: int) -> bool:
    """True when the number reads as a measurement, score or version value."""
    before = _plain_before(text, start, 48)
    if re.search(r"\bfrom\s+\d+(?:\.\d+)+\s+to\s*$", before, re.I):
        return True
    if VALUE_PHRASE.search(before) or VALUE_ADVERB.search(before):
        return True
    if re.match(r"\s*out of\b", text[end : end + 20], re.I):
        return True
    # "from 1.5 to 2.5" is a range of values, not two section references.
    if re.search(r"\bfrom\s*$", before, re.I) and re.match(
        r"\s*to\b", text[end : end + 10], re.I
    ):
        return True
    return False


def _reference_group(text: str, start: int) -> bool:
    """True when a parenthesis makes the number's navigational intent clear.

    The group may be only references ("(6.1.2, 6.3)") or name a subject and
    then the section that owns it ("(ATAM, 15.3.1)", "(OWASP ASVS usage
    (9.5.2))"). A number after a comma, semicolon or "and" inside parentheses is
    read as a location, which is how the manuscript cites a section next to a
    method name.
    """
    depth, opener = 0, None
    limit = max(0, start - 400)
    for index in range(start - 1, limit - 1, -1):
        char = text[index]
        if char in ")]":
            depth += 1
        elif char in "([":
            if depth == 0:
                opener = index
                break
            depth -= 1
        elif char == "\n":
            break
    if opener is None:
        return False
    group = VISIBLE_LINK.sub(r"\1", text[opener + 1 : start])
    residue = GROUP_REFERENCE.sub("", group)
    residue = re.sub(r"[\s,;:–—-]+", "", residue)
    if not residue:
        return True
    return bool(re.search(r"(?:,|;|\band)\s*$", group, re.I))


def _reference_context(text: str, start: int, end: int, depth: int = 0) -> bool:
    """Whether the text immediately around a bare number says it is a location."""
    before = _plain_before(text, start, 48)
    if re.search(r"(?:^|[\s(\[])(?:see|sections?|§)\s*$", before, re.I):
        return True
    previous, _ = _words_around(text, start, end)
    if previous in REFERENCE_CUES:
        return True
    # "which is the input that 11.4 assumes": a relative clause whose verb is a
    # handbook action still navigates.
    if re.search(r"\bthat\s*$", before, re.I) and re.match(
        r"\s*(?:assumes|defines|covers|provides|describes|requires|owns|governs|"
        r"addresses|records)\b",
        text[end : end + 30],
        re.I,
    ):
        return True
    if _reference_group(text, start):
        return True
    if CHAPTER_LIST.search(before):
        return True
    if APPENDIX_LIST.search(before):
        return True
    # A sentence or clause that opens with a location and a handbook verb
    # ("4.9; 9.7.3 provide evidence") is navigation, not a value.
    if re.search(r"(?:^|[.;:]\s*)$", before) and (
        SENTENCE_VERB.match(text[end : end + 30])
        or re.match(r"\s*[,;]\s*\[?\d", text[end : end + 12])
    ):
        return True
    # "5.2.3 and 5.3": a list continues a reference that is itself valid.
    if depth < 4 and (match := PREVIOUS_REF.search(before)):
        previous_start = start - len(before) + match.start(1)
        if _reference_context(
            text, previous_start, previous_start + len(match.group(1)), depth + 1
        ):
            return True
    return False


def _section_ok(
    number: str,
    text: str,
    start: int,
    end: int,
    sections: dict[str, str],
    bibliography: bool = False,
    reference: bool = False,
) -> bool:
    anchor = _section_target(number)
    if anchor not in sections:
        return False
    if bibliography:
        return False
    if _value_context(text, start, end):
        return False
    previous, following = _words_around(text, start, end)
    if previous in VERSION_WORDS or previous in CONTEXT_WORDS:
        return False
    # A version list such as "TLS 1.2 minimum, 1.3 preferred": the later numbers are versions too.
    # A handbook location ("Section 8.4 introduces …, Section 2.12 sets …") starts no version list.
    earlier = _plain_before(text, start, 320)
    if VERSION_LIST.search(earlier):
        return False
    if (
        following in UNIT_WORDS
        or following in MAGNITUDE_WORDS
        or following.startswith("%")
    ):
        return False
    if re.match(
        r"\s*(?:RC|rc|Release|release|International|Specification|Edition)\b",
        text[end : end + 30],
    ):
        return False
    if reference:
        # A declared reference column (Defined in, See, Where covered) is
        # navigation by construction, even when the cell is only "3.4".
        return True
    return _reference_context(text, start, end)


def _relink_list(
    text: str,
    number_pattern: re.Pattern[str],
    anchor_for: Callable[[str], str],
    valid: dict[str, str],
) -> str:
    """Link every number in a range or list, leaving the surrounding word alone."""

    def replace(match: re.Match[str]) -> str:
        anchor = anchor_for(match.group(0))
        return (
            f"[{match.group(0)}](#{valid[anchor]})"
            if anchor in valid
            else match.group(0)
        )

    return number_pattern.sub(replace, text)


def _chapter_replacement(match: re.Match[str], sections: dict[str, str]) -> str:
    word = "Chapters" if match.group("chapter").startswith("Chapters") else "Chapter"
    numbers = re.findall(r"\d{1,2}", match.group("chapter_nums"))
    if word == "Chapter" and len(numbers) == 1:
        anchor = f"sec_ch_{int(numbers[0])}"
        return (
            f"[Chapter {numbers[0]}](#{sections[anchor]})"
            if anchor in sections
            else match.group(0)
        )

    def number(value: re.Match[str]) -> str:
        anchor = f"sec_ch_{int(value.group(0))}"
        return (
            f"[{value.group(0)}](#{sections[anchor]})"
            if anchor in sections
            else value.group(0)
        )

    return word + " " + re.sub(r"\d{1,2}", number, match.group("chapter_nums"))


def _replace(
    match: re.Match[str],
    line: str,
    targets: Targets,
    reference_cell: bool = False,
    bibliography: bool = False,
) -> str:
    sections, figures, tables = targets
    for kind in (
        "figure",
        "fig_short",
        "table",
        "appendix",
        "appendices",
        "chapter",
        "section_cue",
        "appendix_section",
        "section",
    ):
        if not match.group(kind):
            continue
        if kind in ("figure", "fig_short"):
            numbers = match.group(
                "figure_nums" if kind == "figure" else "fig_short_nums"
            )
            found = re.findall(REF_NUMBER, numbers)
            if (
                kind == "figure"
                and match.group("figure").startswith("Figure ")
                and len(found) == 1
            ):
                anchor = "fig-" + found[0].lower().replace(".", "-")
                return (
                    f"[Figure {found[0]}](#{figures[anchor]})"
                    if anchor in figures
                    else match.group(0)
                )
            return _relink_list(
                match.group(kind),
                re.compile(REF_NUMBER),
                lambda n: "fig-" + n.lower().replace(".", "-"),
                figures,
            )
        if kind == "table":
            found = re.findall(REF_NUMBER, match.group("table_nums"))
            if match.group("table").startswith("Table ") and len(found) == 1:
                anchor = "tbl-" + found[0].lower().replace(".", "-")
                return (
                    f"[Table {found[0]}](#{tables[anchor]})"
                    if anchor in tables
                    else match.group(0)
                )
            return _relink_list(
                match.group("table"),
                re.compile(REF_NUMBER),
                lambda n: "tbl-" + n.lower().replace(".", "-"),
                tables,
            )
        if kind == "appendix":
            number = match.group("appendix_num")
            anchor = _appendix_target(number)
            return (
                f"[Appendix {number}](#{sections[anchor]})"
                if anchor in sections
                else match.group(0)
            )
        if kind == "appendices":

            def appendix(value: re.Match[str]) -> str:
                anchor = _appendix_target(value.group(0))
                return (
                    f"[{value.group(0)}](#{sections[anchor]})"
                    if anchor in sections
                    else value.group(0)
                )

            return "Appendices " + re.sub(
                r"[A-Z](?:\.\d{1,2})?", appendix, match.group("appendices_nums")
            )
        if kind == "chapter":
            return _chapter_replacement(match, sections)
        if kind == "section_cue":
            number = match.group("section_cue_num")
            # "Section 9.5" is an explicit handbook cue even in a bibliography.
            if _section_ok(
                number, line, match.start(), match.end(), sections, reference=True
            ):
                return f"[Section {number}](#{sections[_section_target(number)]})"
            return match.group(0)
        if kind == "appendix_section":
            number = match.group("appendix_section_num")
            anchor = _section_target(number)
            if anchor in sections and _section_ok(
                number,
                line,
                match.start(),
                match.end(),
                sections,
                bibliography,
                reference_cell,
            ):
                return f"[{number}](#{sections[anchor]})"
            return match.group(0)
        number = match.group("section_num")
        if _section_ok(
            number,
            line,
            match.start(),
            match.end(),
            sections,
            bibliography,
            reference_cell,
        ):
            return f"[{number}](#{sections[_section_target(number)]})"
        return match.group(0)
    return match.group(0)


def _overlaps(span: tuple[int, int], protected: list[tuple[int, int]]) -> bool:
    return any(start < span[1] and span[0] < end for start, end in protected)


def _transform(
    line: str,
    targets: Targets,
    reference_cell: bool = False,
    bibliography: bool = False,
) -> str:
    protected = _protected_spans(line)
    matches = [
        match
        for match in REFERENCE.finditer(line)
        if not _overlaps(match.span(), protected)
    ]
    for match in reversed(matches):
        replacement = _replace(match, line, targets, reference_cell, bibliography)
        replacement = GENERATED.sub(r"\g<0>{.handbook-xref}", replacement)
        line = line[: match.start()] + replacement + line[match.end() :]
    return line


def _bare_numbers(line: str, sections: dict[str, str], chapters: bool) -> str:
    protected = _protected_spans(line)
    matches = [
        match
        for match in BARE_NUMBER.finditer(line)
        if not _overlaps(match.span(), protected)
    ]
    for match in reversed(matches):
        anchor = (
            f"sec_ch_{int(match.group(0))}"
            if chapters
            else _section_target(match.group(0))
        )
        previous, following = _words_around(line, match.start(), match.end())
        value = (
            _value_context(line, match.start(), match.end())
            or previous in VERSION_WORDS
            or previous in CONTEXT_WORDS
            or following in UNIT_WORDS
            or following in MAGNITUDE_WORDS
            or line[match.end() :].lstrip().startswith(("%", "°"))
        )
        if anchor in sections and not value:
            line = (
                line[: match.start()]
                + f"[{match.group(0)}](#{sections[anchor]}){{.handbook-xref}}"
                + line[match.end() :]
            )
    return line


REFERENCE_HEADER_CUE = re.compile(
    r"\b(?:see|defined in|where covered|where used|covered|chapter|chapters|section|sections|"
    r"appendix|appendices|table|tables|figure|figures|reference|references)\b",
    re.I,
)


def _reference_header(header: str) -> bool:
    """True for a column that is navigation by declaration.

    Exact legacy names keep working; a header such as "Evidence and see" is
    also a reference column because it says so in words. "Version", "Date" and
    measurement columns never match.
    """
    name = header.strip().lower()
    return name in REFERENCE_HEADERS or bool(REFERENCE_HEADER_CUE.search(name))


def _table_cell(cell: str, header: str, targets: Targets) -> str:
    reference = _reference_header(header)
    if header == "table":
        match = re.fullmatch(r"\s*([0-9A-Z]+\.\d+)\s*", cell)
        anchor = "tbl-" + match.group(1).lower().replace(".", "-") if match else ""
        if match and anchor in targets[2]:
            return f"[{match.group(1)}](#{targets[2][anchor]}){{.handbook-xref}}"
        return cell
    text = _transform(cell, targets, reference_cell=reference)
    if header in BARE_CHAPTER_HEADERS:
        text = _bare_numbers(text, targets[0], chapters=True)
    return text


def _table_ref_columns(header: str) -> dict[int, str]:
    return {
        index: name.strip().lower()
        for index, name in enumerate(cells(header))
        if _reference_header(name)
    }


def _protected_spans(line: str) -> list[tuple[int, int]]:
    """Exact backtick runs and balanced inline/reference links, including images."""
    spans = [
        match.span()
        for match in re.finditer(r"<(code|pre)\b[^>]*>.*?</\1\s*>", line, re.I | re.S)
    ]
    index = 0
    while index < len(line):
        if line[index] == "\\":
            index += 2
            continue
        if line[index] == "`":
            opener = re.match(r"`+", line[index:])
            assert opener is not None
            token = opener.group()
            closer = re.search(
                r"(?<!`)" + re.escape(token) + r"(?!`)", line[index + len(token) :]
            )
            end = index + len(token) + closer.end() if closer else len(line)
            spans.append((index, end))
            index = end
            continue
        if line[index] == "[":
            start = index
            depth = 1
            index += 1
            while index < len(line) and depth:
                if line[index] == "\\":
                    index += 2
                    continue
                if line[index] == "[":
                    depth += 1
                elif line[index] == "]":
                    depth -= 1
                index += 1
            label_end = index
            if depth:
                spans.append((start, len(line)))
            if not depth and index < len(line) and line[index] in "([":
                opening = line[index]
                closing = ")" if opening == "(" else "]"
                depth = 1
                index += 1
                while index < len(line) and depth:
                    if line[index] == "\\":
                        index += 2
                        continue
                    if line[index] == opening:
                        depth += 1
                    elif line[index] == closing:
                        depth -= 1
                    index += 1
                spans.append((start, index))
            elif not depth:
                # Shortcut reference labels are never candidates for automatic links.
                spans.append((start, label_end))
            continue
        if line[index] == "<":
            end = line.find(">", index)
            if end >= 0:
                spans.append((index, end + 1))
                index = end + 1
                continue
        index += 1
    return spans


def cells(line: str) -> list[str]:
    """Split pipe cells without treating escaped/code/link pipes as delimiters."""
    protected = _protected_spans(line)
    separators = [
        m.start()
        for m in re.finditer(r"(?<!\\)\|", line)
        if not _overlaps(m.span(), protected)
    ]
    boundaries = [-1, *separators, len(line)]
    result = [line[a + 1 : b].strip() for a, b in zip(boundaries, boundaries[1:])]
    if line.lstrip().startswith("|"):
        result.pop(0)
    if line.rstrip().endswith("|"):
        result.pop()
    return result


def _visible(text: str) -> set[int]:
    """Line positions outside YAML, exact Markdown fences, comments and indented code."""
    result: set[int] = set()
    fence = ""
    comment = False
    front = text.startswith("---\n")
    lines = text.split("\n")
    offsets: list[int] = []
    position = 0
    for line in lines:
        offsets.append(position)
        position += len(line) + 1
    inline = _protected_spans(text)
    for index, line in enumerate(lines):
        if front:
            if index and line.strip() in ("---", "..."):
                front = False
            continue
        marker = FENCE.match(line)
        if marker:
            token = marker.group(1)
            if not fence:
                fence = token
            elif (
                token[0] == fence[0]
                and len(token) >= len(fence)
                and not line[marker.end() :].strip()
            ):
                fence = ""
            continue
        if fence:
            continue
        if any(start < offsets[index] < end for start, end in inline):
            continue
        if comment:
            if "-->" in line:
                comment = False
            continue
        if "<!--" in line:
            comment = "-->" not in line.split("<!--", 1)[1]
            continue
        if line.startswith(("    ", "\t")):
            continue
        result.add(index)
    return result


def heading_id(level: int, title: str) -> str:
    """Number-based names are independent of heading prose and writer format."""
    title = ATTRIBUTES.sub("", title).strip()
    if level == 1:
        if match := re.match(r"^(\d+)[.]?\s", title):
            return f"sec_ch_{int(match[1])}"
        if match := re.match(r"^Appendix ([A-Z])\b", title):
            return f"sec_app_{match[1].lower()}"
    if match := re.match(r"^([0-9A-Z]+(?:\.\d+)+)\s", title):
        return "sec_" + match[1].lower().replace(".", "_")
    return "sec_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def _with_id(line: str, identity: str) -> str:
    if match := ATTRIBUTES.search(line):
        if IDENTIFIER.search(match[1]):
            return line
        return line[: match.start()] + " {" + match[1] + " #" + identity + "}"
    return line + " {#" + identity + "}"


@dataclass
class Registry:
    targets: Targets
    pages: dict[str, str]


def stage_cross_references(
    workspace: Path, entries: list[str], *, groups: dict[str, list[str]] | None = None, link_prose: bool = True
) -> Registry:
    """Build the whitelist first, then link prose across the entire reading order."""
    targets: Targets = ({}, {}, {})
    pages: dict[str, str] = {}
    texts: dict[str, str] = {}

    def register(kind: int, symbolic: str, actual: str, entry: str) -> None:
        if actual in pages:
            raise BuildError(
                f"duplicate navigation anchor {actual!r} in {entry} and {pages[actual]}"
            )
        if symbolic in targets[kind]:
            raise BuildError(f"ambiguous navigation reference {symbolic!r}")
        targets[kind][symbolic] = actual
        pages[actual] = entry

    appendix_set = set((groups or {}).get("appendices", []))
    chapter_number = appendix_number = 0
    shared: dict[str, tuple[int, int]] = {"0": (0, 0), "bm": (0, 0)}
    for entry in entries:
        text = (workspace / entry).read_text(encoding="utf-8")
        # Mirror 0051's native assignments using its scanners. Do not infer a
        # float number from file position or a manually prefixed caption.
        if entry in appendix_set:
            appendix_number += 1
            float_prefix = _appendix_letter(appendix_number).lower()
        elif _is_unnumbered(text):
            float_prefix = "bm" if chapter_number or appendix_number else "0"
        else:
            chapter_number += 1
            float_prefix = str(chapter_number)
        table_start, figure_start = shared.get(float_prefix, (0, 0))
        if float_prefix in shared:
            shared[float_prefix] = (
                table_start + _count_tables(text),
                figure_start + _count_figures(text),
            )
        lines = text.split("\n")
        visible = _visible(text)
        heading_seen: dict[str, int] = {}
        figure_number = table_number = 0
        previous = ""
        for index, line in enumerate(lines):
            if index not in visible:
                continue
            attributes = ATTRIBUTES.search(line)
            explicit = IDENTIFIER.search(attributes[1]) if attributes else None
            if match := HEADING.match(line):
                level, title = len(match[1]), match[2]
                symbolic = heading_id(level, title)
                # Unnumbered repeated subheadings get file-scoped deterministic IDs.
                if level > 1 and not re.match(r"^[0-9A-Z]+(?:\.\d+)+\s", title):
                    stem = re.sub(r"[^a-z0-9]+", "-", entry.lower()).strip("-")
                    symbolic += "-" + stem
                    heading_seen[symbolic] = heading_seen.get(symbolic, 0) + 1
                    if heading_seen[symbolic] > 1:
                        symbolic += "-" + str(heading_seen[symbolic])
                actual = explicit[1] if explicit else bookmark_name(symbolic)
                register(0, symbolic, actual, entry)
                lines[index] = _with_id(line, actual)
            elif line.lstrip().startswith("!["):
                figure_number += 1
                display = f"{float_prefix}-{figure_start + figure_number}"
                if display:
                    symbolic = "fig-" + display
                    actual = explicit[1] if explicit else symbolic
                    register(1, symbolic, actual, entry)
                    lines[index] = _with_id(line, actual)
            elif re.match(r"^(?::|Table:)\s+\S", line) and previous.lstrip().startswith(
                "|"
            ):
                table_number += 1
                display = f"{float_prefix}-{table_start + table_number}"
                if display:
                    symbolic = "tbl-" + display
                    actual = explicit[1] if explicit else symbolic
                    register(2, symbolic, actual, entry)
                    staged = _with_id(line, actual)
                    attrs = ATTRIBUTES.search(staged)
                    assert attrs is not None
                    rest = re.sub(
                        r"(?<!\S)#" + re.escape(actual) + r"(?=\s|$)", "", attrs[1]
                    ).strip()
                    lines[index] = (
                        staged[: attrs.start()]
                        + " {#"
                        + actual
                        + (" " + rest if rest else "")
                        + "}"
                    )
            if line.strip():
                previous = line
        texts[entry] = "\n".join(lines)
    registry = Registry(targets, pages)
    for entry, text in texts.items():
        (workspace / entry).write_text(link_references(text, targets) if link_prose else text, encoding="utf-8")
    return registry


def link_references(text: str, targets: Targets) -> str:
    """Link only known navigational tokens; never touch headings/code/bibliography."""
    lines = text.split("\n")
    visible = _visible(text)
    bibliography_level = 0
    columns: dict[int, str] = {}
    output: list[str] = []
    for index, line in enumerate(lines):
        if index not in visible:
            output.append(line)
            continue
        if heading := HEADING.match(line):
            level = len(heading[1])
            title = ATTRIBUTES.sub("", heading[2]).strip()
            if bibliography_level and level <= bibliography_level:
                bibliography_level = 0
            if re.search(
                r"\b(?:Further Reading|References|Bibliography)\b", title, re.I
            ):
                bibliography_level = level
            output.append(line)
            columns = {}
            continue
        if (
            bibliography_level
            or line.lstrip().startswith(("![", ": ", "Table:", ":::", "<"))
            or re.match(r"^\s*\[[^]]+\]:", line)
        ):
            output.append(line)
            continue
        if index + 1 < len(lines) and re.fullmatch(
            r"\s*(?:=+|-+)\s*", lines[index + 1]
        ):
            output.append(line)
            continue
        if line.lstrip().startswith("|"):
            if SEPARATOR.match(line):
                output.append(line)
                continue
            if index + 1 < len(lines) and SEPARATOR.match(lines[index + 1]):
                columns = _table_ref_columns(line)
                output.append(line)
                continue
            if columns:
                row = cells(line)
                for column, header in columns.items():
                    if column < len(row):
                        row[column] = _table_cell(row[column], header, targets)
                line = "| " + " | ".join(row) + " |"
            output.append(_transform(line, targets))
            continue
        columns = {}
        output.append(_transform(line, targets))
    return "\n".join(output)


def rewrite_html_links(
    workspace: Path,
    entries: list[str],
    registry: Registry,
    source_alias: str | None = None,
) -> None:
    """Rebase generated links after the print render; Quarto resolves .qmd to .html."""
    pages = {
        identity: (
            source_alias
            if posixpath.normpath(page) == "index.qmd" and source_alias
            else page
        )
        for identity, page in registry.pages.items()
    }
    for entry in entries:

        def replace(match: re.Match[str]) -> str:
            identity = match[2]
            page = pages[identity]
            target = (
                ""
                if page == entry
                else posixpath.relpath(page, posixpath.dirname(entry) or ".")
            )
            return match[1] + target + "#" + identity + match[3]

        path = workspace / entry
        path.write_text(
            GENERATED_LINK.sub(replace, path.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
