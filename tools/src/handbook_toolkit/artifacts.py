"""Inspect actual publication formats and create deterministic HTML archives."""

from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile, ZipInfo, ZIP_DEFLATED

from .validation import Issue


def archive_tree(source: Path, output: Path, epoch: int) -> None:
    """Archive regular files in sorted order with fixed timestamps and permissions."""
    source = source.resolve()
    output = output.resolve()
    if type(epoch) is not int or epoch < 0:
        raise ValueError("source epoch must be a nonnegative integer")
    if output == source or source in output.parents:
        raise ValueError("archive output must be outside its source tree")
    timestamp = datetime.fromtimestamp(max(epoch, 315532800), timezone.utc)
    stamp = (min(timestamp.year, 2107), timestamp.month, timestamp.day,
             timestamp.hour, timestamp.minute, timestamp.second)
    paths = sorted(source.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("archive inputs must not contain symlinks")
    files = [path for path in paths if path.is_file()]
    if not files:
        raise ValueError("cannot archive an empty source tree")
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for path in files:
            info = ZipInfo(path.relative_to(source).as_posix(), stamp)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


class _Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for field in ("id", "name" if tag == "a" else "id"):
            if values.get(field):
                self.ids.add(values[field])
        for field in ("href", "src"):
            if values.get(field):
                self.links.append(values[field])


def _zip_members(archive: ZipFile) -> set[str]:
    names: set[str] = set()
    for info in archive.infolist():
        name = info.filename
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
            raise ValueError(f"unsafe archive member: {name}")
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError(f"archive symlink is forbidden: {name}")
        if name in names:
            raise ValueError(f"duplicate archive member: {name}")
        names.add(name)
    bad = archive.testzip()
    if bad:
        raise ValueError(f"archive CRC failure: {bad}")
    return names


def _html(archive: ZipFile, names: set[str]) -> None:
    if "index.html" not in names:
        raise ValueError("HTML site archive must contain index.html at its root")
    pages = {name: _Page(archive.read(name).decode("utf-8"))
             for name in names if name.endswith(".html")}
    for name, page in sorted(pages.items()):
        for link in page.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            path = unquote(parsed.path)
            target = (posixpath.normpath(path.lstrip("/")) if path.startswith("/")
                      else posixpath.normpath(posixpath.join(posixpath.dirname(name), path))) if path else name
            if target == ".." or target.startswith("../"):
                raise ValueError(f"HTML link escapes site: {name} -> {link}")
            if path.endswith("/") or target == ".":
                target = posixpath.join(target, "index.html").removeprefix("./")
            if target not in names:
                raise ValueError(f"missing HTML link target: {name} -> {link}")
            if parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:
                raise ValueError(f"missing HTML fragment: {name} -> {link}")


def inspect_payload(path: Path, role: str, *, source_commit: str | None = None) -> list[Issue]:
    """Open PDF, DOCX, HTML/site ZIP or source ZIP and report format failures.

    PDF inspection requires Poppler's pdfinfo. This inspects structure and local
    HTML targets; factual accuracy and visual layout still require human review.
    """
    try:
        if path.is_symlink() or not path.is_file():
            raise ValueError("payload must be a regular file")
        if role == "pdf":
            with path.open("rb") as stream:
                if stream.read(5) != b"%PDF-":
                    raise ValueError("invalid PDF signature")
            result = subprocess.run(["pdfinfo", str(path.resolve())], capture_output=True,
                                    text=True, timeout=30)
            pages = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
            if result.returncode or not pages or int(pages[1]) < 1:
                raise ValueError("pdfinfo could not open a PDF with at least one page")
        elif role in {"html", "docx", "source"}:
            with ZipFile(path) as archive:
                names = _zip_members(archive)
                if role == "html":
                    _html(archive, names)
                elif role == "docx":
                    required = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
                    if not required <= names:
                        raise ValueError("DOCX is missing required package parts")
                    document = ElementTree.fromstring(archive.read("word/document.xml"))
                    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                    if document.tag != namespace + "document" or not any(
                        element.text and element.text.strip() for element in document.iter(namespace + "t")
                    ):
                        raise ValueError("DOCX has no Word document text")
                else:
                    required = {"book.yaml", "LICENSE", "LICENSE-CODE", "NOTICE.md"}
                    if not required <= names or not any(name.endswith(".qmd") for name in names):
                        raise ValueError("source bundle lacks canonical manuscript, descriptor or notices")
                    if any(part in {".git", ".venv", "node_modules"}
                           for name in names for part in PurePosixPath(name).parts):
                        raise ValueError("source bundle contains repository metadata or dependency caches")
                    if not source_commit or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
                        raise ValueError("source inspection requires the expected full commit SHA")
                    if archive.comment.decode("ascii") != source_commit:
                        raise ValueError("source archive commit comment differs from expected source commit")
        else:
            raise ValueError(f"unknown payload role: {role}")
    except (OSError, UnicodeError, ValueError, BadZipFile, ElementTree.ParseError,
            subprocess.SubprocessError) as error:
        return [Issue(str(path), str(error))]
    return []
