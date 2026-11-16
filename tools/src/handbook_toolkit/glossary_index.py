"""Opt-in glossary navigation and analytic Index, derived from MIT reference 13d295b.

No manuscript term is automatically linked. All mutations are private build staging.
"""

from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import posixpath
import re
from typing import TypedDict, Any
from .build_types import BuildError
from .books import _resolve_inside
from .validation import (
    load_document,
    load_packaged_schema,
    schema_issues,
    DocumentError,
)
from .xref_links import (
    HEADING,
    ATTRIBUTES,
    SEPARATOR,
    cells,
    _visible,
    _protected_spans,
    _overlaps,
    heading_id,
    Registry,
)
from .docx_fields import bookmark_name


class Term(TypedDict, total=False):
    term: str
    slug: str
    meaning: str
    defined: str
    aliases: list[str]
    glossary: bool
    see: str
    rationale: str


class Section(TypedDict):
    id: str
    display: str
    rel: str
    chapter: str


SECTION_NUMBER = r"(?:[0-9]{1,2}|[A-Z])(?:\.\d{1,2}){1,3}"
PROPER_NAMES = re.compile(
    r"Azure Event Grid|Event Grid|TOGAF Standard|Scaled Agile Framework|"
    r"NIST (?:AI Risk Management|Cybersecurity) Framework|"
    r"OWASP Application Security Verification Standard|"
    r"Web Security Testing Guide|"
    r"In Search of an Understandable Consensus Algorithm",
    re.I,
)


def glossary_slug(term: str) -> str:
    return re.sub("[^a-z0-9]+", "-", term.lower()).strip("-")


def section_display(title: str) -> str:
    title = re.sub(r"\s*\{[^}]*\}\s*$", "", title).strip()
    match = re.match(r"^((?:\d{1,2}|[A-J])(?:\.\d{1,2}){0,3})\.?\s", title)
    if match:
        return match.group(1)
    match = re.match(r"^Appendix ([A-J])\b", title)
    if match:
        return f"Appendix {match.group(1)}"
    return title


def _alias_flags(alias: str, ignore_case: bool) -> int:
    """Case rules for index matching.

    The Index counts prose uses regardless of case, so `latency` and `Latency`
    both point at the same entry. Short all-caps acronyms stay case-sensitive so
    a term such as `IT` cannot match the pronoun.
    """
    if " " not in alias and "-" not in alias and alias.isupper() and len(alias) <= 6:
        return 0
    return re.I if (ignore_case or " " in alias or "-" in alias) else 0


@lru_cache(maxsize=None)
def _alias_pattern(alias: str, flags: int) -> re.Pattern[str]:
    """Compiled boundary pattern, cached because the scan runs on every line."""
    return re.compile(rf"(?<![\w-]){re.escape(alias)}(?![\w-])", flags)


def glossary_matches(
    line: str, glossary: list[Term], ignore_case: bool = False
) -> list[tuple[int, int, Term]]:
    """Longest, non-overlapping term matches in one line."""
    found = []
    for entry in glossary:
        for alias in entry["aliases"]:
            pattern = _alias_pattern(alias, _alias_flags(alias, ignore_case))
            for match in pattern.finditer(line):
                found.append((match.start(), match.end(), entry))
    found.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    selected = []
    for start, end, entry in found:
        if any(
            start < other_end and other_start < end
            for other_start, other_end, _ in selected
        ):
            continue
        selected.append((start, end, entry))
    return sorted(selected, key=lambda item: item[0])


def _skip_glossary_line(line: str, next_line: str = "") -> bool:
    return (
        line.startswith(
            (
                "#",
                "![",
                ": ",
                ":::",
                "<",
                "| :",
                "```",
                "~~~",
                "**Architecture Review Checklist",
            )
        )
        or SEPARATOR.match(line)
        or SEPARATOR.match(next_line)
    )


def _proper_spans(line: str) -> list[tuple[int, int]]:
    return [match.span() for match in PROPER_NAMES.finditer(line)]


def index_terms(glossary: list[Term], vocabulary: dict) -> list[Term]:
    """The Index vocabulary: curated glossary entries plus index-only entries.

    A term removed from Appendix G must stay findable, so
    `publishing/index-vocabulary.yaml` carries index-only entries and aliases
    consolidated away from a retained entry. When a vocabulary term matches a
    glossary entry, its aliases are merged; otherwise it becomes an index-only
    entry with no glossary anchor.
    """
    entries = [dict(entry, glossary=True) for entry in glossary]
    by_key = {_index_term_key(entry["term"]): entry for entry in entries}
    by_slug = {entry["slug"]: entry for entry in entries}
    data = vocabulary
    for item in data.get("terms", []):
        term = str(item.get("term", "")).strip()
        if not term:
            continue
        aliases = [
            alias.strip() for alias in item.get("aliases") or [] if str(alias).strip()
        ]
        key = _index_term_key(term)
        slug = glossary_slug(term)
        if see := str(item.get("see") or "").strip():
            # A consolidated acronym gets its own visible "see" row, so the
            # printed Index keeps the alphabetical lookup the glossary had.
            target = by_key.get(_index_term_key(see)) or by_slug.get(glossary_slug(see))
            if target is None:
                raise BuildError(
                    f"index vocabulary: see target {see!r} is not an entry"
                )
            entry = dict(
                term=term,
                slug=slug,
                meaning="",
                defined="",
                aliases=[],
                glossary=False,
                see=target["term"],
                rationale=str(item.get("rationale") or "").strip(),
            )
            entries.append(entry)
            by_key[key] = entry
            by_slug[slug] = entry
            if term not in target["aliases"]:
                target["aliases"].append(term)
            continue
        entry = by_key.get(key) or by_slug.get(slug)
        if entry is None:
            entry = dict(
                term=term,
                slug=slug,
                meaning="",
                defined=str(item.get("defined") or "").strip(),
                aliases=[term],
                glossary=False,
                rationale=str(item.get("rationale") or "").strip(),
            )
            entries.append(entry)
            by_key[key] = entry
            by_slug[slug] = entry
        for alias in [term] + aliases:
            if alias and alias not in entry["aliases"]:
                entry["aliases"].append(alias)
    for entry in entries:
        entry["aliases"] = sorted(set(entry["aliases"]), key=str.casefold)
    return entries


def _sorted_glossary_text(text: str) -> str:
    """Order the glossary rows with the Index key, without changing any row."""
    lines = text.split("\n")
    header = next(
        (
            i
            for i, line in enumerate(lines)
            if line.startswith("|")
            and cells(line)
            and cells(line)[0].strip().lower() == "term"
        ),
        None,
    )
    if header is None:
        return text
    start = header + 2
    end = start
    while (
        end < len(lines)
        and lines[end].startswith("|")
        and not SEPARATOR.match(lines[end])
    ):
        end += 1
    rows = sorted(lines[start:end], key=lambda line: _index_term_key(cells(line)[0]))
    return "\n".join(lines[:start] + rows + lines[end:])


def annotate_glossary_entries(text: str, glossary: list[Term]) -> str:
    """Sort Appendix G rows, add the gl-<slug> anchor and insert letter rows."""
    text = _sorted_glossary_text(text)
    by_term = {entry["term"]: entry for entry in glossary}
    out, current_letter = [], None
    for line in text.split("\n"):
        if line.startswith("|") and not SEPARATOR.match(line):
            row = cells(line)
            if row and row[0].strip().lower() != "term" and "{#gl-" not in row[0]:
                entry = by_term.get(row[0].strip())
                if entry:
                    letter = (
                        entry["term"][0].upper() if entry["term"][0].isalpha() else "#"
                    )
                    if letter != current_letter:
                        out.append(f"| **{letter}** | | |")
                        current_letter = letter
                    row[0] = f'[{entry["term"]}]{{#gl-{entry["slug"]}}}'
                    out.append("| " + " | ".join(row) + " |")
                    continue
        out.append(line)
    return "\n".join(out)


def _defined_sections(entry: Term, known: dict[str, str]) -> list[str]:
    numbers = []
    for text in (entry["defined"], entry["meaning"]):
        for match in re.finditer(rf"(?<![\w.])({SECTION_NUMBER})(?![\w.])", text):
            number = match.group(1)
            if number in known and number not in numbers:
                numbers.append(number)
        if numbers:
            break
    return [known[number] for number in numbers]


def _index_term_key(term: str) -> str:
    """Alphabetical key that ignores spaces and hyphens, as book indexes do."""
    return re.sub(r"[\s\-–—/]+", "", term).casefold()


def analytic_index(
    terms: list[Term], appears: dict[str, list[str]], catalog: list[Section]
) -> str:
    """Markdown for the analytic Index page (last back-matter page).

    Every location is kept, grouped under its chapter or appendix in one compact
    cell per term. A two-column table gives each term an unbreakable row, so a
    page break cannot separate a continuation from the term it belongs to; the
    template keeps table cells unbreakable in Typst and the DOCX post-processor
    marks every row `cantSplit`.

    ``terms`` is the Index vocabulary (`index_terms`), which includes entries
    removed from the curated glossary. A term with a glossary entry links to its
    definition; an index-only term stays plain and still lists its locations.
    """
    by_id = {section["id"]: section for section in catalog}
    order = {section["id"]: index for index, section in enumerate(catalog)}
    known = {section["display"]: section["id"] for section in catalog}
    letters = {}
    for entry in terms:
        if see := entry.get("see"):
            parts = [f"see **{see}**"]
            terms_locations = "; ".join(parts)
        else:
            defined = _defined_sections(entry, known)
            used = [
                section
                for section in appears.get(entry["slug"], [])
                if section not in defined
            ]
            defined = [section for section in defined if section in by_id]
            used = [section for section in used if section in by_id]
            defined.sort(key=lambda section: order.get(section, 10**6))
            used.sort(key=lambda section: order.get(section, 10**6))
            parts = []
            if defined:
                links = ", ".join(
                    f'**[{by_id[section]["display"]}](#{section}){{.handbook-xref}}**'
                    for section in defined
                )
                parts.append(f"defined in {links}")
            groups = {}
            for section in used:
                label = _chapter_label(by_id[section])
                if label is None:
                    continue
                groups.setdefault(label, []).append(section)
            for label, sections in groups.items():
                links = ", ".join(
                    f'[{by_id[section]["display"]}](#{section}){{.handbook-xref}}'
                    for section in sections
                )
                parts.append(f"{label}: {links}")
            terms_locations = "; ".join(parts)
        if entry.get("glossary", True):
            term = f'**[{entry["term"]}](#gl-{entry["slug"]}){{.handbook-xref}}**'
        else:
            term = f'**{entry["term"]}**'
        letter = entry["term"][0].upper() if entry["term"][0].isalpha() else "#"
        letters.setdefault(letter, []).append(
            (_index_term_key(entry["term"]), term, terms_locations)
        )
    out = [
        "# Index {.unnumbered #analytic_index}",
        "",
        "Terms are listed with the section that defines them (bold) and the sections where "
        "they appear, grouped by chapter. Glossary terms link to their definition; every "
        "entry links to the sections where it is discussed.",
        "",
        "| [Term]{#handbook_analytic_index_rows} | Locations |",
        "| :----------------------------- | :---------------------------------------------------------------------- |",
    ]
    for letter in sorted(letters):
        out.append(f"| **{letter}** | |")
        for _, term, locations in sorted(letters[letter], key=lambda item: item[0]):
            out.append(f"| {term} | {locations} |")
    return "\n".join(out).rstrip() + "\n"


def _chapter_label(section: Section) -> str:
    cid = section["chapter"]
    return f"Ch. {cid}" if cid.isdigit() else f"App. {cid}"


def glossary_terms(text: str) -> list[Term]:
    """Read the declared Term/Meaning/Defined in table, never unrelated tables."""
    terms: list[Term] = []
    inside = False
    seen: set[str] = set()
    visible = _visible(text)
    for index, line in enumerate(text.splitlines()):
        if index not in visible:
            continue
        if not line.startswith("|"):
            inside = False
            continue
        row = cells(line)
        if row and row[0].casefold() == "term":
            inside = True
            continue
        if not inside or SEPARATOR.match(line):
            continue
        term = row[0].strip()
        slug = glossary_slug(term)
        if not slug or slug in seen:
            raise BuildError(f"empty or duplicate glossary slug: {term!r}")
        seen.add(slug)
        terms.append(
            Term(
                term=term,
                slug=slug,
                meaning=row[1] if len(row) > 1 else "",
                defined=row[2] if len(row) > 2 else "",
                aliases=[a.strip() for a in term.split(" / ") if len(a.strip()) >= 2],
            )
        )
    if not terms:
        raise BuildError("declared glossary has no Term table entries")
    return terms


def scan_sections(
    texts: dict[str, str],
    groups: dict[str, list[str]],
    glossary: str,
    registry: Registry,
    terms: list[Term],
) -> tuple[list[Section], dict[str, list[str]]]:
    """Match prose using the reference's longest-match and acronym rules."""
    catalog: list[Section] = []
    appears: dict[str, list[str]] = {entry["slug"]: [] for entry in terms}
    for group in ("chapters", "appendices"):
        for chapter, entry in enumerate(groups[group], 1):
            if entry == glossary:
                continue
            from .build_staging import _appendix_letter

            label = str(chapter) if group == "chapters" else _appendix_letter(chapter)
            lines = texts[entry].split("\n")
            visible = _visible(texts[entry])
            current = None
            bibliography = 0
            for i, line in enumerate(lines):
                if i not in visible:
                    continue
                if match := HEADING.match(line):
                    level, title = len(match[1]), match[2]
                    if bibliography and level <= bibliography:
                        bibliography = 0
                    if re.search(
                        r"\b(?:Further Reading|References|Bibliography)\b", title, re.I
                    ):
                        bibliography = level
                    if level <= 3:
                        symbolic = heading_id(level, title)
                        # Numbered anchors use the 0052 registry, including explicit IDs.
                        actual = registry.targets[0].get(symbolic)
                        if actual is None:
                            current = None
                        else:
                            current = actual
                            catalog.append(
                                Section(
                                    id=actual,
                                    display=section_display(title),
                                    rel=entry,
                                    chapter=label,
                                )
                            )
                    continue
                if (
                    current is None
                    or bibliography
                    or _skip_glossary_line(
                        line, lines[i + 1] if i + 1 < len(lines) else ""
                    )
                ):
                    continue
                protected = _protected_spans(line) + _proper_spans(line)
                for start, end, term in glossary_matches(line, terms, ignore_case=True):
                    if (
                        not _overlaps((start, end), protected)
                        and current not in appears[term["slug"]]
                    ):
                        appears[term["slug"]].append(current)
    return catalog, appears


def stage_glossary_index(
    workspace: Path,
    book: dict[str, Any],
    groups: dict[str, list[str]],
    registry: Registry,
    texts: dict[str, str],
) -> str:
    """Annotate glossary rows and write a last, unnumbered generated page."""

    root = workspace / book["manuscript"]["root"]
    glossary_path = _resolve_inside(root, book["manuscript"]["glossary"])
    if glossary_path is None:
        raise BuildError("glossary escapes manuscript root")
    glossary = next(
        (e for e in texts if (workspace / e).resolve() == glossary_path), None
    )
    if glossary is None:
        raise BuildError("glossary must be a canonical reading-order file")
    vocab: dict = {}
    if relative := book.get("publication", {}).get("index_vocabulary"):
        path = _resolve_inside(workspace, relative)
        if path is None:
            raise BuildError("index vocabulary escapes repository")
        try:
            vocab = load_document(path)
        except DocumentError as exc:
            raise BuildError(str(exc)) from exc
        issues = schema_issues(
            vocab, load_packaged_schema("index-vocabulary.schema.json"), relative
        )
        if issues:
            raise BuildError("invalid index vocabulary: " + "; ".join(map(str, issues)))
    for identity in ("analytic_index", "handbook_analytic_index_rows"):
        if identity in registry.pages:
            raise BuildError(f"reserved generated Index anchor: {identity}")
    glossary_entries = glossary_terms(texts[glossary])
    terms = index_terms(glossary_entries, vocab)
    slugs: set[str] = set()
    for term in terms:
        if term["slug"] in slugs:
            raise BuildError(f'duplicate index slug: {term["slug"]}')
        slugs.add(term["slug"])
    catalog, appears = scan_sections(texts, groups, glossary, registry, terms)
    known = {section["display"]: section["id"] for section in catalog}
    # Render from the anchored staged source so the appendix's existing IDs survive.
    annotated = annotate_glossary_entries(
        (workspace / glossary).read_text(), glossary_entries
    )
    rows = []
    by_term = {t["slug"]: t for t in glossary_entries}
    for line in annotated.split("\n"):
        if line.startswith("|") and (match := re.search(r"\{#gl-([^}]+)\}", line)):
            slug = match[1]
            if "gl-" + slug in registry.pages:
                raise BuildError(f"duplicate glossary anchor: gl-{slug}")
            registry.pages["gl-" + slug] = glossary
            term = by_term[slug]
            links = _defined_sections(term, known)
            row = cells(line)
            if links:
                displays = {s["id"]: s["display"] for s in catalog}
                while len(row) < 3:
                    row.append("")
                row[2] = ", ".join(
                    f"[{displays[s]}](#{s}){{.handbook-xref}}" for s in links
                )
                line = "| " + " | ".join(row) + " |"
        rows.append(line)
    (workspace / glossary).write_text("\n".join(rows))
    # Deliberate author links must also be whitelisted; do not silently emit broken links.
    for entry, text in texts.items():
        visible = _visible(text)
        for i, line in enumerate(text.split("\n")):
            if i in visible:
                code = [
                    (a, b) for a, b in _protected_spans(line) if line[a : a + 1] == "`"
                ]
                for match in re.finditer(r"\]\(#(gl-[A-Za-z0-9_-]+)\)", line):
                    if (
                        not _overlaps(match.span(), code)
                        and match[1] not in registry.pages
                    ):
                        raise BuildError(
                            f"unresolved glossary link {match[1]} in {entry}"
                        )
    name = "analytic-index.qmd"
    if (workspace / name).exists():
        raise BuildError(f"generated Index would replace source file: {name}")
    (workspace / name).write_text(analytic_index(terms, appears, catalog))
    return name


def rewrite_glossary_links(
    workspace: Path,
    entries: list[str],
    registry: Registry,
    source_alias: str | None = None,
) -> None:
    """Resolve deliberate author #gl links across HTML pages, outside code."""
    for entry in entries:
        path = workspace / entry
        text = path.read_text()
        visible = _visible(text)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if i not in visible:
                continue
            code = [(a, b) for a, b in _protected_spans(line) if line[a : a + 1] == "`"]

            def replace(match: re.Match[str]) -> str:
                if _overlaps(match.span(), code):
                    return match[0]
                page = registry.pages[match[1]]
                if source_alias and posixpath.normpath(page) == "index.qmd":
                    page = source_alias
                target = posixpath.relpath(page, posixpath.dirname(entry) or ".")
                return f"]({target}#{match[1]})"

            lines[i] = re.sub(r"\]\(#(gl-[A-Za-z0-9_-]+)\)", replace, line)
        path.write_text("\n".join(lines))


def word_glossary_sources(
    workspace: Path, entries: list[str], registry: Registry
) -> dict[Path, str]:
    """Encode long glossary IDs before Pandoc's 40-character bookmark truncation."""
    originals: dict[Path, str] = {}
    mapping = {
        identity: bookmark_name(identity)
        for identity in registry.pages
        if identity.startswith("gl-")
    }
    for entry in dict.fromkeys(["index.qmd", *entries]):
        path = workspace / entry
        text = path.read_text()
        # Generated span identifiers and fragment links are the only replacements.
        changed = re.sub(
            r"(?<=\{#)gl-[A-Za-z0-9_-]+|(?<=\]\(#)gl-[A-Za-z0-9_-]+",
            lambda m: mapping.get(m[0], m[0]),
            text,
        )
        if changed != text:
            originals[path] = text
            path.write_text(changed)
    return originals
