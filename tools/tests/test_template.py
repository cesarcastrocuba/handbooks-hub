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
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402
from html_support import Document
from handbook_toolkit.docx_xml import W, fields
from handbook_toolkit.docx_validation import validate_docx
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

    def test_example_review_checklist_uses_neutral_role(self) -> None:
        source = (TEMPLATE / 'manuscript/chapters/01-example.qmd').read_text()
        opening = next(line for line in source.splitlines()
                       if line.startswith(':::') and 'title="Review Checklist — Example Chapter"' in line)
        classes = set(re.findall(r'\.([a-z-]+)', opening))
        self.assertIn('review', classes)
        self.assertIn('callout-note', classes)
        self.assertNotIn('callout-important', classes)

    def test_template_pins_are_exact_and_current(self) -> None:
        descriptor = _load(TEMPLATE / "book.yaml")
        self.assertEqual(descriptor["toolkit"], "0.14.2")
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

            result = _run(["make", "build", f"OUTPUT={output}",
                           "BUILD_FLAGS=--require-page-numbers" if os.environ.get("HANDBOOK_REQUIRE_PAGE_NUMBERS") else "BUILD_FLAGS="], book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual({path.name for path in output.iterdir()}, PAYLOADS)

            with zipfile.ZipFile(output / "book-html.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("handbook-render/fonts/source-sans3/OFL.txt", names)
            self.assertIn("handbook-render/fonts/source-serif4/OFL.txt", names)

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
            self.assertIn("An argument moves from scope and purpose", markdown)
            self.assertNotIn("![", markdown)
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                page = Document(archive.read("manuscript/chapters/01-example.html").decode()).root
                self.assertTrue(page.find("img"))
                alt = [image.attrs.get("alt") for image in page.find("img")]
                self.assertTrue(any(value and "Three connected boxes" in value for value in alt))
                figures = Document(archive.read("figures.html").decode()).root
                self.assertTrue(any("#fig-section-structure" in (link.attrs.get("href") or "") for link in figures.find("a")))
            with zipfile.ZipFile(output / "book-html.zip") as archive:
                chapter = Document(archive.read("manuscript/chapters/01-example.html").decode()).root
            review_boxes = [node for node in chapter.find('div')
                            if {'review', 'callout'} <= set((node.attrs.get('class') or '').split())]
            self.assertEqual(len(review_boxes), 1)
            self.assertIn('Review Checklist — Example Chapter', review_boxes[0].text())

            with zipfile.ZipFile(output / "book.docx") as archive:
                validate_docx(archive)
                document = ET.fromstring(archive.read("word/document.xml"))
                from handbook_toolkit import design
                review = next(node for node in document.iter(W + 'p')
                              if 'Review Checklist — Example Chapter' in ''.join(node.itertext()))
                self.assertEqual(review.find(W + 'pPr/' + W + 'pStyle').get(W + 'val'), 'CalloutReviewTitle')
                box = next(node for node in document.iter(W + 'tbl')
                           if review in list(node.iter(W + 'p')))
                cell = box.find(W + 'tr/' + W + 'tc')
                self.assertEqual(cell.find(W + 'tcPr/' + W + 'shd').get(W + 'fill'),
                                 design.docx_values()['callout_review_tint'].lstrip('#'))
                self.assertTrue(any(field.instruction == "TOC \\h \\z \\f F" for field in fields(document)))
                self.assertTrue(any(name.endswith(".svg") for name in archive.namelist()))
                # Change 0076: the figure is no longer inside Quarto's layout table; the
                # image paragraph and its caption are body blocks, so nothing styles them
                # as a data table and Word keeps the image with its caption.
                self.assertFalse([table for table in document.iter(W+"tbl") if table.find(".//"+W+"drawing") is not None])
                blocks = [node for node in document.find(W+"body") if node.tag == W+"p"]
                images = [i for i, p in enumerate(blocks) if p.find(".//"+W+"drawing") is not None]
                self.assertEqual(len(images), 1)
                image = blocks[images[0]]
                caption = blocks[images[0] + 1]
                self.assertEqual(caption.find(W+"pPr/"+W+"pStyle").get(W+"val"), "ImageCaption")
                self.assertIsNotNone(image.find(W+"pPr/"+W+"keepNext"))
                self.assertFalse(caption.findall(".//"+W+"b"))


            if PDFTOTEXT is not None:
                text = subprocess.check_output(
                    [PDFTOTEXT, str(output / "book.pdf"), "-"], text=True
                )
                self.assertIn("Example Chapter", text)
                self.assertIn("List of Figures", text)
                self.assertIn("An argument moves", text)


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

    def test_release_checks_the_actual_deployed_site_with_read_only_permissions(self) -> None:
        jobs = _load(TEMPLATE_WORKFLOWS / 'release.yml')['jobs']
        self.assertEqual(jobs['deploy']['outputs']['page_url'], '${{ steps.deployment.outputs.page_url }}')
        verify = jobs['verify']
        self.assertEqual(verify['needs'], 'deploy')
        self.assertEqual(verify['permissions'], {'contents': 'read'})
        checkout = next(step for step in verify['steps'] if step.get('uses', '').startswith('actions/checkout@'))
        self.assertIs(checkout['with']['persist-credentials'], False)
        install = next(step for step in verify['steps'] if 'pip install' in step.get('run', ''))
        self.assertIn('-r requirements.txt', install['run'])
        check = next(step for step in verify['steps'] if 'handbook_toolkit.site_check' in step.get('run', ''))
        self.assertEqual(check['env']['PAGE_URL'], '${{ needs.deploy.outputs.page_url }}')
        self.assertEqual(check['run'], 'python3 -m handbook_toolkit.site_check "$PAGE_URL"')

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

    def test_release_accepts_prerelease_versions(self) -> None:
        release_text = (TEMPLATE_WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        match = re.search(r"grep -Eq '([^']+)'", release_text)
        self.assertIsNotNone(match)
        pattern = re.compile(match.group(1))
        self.assertTrue(pattern.fullmatch("0.1.0"))
        self.assertTrue(pattern.fullmatch("3.1.0-rc.1"))
        self.assertTrue(pattern.fullmatch("3.1.0-rc.12"))
        self.assertIsNone(pattern.fullmatch("3.1.0-rc.0"))
        self.assertIsNone(pattern.fullmatch("3.1.0-rc"))
        self.assertIsNone(pattern.fullmatch("v3.1.0"))
        self.assertIsNone(pattern.fullmatch("3.1.0-beta"))
        self.assertIn("--prerelease --latest=false", release_text)

    def test_extra_release_assets_step_structure_and_order(self) -> None:
        release = _load(TEMPLATE_WORKFLOWS / "release.yml")
        steps = release["jobs"]["build"]["steps"]
        names = [step.get("name", "") for step in steps]
        self.assertIn("Build book-owned extra release assets (opt-in)", names)
        extra_idx = names.index("Build book-owned extra release assets (opt-in)")
        pages_idx = names.index("Upload the Pages artifact")
        publish_idx = names.index("Publish every verified file to the release")
        self.assertLess(pages_idx, extra_idx)
        self.assertLess(extra_idx, publish_idx)

        extra_step = steps[extra_idx]
        self.assertEqual(extra_step["env"]["EXTRA_ASSETS_DIR"], "${{ runner.temp }}/extra-assets")
        self.assertEqual(extra_step["env"]["RELEASE_DIR"], "${{ runner.temp }}/release")
        self.assertNotIn("${{", extra_step.get("run", ""))
        run_text = extra_step.get("run", "")
        self.assertIn('export PATH="$RUNNER_TEMP/toolkit-venv/bin:$PATH"', run_text)
        self.assertIn('PYTHON="$RUNNER_TEMP/toolkit-venv/bin/python"', run_text)
        self.assertIn('SOURCE_DATE_EPOCH="$(git log -1 --format=%ct "$SOURCE_COMMIT")"', run_text)
        self.assertIn("make -qp 2>/dev/null", run_text)
        self.assertIn("grep -q '^release-assets:'", run_text)
        val_step = next(s for s in steps if s.get("name") == "Validate the request")
        self.assertNotIn("SOURCE_DATE_EPOCH", val_step.get("run", ""))

    def test_release_workflow_no_expression_interpolated_into_shell(self) -> None:
        release = _load(TEMPLATE_WORKFLOWS / "release.yml")
        for job_name, job in release.get("jobs", {}).items():
            for step in job.get("steps", []):
                run = step.get("run", "")
                self.assertNotIn("${{", run, f"Step {step.get('name', 'unnamed')} in job {job_name} interpolates expression into shell")

    def test_extra_release_assets_opt_in_detection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mf_no = root / "Makefile.no"
            mf_no.write_text("check:\n\t@echo ok\n")
            p_no = subprocess.run(f"(make -f {mf_no} -qp 2>/dev/null || true) | grep -q '^release-assets:'", shell=True)
            self.assertNotEqual(p_no.returncode, 0)

            mf_yes = root / "Makefile.yes"
            mf_yes.write_text("release-assets:\n\t@echo ok\n")
            p_yes = subprocess.run(f"(make -f {mf_yes} -qp 2>/dev/null || true) | grep -q '^release-assets:'", shell=True)
            self.assertEqual(p_yes.returncode, 0)

    def test_extra_release_assets_script_validation(self) -> None:
        import textwrap
        release_text = (TEMPLATE_WORKFLOWS / "release.yml").read_text(encoding="utf-8")
        match = re.search(r"make release-assets.*?<<'PY'\n(.*?)\n\s*PY", release_text, re.DOTALL)
        self.assertIsNotNone(match)
        py_code = textwrap.dedent(match.group(1))

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            extra_dir = root / "extra"
            release_dir = root / "release"
            extra_dir.mkdir()
            release_dir.mkdir()

            env = os.environ.copy()
            env["EXTRA_ASSETS_DIR"] = str(extra_dir)
            env["RELEASE_DIR"] = str(release_dir)
            env["SOURCE_DATE_EPOCH"] = "1794765019"

            # 1. Empty extra dir should fail
            res = subprocess.run([sys.executable, "-c", py_code], env=env, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("no files", res.stderr)

            # 2. Subdirectory inside extra dir should fail
            (extra_dir / "subdir").mkdir()
            res = subprocess.run([sys.executable, "-c", py_code], env=env, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("regular file", res.stderr)
            (extra_dir / "subdir").rmdir()

            # 3. Invalid filename should fail
            (extra_dir / "bad name.txt").write_text("hello")
            res = subprocess.run([sys.executable, "-c", py_code], env=env, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("invalid extra release asset name", res.stderr)
            (extra_dir / "bad name.txt").unlink()

            # 4. Forbidden name collision should fail
            (extra_dir / "book.pdf").write_text("fake pdf")
            res = subprocess.run([sys.executable, "-c", py_code], env=env, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("collides with publication files", res.stderr)
            (extra_dir / "book.pdf").unlink()

            # 5. Oversized single file should fail (>10 MB)
            oversized = extra_dir / "big.bin"
            with open(oversized, "wb") as f:
                f.seek(10 * 1024 * 1024)
                f.write(b"X")
            res = subprocess.run([sys.executable, "-c", py_code], env=env, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("exceeds max file size", res.stderr)
            oversized.unlink()

            # 6. Valid files pack deterministically into book-extras.zip
            (extra_dir / "checklists.json").write_text('{"item": 1}')
            (extra_dir / "assessment.csv").write_text('id,score\n1,100\n')
            res = subprocess.run([sys.executable, "-c", py_code], env=env, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr)
            extras_zip = release_dir / "book-extras.zip"
            self.assertTrue(extras_zip.is_file())

            with zipfile.ZipFile(extras_zip) as z:
                self.assertEqual(z.namelist(), ["assessment.csv", "checklists.json"])
                info = z.getinfo("assessment.csv")
                self.assertEqual(info.date_time[:3], (2026, 11, 15))
                self.assertEqual(info.external_attr >> 16, 0o100644)

    def test_extra_release_assets_step_run_script_execution(self) -> None:
        release = _load(TEMPLATE_WORKFLOWS / "release.yml")
        steps = release["jobs"]["build"]["steps"]
        extra_step = next(s for s in steps if s.get("name") == "Build book-owned extra release assets (opt-in)")
        run_script = extra_step["run"]

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            book_dir = root / "book"
            book_dir.mkdir()
            subprocess.run(["git", "init"], cwd=book_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=book_dir, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=book_dir, check=True)
            (book_dir / "README.md").write_text("# Book\n")
            subprocess.run(["git", "add", "README.md"], cwd=book_dir, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=book_dir, check=True)

            runner_temp = root / "runner_temp"
            toolkit_venv = runner_temp / "toolkit-venv" / "bin"
            toolkit_venv.mkdir(parents=True)
            (toolkit_venv / "python").symlink_to(sys.executable)

            extra_assets = runner_temp / "extra-assets"
            release_dir = runner_temp / "release"
            release_dir.mkdir(parents=True)

            source_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=book_dir, check=True, capture_output=True, text=True
            ).stdout.strip()

            env = os.environ.copy()
            env["RUNNER_TEMP"] = str(runner_temp)
            env["EXTRA_ASSETS_DIR"] = str(extra_assets)
            env["RELEASE_DIR"] = str(release_dir)
            env["SOURCE_COMMIT"] = source_commit

            # Case A: Makefile has no release-assets target -> skips cleanly
            (book_dir / "Makefile").write_text("check:\n\t@echo ok\n")
            subprocess.run(["git", "add", "Makefile"], cwd=book_dir, check=True)
            subprocess.run(["git", "commit", "-m", "add makefile"], cwd=book_dir, check=True)
            source_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=book_dir, check=True, capture_output=True, text=True
            ).stdout.strip()
            env["SOURCE_COMMIT"] = source_commit

            res_skip = subprocess.run(["bash", "-c", run_script], cwd=book_dir, env=env, capture_output=True, text=True)
            self.assertEqual(res_skip.returncode, 0, res_skip.stderr)
            self.assertIn("No release-assets target found", res_skip.stdout)
            self.assertFalse((release_dir / "book-extras.zip").exists())

            # Case B: Makefile defines release-assets target -> executes, packages, checksums
            (book_dir / "Makefile").write_text(
                "release-assets:\n"
                "\t@mkdir -p \"$(RELEASE_ASSETS_DIR)\"\n"
                "\t@echo '{\"test\": true}' > \"$(RELEASE_ASSETS_DIR)/data.json\"\n"
            )
            subprocess.run(["git", "add", "Makefile"], cwd=book_dir, check=True)
            subprocess.run(["git", "commit", "-m", "update makefile"], cwd=book_dir, check=True)
            source_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=book_dir, check=True, capture_output=True, text=True
            ).stdout.strip()
            env["SOURCE_COMMIT"] = source_commit

            res_build = subprocess.run(["bash", "-c", run_script], cwd=book_dir, env=env, capture_output=True, text=True)
            self.assertEqual(res_build.returncode, 0, res_build.stderr)
            self.assertIn("Building book-owned extra release assets...", res_build.stdout)
            self.assertIn("packaged 1 extra release assets into book-extras.zip", res_build.stdout)
            extras_zip = release_dir / "book-extras.zip"
            checksum_file = release_dir / "EXTRAS-SHA256SUMS.txt"
            self.assertTrue(extras_zip.is_file())
            self.assertTrue(checksum_file.is_file())
            with zipfile.ZipFile(extras_zip) as z:
                self.assertEqual(z.namelist(), ["data.json"])
                self.assertEqual(z.read("data.json"), b'{"test": true}\n')
            chk_content = checksum_file.read_text(encoding="utf-8")
            self.assertIn("book-extras.zip", chk_content)

    def test_documentation_specifies_fast_checks_as_required_check(self) -> None:
        author_guide = (support.REPO_ROOT / "docs/author-guide.md").read_text(encoding="utf-8")
        self.assertIn("requires the `Fast checks` status check", author_guide)
        self.assertIn("wait for `Fast checks` and merge", author_guide)
        quickstart = (TEMPLATE / "docs/AUTHOR_QUICKSTART.md").read_text(encoding="utf-8")
        self.assertIn("require the `Fast checks` status check", quickstart)
        self.assertIn("wait for `Fast checks` to pass", quickstart)

    def test_catalog_refuses_prereleases(self) -> None:
        from handbook_toolkit.validation import load_packaged_schema
        schema = load_packaged_schema("catalog.schema.json")
        version_pattern = re.compile(
            schema["properties"]["books"]["items"]["properties"]["latest_release"]["properties"]["version"]["pattern"]
        )
        tag_pattern = re.compile(
            schema["properties"]["books"]["items"]["properties"]["latest_release"]["properties"]["tag"]["pattern"]
        )
        self.assertIsNone(version_pattern.fullmatch("3.1.0-rc.1"))
        self.assertIsNone(tag_pattern.fullmatch("v3.1.0-rc.1"))
        self.assertTrue(version_pattern.fullmatch("3.1.0"))
        self.assertTrue(tag_pattern.fullmatch("v3.1.0"))

    def test_manifest_schema_accepts_prerelease_version(self) -> None:
        from handbook_toolkit.validation import load_packaged_schema
        schema = load_packaged_schema("publication-manifest.schema.json")
        version_pattern = re.compile(
            schema["properties"]["book"]["properties"]["version"]["pattern"]
        )
        self.assertTrue(version_pattern.fullmatch("3.1.0-rc.1"))
        self.assertTrue(version_pattern.fullmatch("0.1.0"))

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
            quarto["format"]["html"]["theme"], {"light": "cosmo", "dark": "cosmo"}
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
                'toolkit: "0.14.2"',
                'version: "1.1.0"',
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
            readme = (book / "README.md").read_text(encoding="utf-8")
            self.assertTrue(readme.startswith(f"# {IDENTITY['title']}\n"))
            self.assertIn(IDENTITY["summary"], readme)
            self.assertIn("[`AGENTS.md`](AGENTS.md)", readme)
            self.assertIn("[`NOTICE.md`](NOTICE.md)", readme)
            self.assertIn("make check", readme)
            self.assertNotIn("A starting point for an independent handbook repository", readme)

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

    def test_initialization_includes_optional_project_status_and_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            book = _copy_template(Path(temp), replace=False)
            (book / "PROJECT_STATUS.md").write_text("# Project Status\n", encoding="utf-8")
            (book / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
            result = _initialize(book)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            readme = (book / "README.md").read_text(encoding="utf-8")
            self.assertIn("[`PROJECT_STATUS.md`](PROJECT_STATUS.md)", readme)
            self.assertIn("[`DECISIONS.md`](DECISIONS.md)", readme)

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
