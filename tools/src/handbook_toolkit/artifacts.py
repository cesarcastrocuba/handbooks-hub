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
import zlib

import yaml

from .books import READING_KEYS
from .validation import Issue, load_packaged_schema, schema_issues

MAX_MEMBERS = 20000
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_MEMBER_BYTES = 128 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1000
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)*?\1")
CONTROL_TABLE = "| Field | Value |"
VERSION_ROW = re.compile(r"^\| Version \| (.+?) \|\s*$", re.MULTILINE)
COMMIT_ROW = re.compile(r"^\| Commit \| ([0-9a-f]{40}) \|\s*$", re.MULTILINE)


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
    members = archive.infolist()
    if len(members) > MAX_MEMBERS or sum(info.file_size for info in members) > MAX_TOTAL_BYTES:
        raise ValueError("archive exceeds member-count or uncompressed-size limit")
    for info in members:
        if info.flag_bits & 1:
            raise ValueError("encrypted archive members are not supported")
        if info.file_size > MAX_MEMBER_BYTES or (
            info.file_size > max(info.compress_size, 1) * MAX_COMPRESSION_RATIO
        ):
            raise ValueError("archive member exceeds size or compression-ratio limit")
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


def _source(archive: ZipFile, names: set[str], commit: str | None) -> None:
    required = {"book.yaml", "LICENSE", "LICENSE-CODE", "NOTICE.md"}
    if not required <= names:
        raise ValueError("source bundle lacks descriptor or licenses/notices")
    if any(part in {".git", ".venv", "node_modules", ".quarto", "__pycache__", ".pytest_cache"}
           for name in names for part in PurePosixPath(name).parts):
        raise ValueError("source bundle contains repository metadata or dependency caches")
    if not commit or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("source inspection requires the expected full commit SHA")
    if archive.comment.decode("ascii") != commit:
        raise ValueError("source archive commit comment differs from expected source commit")
    descriptor = yaml.safe_load(archive.read("book.yaml"))
    if schema_issues(descriptor, load_packaged_schema("book.schema.json"), "book.yaml"):
        raise ValueError("source bundle has an invalid book descriptor")
    reading_path = posixpath.normpath(descriptor["manuscript"]["reading_order"])
    if reading_path not in names:
        raise ValueError("source bundle lacks the declared reading-order file")
    reading = yaml.safe_load(archive.read(reading_path))
    if not isinstance(reading, dict) or set(reading) - set(READING_KEYS):
        raise ValueError("source reading order must contain known manuscript groups")
    if not isinstance(reading.get("chapters"), list) or not reading["chapters"]:
        raise ValueError("source reading order must list at least one chapter")
    root = posixpath.normpath(descriptor["manuscript"]["root"])
    listed = []
    for group in READING_KEYS:
        entries = reading.get(group, [])
        if entries is None:
            continue
        if not isinstance(entries, list):
            raise ValueError("source reading-order groups must be lists")
        for entry in entries:
            if (not isinstance(entry, str) or not entry.endswith(".qmd") or
                    PurePosixPath(entry).is_absolute() or ".." in PurePosixPath(entry).parts or
                    "\\" in entry or ":" in entry):
                raise ValueError("source reading order has an unsafe or non-Quarto path")
            listed.append(posixpath.normpath(posixpath.join(root, entry)))
    prefix = "" if root == "." else root + "/"
    discovered = {name for name in names if name.startswith(prefix) and name.endswith(".qmd")}
    if len(set(listed)) != len(listed) or set(listed) != discovered:
        raise ValueError("source reading order must cover every canonical manuscript exactly once")


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


def _prose_contains(text: str, needle: str) -> bool:
    """Return True when *needle* appears outside fenced code blocks and inline code spans.

    A handbook may legitimately show ``<script>`` inside a code example. Only prose that
    would render as raw HTML in the Markdown edition is a defect.
    """

    fence: str | None = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token[0] * len(token)
            elif token.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue
        if needle in INLINE_CODE.sub("", line).lower():
            return True
    return False


def _markdown(path: Path, commit: str | None, version: str | None) -> None:
    """Check the single-file Markdown edition: header, identity and no raw prose script."""

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Markdown payload must be UTF-8") from exc
    if not text.strip():
        raise ValueError("Markdown payload is empty")
    if not text.lstrip().startswith("# "):
        raise ValueError("Markdown payload must open with a level-one heading")
    if CONTROL_TABLE not in text:
        raise ValueError("Markdown payload lacks the document-control table")
    declared = VERSION_ROW.search(text)
    if declared is None:
        raise ValueError("Markdown payload lacks the document-control version field")
    if version is not None and declared.group(1).strip() != version:
        raise ValueError("Markdown payload version differs from the publication manifest")
    commit_row = COMMIT_ROW.search(text)
    if commit_row is None:
        raise ValueError("Markdown payload lacks the document-control commit field")
    if commit is not None and commit_row.group(1) != commit:
        raise ValueError("Markdown payload commit differs from the publication manifest")
    if _prose_contains(text, "<script"):
        raise ValueError("Markdown payload must not contain raw HTML script in prose")


def inspect_payload(
    path: Path, role: str, *, source_commit: str | None = None, version: str | None = None
) -> list[Issue]:
    """Open PDF, DOCX, HTML/site ZIP, Markdown or source ZIP and report format failures.

    PDF inspection requires Poppler's pdfinfo. This inspects structure and local
    HTML targets; factual accuracy and visual layout still require human review.
    The Markdown check reads the document-control header and rejects raw scripts in prose;
    code examples may show any markup. ``version`` and ``source_commit`` compare its
    identity with an independently known publication, and the local build rejects leaks of
    its own absolute paths before the payload is written.
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
        elif role == "markdown":
            _markdown(path, source_commit, version)
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
                    _source(archive, names, source_commit)
        else:
            raise ValueError(f"unknown payload role: {role}")
    except (OSError, UnicodeError, ValueError, BadZipFile, ElementTree.ParseError,
            subprocess.SubprocessError, RuntimeError, NotImplementedError, zlib.error,
            yaml.YAMLError) as error:
        return [Issue(str(path), str(error))]
    return []
