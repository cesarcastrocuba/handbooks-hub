"""Build identity."""

from __future__ import annotations
import os
from pathlib import Path
import platform
import zlib
import yaml

from .build_types import BuildError, QUARTO_VERSION, COMMIT, VERSION, _run, _git

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

def _require_prerelease_version(version: str, mode: str, preview: bool) -> None:
    if (mode == "section-pilot" or preview) and "-" not in version:
        raise BuildError(
            "section-pilot and --preview builds require a prerelease book version "
            "such as 0.1.0-preview, not a stable release version"
        )

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
