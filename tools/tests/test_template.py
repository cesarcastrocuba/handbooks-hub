"""Template 1.1 copy, check, workflow and onboarding regression.

The fast test copies the template outside the hub, replaces its identifiers, installs nothing from
the hub checkout and runs the template's own ``make check``. The build test additionally runs a real
six-file build when Quarto and ``pdfinfo`` are available. The workflow tests pin every action to a
full commit SHA already used by the hub and forbid expression interpolation inside shell scripts. The
onboarding tests run the book-owned ``initialize_book.py`` on a copy.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402

TEMPLATE = support.REPO_ROOT / "template/book"
TEMPLATE_WORKFLOWS = TEMPLATE / ".github/workflows"
HUB_WORKFLOWS = support.REPO_ROOT / ".github/workflows"
INITIALIZE = TEMPLATE / ".github/scripts/initialize_book.py"
QUARTO = shutil.which("quarto")
PDFINFO = shutil.which("pdfinfo")
PDFTOTEXT = shutil.which("pdftotext")
BUILD_AVAILABLE = QUARTO is not None and PDFINFO is not None

PAYLOADS = {
    "book-html.zip",
    "book.pdf",
    "book.docx",
    "book-source.zip",
    "publication-manifest.json",
    "SHA256SUMS.txt",
}

REPLACEMENTS = {
    "id: template-book": "id: copied-book",
    "title: Handbook template": "title: Copied Handbook",
    "slug: template-book": "slug: copied-book",
    "summary: Replace this summary before the book is listed in the hub catalog.":
        "summary: A copied template used to prove the book boundary.",
}

IDENTITY = {
    "id": "copied-book",
    "title": "Copied Handbook",
    "author": "Ada Lovelace",
    "summary": "A copied template used to prove the initialization step.",
    "category": "architecture",
    "repository-url": "https://github.com/example/copied-book",
}

USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s@]+)@([0-9a-f]{40})\s*(?:#.*)?$")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def _environment() -> dict[str, str]:
    return dict(
        os.environ,
        PYTHONPATH=str(support.SRC),
        TOOLKIT=f"{sys.executable} -m handbook_toolkit",
    )


def _copy_template(root: Path, replace: bool = True) -> Path:
    book = root / "book"
    shutil.copytree(TEMPLATE, book)
    if replace:
        descriptor = book / "book.yaml"
        text = descriptor.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS.items():
            if old not in text:
                raise AssertionError(f"template descriptor is missing {old!r}")
            text = text.replace(old, new)
        descriptor.write_text(text, encoding="utf-8")
    _git(book, "init", "-q", "-b", "main")
    _git(book, "add", "-A")
    _git(
        book,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-q",
        "-m",
        "template copy",
    )
    return book


def _run(command: list[str], book: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=book,
        env=_environment(),
        capture_output=True,
        text=True,
        check=False,
    )


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(document: dict) -> dict:
    # PyYAML resolves the bare YAML 1.1 key ``on`` to the boolean True.
    return document.get("on", document.get(True))


def _steps(document: dict):
    for job in document.get("jobs", {}).values():
        for step in job.get("steps", []):
            yield step


def _hub_action_shas() -> set[str]:
    shas: set[str] = set()
    for path in HUB_WORKFLOWS.glob("*.yml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = USES.match(line)
            if match:
                shas.add(match.group(2))
    return shas


def _github_snapshot(book: Path) -> dict[str, str]:
    return {
        path.relative_to(book).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((book / ".github").rglob("*"))
        if path.is_file()
    }


def _initialize(book: Path, identity: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    values = identity or IDENTITY
    command = [
        sys.executable,
        str(book / ".github/scripts/initialize_book.py"),
        "--root",
        str(book),
    ]
    for key, value in values.items():
        command.extend([f"--{key}", value])
    return _run(command, book)


class TemplateTests(unittest.TestCase):
    def test_copied_template_passes_its_own_fast_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp))
            self.assertFalse((book / "tools").exists())
            self.assertFalse((book / "schemas").exists())

            result = _run(["make", "check"], book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("validate-book", result.stdout + result.stderr)
            self.assertIn("OK", result.stdout + result.stderr)

    def test_template_pins_are_exact_and_current(self) -> None:
        descriptor = _load(TEMPLATE / "book.yaml")
        self.assertRegex(descriptor["toolkit"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(descriptor["profile"]["version"], r"^\d+\.\d+\.\d+$")
        requirements = (TEMPLATE / "requirements.txt").read_text(encoding="utf-8")
        self.assertRegex(requirements, r"@[0-9a-f]{40}#subdirectory=tools")
        for name in ("LICENSE", "LICENSE-CODE", "NOTICE.md", "Makefile", "publishing/_quarto.yml"):
            self.assertTrue((TEMPLATE / name).is_file(), name)
        for name in (".gitignore", "docs/AUTHOR_QUICKSTART.md"):
            self.assertTrue((TEMPLATE / name).is_file(), name)

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for the real build")
    def test_copied_template_builds_six_verified_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book = _copy_template(root)
            output = root / "dist"

            result = _run(["make", "build", f"OUTPUT={output}"], book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual({path.name for path in output.iterdir()}, PAYLOADS)

            manifest = json.loads((output / "publication-manifest.json").read_text())
            self.assertEqual(manifest["book"]["commit"], _git(book, "rev-parse", "HEAD"))
            self.assertEqual(manifest["book"]["version"], "0.1.0-preview")

            if PDFTOTEXT is not None:
                text = subprocess.check_output(
                    [PDFTOTEXT, str(output / "book.pdf"), "-"], text=True
                )
                self.assertIn("Example Chapter", text)


class TemplateWorkflowTests(unittest.TestCase):
    def test_all_three_workflows_exist(self) -> None:
        names = {path.name for path in TEMPLATE_WORKFLOWS.glob("*.yml")}
        self.assertEqual(names, {"ci.yml", "release.yml", "initialize-book.yml"})

    def test_actions_are_pinned_to_hub_commit_shas(self) -> None:
        hub_shas = _hub_action_shas()
        self.assertTrue(hub_shas)
        for path in sorted(TEMPLATE_WORKFLOWS.glob("*.yml")):
            document = _load(path)
            for step in _steps(document):
                uses = step.get("uses")
                if not uses:
                    continue
                match = USES.match(f"  uses: {uses}")
                self.assertIsNotNone(match, f"{path.name}: action is not pinned: {uses}")
                self.assertIn(match.group(2), hub_shas, f"{path.name}: SHA is not used by the hub")

    def test_no_expression_is_interpolated_into_a_shell_script(self) -> None:
        for path in sorted(TEMPLATE_WORKFLOWS.glob("*.yml")):
            document = _load(path)
            for step in _steps(document):
                script = step.get("run")
                if script is not None:
                    self.assertNotIn("${{", script, f"{path.name}: expression inside run")

    def test_triggers_and_permissions(self) -> None:
        ci = _load(TEMPLATE_WORKFLOWS / "ci.yml")
        self.assertIn("push", _triggers(ci))
        self.assertIn("pull_request", _triggers(ci))
        self.assertEqual(ci["permissions"], {"contents": "read"})

        release = _load(TEMPLATE_WORKFLOWS / "release.yml")
        self.assertEqual(set(_triggers(release)), {"workflow_dispatch"})
        self.assertIs(_triggers(release)["workflow_dispatch"]["inputs"]["version"]["required"], True)
        self.assertEqual(release["permissions"]["contents"], "write")
        self.assertEqual(release["permissions"]["pages"], "write")

        initialize = _load(TEMPLATE_WORKFLOWS / "initialize-book.yml")
        self.assertEqual(set(_triggers(initialize)), {"workflow_dispatch"})
        inputs = _triggers(initialize)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(inputs), {"title", "id", "author", "summary", "category"})
        self.assertEqual(
            inputs["category"]["options"],
            [
                "architecture",
                "authoring",
                "cloud",
                "data",
                "engineering",
                "governance",
                "publishing",
                "security",
            ],
        )
        self.assertEqual(initialize["permissions"], {"contents": "write"})


class InitializeBookTests(unittest.TestCase):
    def test_initializes_a_copy_and_refuses_a_second_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp), replace=False)
            before = _github_snapshot(book)

            result = _initialize(book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(_github_snapshot(book), before)

            descriptor = _load(book / "book.yaml")
            self.assertEqual(descriptor["id"], IDENTITY["id"])
            self.assertEqual(descriptor["title"], IDENTITY["title"])
            self.assertEqual(descriptor["catalog"]["slug"], IDENTITY["id"])
            self.assertEqual(descriptor["catalog"]["summary"], IDENTITY["summary"])
            self.assertEqual(descriptor["catalog"]["categories"], [IDENTITY["category"]])
            self.assertEqual(descriptor["repository"]["url"], IDENTITY["repository-url"])

            quarto = _load(book / "publishing/_quarto.yml")
            self.assertEqual(quarto["book"]["title"], IDENTITY["title"])
            self.assertEqual(quarto["book"]["author"], IDENTITY["author"])

            metadata = _load(book / "publishing/metadata.yaml")
            self.assertEqual(metadata["version"], "0.1.0")
            self.assertEqual(metadata["status"], "Draft")

            self.assertIn(IDENTITY["author"], (book / "NOTICE.md").read_text(encoding="utf-8"))
            self.assertIn(IDENTITY["author"], (book / "LICENSE-CODE").read_text(encoding="utf-8"))
            self.assertTrue(
                (book / "README.md").read_text(encoding="utf-8").startswith(
                    f"# {IDENTITY['title']}\n"
                )
            )

            validation = _run(
                [
                    sys.executable,
                    "-m",
                    "handbook_toolkit",
                    "--root",
                    str(book),
                    "validate-book",
                    "--full",
                ],
                book,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr or validation.stdout)

            second = _initialize(book)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already initialized", second.stderr)

    def test_rejects_invalid_input_without_writing(self) -> None:
        cases = {
            "bad id": dict(IDENTITY, id="Bad_Id"),
            "bad category": dict(IDENTITY, category="astronomy"),
            "long summary": dict(IDENTITY, summary="x" * 281),
            "empty title": dict(IDENTITY, title="   "),
            "bad repository": dict(IDENTITY, **{"repository-url": "git://example/copied-book"}),
        }
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp), replace=False)
            original = (book / "book.yaml").read_bytes()
            for label, identity in cases.items():
                with self.subTest(label):
                    result = _initialize(book, identity)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("initialize-book:", result.stderr)
                    self.assertEqual((book / "book.yaml").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
