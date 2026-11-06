"""Build a handbook release payload set without publishing it.

The build is deliberately conservative:

* the source repository must be clean at the exact requested commit;
* only tracked files from that commit are staged, via ``git archive``;
* Quarto renders HTML, Typst/PDF and DOCX once from a generated project config;
* all four payloads are inspected before identity files are written;
* the four payloads plus manifest/checksums are assembled in a private staging directory;
* the verified staging directory is atomically renamed to the final output.

This module does not publish, upload, deploy, approve or release anything.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
from typing import Any
import zipfile
import zlib

import yaml

from . import __version__
from .artifacts import archive_tree, inspect_payload
from .publication import verify_publication, write_manifest
from .profiles import validate_profile
from .books import validate_book
from .validation import (
    load_document,
    load_packaged_schema,
)

QUARTO_VERSION = "1.11.9"
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?\Z")
ROLES = ("html", "pdf", "docx", "source")
PAYLOADS = {
    "html": "book-html.zip",
    "pdf": "book.pdf",
    "docx": "book.docx",
    "source": "book-source.zip",
}


class BuildError(ValueError):
    """Raised when a build cannot produce a verified release directory."""


@dataclass(frozen=True)
class BuildResult:
    output: Path
    commit: str
    version: str
    epoch: int
    tool_versions: dict[str, str]


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildError(f"cannot run {command[0]}: {exc}") from exc
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise BuildError(f"{' '.join(command)} failed: {detail}")
    return (result.stdout.strip() or result.stderr.strip())


def _git(repo: Path, *args: str) -> str:
    return _run(["git", "-C", str(repo), *args])


def _require_clean_commit(repo: Path, commit: str) -> None:
    if not COMMIT.fullmatch(commit):
        raise BuildError("commit must be a full 40-character lowercase SHA")
    if not repo.is_dir():
        raise BuildError(f"repository does not exist: {repo}")
    head = _git(repo, "rev-parse", "HEAD")
    if head != commit:
        raise BuildError(f"requested commit {commit} is not HEAD ({head})")
    if _git(repo, "status", "--porcelain"):
        raise BuildError("source repository must be clean before building")


def _reading_order(book: dict[str, Any], repo: Path) -> list[str]:
    manuscript = book["manuscript"]
    root = repo / manuscript["root"]
    path = repo / manuscript["reading_order"]
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BuildError(f"cannot read reading order {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise BuildError("reading order must be a YAML mapping")
    entries: list[str] = []
    for group in ("front", "chapters", "back", "appendices", "references"):
        values = document.get(group, []) or []
        if not isinstance(values, list):
            raise BuildError(f"reading order group {group} must be a list")
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
            entries.append(f"{manuscript['root']}/{value}")
    if not entries:
        raise BuildError("reading order contains no manuscript entries")
    return entries


def _book_version(repo: Path, requested: str | None) -> str:
    if requested is not None:
        version = requested
    else:
        path = repo / "publishing/metadata.yaml"
        try:
            metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise BuildError(f"cannot read publishing/metadata.yaml: {exc}") from exc
        version = metadata.get("version") if isinstance(metadata, dict) else None
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise BuildError("book version must be an exact semantic version such as 1.0.0")
    return version


def _epoch(repo: Path, commit: str, requested: int | None) -> int:
    if requested is not None:
        epoch = requested
    elif os.environ.get("SOURCE_DATE_EPOCH"):
        try:
            epoch = int(os.environ["SOURCE_DATE_EPOCH"])
        except ValueError as exc:
            raise BuildError("SOURCE_DATE_EPOCH must be an integer") from exc
    else:
        epoch = int(_git(repo, "show", "-s", "--format=%ct", commit))
    if epoch < 0:
        raise BuildError("source epoch must be nonnegative")
    return epoch


def _tool_versions(quarto: str) -> dict[str, str]:
    quarto_version = _run([quarto, "--version"]).splitlines()[-1].strip()
    if quarto_version != QUARTO_VERSION:
        raise BuildError(
            f"Quarto {QUARTO_VERSION} is required; found {quarto_version or 'unknown'}"
        )
    pandoc = _run([quarto, "pandoc", "--version"]).splitlines()[0].split()[-1]
    typst = _run([quarto, "typst", "--version"]).splitlines()[0].split()[1]
    return {
        "quarto": quarto_version,
        "pandoc": pandoc,
        "typst": typst,
        "python": platform.python_version(),
        "zlib": zlib.ZLIB_RUNTIME_VERSION,
    }


def _render_config(book: dict[str, Any], config: dict[str, Any], entries: list[str]) -> dict[str, Any]:
    project = config.setdefault("project", {})
    if not isinstance(project, dict) or project.get("type", "book") != "book":
        raise BuildError("publishing/_quarto.yml must declare a Quarto book project")
    project["type"] = "book"
    project["output-dir"] = "_output"

    book_config = config.setdefault("book", {})
    if not isinstance(book_config, dict):
        raise BuildError("publishing/_quarto.yml book section must be a mapping")
    book_config["title"] = book["title"]
    book_config["chapters"] = ["index.qmd", *entries]

    formats = config.setdefault("format", {})
    if not isinstance(formats, dict):
        raise BuildError("publishing/_quarto.yml format section must be a mapping")
    for name in ("html", "typst", "docx"):
        formats.setdefault(name, {})
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


def _one_file(directory: Path, suffix: str) -> Path:
    matches = sorted(directory.rglob(f"*{suffix}"))
    if len(matches) != 1:
        raise BuildError(
            f"expected exactly one {suffix} output under {directory}, found {len(matches)}"
        )
    return matches[0]


def _payload_paths(workspace: Path, dist: Path, epoch: int) -> dict[str, Path]:
    output = workspace / "_output"
    if not (output / "index.html").is_file():
        raise BuildError("Quarto did not produce _output/index.html")
    site = dist.parent / "site"
    shutil.copytree(
        output,
        site,
        ignore=shutil.ignore_patterns("*.pdf", "*.docx", "*.typst"),
    )
    archive_tree(site, dist / PAYLOADS["html"], epoch)
    pdf = _one_file(output, ".pdf")
    docx = _one_file(output, ".docx")
    shutil.copy2(pdf, dist / PAYLOADS["pdf"])
    shutil.copy2(docx, dist / PAYLOADS["docx"])
    return {
        "html": dist / PAYLOADS["html"],
        "pdf": dist / PAYLOADS["pdf"],
        "docx": dist / PAYLOADS["docx"],
        "source": dist / PAYLOADS["source"],
    }


def build_book(
    repo: Path,
    commit: str,
    output: Path,
    *,
    profile: Path,
    version: str | None = None,
    epoch: int | None = None,
    quarto: str = "quarto",
) -> BuildResult:
    """Build a verified six-file publication directory at *output*.

    ``output`` must not exist and must be outside the source repository. All work
    happens in a private sibling staging directory; only a complete, inspected
    and identity-verified directory is atomically renamed into place.
    """

    repo = Path(repo).resolve()
    output = Path(output).resolve()
    profile = Path(profile).resolve()

    _require_clean_commit(repo, commit)
    if output.exists() or output.is_symlink():
        raise BuildError(f"output already exists: {output}")
    try:
        output.relative_to(repo)
    except ValueError:
        pass
    else:
        raise BuildError("output must be outside the source repository")
    output.parent.mkdir(parents=True, exist_ok=True)

    book_path = repo / "book.yaml"
    book_result = validate_book(book_path, load_packaged_schema("book.schema.json"))
    if not book_result.ok:
        raise BuildError("invalid book descriptor: " + "; ".join(map(str, book_result.issues)))

    profile_result = validate_profile(profile, load_packaged_schema("profile.schema.json"))
    if not profile_result.ok:
        raise BuildError("invalid profile: " + "; ".join(map(str, profile_result.issues)))

    book = load_document(book_path)
    profile_document = load_document(profile)
    if book["profile"]["id"] != profile_document["id"] or book["profile"]["version"] != profile_document["version"]:
        raise BuildError("book.yaml profile pin does not match the explicit --profile")

    entries = _reading_order(book, repo)
    book_version = _book_version(repo, version)
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
        _extract_source(source_zip, workspace)

        config_path = workspace / "publishing/_quarto.yml"
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise BuildError(f"cannot read publishing/_quarto.yml: {exc}") from exc
        if not isinstance(config, dict):
            raise BuildError("publishing/_quarto.yml must be a YAML mapping")

        (workspace / "_quarto.yml").write_text(
            yaml.safe_dump(
                _render_config(book, config, entries),
                sort_keys=True,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        (workspace / "index.qmd").write_text(
            f"# {book['title']}\n",
            encoding="utf-8",
        )

        environment = os.environ.copy()
        environment["SOURCE_DATE_EPOCH"] = str(source_epoch)
        _run(
            [quarto, "render", "."],
            cwd=workspace,
            env=environment,
        )

        payloads = _payload_paths(workspace, dist, source_epoch)
        for role in ROLES:
            issues = inspect_payload(
                payloads[role],
                role,
                source_commit=commit if role == "source" else None,
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
                "command": f"handbook-toolkit build-book --commit {commit}",
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
