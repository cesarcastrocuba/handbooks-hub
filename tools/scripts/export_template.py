#!/usr/bin/env python3
"""Export the tracked files of ``template/book/`` into a new directory.

The export is the source of the ``handbooks-template`` mirror. It copies exactly the files tracked
by Git under ``template/book/``, dotfiles included, and adds nothing else: no README, no manifest and
no ``.git`` directory. The file list and its order are deterministic, and the script makes no network
requests.

Usage::

    python3 tools/scripts/export_template.py --output DIR
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from typing import NoReturn

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "template" / "book"
PREFIX = "template/book"


def _fail(message: str) -> NoReturn:
    print(f"export-template: {message}", file=sys.stderr)
    raise SystemExit(2)


def tracked_files() -> list[str]:
    """Return the tracked files under ``template/book`` as sorted repository-relative paths."""

    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "--", PREFIX],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        _fail(result.stderr.decode("utf-8", errors="replace").strip() or "git ls-files failed")
    entries = [entry for entry in result.stdout.decode("utf-8").split("\0") if entry]
    return sorted(entries)


def export(output: Path) -> int:
    output = output.resolve()
    if output == TEMPLATE or TEMPLATE in output.parents:
        _fail("output must not be inside template/book")
    if output.exists():
        if not output.is_dir():
            _fail(f"output exists and is not a directory: {output}")
        if any(output.iterdir()):
            _fail(f"output directory is not empty: {output}")
    else:
        output.mkdir(parents=True)

    files = tracked_files()
    if not files:
        _fail("no tracked files under template/book")

    for entry in files:
        source = REPO_ROOT / entry
        relative = Path(entry).relative_to(PREFIX)
        if not source.is_file():
            _fail(f"tracked file is missing from the working tree: {entry}")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        shutil.copymode(source, destination)

    return len(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export the tracked template/book files into a new directory."
    )
    parser.add_argument("--output", required=True, help="new or empty output directory")
    args = parser.parse_args(argv)

    count = export(Path(args.output))
    print(f"exported {count} files to {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
