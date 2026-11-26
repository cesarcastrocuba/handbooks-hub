"""Workflows that run the toolkit tests or build a book install qpdf 11 or later."""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

WORKFLOWS = support.REPO_ROOT / ".github/workflows"
RUNS_THE_TOOLKIT = re.compile(
    r"\bmake (?:check|full)\b|\bbuild-book\b|\bedition_preview\.py\b|test_build\.py\b"
)
QPDF_INSTALL = re.compile(
    r"apt-get install[^\n]*\bqpdf\b|brew install[^\n]*\bqpdf\b"
)
QPDF_VERSION = re.compile(r"qpdf --version[^\n]*-ge 11")


def workflow_jobs():
    for path in sorted(WORKFLOWS.glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for name, job in (document.get("jobs") or {}).items():
            script = "\n".join(
                str(step.get("run", "")) for step in job.get("steps", []) if step
            )
            yield path.name, name, script


class WorkflowSystemDependenciesTests(unittest.TestCase):
    def test_jobs_that_build_or_test_a_book_install_and_verify_qpdf(self) -> None:
        checked = set()
        for workflow, job, script in workflow_jobs():
            if not RUNS_THE_TOOLKIT.search(script):
                continue
            checked.add((workflow, job))
            with self.subTest(workflow=workflow, job=job):
                self.assertRegex(script, QPDF_INSTALL)
                self.assertRegex(script, QPDF_VERSION)
        self.assertTrue(checked)
        self.assertLessEqual(
            {
                ("ci.yml", "checks"),
                ("ci.yml", "publication-build"),
                ("catalog-update.yml", "prepare"),
                ("clean-clone.yml", "clean-clone"),
                ("portal-pages.yml", "build"),
            },
            checked,
        )

    def test_every_workflow_is_readable_yaml(self) -> None:
        files = sorted(WORKFLOWS.glob("*.yml"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(workflow=path.name):
                document = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIsInstance(document.get("jobs"), dict)

    def test_no_workflow_triggers_a_qpdf_install_without_the_version_check(self) -> None:
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            if not QPDF_INSTALL.search(text):
                continue
            with self.subTest(workflow=path.name):
                self.assertRegex(text, QPDF_VERSION)


if __name__ == "__main__":
    unittest.main()
