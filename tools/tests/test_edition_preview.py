"""Edition preview: the script's decisions and the CI job that runs it.

The real build, the LibreOffice conversion and the screenshots run in the ``edition-preview`` CI
job; these tests cover the logic that does not need Quarto, LibreOffice or a browser.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

SCRIPT = support.REPO_ROOT / "tools" / "scripts" / "edition_preview.py"
WORKFLOW = support.REPO_ROOT / ".github" / "workflows" / "ci.yml"
PINNED_ACTION = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")


def _load_script():
    spec = importlib.util.spec_from_file_location("edition_preview", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


preview = _load_script()


def _write(path: Path, text: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _repository(root: Path, version: str = "1.2.0") -> Path:
    repo = root / "book"
    _write(repo / "publishing" / "metadata.yaml", f'version: "{version}"\n')
    for arguments in (
        ("init", "-q", "-b", "main"),
        ("add", "-A"),
        ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", "fixture"),
    ):
        subprocess.run(["git", "-C", str(repo), *arguments], check=True, capture_output=True)
    return repo


class PreviewVersionTests(unittest.TestCase):
    def test_a_release_version_is_marked_as_a_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            _write(repo / "publishing" / "metadata.yaml", 'version: "1.2.0"\n')
            self.assertEqual(preview.preview_version(repo), "1.2.0-preview")

    def test_a_prerelease_version_is_kept(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            _write(repo / "publishing" / "metadata.yaml", 'version: "0.1.0-preview"\n')
            self.assertEqual(preview.preview_version(repo), "0.1.0-preview")

    def test_missing_metadata_or_version_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            with self.assertRaises(preview.PreviewError):
                preview.preview_version(repo)
            _write(repo / "publishing" / "metadata.yaml", "status: draft\n")
            with self.assertRaises(preview.PreviewError):
                preview.preview_version(repo)


class PageSelectionTests(unittest.TestCase):
    def test_top_level_pages_and_the_largest_nested_page_are_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            index = _write(site / "index.html")
            tables = _write(site / "tables.html")
            _write(site / "manuscript" / "chapters" / "ch01.html", "short")
            largest = _write(site / "manuscript" / "chapters" / "ch02.html", "much longer page")
            _write(site / "site_libs" / "quarto.js")
            self.assertEqual(preview.select_pages(site), [index, tables, largest])

    def test_a_site_with_one_page_selects_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            index = _write(site / "index.html")
            self.assertEqual(preview.select_pages(site), [index])

    def test_a_site_without_pages_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(preview.PreviewError):
                preview.select_pages(Path(temp))

    def test_screenshot_names_are_flat_and_unique_per_variant(self) -> None:
        site = Path("/site")
        page = site / "manuscript" / "chapters" / "ch02.html"
        names = {
            preview.screenshot_name(site, page, viewport, scheme)
            for viewport in preview.VIEWPORTS
            for scheme in preview.COLOR_SCHEMES
        }
        self.assertEqual(len(names), len(preview.VIEWPORTS) * len(preview.COLOR_SCHEMES))
        self.assertIn("manuscript--chapters--ch02.desktop.dark.png", names)


class SummaryTests(unittest.TestCase):
    def test_summary_lists_files_identity_and_skipped_steps(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            _write(output / "edition" / "book.docx", "docx")
            _write(output / "site" / "index.html")
            _write(output / "site" / "site_libs" / "quarto.js")
            result = preview.Preview(
                output=output,
                commit="a" * 40,
                version="1.2.0-preview",
                skipped=["Screenshots: the `playwright` package is not installed"],
            )
            summary = preview.render_summary(result)
        self.assertIn("`" + "a" * 40 + "`", summary)
        self.assertIn("`1.2.0-preview` (preview build, not a release)", summary)
        self.assertIn("| `edition/book.docx` | 4 |", summary)
        self.assertNotIn("site/index.html", summary)
        self.assertIn("(1 HTML pages)", summary)
        self.assertIn("## Not run", summary)
        self.assertIn("- Screenshots: the `playwright` package is not installed", summary)


class BuildPreviewGuardTests(unittest.TestCase):
    def test_an_existing_output_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = _repository(Path(temp))
            output = Path(temp) / "out"
            output.mkdir()
            with self.assertRaisesRegex(preview.PreviewError, "output already exists"):
                preview.build_preview(repo, output, quarto="quarto", require_tools=False)

    def test_uncommitted_changes_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = _repository(Path(temp))
            _write(repo / "draft.txt")
            with self.assertRaisesRegex(preview.PreviewError, "uncommitted changes"):
                preview.build_preview(repo, Path(temp) / "out", quarto="quarto", require_tools=False)

    def test_a_failed_run_exits_with_a_message_and_status_two(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", temp, "--output", str(Path(temp) / "out")],
                capture_output=True,
                text=True,
                check=False,
                env={"PYTHONPATH": str(support.SRC), "PATH": "/usr/bin:/bin"},
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("edition-preview:", result.stderr)


class EditionPreviewJobTests(unittest.TestCase):
    def setUp(self) -> None:
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        self.job = workflow["jobs"]["edition-preview"]

    def test_it_runs_only_for_pull_requests_with_read_only_permissions(self) -> None:
        self.assertEqual(self.job["if"], "github.event_name == 'pull_request'")
        self.assertEqual(self.job["permissions"], {"contents": "read"})

    def test_it_previews_the_template_and_the_sample_independently(self) -> None:
        strategy = self.job["strategy"]
        self.assertFalse(strategy["fail-fast"])
        self.assertEqual([entry["book"] for entry in strategy["matrix"]["include"]], ["template", "sample"])

    def test_template_job_uploads_portal_parity_and_screenshots(self) -> None:
        step=next(step for step in self.job['steps'] if step.get('name')=='Preview both portal engines and their parity')
        self.assertEqual(step['if'],"matrix.book == 'template'")
        self.assertIn('tools/scripts/portal_preview.py',step['run'])
        self.assertIn('$RUNNER_TEMP/edition-preview/portal',step['run'])

    def test_every_action_is_pinned_to_a_commit(self) -> None:
        actions = [step["uses"] for step in self.job["steps"] if "uses" in step]
        self.assertTrue(actions)
        for action in actions:
            self.assertRegex(action, PINNED_ACTION)

    def test_the_book_checkout_keeps_no_credentials(self) -> None:
        checkouts = [
            step for step in self.job["steps"] if step.get("uses", "").startswith("actions/checkout@")
        ]
        self.assertEqual(len(checkouts), 2)
        for step in checkouts:
            self.assertIs(step["with"]["persist-credentials"], False)

    def test_no_expression_is_interpolated_into_a_shell_script(self) -> None:
        for step in self.job["steps"]:
            self.assertNotIn("${{", step.get("run", ""))

    def test_the_artifact_is_named_per_book_and_expires(self) -> None:
        upload = next(
            step for step in self.job["steps"] if step.get("uses", "").startswith("actions/upload-artifact@")
        )
        self.assertEqual(upload["with"]["name"], "edition-preview-${{ matrix.book }}")
        self.assertEqual(upload["with"]["retention-days"], 14)
        self.assertEqual(upload["with"]["if-no-files-found"], "error")


if __name__ == "__main__":
    unittest.main()
