"""Build types."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess


QUARTO_VERSION = "1.11.9"

COMMIT = re.compile(r"[0-9a-f]{40}\Z")

VERSION = re.compile(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?\Z")

ROLES = ("html", "pdf", "docx", "markdown", "source")

PAYLOADS = {
    "html": "book-html.zip",
    "pdf": "book.pdf",
    "docx": "book.docx",
    "markdown": "book.md",
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
