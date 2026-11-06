"""Repository-level and documentation-link tests."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit.repository import check_documentation_links, verify_repository  # noqa: E402


class RepositoryTests(unittest.TestCase):
    def test_repository_full_verification(self) -> None:
        results = verify_repository(support.REPO_ROOT, full=True)
        problems = [str(issue) for result in results for issue in result.issues]
        self.assertEqual(problems, [])

    def test_documentation_links_reject_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "README.md").write_text("[docs](docs/a.md)\n", encoding="utf-8")
            (root / "docs/a.md").write_text(
                "[ok](b.md) [bad](missing.md) [web](https://example.com) [anchor](#section)\n",
                encoding="utf-8",
            )
            (root / "docs/b.md").write_text("# B\n", encoding="utf-8")
            result = check_documentation_links(root)
            self.assertFalse(result.ok)
            self.assertTrue(any("missing.md" in issue.message for issue in result.issues))

    def test_documentation_links_skip_fenced_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text(
                "```markdown\n[not a link](missing.md)\n```\n[ok](README.md)\n",
                encoding="utf-8",
            )
            result = check_documentation_links(root)
            self.assertTrue(result.ok, [str(issue) for issue in result.issues])

    def test_documentation_links_reject_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("[escape](../../outside.md)\n", encoding="utf-8")
            result = check_documentation_links(root)
            self.assertFalse(result.ok)
            self.assertTrue(any("escapes the repository" in issue.message for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
