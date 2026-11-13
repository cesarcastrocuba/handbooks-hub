"""Template 1.1 copy, check, workflow and onboarding regression.

The fast test copies the template outside the hub, replaces its identifiers, installs
nothing from the hub checkout and runs the template's own ``make check``. The build test
additionally runs a real seven-file build when Quarto and ``pdfinfo`` are available. The
workflow tests pin every action to a full commit SHA already used by the hub and forbid expression
interpolation inside shell scripts. The onboarding tests run the book-owned ``initialize_book.py``
on a copy.
"""

from __future__ import annotations

from copy import deepcopy
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
import zipfile

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from handbook_toolkit import __version__

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
    "book.md",
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


def _copy_template(root: Path, replace: bool = True, toolkit_version: str | None = None) -> Path:
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
    if toolkit_version is not None:
        # This gate exercises the PR builder; the released-template pin has its
        # own install boundary and advances only in the coordinator's release PR.
        descriptor = book / "book.yaml"
        document = _load(descriptor)
        document["toolkit"] = toolkit_version
        descriptor.write_text(yaml.safe_dump(document, sort_keys=False))
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


def _default_build_output(book: Path) -> Path:
    """Return the output path the Makefile uses when ``OUTPUT`` is not overridden."""

    result = _run(["make", "-n", "build"], book)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    match = re.search(r"--output\s+(\S+)", result.stdout)
    if match is None:
        raise AssertionError(f"make -n build printed no --output: {result.stdout}")
    return (book / match.group(1)).resolve()


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
        self.assertEqual(descriptor["toolkit"], "0.9.1")
        self.assertRegex(descriptor["toolkit"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(descriptor["profile"]["version"], r"^\d+\.\d+\.\d+$")
        requirements = (TEMPLATE / "requirements.txt").read_text(encoding="utf-8")
        self.assertRegex(requirements, r"@[0-9a-f]{40}#subdirectory=tools")
        for name in ("LICENSE", "LICENSE-CODE", "NOTICE.md", "Makefile", "publishing/_quarto.yml"):
            self.assertTrue((TEMPLATE / name).is_file(), name)
        for name in (".gitignore", "docs/AUTHOR_QUICKSTART.md"):
            self.assertTrue((TEMPLATE / name).is_file(), name)

    def test_default_build_output_is_outside_the_book(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp))
            output = _default_build_output(book)
            self.assertNotEqual(output, book.resolve())
            self.assertNotIn(book.resolve(), output.parents)
            self.assertEqual(output.name, "dist")

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for the real build")
    def test_copied_template_builds_with_default_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book = _copy_template(root, toolkit_version=__version__)

            result = _run(["make", "build"], book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            output = root / "dist"
            self.assertEqual({path.name for path in output.iterdir()}, PAYLOADS)

    @unittest.skipUnless(BUILD_AVAILABLE, "Quarto and pdfinfo are required for the real build")
    def test_copied_template_builds_seven_verified_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            book = _copy_template(root, toolkit_version=__version__)
            output = root / "dist"

            result = _run(["make", "build", f"OUTPUT={output}"], book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual({path.name for path in output.iterdir()}, PAYLOADS)

            with zipfile.ZipFile(output / "book-html.zip") as archive:
                names = set(archive.namelist())
            self.assertIn(".handbook-render/fonts/source-sans3/OFL.txt", names)
            self.assertIn(".handbook-render/fonts/source-serif4/OFL.txt", names)

            manifest = json.loads((output / "publication-manifest.json").read_text())
            self.assertEqual(manifest["book"]["commit"], _git(book, "rev-parse", "HEAD"))
            self.assertEqual(manifest["book"]["version"], "0.1.0-preview")
            self.assertEqual(manifest["schema_version"], "1.1")
            self.assertEqual(
                {entry["role"] for entry in manifest["artifacts"]},
                {"html", "pdf", "docx", "markdown", "source"},
            )
            markdown = (output / "book.md").read_text(encoding="utf-8")
            self.assertIn("| Version | 0.1.0-preview |", markdown)
            self.assertIn(f"| Commit | {_git(book, 'rev-parse', 'HEAD')} |", markdown)
            self.assertIn("Example Chapter", markdown)

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

    def test_workflow_level_permissions_are_read_only(self) -> None:
        for path in sorted(TEMPLATE_WORKFLOWS.glob("*.yml")):
            self.assertEqual(_load(path)["permissions"], {"contents": "read"}, path.name)

    def test_triggers_and_permissions(self) -> None:
        ci = _load(TEMPLATE_WORKFLOWS / "ci.yml")
        self.assertIn("push", _triggers(ci))
        self.assertIn("pull_request", _triggers(ci))
        self.assertEqual(ci["jobs"]["check"]["permissions"], {"contents": "read"})

        release = _load(TEMPLATE_WORKFLOWS / "release.yml")
        self.assertEqual(set(_triggers(release)), {"workflow_dispatch"})
        self.assertIs(_triggers(release)["workflow_dispatch"]["inputs"]["version"]["required"], True)
        self.assertEqual(
            release["jobs"]["build"]["permissions"],
            {"contents": "write", "pages": "read"},
        )
        self.assertEqual(
            release["jobs"]["deploy"]["permissions"],
            {"pages": "write", "id-token": "write"},
        )

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
        self.assertEqual(initialize["jobs"]["initialize"]["permissions"], {"contents": "write"})

    def test_no_git_network_command_runs_without_credentials(self) -> None:
        # A checkout with persist-credentials: false leaves no credential helper. Any later
        # `git fetch` or `git push` in the same job would fail on a private repository, so it must
        # authenticate explicitly. initialize-book.yml keeps the checkout credentials and pushes.
        for path in sorted(TEMPLATE_WORKFLOWS.glob("*.yml")):
            document = _load(path)
            for job in document.get("jobs", {}).values():
                without_credentials = False
                for step in job.get("steps", []):
                    uses = step.get("uses", "")
                    if uses.startswith("actions/checkout@"):
                        without_credentials = (
                            step.get("with", {}).get("persist-credentials") is False
                        )
                    script = step.get("run", "")
                    for command in ("git fetch", "git push"):
                        if command not in script or not without_credentials:
                            continue
                        env = step.get("env", {})
                        authenticated = any(
                            "token" in key.lower() or "TOKEN" in str(value)
                            for key, value in env.items()
                        )
                        self.assertTrue(
                            authenticated,
                            f"{path.name}: {command!r} after a credential-less checkout",
                        )

    def test_release_checks_tags_through_the_api(self) -> None:
        release = (TEMPLATE_WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        self.assertNotIn("git fetch", release)
        self.assertIn(
            'gh api "repos/$GITHUB_REPOSITORY/git/ref/tags/$TAG"', release
        )

    def test_release_is_published_only_after_the_pages_artifact(self) -> None:
        release = _load(TEMPLATE_WORKFLOWS / "release.yml")
        names = [step.get("name", "") for step in release["jobs"]["build"]["steps"]]
        self.assertLess(
            names.index("Upload the Pages artifact"),
            names.index("Publish every verified file to the release"),
        )

    def test_reader_navigation_and_issue_forms(self) -> None:
        quarto = yaml.safe_load((TEMPLATE / "publishing/_quarto.yml").read_text(encoding="utf-8"))
        book = quarto["book"]
        self.assertTrue(book["search"])
        self.assertEqual(book["repo-url"], "https://github.com/OWNER/REPOSITORY")
        self.assertEqual(book["repo-actions"], ["issue"])
        self.assertEqual(book["navbar"]["right"][0]["href"],
                         "https://cesarcastrocuba.github.io/handbooks-hub/")
        self.assertEqual(
            book["navbar"]["right"][1]["href"],
            "https://github.com/OWNER/REPOSITORY/tree/main/manuscript",
        )
        self.assertEqual(
            quarto["format"]["html"]["theme"], {"light": "cosmo", "dark": "darkly"}
        )
        self.assertTrue(quarto["format"]["html"]["respect-user-color-scheme"])
        for name, title in (
            ("content-correction.yml", "Content correction"),
            ("content-proposal.yml", "Content proposal"),
        ):
            with self.subTest(form=name):
                form = yaml.safe_load(
                    (TEMPLATE / ".github/ISSUE_TEMPLATE" / name).read_text(encoding="utf-8")
                )
                self.assertEqual(form["name"], title)
                self.assertTrue(form["body"])


class InitializeBookTests(unittest.TestCase):
    def assert_only_these_lines_changed(
        self, before: str, after: str, prefixes: tuple[str, ...]
    ) -> None:
        before_lines = before.splitlines()
        after_lines = after.splitlines()
        self.assertEqual(len(before_lines), len(after_lines))
        for old, new in zip(before_lines, after_lines):
            if old == new:
                continue
            self.assertTrue(
                any(old.startswith(prefix) for prefix in prefixes),
                f"unexpected line changed: {old!r} -> {new!r}",
            )

    def test_initialization_preserves_comments_and_quoting(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp), replace=False)
            names = ("book.yaml", "publishing/_quarto.yml", "publishing/metadata.yaml")
            originals = {name: (book / name).read_text(encoding="utf-8") for name in names}

            result = _initialize(book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            self.assert_only_these_lines_changed(
                originals["book.yaml"],
                (book / "book.yaml").read_text(encoding="utf-8"),
                ("id:", "title:", "  slug:", "  summary:", "    - ", "  url:"),
            )
            self.assert_only_these_lines_changed(
                originals["publishing/_quarto.yml"],
                (book / "publishing/_quarto.yml").read_text(encoding="utf-8"),
                ("  title:", "  author:", "  repo-url:", "        href:"),
            )
            self.assert_only_these_lines_changed(
                originals["publishing/metadata.yaml"],
                (book / "publishing/metadata.yaml").read_text(encoding="utf-8"),
                ("version:", "status:"),
            )

            descriptor = (book / "book.yaml").read_text(encoding="utf-8")
            for line in (
                "# Book descriptor. Replace the identifiers and summary before the first commit.",
                "# Keep toolkit and profile versions exact: ranges are rejected by the schema.",
                'schema_version: "1.0"',
                'toolkit: "0.9.1"',
                'version: "1.0.0"',
                "default_branch: main",
            ):
                self.assertIn(line, descriptor)
            metadata = (book / "publishing/metadata.yaml").read_text(encoding="utf-8")
            self.assertIn("# Provisional publication metadata. Replace identifiers before release.", metadata)
            self.assertIn('language: "en"', metadata)
            self.assertIn(
                'date: "2026-11-06"',
                (book / "publishing/_quarto.yml").read_text(encoding="utf-8"),
            )

    def test_awkward_values_round_trip_and_leave_unrelated_keys(self) -> None:
        identity = {
            "id": "awkward-book",
            "title": 'A: "double" \'single\' #hash — Ünïcode  ',
            "author": '  Zoë O\'Brien: #1 "Author"  ',
            "summary": "  A: summary # with 'single', \"double\", ünïcode.  ",
            "category": "engineering",
            "repository-url": "https://github.com/example/awkward-book",
        }
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp), replace=False)
            before_book = _load(book / "book.yaml")
            before_quarto = _load(book / "publishing/_quarto.yml")
            before_metadata = _load(book / "publishing/metadata.yaml")

            result = _initialize(book, identity)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            after_book = _load(book / "book.yaml")
            after_quarto = _load(book / "publishing/_quarto.yml")
            after_metadata = _load(book / "publishing/metadata.yaml")

            expected_book = deepcopy(before_book)
            expected_book["id"] = identity["id"]
            expected_book["title"] = identity["title"]
            expected_book["catalog"]["slug"] = identity["id"]
            expected_book["catalog"]["summary"] = identity["summary"]
            expected_book["catalog"]["categories"] = [identity["category"]]
            expected_book["repository"]["url"] = identity["repository-url"]
            self.assertEqual(after_book, expected_book)

            expected_quarto = deepcopy(before_quarto)
            expected_quarto["book"]["title"] = identity["title"]
            expected_quarto["book"]["author"] = identity["author"]
            expected_quarto["book"]["repo-url"] = identity["repository-url"]
            for item in expected_quarto["book"]["navbar"]["right"]:
                if item.get("href", "").startswith("https://github.com/OWNER/REPOSITORY"):
                    item["href"] = item["href"].replace(
                        "https://github.com/OWNER/REPOSITORY", identity["repository-url"]
                    )
            self.assertEqual(after_quarto, expected_quarto)

            expected_metadata = deepcopy(before_metadata)
            expected_metadata["version"] = "0.1.0"
            expected_metadata["status"] = "Draft"
            self.assertEqual(after_metadata, expected_metadata)

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
            self.assertEqual(quarto["book"]["repo-url"], IDENTITY["repository-url"])
            self.assertTrue(quarto["book"]["search"])
            self.assertEqual(
                quarto["book"]["navbar"]["right"][1]["href"],
                f"{IDENTITY['repository-url']}/tree/main/manuscript",
            )
            self.assertEqual(
                quarto["book"]["navbar"]["right"][2]["href"],
                f"{IDENTITY['repository-url']}/releases",
            )
            self.assertTrue(quarto["format"]["html"]["respect-user-color-scheme"])

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
