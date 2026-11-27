"""Online release gate: verify remote bytes before a catalog can be deployed."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import ssl
import tempfile
import time
from urllib.parse import quote, urldefrag, urljoin, urlsplit
from zipfile import BadZipFile, ZipFile

import yaml

from .artifacts import inspect_payload
from .catalog import validate_catalog
from .publication import CHECKSUMS, MANIFEST, verify_publication
from .validation import CheckResult, Issue, load_document, load_packaged_schema, schema_issues

MAX_DOWNLOAD = 512 * 1024 * 1024
API_HOST = "api.github.com"
TOKEN_VARIABLE = "GITHUB_TOKEN"
RATE_LIMITED = {403, 429}
# Transient statuses from a non-API host. The API host retries every 5xx and 429.
RETRYABLE_FILE = {429, 500, 502, 503, 504}
RETRY_ATTEMPTS = 3
RETRY_AFTER_LIMIT = 30
_sleep = time.sleep
EXTRAS_ZIP = "book-extras.zip"
EXTRAS_SUMS = "EXTRAS-SHA256SUMS.txt"
EXTRAS = {EXTRAS_ZIP, EXTRAS_SUMS}
EXTRAS_SUMS_LIMIT = 64 * 1024


def _public_addresses(host: str) -> list[str]:
    addresses = sorted({entry[4][0] for entry in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
    if not addresses:
        raise ValueError("download host has no resolved addresses")
    for value in addresses:
        address = ipaddress.ip_address(value)
        if not address.is_global or address.is_multicast or address.is_reserved:
            raise ValueError("download destination must resolve only to public unicast addresses")
    return addresses


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to a checked IP while verifying the original hostname's certificate."""

    def __init__(self, host: str, address: str):
        super().__init__(host, port=443, timeout=30, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        transport = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(transport, server_hostname=self.host)
        except BaseException:
            transport.close()
            raise


def _request_headers(host: str) -> dict[str, str]:
    """Headers for one request. The token, when set, goes to the GitHub API host and nowhere else."""

    headers = {"User-Agent": "handbook-toolkit-release-verifier"}
    if host != API_HOST:
        return headers
    headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    token = os.environ.get(TOKEN_VARIABLE)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _failure(host: str, response: http.client.HTTPResponse) -> ValueError:
    message = f"remote asset returned HTTP {response.status} from {host}"
    if response.status in RATE_LIMITED and response.getheader("X-RateLimit-Remaining") == "0":
        message += (
            f": the GitHub API rate limit is exhausted; set {TOKEN_VARIABLE} to authenticate "
            "the requests"
        )
    return ValueError(message)


def _retryable(host: str, response: http.client.HTTPResponse) -> bool:
    if host == API_HOST:
        return response.status == 429 or 500 <= response.status <= 599
    return response.status in RETRYABLE_FILE


def _retry_delay(response: http.client.HTTPResponse, attempt: int) -> float:
    retry_after = response.getheader("Retry-After")
    if retry_after is not None and re.fullmatch(r"\d+", retry_after.strip()):
        return min(RETRY_AFTER_LIMIT, int(retry_after.strip()))
    return float(2 ** (attempt + 1))


def _connect(host: str, addresses: list[str]) -> _PinnedHTTPSConnection:
    for address in addresses:
        candidate = _PinnedHTTPSConnection(host, address)
        try:
            candidate.connect()
            return candidate
        except OSError:
            candidate.close()
    raise OSError("cannot connect to a verified public destination")


def _download(url: str, destination: Path, limit: int) -> None:
    hops = 0
    while True:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.port not in (None, 443):
            raise ValueError("downloads require HTTPS on the standard port")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("download URLs must not contain credentials")
        host = parsed.hostname.encode("idna").decode("ascii")
        addresses = _public_addresses(host)
        hops += 1
        if hops > 6:
            raise ValueError("download exceeded the redirect limit")
        target = quote(parsed.path or "/", safe="/%:@-._~!$&'()*+,;=")
        if parsed.query:
            target += "?" + quote(parsed.query, safe="=&%:+,;/?@-._~")
        attempts = 0
        while True:
            connection = _connect(host, addresses)
            try:
                connection.request("GET", target, headers=_request_headers(host))
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    location = response.getheader("Location")
                    if not location:
                        raise ValueError("redirect is missing its destination")
                    url = urljoin(url, location)
                    break  # the next target is resolved, checked and pinned again
                if response.status == 200:
                    with destination.open("xb") as stream:
                        size = 0
                        while chunk := response.read(64 * 1024):
                            size += len(chunk)
                            if size > limit:
                                raise ValueError("remote asset exceeds its allowed byte limit")
                            stream.write(chunk)
                    return
                if _retryable(host, response) and attempts < RETRY_ATTEMPTS:
                    _sleep(_retry_delay(response, attempts))
                    attempts += 1
                    continue
                raise _failure(host, response)
            finally:
                connection.close()


def _json(url: str) -> dict:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "response.json"
        _download(url, path, 2 * 1024 * 1024)
        result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("API response must be an object")
    return result


def _tag_commit(api: str, tag: str) -> str:
    target = _json(f"{api}/git/ref/tags/{quote(tag, safe='')}").get("object", {})
    for _ in range(6):
        if not isinstance(target, dict):
            raise ValueError("tag reference target must be an object")
        sha = target.get("sha", "")
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("tag does not resolve to a full commit SHA")
        if target.get("type") == "commit":
            return sha
        if target.get("type") != "tag":
            break
        target = _json(f"{api}/git/tags/{sha}").get("object", {})
    raise ValueError("tag does not resolve to a commit within the supported tag depth")



def _release_authors(source: Path) -> list[str]:
    """Return the ``author`` names stated by ``publishing/metadata.yaml`` in a source archive."""

    try:
        with ZipFile(source) as archive:
            try:
                payload = archive.read("publishing/metadata.yaml")
            except KeyError:
                raise ValueError(
                    "source archive has no publishing/metadata.yaml to check the catalog authors"
                ) from None
    except BadZipFile as exc:
        raise ValueError("source archive is not a valid ZIP archive") from exc
    try:
        document = yaml.safe_load(payload.decode("utf-8"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"publishing/metadata.yaml is not readable YAML: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("publishing/metadata.yaml must be a mapping")
    author = document.get("author")
    if isinstance(author, str):
        authors = [author]
    elif isinstance(author, list) and author and all(isinstance(name, str) for name in author):
        authors = list(author)
    else:
        raise ValueError("publishing/metadata.yaml must state an author name or a list of names")
    return [name.strip() for name in authors]


def _verify_authors(book: dict, entries: list[dict], root: Path) -> None:
    """The catalog authors must be the release's own author names."""

    expected = book.get("authors")
    if expected is None:
        return
    source = next((entry for entry in entries if entry["role"] == "source"), None)
    if source is None:
        raise ValueError("catalog authors cannot be verified: the release has no source payload")
    actual = _release_authors(root / source["path"])
    if actual != expected:
        raise ValueError(
            "catalog authors differ from publishing/metadata.yaml in the release source: "
            f"{expected!r} != {actual!r}"
        )


def _verify_book(book: dict) -> None:
    release = book["latest_release"]
    parsed = urlsplit(release["url"])
    parts = parsed.path.strip("/").split("/")
    if parsed.hostname != "github.com" or len(parts) != 5 or parts[2:4] != ["releases", "tag"]:
        raise ValueError("online release verification currently supports GitHub Releases URLs")
    owner, repository, _, _, tag = parts
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in (owner, repository)):
        raise ValueError("invalid GitHub repository path")
    if tag != release["tag"]:
        raise ValueError("release URL tag differs from catalog")
    prefix = f"https://github.com/{owner}/{repository}/releases/download/{tag}/"
    if release["manifest_url"] != prefix + MANIFEST or release["checksums_url"] != prefix + CHECKSUMS:
        raise ValueError("identity URLs must belong to the same exact release and canonical filenames")
    extras = release.get("extras")
    if extras is not None and (
        extras["archive"] != prefix + EXTRAS_ZIP
        or extras["checksums_url"] != prefix + EXTRAS_SUMS
    ):
        raise ValueError("catalog extras URLs must belong to the same exact release and canonical filenames")
    api = f"https://api.github.com/repos/{owner}/{repository}"
    published = _json(f"{api}/releases/tags/{quote(tag, safe='')}")
    if published.get("draft") is not False or published.get("prerelease") is not False or published.get("tag_name") != tag:
        raise ValueError("catalog requires a published stable release with the exact tag")
    if str(published.get("published_at", ""))[:10] != release["published_at"]:
        raise ValueError("release publication date differs from catalog")
    commit = _tag_commit(api, tag)
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder) / "assets"
        root.mkdir()
        _download(release["manifest_url"], root / MANIFEST, 2 * 1024 * 1024)
        document = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        if schema_issues(document, load_packaged_schema("publication-manifest.schema.json"), MANIFEST):
            raise ValueError("remote publication manifest is invalid")
        if document["book"] != {"id": book["id"], "version": release["version"], "commit": commit}:
            raise ValueError("manifest identity differs from catalog or resolved release tag")
        entries = document["artifacts"]
        names = [entry["path"] for entry in entries]
        if len(set(names)) != len(names) or {MANIFEST, CHECKSUMS} & set(names):
            raise ValueError("remote manifest has duplicate or reserved payload names")
        declared = {entry["role"]: prefix + entry["path"] for entry in entries}
        for role, url in release.get("assets", {}).items():
            if declared.get(role) != url:
                raise ValueError(f"catalog download link for {role} is not an artifact of the release manifest")
        expected = set(names) | {MANIFEST, CHECKSUMS}
        assets = published.get("assets", [])
        if not isinstance(assets, list) or not all(isinstance(asset, dict) for asset in assets):
            raise ValueError("release assets are malformed")
        asset_names = [asset.get("name") for asset in assets]
        if not all(isinstance(name, str) for name in asset_names) or len(set(asset_names)) != len(asset_names):
            raise ValueError("release assets have missing or duplicate names")
        present = set(asset_names)
        if present not in (expected, expected | EXTRAS):
            if present & EXTRAS and EXTRAS - present:
                raise ValueError(
                    "release extras must carry both book-extras.zip and EXTRAS-SHA256SUMS.txt"
                )
            raise ValueError(
                f"release must contain exactly the {len(expected)} declared assets, "
                "optionally with book-extras.zip and EXTRAS-SHA256SUMS.txt"
            )
        if extras is not None and not EXTRAS <= present:
            raise ValueError(
                "catalog lists extras but the release has no "
                "book-extras.zip and EXTRAS-SHA256SUMS.txt pair"
            )
        for asset in assets:
            if asset.get("state") != "uploaded" or asset.get("browser_download_url") != prefix + asset["name"]:
                raise ValueError("release asset is incomplete or has a mixed-release URL")
        if present != expected:
            _verify_extras(prefix, {asset["name"]: asset for asset in assets}, root.parent / "extras")
        _download(release["checksums_url"], root / CHECKSUMS, 2 * 1024 * 1024)
        for entry in entries:
            if entry["bytes"] > MAX_DOWNLOAD:
                raise ValueError("release payload exceeds the online verification size limit")
            _download(prefix + entry["path"], root / entry["path"], entry["bytes"])
        integrity = verify_publication(root)
        if not integrity.ok:
            raise ValueError("remote integrity failure: " + "; ".join(map(str, integrity.issues)))
        _verify_authors(book, entries, root)
        for entry in entries:
            issues = inspect_payload(
                root / entry["path"], entry["role"], source_commit=commit, build_invariants=False
            )
            if issues:
                raise ValueError("remote format failure: " + "; ".join(map(str, issues)))
        html = next(entry for entry in entries if entry["role"] == "html")
        reading_url = urldefrag(book["reading_url"])[0]
        if urlsplit(reading_url).path.endswith(".html"):
            base = urljoin(reading_url, "./")
        else:
            reading_url = reading_url.rstrip("/") + "/"
            base = reading_url
        with ZipFile(root / html["path"]) as archive:
            for index, member in enumerate(archive.infolist()):
                if member.is_dir():
                    continue
                url = reading_url if member.filename == "index.html" else urljoin(base, quote(member.filename, safe="/"))
                live = Path(folder) / f"live-{index}"
                _download(url, live, member.file_size)
                if hashlib.sha256(live.read_bytes()).digest() != hashlib.sha256(archive.read(member)).digest():
                    raise ValueError(f"live reading asset differs from released HTML: {member.filename}")


def _verify_extras(prefix: str, assets: dict[str, dict], directory: Path) -> None:
    """Verify the optional book-extras pair, never part of the catalog asset roles."""
    directory.mkdir(parents=True, exist_ok=True)
    archive = assets[EXTRAS_ZIP]
    size = archive.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError("book-extras.zip asset has no usable size")
    if size > MAX_DOWNLOAD:
        raise ValueError("book-extras.zip exceeds the online verification size limit")
    _download(prefix + EXTRAS_SUMS, directory / EXTRAS_SUMS, EXTRAS_SUMS_LIMIT)
    try:
        lines = (directory / EXTRAS_SUMS).read_text(encoding="utf-8").splitlines()
    except UnicodeError as exc:
        raise ValueError("EXTRAS-SHA256SUMS.txt is not UTF-8 text") from exc
    if len(lines) != 1:
        raise ValueError("EXTRAS-SHA256SUMS.txt must contain exactly one checksum line")
    match = re.fullmatch(r"([0-9a-f]{64}) [ *]book-extras\.zip", lines[0])
    if match is None:
        raise ValueError("EXTRAS-SHA256SUMS.txt must name book-extras.zip with its SHA-256")
    _download(prefix + EXTRAS_ZIP, directory / EXTRAS_ZIP, size)
    if hashlib.sha256((directory / EXTRAS_ZIP).read_bytes()).hexdigest() != match.group(1):
        raise ValueError("book-extras.zip checksum does not match EXTRAS-SHA256SUMS.txt")
    try:
        with ZipFile(directory / EXTRAS_ZIP) as bundle:
            if bundle.testzip() is not None:
                raise ValueError("book-extras.zip failed its archive integrity check")
            for member in bundle.infolist():
                name = member.filename
                path = PurePosixPath(name)
                if path.is_absolute() or re.match(r"^[A-Za-z]:", name) or ".." in path.parts:
                    raise ValueError(f"book-extras.zip contains an unsafe member path: {name}")
    except BadZipFile as exc:
        raise ValueError("book-extras.zip is not a valid ZIP archive") from exc


def verify_catalog_releases(catalog: Path) -> CheckResult:
    """Verify every catalog release; an empty catalog performs no network access."""
    checked = validate_catalog(catalog, load_packaged_schema("catalog.schema.json"))
    if not checked.ok:
        return checked
    issues = []
    for book in load_document(catalog)["books"]:
        try:
            _verify_book(book)
        except (OSError, ValueError, UnicodeError, KeyError, TypeError, http.client.HTTPException) as error:
            issues.append(Issue(book["id"], str(error)))
    return CheckResult("online catalog release verification", tuple(issues))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify catalog releases before portal deployment")
    parser.add_argument("catalog", type=Path)
    args = parser.parse_args()
    result = verify_catalog_releases(args.catalog)
    for issue in result.issues:
        print(issue)
    print("release verification: " + ("OK" if result.ok else "FAILED"))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
