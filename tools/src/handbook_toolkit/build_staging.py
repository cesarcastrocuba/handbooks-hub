"""Build staging."""

from __future__ import annotations
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Any
import zipfile
import yaml
from . import design
from .manuscript import validate_manuscript
from .references import FENCE, IMAGE

from .build_types import BuildError

def _reading_groups(book: dict[str, Any], repo: Path) -> dict[str, list[str]]:
    manuscript = book["manuscript"]
    root = repo / manuscript["root"]
    path = repo / manuscript["reading_order"]
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BuildError(f"cannot read reading order {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise BuildError("reading order must be a YAML mapping")
    groups: dict[str, list[str]] = {}
    for group in ("front", "chapters", "back", "appendices", "references"):
        values = document.get(group, []) or []
        if not isinstance(values, list):
            raise BuildError(f"reading order group {group} must be a list")
        checked: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value.endswith(".qmd"):
                raise BuildError(f"reading order entry is not a .qmd path: {value!r}")
            candidate = (root / value).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError as exc:
                raise BuildError(f"reading order entry escapes manuscript root: {value}") from exc
            if not candidate.is_file():
                raise BuildError(f"reading order entry does not exist: {value}")
            checked.append(f"{manuscript['root']}/{value}")
        groups[group] = checked
    if not groups["chapters"]:
        raise BuildError("reading order contains no chapters")
    return groups

def _validate_manuscripts(
    workspace: Path,
    book: dict[str, Any],
    profile: dict[str, Any],
    mode: str,
) -> None:
    groups = _reading_groups(book, workspace)
    chapters = groups["chapters"]
    appendices = groups["appendices"]
    if mode == "section-pilot":
        if len(chapters) != 1 or appendices:
            raise BuildError(
                "section-pilot mode requires exactly one chapter and no appendices in the reading order"
            )
        targets = chapters
    else:
        # Front matter, back matter and references are separate special groups.
        targets = [*chapters, *appendices]
    is_v11 = profile.get("version", "1.0.0") not in ("1.0.0", "0.2.0")
    for entry in targets:
        path = workspace / entry
        target_mode = mode
        if is_v11 and entry in appendices and mode == "chapter":
            target_mode = "appendix"
        result = validate_manuscript(path, profile, target_mode)
        if not result.ok:
            raise BuildError(
                f"manuscript validation failed for {entry}: "
                + "; ".join(map(str, result.issues))
            )

def _strip_heading_number(title: str) -> str:
    stripped = re.sub(
        r"^Appendix\s+[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*\s*(?:[—–:]|-)\s*",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    if stripped != title:
        return stripped
    stripped = re.sub(r"^[A-Za-z]\.\d+(?:\.\d+)*[ .]+", "", title).strip()
    if stripped != title:
        return stripped
    return re.sub(r"^\d+(?:\.\d+)*[ .]+", "", title).strip()


def _appendix_letter(index: int) -> str:
    """Return 'A', 'B', ... 'Z', 'AA', etc. for 1-based index."""
    result = ""
    while index > 0:
        index -= 1
        result = chr(ord("A") + (index % 26)) + result
        index //= 26
    return result


def _is_unnumbered(text: str) -> bool:
    match = re.search(r"^#{1,3}\s+.*$", text, re.MULTILINE)
    if not match:
        return False
    return bool(re.search(r"\{[^}]*\.unnumbered[^}]*\}", match.group(0)))


def _count_tables(text: str) -> int:
    count = 0
    prev = ""
    for line in text.splitlines():
        if re.match(r"^(?::|Table:)\s+(.*\S)\s*$", line) and prev.lstrip().startswith("|"):
            count += 1
        if line.strip():
            prev = line
    return count


def _count_figures(text: str) -> int:
    return len([m for m in re.finditer(r"!\[[^\]]*\]\([^)]*\)\{[^}]*#fig-[A-Za-z0-9_-]+[^}]*\}", text)])


FIGURE_PREFIX = re.compile(
    r"^Figure\s+(?P<label>[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)\s*(?:[—–:]|-)\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
TABLE_PREFIX = re.compile(
    r"^Table\s+(?P<label>[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)\s*(?:[—–:]|-)\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
IMAGE_WITH_ATTRS = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]*)\)(?P<attrs>\{[^}]*\})?"
)


def _transform_chapter(
    text: str,
    chapter_label: str | int | None = None,
    *,
    tbl_prefix: str | None = None,
    table_start: int = 0,
    figure_start: int = 0,
    strip_heading_numbers: bool = True,
    path: str = "",
) -> str:
    """Stage a chapter wrapper, explicit table captions and normalized figure captions without changing source."""

    if isinstance(chapter_label, int):
        ch_str: str | None = str(chapter_label)
        actual_tbl_prefix = tbl_prefix if tbl_prefix is not None else ch_str
    elif isinstance(chapter_label, str):
        ch_str = chapter_label
        actual_tbl_prefix = tbl_prefix if tbl_prefix is not None else chapter_label.lower()
    else:
        ch_str = None
        actual_tbl_prefix = tbl_prefix if tbl_prefix is not None else "0"

    front: dict[str, Any] = {}
    body = text
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if match:
        try:
            loaded = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise BuildError(f"cannot parse staged chapter front matter: {exc}") from exc
        if isinstance(loaded, dict):
            front = loaded
        body = match.group(2)
    front.pop("title", None)

    lines = body.splitlines()
    first = next(
        (index for index, line in enumerate(lines) if re.match(r"^#{1,3}\s+", line)),
        None,
    )
    if first is None:
        raise BuildError("staged chapter has no heading to use as the rendered chapter title")
    heading = lines[first]
    title = re.sub(r"^#{1,3}\s+", "", heading)
    if strip_heading_numbers:
        title = _strip_heading_number(title)
    if len(re.findall(r"[A-Za-z]", title)) < 3:
        raise BuildError("staged chapter heading is not meaningful")
    remaining = lines[:first] + lines[first + 1 :]

    output: list[str] = [f"# {title}", ""]
    if front:
        output = ["---", *yaml.safe_dump(front, sort_keys=False).splitlines(), "---", "", *output]
    table_number = 0
    figure_number = 0
    previous = ""
    in_fence = False
    fence_char = ""
    fence_length = 0

    for line in remaining:
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_length = len(marker)
            elif (
                marker[0] == fence_char
                and len(marker) >= fence_length
            ):
                in_fence = False
                fence_char = ""
                fence_length = 0
            output.append(line)
            previous = line if line.strip() else previous
            continue

        if in_fence:
            output.append(line)
            previous = line if line.strip() else previous
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match and strip_heading_numbers:
            line = f"{heading_match.group(1)} {_strip_heading_number(heading_match.group(2))}"

        # Figure prefix stripping and mismatch validation
        if "![" in line and "#fig-" in line:
            def replace_figure(m: re.Match[str]) -> str:
                nonlocal figure_number
                alt = m.group("alt")
                src = m.group("src")
                attrs = m.group("attrs") or ""
                if re.search(r"#fig-[A-Za-z0-9_-]+", attrs):
                    figure_number += 1
                    assigned_fig = figure_start + figure_number
                    expected = f"{ch_str}.{figure_number}" if ch_str else f"0.{assigned_fig}"
                    pm = FIGURE_PREFIX.match(alt.strip())
                    if pm:
                        label = pm.group("label")
                        if ch_str is not None:
                            if label.casefold() != expected.casefold():
                                raise BuildError(
                                    f"figure caption label {label!r} does not match expected number {expected!r}"
                                    + (f" in {path}" if path else "")
                                )
                        else:
                            if label.casefold() != expected.casefold() and label.casefold() != str(figure_number).casefold():
                                raise BuildError(
                                    f"figure caption label {label!r} does not match expected number {expected!r}"
                                    + (f" in {path}" if path else "")
                                )
                        new_alt = pm.group("rest").strip()
                        return f"![{new_alt}]({src}){attrs}"
                return m.group(0)

            line = IMAGE_WITH_ATTRS.sub(replace_figure, line)

        # Table prefix stripping, mismatch validation and auto label assignment
        caption = re.match(r"^(?::|Table:)\s+(.*\S)\s*$", line)
        if caption and previous.lstrip().startswith("|"):
            table_number += 1
            caption_text = caption.group(1).strip()
            explicit_label = re.search(r"\{#tbl-([^}]+)\}\s*$", caption_text)
            clean_caption = re.sub(r"\s*\{[^}]*\}\s*$", "", caption_text).strip()

            assigned_num = table_start + table_number
            expected_tbl = f"{ch_str}.{table_number}" if ch_str else f"0.{assigned_num}"
            tpm = TABLE_PREFIX.match(clean_caption)
            if tpm:
                tbl_label = tpm.group("label")
                if ch_str is not None:
                    if tbl_label.casefold() != expected_tbl.casefold():
                        raise BuildError(
                            f"table caption label {tbl_label!r} does not match expected number {expected_tbl!r}"
                            + (f" in {path}" if path else "")
                        )
                else:
                    if tbl_label.casefold() != expected_tbl.casefold() and tbl_label.casefold() != str(table_number).casefold():
                        raise BuildError(
                            f"table caption label {tbl_label!r} does not match expected number {expected_tbl!r}"
                            + (f" in {path}" if path else "")
                        )
                clean_caption = tpm.group("rest").strip()

            if explicit_label:
                line = f": {clean_caption} {{#tbl-{explicit_label.group(1)}}}"
            else:
                line = f": {clean_caption} {{#tbl-{actual_tbl_prefix}-{assigned_num}}}"
            output.extend(["", line, ""])
            previous = ""
            continue

        output.append(line)
        if line.strip():
            previous = line
    return "\n".join(output).rstrip() + "\n"

def _is_local_path(target: str) -> bool:
    return not (target.startswith(("/", "#")) or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target))


def _rebase_image(match: re.Match[str], directory: PurePosixPath) -> str:
    target = match.group(1)
    bare = target[1:-1] if target.startswith("<") else target
    if not _is_local_path(bare):
        return match.group(0)
    rebased = posixpath.normpath((directory / bare).as_posix())
    start, end = match.span(1)
    replacement = f"<{rebased}>" if target.startswith("<") else rebased
    return match.string[match.start():start] + replacement + match.string[end:match.end()]


def _rebase_images(text: str, directory: PurePosixPath) -> str:
    """Point the relative images of a page at *directory*, the place the page was written in.

    The first page is staged at the project root as ``index.qmd``; its images still live next to
    its source. Fenced code and inline code are left alone.
    """

    if directory == PurePosixPath("."):
        return text
    lines: list[str] = []
    fence = ""
    for line in text.split("\n"):
        marker = FENCE.match(line)
        if marker and not fence:
            fence = marker.group(1)
        elif marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
            fence = ""
        elif not fence:
            spans = line.split("`")
            spans[::2] = [IMAGE.sub(lambda match: _rebase_image(match, directory), span) for span in spans[::2]]
            line = "`".join(spans)
        lines.append(line)
    return "\n".join(lines)


class RenderedEntries(list[str]):
    appendix_start: int | None = None


yaml.SafeDumper.add_representer(RenderedEntries, yaml.SafeDumper.represent_list)


def _prepare_render(
    workspace: Path,
    entries: list[str],
    *,
    appendices: list[str] | None = None,
) -> list[str]:
    """Create root index and transformed chapter files for Quarto.

    Every reading-order file is transformed in place in the private staging workspace. The first
    one is also staged as ``index.qmd`` so Quarto has a home page without a separate generated
    chapter; that copy has its images rebased, because it no longer sits in its source directory.
    Canonical source in the commit is untouched.
    """

    if not entries:
        raise BuildError("no manuscript entries to render")

    appendix_set = set(appendices or ())
    chapter_counter = 0
    appendix_counter = 0
    front_table_counter = 0
    front_figure_counter = 0
    first_appendix_start = None

    def get_assignment(entry: str, text: str) -> tuple[str | None, str, int, int]:
        nonlocal chapter_counter, appendix_counter, front_table_counter, front_figure_counter, first_appendix_start
        if entry in appendix_set:
            if first_appendix_start is None:
                first_appendix_start = chapter_counter + 1
            appendix_counter += 1
            letter = _appendix_letter(appendix_counter)
            return letter, letter.lower(), 0, 0
        if _is_unnumbered(text):
            t_start = front_table_counter
            front_table_counter += _count_tables(text)
            f_start = front_figure_counter
            front_figure_counter += _count_figures(text)
            return None, "0", t_start, f_start
        chapter_counter += 1
        return str(chapter_counter), str(chapter_counter), 0, 0

    first = entries[0]
    first_path = workspace / first
    try:
        first_text = first_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"cannot read staged chapter {first}: {exc}") from exc
    ch_label, tbl_pfx, start_idx, f_start_idx = get_assignment(first, first_text)
    index_text = _transform_chapter(
        first_text,
        ch_label,
        tbl_prefix=tbl_pfx,
        table_start=start_idx,
        figure_start=f_start_idx,
        path=first,
    )
    first_path.write_text(index_text, encoding="utf-8")
    (workspace / "index.qmd").write_text(
        _rebase_images(index_text, PurePosixPath(first).parent), encoding="utf-8"
    )

    rendered = RenderedEntries(["index.qmd"])
    for entry in entries[1:]:
        path = workspace / entry
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise BuildError(f"cannot read staged chapter {entry}: {exc}") from exc
        ch_label, tbl_pfx, start_idx, f_start_idx = get_assignment(entry, text)
        transformed = _transform_chapter(
            text,
            ch_label,
            tbl_prefix=tbl_pfx,
            table_start=start_idx,
            figure_start=f_start_idx,
            path=entry,
        )
        path.write_text(transformed, encoding="utf-8")
        rendered.append(entry)
    rendered.appendix_start = first_appendix_start
    return rendered

def _render_config(
    book: dict[str, Any],
    config: dict[str, Any],
    entries: list[str],
    resources: dict[str, Path],
    workspace: Path,
    *,
    appendices: list[str] | None = None,
    toc_depth: int | None = None,
    edition_date: str | None = None,
) -> dict[str, Any]:
    project = config.setdefault("project", {})
    if not isinstance(project, dict) or project.get("type", "book") != "book":
        raise BuildError("publishing/_quarto.yml must declare a Quarto book project")
    project["type"] = "book"
    project["output-dir"] = "_output"
    config["number-sections"] = True

    book_config = config.setdefault("book", {})
    if not isinstance(book_config, dict):
        raise BuildError("publishing/_quarto.yml book section must be a mapping")
    book_config["title"] = book["title"]
    if appendices:
        first_app_idx = min(entries.index(a) for a in appendices)
        book_config["chapters"] = list(entries[:first_app_idx])
        book_config["appendices"] = list(entries[first_app_idx:])
    else:
        book_config["chapters"] = list(entries)
    if edition_date is not None:
        # The edition date comes from the source commit, never a hand-kept value.
        book_config["date"] = edition_date
        config.setdefault("date-format", "MMMM YYYY")

    config.setdefault("tbl-cap-location", "bottom")
    config.setdefault("number-sections", True)
    crossref = config.setdefault("crossref", {})
    if isinstance(crossref, dict):
        crossref.setdefault("chapters", True)
    formats = config.get("format", {})
    if not isinstance(formats, dict):
        raise BuildError("publishing/_quarto.yml format section must be a mapping")
    config["format"] = {name: formats.get(name, {}) for name in ("html", "typst", "docx")}
    config["filters"] = [
        {"at": "pre-ast", "path": (resources["filters/table-layout.lua"]).relative_to(workspace).as_posix()},
        {"at": "pre-ast", "path": (resources["filters/task-checkbox.lua"]).relative_to(workspace).as_posix()},
        {"at": "pre-ast", "path": (resources["filters/docx-callouts.lua"]).relative_to(workspace).as_posix()},
    ]
    if "filters/front-crossrefs.lua" in resources:
        config["filters"].append({
            "at": "post-render",
            "path": resources["filters/front-crossrefs.lua"].relative_to(workspace).as_posix(),
        })

    if "filters/index-resources.lua" in resources:
        config["filters"].insert(0, {
            "at": "pre-ast",
            "path": resources["filters/index-resources.lua"].relative_to(workspace).as_posix(),
        })

    def staged(name: str) -> str:
        return resources[name].relative_to(workspace).as_posix()

    typst_format = config["format"]["typst"]
    typst_format["mainfont"] = design.load_tokens()["type"]["brand"]["text_family"]
    typst_format["monofont"] = "JetBrains Mono"
    typst_format["font-paths"] = [
        resources["fonts/source-sans3/HandbookSans-Regular.ttf"].parent.relative_to(workspace).as_posix(),
        resources["fonts/source-serif4/HandbookSerif-Regular.ttf"].parent.relative_to(workspace).as_posix(),
        resources["fonts/jetbrains-mono/JetBrainsMono-Regular.ttf"].parent.relative_to(workspace).as_posix(),
    ]
    # Design constants are generated from the packaged tokens; the hand-written
    # theme reads them and never carries its own palette.
    typst_tokens = resources["typst/handbook-typst.typ"].parent / "design-tokens.typ"
    typst_tokens.write_text(design.typst_preamble(), encoding="utf-8")
    # Styles and page furniture are header includes so they apply before the
    # cover is laid out; the generated cover and Contents open the body.
    header_includes = [
        typst_tokens.relative_to(workspace).as_posix(),
    ]
    if "typst/book-data.typ" in resources:
        header_includes.append(staged("typst/book-data.typ"))
    header_includes.append(staged("typst/handbook-typst.typ"))
    typst_format["include-in-header"] = header_includes
    if "typst/front.typ" in resources:
        typst_format["include-before-body"] = staged("typst/front.typ")
    elif "typst/handbook-typst.typ" in resources:
        typst_format["include-before-body"] = staged("typst/handbook-typst.typ")
    # The generated front places the Contents after the cover page.
    typst_format["toc"] = False
    if "template-partials" not in typst_format:
        typst_format["template-partials"] = [staged("typst/typst-show.typ")]
    if "margin" not in typst_format:
        typst_format["margin"] = {"x": "2.2cm", "y": "2.4cm"}

    docx_format = config["format"]["docx"]
    if "reference-doc" not in docx_format:
        docx_format["reference-doc"] = staged("docx/reference.docx")
    if toc_depth is not None:
        for name in ("typst", "docx"):
            config["format"][name].setdefault("toc-depth", toc_depth)
    config["format"]["docx"].setdefault("toc-title", "Contents")
    for name in ("typst", "docx"):
        config["format"][name].setdefault("lot", True)
        config["format"][name].setdefault("lof", True)

    html_format = config["format"]["html"]
    html_format.setdefault("toc-title", "Contents")
    themes = {}
    for scheme in ("light", "dark"):
        theme = workspace / f"handbook-{scheme}.scss"
        theme.write_text(design.book_scss(scheme), encoding="utf-8")
        themes[scheme] = ["cosmo", theme.name]
    html_format["theme"] = themes
    html_tokens = resources["html/handbook.css"].parent / "design-tokens.css"
    html_tokens.write_text(design.book_theme_css(), encoding="utf-8")
    tokens_css = html_tokens.relative_to(workspace).as_posix()
    existing_css = html_format.get("css")
    if existing_css is None:
        stylesheets = [resources["html/handbook.css"].relative_to(workspace).as_posix()]
    elif isinstance(existing_css, str):
        stylesheets = [existing_css]
    else:
        stylesheets = list(existing_css)
    if "html/reading.css" in resources:
        stylesheets.append(staged("html/reading.css"))
    html_format["css"] = [tokens_css] + [sheet for sheet in stylesheets if sheet != tokens_css]
    execute = config.setdefault("execute", {})
    if not isinstance(execute, dict):
        raise BuildError("publishing/_quarto.yml execute section must be a mapping")
    execute["enabled"] = False
    return config

def _extract_source(source_zip: Path, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(source_zip) as archive:
            for info in archive.infolist():
                name = info.filename
                path = Path(name)
                if path.is_absolute() or ".." in path.parts or info.is_dir():
                    if info.is_dir():
                        continue
                    raise BuildError(f"unsafe source archive member: {name}")
            archive.extractall(workspace)
    except (OSError, zipfile.BadZipFile) as exc:
        raise BuildError(f"cannot extract source archive: {exc}") from exc
