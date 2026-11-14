"""Orchestrate a verified seven-file publication without publishing it."""

from __future__ import annotations
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any
import zipfile
import yaml
from . import __version__
from . import design
from .artifacts import inspect_payload
from .publication import verify_publication, write_manifest
from .profiles import validate_profile
from .profile_resources import load_profile
from .books import validate_book
from .references import validate_references
from .render_resources import stage_render_resources
from .validation import (
    DocumentError,
    load_document,
    load_packaged_schema,
)
from .print_layout import (
    DEFAULT_RUNNING_HEADER,
    document_control_table,
    edition_date,
    edition_fields,
    inject_document_control,
    license_label,
    toc_depth,
    typst_book_data,
    typst_front,
)

from .build_types import (
    ROLES,
    PAYLOADS,
    BuildError,
    BuildResult,
    _run,
    _git,
)
from .build_identity import (
    _require_clean_commit,
    _book_version,
    _require_prerelease_version,
    _epoch,
    _tool_versions,
)
from .build_staging import (
    _reading_groups,
    _validate_manuscripts,
    _prepare_render,
    _render_config,
    _extract_source,
)
from .web_lists import generate_list_pages
from .build_html import (
    _payload_paths,
)
from .build_markdown import (
    _markdown_sources,
    _markdown_header,
    _clean_markdown,
    _reject_local_paths,
    _render_markdown,
)

__all__ = ["build_book", "BuildError", "BuildResult", "PAYLOADS", "ROLES", "_render_config", "_clean_markdown", "_markdown_header", "_markdown_sources", "_reject_local_paths"]

def build_book(
    repo: Path,
    commit: str,
    output: Path,
    *,
    profile: Path | None = None,
    version: str | None = None,
    epoch: int | None = None,
    quarto: str = "quarto",
    mode: str = "chapter",
    preview: bool = False,
) -> BuildResult:
    """Build a verified seven-file publication directory at *output*.

    ``output`` must not exist and must be outside the source repository. All work
    happens in a private sibling staging directory; only a complete, inspected
    and identity-verified directory is atomically renamed into place.
    """

    repo = Path(repo).resolve()
    raw_output = Path(output)
    profile_path = Path(profile).resolve() if profile is not None else None
    if mode not in {"chapter", "section-pilot"}:
        raise BuildError('mode must be "chapter" or "section-pilot"')

    _require_clean_commit(repo, commit)
    if raw_output.is_symlink() or raw_output.exists():
        raise BuildError(f"output already exists: {raw_output}")
    output = raw_output.resolve()
    if output.exists() or output.is_symlink():
        raise BuildError(f"output already exists: {output}")
    try:
        output.relative_to(repo)
    except ValueError:
        pass
    else:
        raise BuildError("output must be outside the source repository")
    output.parent.mkdir(parents=True, exist_ok=True)

    source_epoch = _epoch(repo, commit, epoch)
    tool_versions = _tool_versions(quarto)

    staging = Path(tempfile.mkdtemp(prefix=".handbook-build-", dir=output.parent))
    dist = staging / "dist"
    workspace = staging / "work"
    dist.mkdir()
    try:
        source_zip = dist / PAYLOADS["source"]
        _git(repo, "archive", "--format=zip", f"--output={source_zip}", commit)
        with zipfile.ZipFile(source_zip) as archive:
            if archive.comment.decode("ascii", errors="replace") != commit:
                raise BuildError("git archive did not record the exact source commit")
        source_issues = inspect_payload(source_zip, "source", source_commit=commit)
        if source_issues:
            raise BuildError(
                "source inspection failed: " + "; ".join(map(str, source_issues))
            )
        _extract_source(source_zip, workspace)

        book_path = workspace / "book.yaml"
        book_result = validate_book(book_path, load_packaged_schema("book.schema.json"))
        if not book_result.ok:
            raise BuildError("invalid book descriptor: " + "; ".join(map(str, book_result.issues)))
        book = load_document(book_path)
        if profile_path is not None:
            profile_result = validate_profile(
                profile_path, load_packaged_schema("profile.schema.json")
            )
            if not profile_result.ok:
                raise BuildError(
                    "invalid profile: " + "; ".join(map(str, profile_result.issues))
                )
            profile_document = load_document(profile_path)
        else:
            try:
                profile_document = load_profile(
                    book["profile"]["id"], book["profile"]["version"]
                )
            except DocumentError as exc:
                raise BuildError(
                    "cannot resolve the book profile from the installed package: " + str(exc)
                ) from exc
        if book["profile"]["id"] != profile_document["id"] or book["profile"]["version"] != profile_document["version"]:
            raise BuildError("book.yaml profile pin does not match the resolved profile")
        if book["toolkit"] != __version__ and not preview:
            raise BuildError(
                f"book.yaml toolkit pin {book['toolkit']} does not match builder {__version__}; "
                "use an explicit --preview build only for a non-release preview"
            )
        reference_result = validate_references(
            workspace / "book.yaml", load_packaged_schema("book.schema.json")
        )
        if not reference_result.ok:
            raise BuildError(
                "reference validation failed: "
                + "; ".join(map(str, reference_result.issues))
            )
        groups = _reading_groups(book, workspace)
        entries = [entry for group in ("front", "chapters", "back", "appendices", "references") for entry in groups[group]]
        _validate_manuscripts(workspace, book, profile_document, mode)
        book_version = _book_version(workspace, version)
        _require_prerelease_version(book_version, mode, preview)
        resources = stage_render_resources(workspace / ".handbook-render")
        brand = design.load_tokens()
        brand_colours = {
            role: values["light"] for role, values in brand["color"].items()
        }
        (workspace / "_brand.yml").write_text(
            "color:\n"
            f"  palette:\n    canvas: \"{brand_colours['canvas']}\"\n"
            f"    ink: \"{brand_colours['text']}\"\n"
            f"    accent: \"{brand_colours['accent']}\"\n"
            "  background: canvas\n  foreground: ink\n  primary: accent\n",
            encoding="utf-8",
        )
        metadata_path = workspace / "publishing/metadata.yaml"
        metadata: dict[str, Any] = {}
        if metadata_path.is_file():
            try:
                loaded_meta = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
                if isinstance(loaded_meta, dict):
                    metadata = loaded_meta
            except (OSError, yaml.YAMLError) as exc:
                raise BuildError(f"cannot read publishing/metadata.yaml: {exc}") from exc

        config_path = workspace / "publishing/_quarto.yml"
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise BuildError(f"cannot read publishing/_quarto.yml: {exc}") from exc
        if not isinstance(config, dict):
            raise BuildError("publishing/_quarto.yml must be a YAML mapping")

        author = str(metadata.get("author") or config.get("book", {}).get("author") or "")
        language = str(metadata.get("language") or config.get("lang") or "en")
        fields = edition_fields(
            book,
            metadata,
            version=book_version,
            preview=preview,
            epoch=source_epoch,
            profile=profile_document,
            author=author,
            language=language,
        )
        control_table = document_control_table(fields)
        # The Markdown edition carries its own document-control header, so it is captured
        # before the print editions inject the table into the front matter.
        markdown_source = _markdown_sources(workspace, entries)
        for entry in entries:
            entry_path = workspace / entry
            content = entry_path.read_text(encoding="utf-8")
            injected = inject_document_control(content, control_table)
            if injected is not None:
                entry_path.write_text(injected, encoding="utf-8")
                break

        entry_texts = [(workspace / entry).read_text(encoding="utf-8") for entry in entries]
        depth = toc_depth(entry_texts)

        title = str(book.get("title", ""))
        licenses = book.get("license", {})
        license_text = license_label(str(licenses.get("content", "")))
        running_header = str(metadata.get("series_label") or DEFAULT_RUNNING_HEADER)
        book_data_file = resources["typst/handbook-typst.typ"].parent / "book-data.typ"
        book_data_file.write_text(
            typst_book_data(
                title=title,
                license_text=license_text,
                running_header=running_header,
            ),
            encoding="utf-8",
        )
        resources["typst/book-data.typ"] = book_data_file

        front_file = resources["typst/handbook-typst.typ"].parent / "front.typ"
        edition_dt = edition_date(source_epoch)
        date_str = edition_dt.strftime("%B %Y")
        version_line = f"Version {book_version}, {date_str}"
        scope_line = str(metadata.get("scope_banner") or "")
        series_label = str(metadata.get("series_label") or "")
        disclaimer = str(metadata.get("disclaimer") or "")
        front_file.write_text(
            typst_front(
                series_label=series_label,
                version_line=version_line,
                scope_line=scope_line,
                author=author,
                license_text=license_text,
                disclaimer=disclaimer,
                depth=depth,
            ),
            encoding="utf-8",
        )
        resources["typst/front.typ"] = front_file

        rendered_entries = _prepare_render(workspace, entries)

        (workspace / "_quarto.yml").write_text(
            yaml.safe_dump(
                _render_config(
                    book,
                    config,
                    rendered_entries,
                    resources,
                    workspace,
                    toc_depth=depth,
                    edition_date=date_str,
                ),
                sort_keys=True,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["SOURCE_DATE_EPOCH"] = str(source_epoch)
        for print_format in ("typst", "docx"):
            _run([quarto, "render", ".", "--to", print_format, "--no-clean", "--no-execute"],
                 cwd=workspace, env=environment)

        # Lists are native HTML chapters; print and Markdown keep their own indexes.
        html_config = yaml.safe_load((workspace / "_quarto.yml").read_text())
        lists = generate_list_pages(workspace, rendered_entries)
        html_config["book"]["chapters"] = [rendered_entries[0], *lists, *rendered_entries[1:]]
        (workspace / "_quarto.yml").write_text(yaml.safe_dump(html_config), encoding="utf-8")
        _run([quarto, "render", ".", "--to", "html", "--no-clean", "--no-execute"],
             cwd=workspace, env=environment)

        payloads = _payload_paths(workspace, dist, source_epoch)
        markdown_text = _markdown_header(book, fields, commit) + _clean_markdown(
            _render_markdown(workspace, markdown_source, resources, quarto, environment)
        )
        _reject_local_paths(
            markdown_text,
            [repo, workspace, staging, output, Path.home()],
        )
        markdown_path = dist / PAYLOADS["markdown"]
        markdown_path.write_text(markdown_text, encoding="utf-8")
        payloads["markdown"] = markdown_path
        for role in ROLES:
            issues = inspect_payload(
                payloads[role],
                role,
                source_commit=commit if role == "source" else None,
                version=book_version if role == "markdown" else None,
            )
            if issues:
                raise BuildError(
                    f"{role} inspection failed: " + "; ".join(map(str, issues))
                )

        metadata = {
            "book": {"id": book["id"], "version": book_version, "commit": commit},
            "toolkit": __version__,
            "profile": {
                "id": profile_document["id"],
                "version": profile_document["version"],
            },
            "build": {
                "command": "handbook-toolkit build-book --commit "
                + commit
                + f" --mode {mode}"
                + (" --preview" if preview else ""),
                "source_date_epoch": source_epoch,
                "tool_versions": tool_versions,
            },
        }
        write_manifest(dist, metadata, {role: payloads[role].name for role in ROLES})
        verification = verify_publication(dist)
        if not verification.ok:
            raise BuildError(
                "publication identity verification failed: "
                + "; ".join(map(str, verification.issues))
            )
        if output.exists() or output.is_symlink():
            raise BuildError(f"output appeared during build; refusing to replace: {output}")

        os.replace(dist, output)
        return BuildResult(output, commit, book_version, source_epoch, tool_versions)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)

