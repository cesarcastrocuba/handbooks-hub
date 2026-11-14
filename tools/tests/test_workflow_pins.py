"""Every workflow action is pinned to a commit, one commit per action.

A tag moves; a full commit does not. The same action must also use the same commit
everywhere, so a bump is one reviewed change rather than a drift between workflows.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

WORKFLOW_DIRECTORIES = (
    support.REPO_ROOT / ".github" / "workflows",
    support.REPO_ROOT / "template" / "book" / ".github" / "workflows",
)
USES = re.compile(
    r"^[ \t]*(?:-[ \t]*)?uses:[ \t]*(?P<action>[\w.-]+/[\w./-]+)@(?P<commit>[0-9a-f]{40})"
    r"[ \t]+#[ \t]*(?P<version>\S.*)$"
)


def workflow_files() -> list[Path]:
    files = [path for directory in WORKFLOW_DIRECTORIES for path in sorted(directory.glob("*.yml"))]
    files += [path for directory in WORKFLOW_DIRECTORIES for path in sorted(directory.glob("*.yaml"))]
    return files


def uses_lines() -> list[tuple[Path, int, re.Match[str]]]:
    found: list[tuple[Path, int, re.Match[str]]] = []
    for path in workflow_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "uses:" not in line:
                continue
            found.append((path, number, USES.match(line)))
    return found


class WorkflowPinTests(unittest.TestCase):
    def test_the_workflow_directories_are_found(self) -> None:
        self.assertGreaterEqual(len(workflow_files()), 6)

    def test_every_action_is_pinned_to_a_full_commit_with_its_version(self) -> None:
        self.assertTrue(uses_lines())
        for path, number, match in uses_lines():
            with self.subTest(file=path.name, line=number):
                self.assertIsNotNone(
                    match, f"{path.name}:{number} is not pinned to a commit with a version comment"
                )

    def test_each_action_uses_one_commit_across_the_repository(self) -> None:
        commits: dict[str, set[str]] = {}
        for _path, _number, match in uses_lines():
            if match is None:
                continue
            commits.setdefault(match.group("action"), set()).add(match.group("commit"))
        for action, pinned in sorted(commits.items()):
            with self.subTest(action=action):
                self.assertEqual(
                    len(pinned), 1, f"{action} is pinned to more than one commit: {sorted(pinned)}"
                )


if __name__ == "__main__":
    unittest.main()
