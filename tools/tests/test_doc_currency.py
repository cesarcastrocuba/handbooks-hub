"""Documentation currency: version statements must match the files that own them."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

from handbook_toolkit.doc_currency import LABEL, check_documentation_currency  # noqa: E402

SLUG = "sample-book"


def _repository(root: Path, *, readme: str = "", status: str = "", extra: dict[str, str] | None = None) -> Path:
    files = {
        "tools/pyproject.toml": '[project]\nname = "handbook-toolkit"\nversion = "1.3.0"\n',
        "template/book/book.yaml": 'toolkit: "1.2.0"\n',
        "template/book/README.md": "# Book template 2.0.0\n\nText.\n",
        "catalog/catalog.json": '{"books": [{"slug": "%s"}]}\n' % SLUG,
        "README.md": readme,
        "STATUS.md": status,
        **(extra or {}),
    }
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _messages(root: Path) -> list[str]:
    result = check_documentation_currency(root)
    assert result.label == LABEL
    return [str(issue).replace(str(root.resolve()) + "/", "") for issue in result.issues]


class DocumentationCurrencyTests(unittest.TestCase):
    def test_the_repository_itself_is_current(self) -> None:
        self.assertEqual(_messages(support.REPO_ROOT), [])

    def test_released_and_development_toolkit_versions_are_both_current(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _repository(
                Path(temp),
                readme="Released in toolkit `1.2.0`; template `2.0.0`.\n",
                status="Toolkit `1.3.0` is in development.\n",
            )
            self.assertEqual(_messages(root), [])

    def test_a_stale_toolkit_version_is_reported_with_its_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _repository(Path(temp), status="Line one.\nToolkit `1.1.0` is tagged.\n")
            self.assertEqual(
                _messages(root),
                [
                    "STATUS.md:2: states toolkit 1.1.0; tools/pyproject.toml and the template "
                    "pin say 1.2.0 or 1.3.0"
                ],
            )

    def test_a_stale_template_version_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _repository(Path(temp), readme="Book template `1.9.0` ships workflows.\n")
            self.assertEqual(
                _messages(root),
                ["README.md:1: states template 1.9.0; template/book/README.md says 2.0.0"],
            )

    def test_the_readme_must_not_repeat_a_catalog_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _repository(
                Path(temp),
                readme=f"The catalog lists `{SLUG}` `v1.0.0`.\n",
                status=f"Catalog: `{SLUG}` `v1.0.0`; unrelated `other-thing` `v9.9.9`.\n",
            )
            messages = _messages(root)
        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].startswith(f"README.md:1: repeats the release v1.0.0 of {SLUG}"))

    def test_wording_about_a_past_future_is_rejected_outside_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _repository(
                Path(temp),
                extra={
                    "docs/setup.md": "Quarto belongs to the future publication setup.\n",
                    "docs/contract.md": "> **Status: planned.** Nothing exists yet.\n",
                    "docs/decisions.md": "Recorded as future publication work in 2026.\n",
                    "sdd/changes/0001/record.md": "The audit quoted 'future publication'.\n",
                },
            )
            self.assertEqual(
                _messages(root),
                [
                    "docs/contract.md:1: describes shipped work as pending: 'status: planned'",
                    "docs/setup.md:1: describes shipped work as pending: 'future publication'",
                ],
            )

    def test_a_missing_or_malformed_source_of_truth_is_one_clear_issue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = _repository(Path(temp))
            (root / "template/book/README.md").write_text("# Template\n", encoding="utf-8")
            messages = _messages(root)
            self.assertEqual(len(messages), 1)
            self.assertIn("has no '# Book template X.Y.Z' heading", messages[0])
            (root / "catalog/catalog.json").unlink()
            messages = _messages(root)
            self.assertEqual(len(messages), 1)
            self.assertIn("cannot read", messages[0])


if __name__ == "__main__":
    unittest.main()
