"""Documented CLI examples must be syntactically valid.

The global ``--root`` and ``--schemas`` options belong before the subcommand. This regression
extracts ``handbook-toolkit`` examples from fenced code and table cells and runs them through the
real parser without executing them. It catches documentation drift such as
``handbook-toolkit verify --root .``, which argparse rejects.
"""

from __future__ import annotations

from contextlib import redirect_stderr
import io
from pathlib import Path
import re
import shlex
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.cli import build_parser  # noqa: E402

CURRENT_COMMANDS = {"verify", "validate-catalog", "validate-profile", "validate-book", "version"}
INLINE = re.compile(
    r"`((?:handbook-toolkit|python3? -m handbook_toolkit) [^`]+)`"
)


def _command_text(text: str) -> str | None:
    text = text.strip()
    if text.startswith("handbook-toolkit "):
        return text
    for marker in ("python3 -m handbook_toolkit ", "python -m handbook_toolkit "):
        if marker in text:
            tail = text.split(marker, 1)[1].strip()
            if tail and not tail.endswith("\\"):
                return f"handbook-toolkit {tail}"
    return None


def _documentation_files() -> list[Path]:
    root = support.REPO_ROOT
    files = [
        root / "README.md",
        root / "AGENTS.md",
        root / "CONTRIBUTING.md",
        root / "STATUS.md",
        root / "tools/README.md",
        root / "template/book/README.md",
    ]
    for directory in ("docs", "sdd"):
        base = root / directory
        if base.is_dir():
            files.extend(sorted(base.rglob("*.md")))
    return [path for path in files if path.is_file()]


def _candidate_commands() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for path in _documentation_files():
        in_fence = False
        previous = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("```", "~~~")):
                in_fence = not in_fence
                previous = ""
                continue
            candidates = []
            if in_fence:
                text = stripped[2:] if stripped.startswith("$ ") else stripped
                marked_invalid = "invalid" in previous.lower() or "reject" in previous.lower()
                candidate = _command_text(text)
                if candidate and not marked_invalid:
                    candidates.append(candidate)
            if line.lstrip().startswith("|"):
                for match in INLINE.finditer(line):
                    candidate = _command_text(match.group(1))
                    if candidate:
                        candidates.append(candidate)
            for candidate in candidates:
                found.append((path, candidate.strip()))
            if stripped:
                previous = stripped
    return found


def _first_command(tokens: list[str]) -> str | None:
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token in {"--root", "--schemas"}:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token
    return None


class DocumentedCommandTests(unittest.TestCase):
    def test_documented_cli_examples_are_parseable(self) -> None:
        parser = build_parser()
        checked = 0
        problems: list[str] = []
        for path, text in _candidate_commands():
            tokens = shlex.split(text)
            if any(token.startswith("[") or "<" in token or "..." in token for token in tokens):
                continue
            command = _first_command(tokens)
            if command not in CURRENT_COMMANDS:
                continue
            checked += 1
            try:
                with redirect_stderr(io.StringIO()):
                    parser.parse_args(tokens[1:])
            except SystemExit:
                problems.append(f"{path}: invalid example: {text}")
        self.assertGreaterEqual(checked, 5, "expected several documented toolkit examples")
        self.assertEqual(problems, [])

    def test_global_options_are_rejected_after_the_subcommand(self) -> None:
        parser = build_parser()
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["verify", "--root", "."])


if __name__ == "__main__":
    unittest.main()
