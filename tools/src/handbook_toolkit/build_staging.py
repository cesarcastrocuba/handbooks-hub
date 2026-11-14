"""Build staging."""

from __future__ import annotations
from pathlib import Path, PurePosixPath
import re
from typing import Any
import zipfile
import yaml
from . import design
from .manuscript import validate_manuscript

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
    for entry in targets:
        path = workspace / entry
        result = validate_manuscript(path, profile, mode)
        if not result.ok:
            raise BuildError(
                f"manuscript validation failed for {entry}: "
                + "; ".join(map(str, result.issues))
            )

def _strip_heading_number(title: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*[ .]+", "", title).strip()

def _transform_chapter(text: str, chapter_number: int) -> str:
    """Stage a chapter wrapper and explicit table captions without changing source."""

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
    title = _strip_heading_number(re.sub(r"^#{1,3}\s+", "", heading))
    if len(re.findall(r"[A-Za-z]", title)) < 3:
        raise BuildError("staged chapter heading is not meaningful")
    remaining = lines[:first] + lines[first + 1 :]

    output: list[str] = [f"# {title}", ""]
    if front:
        output = ["---", *yaml.safe_dump(front, sort_keys=False).splitlines(), "---", "", *output]
    table_number = 0
    previous = ""
    for line in remaining:
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            line = f"{heading_match.group(1)} {_strip_heading_number(heading_match.group(2))}"
        caption = re.match(r"^(?::|Table:)\s+(.*\S)\s*$", line)
        if caption and previous.lstrip().startswith("|"):
            table_number += 1
            if not re.search(r"\{#tbl-[^}]+\}\s*$", caption.group(1)):
                caption_text = re.sub(r"\s*\{[^}]*\}\s*$", "", caption.group(1)).strip()
                line = f": {caption_text} {{#tbl-{chapter_number}-{table_number}}}"
            output.extend(["", line, ""])
            previous = ""
            continue
        output.append(line)
        if line.strip():
            previous = line
    return "\n".join(output).rstrip() + "\n"

def _prepare_render(workspace: Path, entries: list[str]) -> list[str]:
    """Create root index and transformed chapter files for Quarto.

    The first reading-order file becomes ``index.qmd`` so Quarto has a home page without a
    separate generated chapter. Other chapter/appendix files are transformed in place in the
    private staging workspace. Canonical source in the commit is untouched.
    """

    if not entries:
        raise BuildError("no manuscript entries to render")
    first = entries[0]
    first_path = workspace / first
    try:
        first_text = first_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BuildError(f"cannot read staged chapter {first}: {exc}") from exc
    index_text = _transform_chapter(first_text, 1)
    (workspace / ".handbook-index-source-dir").write_text(str(PurePosixPath(first).parent))
    (workspace / "index.qmd").write_text(index_text, encoding="utf-8")

    rendered: list[str] = ["index.qmd"]
    chapter_number = 1
    for entry in entries[1:]:
        path = workspace / entry
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise BuildError(f"cannot read staged chapter {entry}: {exc}") from exc
        chapter_number += 1
        path.write_text(_transform_chapter(text, chapter_number), encoding="utf-8")
        rendered.append(entry)
    return rendered

def _render_config(
    book: dict[str, Any],
    config: dict[str, Any],
    entries: list[str],
    resources: dict[str, Path],
    workspace: Path,
    *,
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
    book_config["chapters"] = entries
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

    if "filters/index-resources.lua" in resources:
        config["filters"].insert(0, {
            "at": "pre-ast",
            "path": resources["filters/index-resources.lua"].relative_to(workspace).as_posix(),
        })
        origin = workspace / ".handbook-index-source-dir"
        if origin.is_file():
            config["handbook-index-source-dir"] = origin.read_text()

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
        staged("typst/handbook-typst.typ"),
    ]
    if "typst/book-data.typ" in resources:
        header_includes.append(staged("typst/book-data.typ"))
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
