#!/usr/bin/env python3
"""Build a non-release edition preview of one book, for review before anything is tagged.

The preview is what a reader would receive: the five payloads from ``build-book --preview``, the
reading site unpacked, the DOCX converted to PDF by LibreOffice (what a viewer other than Word
shows) and screenshots of the reading site in light and dark at desktop and phone width.

The LibreOffice conversion and the screenshots need tools that are not toolkit dependencies. They
are skipped with a recorded reason when the tool is absent, unless ``--require-tools`` is given.

Usage::

    python3 tools/scripts/edition_preview.py --repo BOOK_REPOSITORY --output DIR
    python3 tools/scripts/edition_preview.py --template --output DIR
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

import yaml

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import export_template  # noqa: E402

from handbook_toolkit.build import PAYLOADS, BuildError, build_book  # noqa: E402

PREVIEW_SUFFIX = "-preview"
VIEWPORTS = {"desktop": (1440, 1800), "phone": (390, 1800)}
COLOR_SCHEMES = ("light", "dark")
SUMMARY = "PREVIEW.md"


class PreviewError(Exception):
    """The preview could not be produced."""


@dataclass
class Preview:
    """What one preview run produced and what it had to skip."""

    output: Path
    commit: str
    version: str
    skipped: list[str] = field(default_factory=list)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise PreviewError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def preview_version(repo: Path) -> str:
    """Return the book version marked as a preview, so it cannot pass for a release."""

    path = repo / "publishing" / "metadata.yaml"
    try:
        metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PreviewError(f"cannot read {path}: {exc}") from exc
    version = metadata.get("version") if isinstance(metadata, dict) else None
    if not isinstance(version, str) or not version:
        raise PreviewError(f"{path} has no version")
    return version if "-" in version else version + PREVIEW_SUFFIX


def template_repository(root: Path) -> Path:
    """Export the tracked template into a new Git repository with one commit."""

    book = root / "template-book"
    export_template.export(book)
    _git(book, "init", "-q", "-b", "main")
    _git(book, "add", "-A")
    _git(
        book,
        "-c",
        "user.name=Edition preview",
        "-c",
        "user.email=preview@example.invalid",
        "commit",
        "-q",
        "-m",
        "template export for an edition preview",
    )
    return book


def select_pages(site: Path) -> list[Path]:
    """Choose the pages to capture: every top-level page and the largest page below it.

    The top level holds the first page and the generated lists. The largest remaining page is the
    one with the most content, so it shows the most components in one capture.
    """

    pages = sorted(site.glob("*.html"))
    nested = [path for path in site.rglob("*.html") if path.parent != site]
    if nested:
        pages.append(max(nested, key=lambda path: (path.stat().st_size, path.as_posix())))
    if not pages:
        raise PreviewError(f"the reading site has no HTML page: {site}")
    return pages


def screenshot_name(site: Path, page: Path, viewport: str, scheme: str) -> str:
    stem = page.relative_to(site).with_suffix("").as_posix().replace("/", "--")
    return f"{stem}.{viewport}.{scheme}.png"


def unpack_site(archive: Path, site: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(site)


def convert_with_libreoffice(docx: Path, directory: Path) -> None:
    """Convert the DOCX to PDF with LibreOffice, using a private profile directory."""

    directory.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as profile:
        result = subprocess.run(
            [
                "soffice",
                f"-env:UserInstallation={Path(profile).as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(directory),
                str(docx),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    converted = directory / (docx.stem + ".pdf")
    if result.returncode or not converted.is_file():
        raise PreviewError(f"LibreOffice conversion failed: {result.stderr.strip() or result.stdout.strip()}")
    converted.rename(directory / "book-docx-as-libreoffice.pdf")


def capture_screenshots(site: Path, pages: list[Path], directory: Path) -> None:
    from playwright.sync_api import sync_playwright

    directory.mkdir(parents=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for viewport, (width, height) in VIEWPORTS.items():
                for scheme in COLOR_SCHEMES:
                    context = browser.new_context(
                        viewport={"width": width, "height": height}, color_scheme=scheme
                    )
                    tab = context.new_page()
                    for page in pages:
                        tab.goto(page.as_uri(), wait_until="load")
                        tab.screenshot(path=str(directory / screenshot_name(site, page, viewport, scheme)))
                    context.close()
        finally:
            browser.close()


def _playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return True


def render_summary(preview: Preview) -> str:
    """Describe the preview: identity, every file with its size, and what was skipped."""

    lines = [
        "# Edition preview",
        "",
        f"- Source commit: `{preview.commit}`",
        f"- Version: `{preview.version}` (preview build, not a release)",
        "",
        "| File | Bytes |",
        "| --- | ---: |",
    ]
    files = sorted(
        path
        for path in preview.output.rglob("*")
        if path.is_file() and path.name != SUMMARY and path.relative_to(preview.output).parts[0] != "site"
    )
    lines += [f"| `{path.relative_to(preview.output).as_posix()}` | {path.stat().st_size} |" for path in files]
    pages = sum(1 for _ in (preview.output / "site").rglob("*.html"))
    lines += ["", f"The reading site is unpacked under `site/` ({pages} HTML pages)."]
    if preview.skipped:
        lines += ["", "## Not run", ""] + [f"- {reason}" for reason in preview.skipped]
    return "\n".join(lines) + "\n"


def build_preview(repo: Path, output: Path, *, quarto: str, require_tools: bool) -> Preview:
    repo = repo.resolve()
    output = output.resolve()
    if output.exists():
        raise PreviewError(f"output already exists: {output}")
    if _git(repo, "status", "--porcelain"):
        raise PreviewError(f"the book repository has uncommitted changes: {repo}")
    commit = _git(repo, "rev-parse", "HEAD")
    version = preview_version(repo)

    output.mkdir(parents=True)
    edition = output / "edition"
    try:
        build_book(repo, commit, edition, version=version, quarto=quarto, preview=True)
    except BuildError as exc:
        raise PreviewError(f"build-book failed: {exc}") from exc

    preview = Preview(output=output, commit=commit, version=version)
    site = output / "site"
    unpack_site(edition / PAYLOADS["html"], site)

    def skip(reason: str) -> None:
        if require_tools:
            raise PreviewError(reason)
        preview.skipped.append(reason)

    if shutil.which("soffice"):
        convert_with_libreoffice(edition / PAYLOADS["docx"], output / "libreoffice")
    else:
        skip("LibreOffice conversion: `soffice` is not installed")
    if _playwright_available():
        capture_screenshots(site, select_pages(site), output / "screenshots")
    else:
        skip("Screenshots: the `playwright` package is not installed")

    (output / SUMMARY).write_text(render_summary(preview), encoding="utf-8")
    return preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a non-release edition preview of one book.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo", help="book repository with a clean working tree")
    source.add_argument("--template", action="store_true", help="preview the hub's template book")
    parser.add_argument("--output", required=True, help="new output directory; must not exist")
    parser.add_argument("--quarto", default="quarto", help="Quarto executable (default: quarto)")
    parser.add_argument(
        "--require-tools",
        action="store_true",
        help="fail instead of skipping when LibreOffice or Playwright is missing",
    )
    args = parser.parse_args(argv)

    try:
        with tempfile.TemporaryDirectory() as temp:
            repo = template_repository(Path(temp)) if args.template else Path(args.repo)
            preview = build_preview(
                repo, Path(args.output), quarto=args.quarto, require_tools=args.require_tools
            )
    except PreviewError as exc:
        print(f"edition-preview: {exc}", file=sys.stderr)
        return 2
    print((preview.output / SUMMARY).read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
