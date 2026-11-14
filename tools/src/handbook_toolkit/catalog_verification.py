"""Online release gate: verify remote bytes before a catalog can be deployed."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import ssl
import tempfile
from urllib.parse import quote, urldefrag, urljoin, urlsplit
from zipfile import ZipFile

from .artifacts import inspect_payload
from .catalog import validate_catalog
from .publication import CHECKSUMS, MANIFEST, verify_publication
from .validation import CheckResult, Issue, load_document, load_packaged_schema, schema_issues

MAX_DOWNLOAD = 512 * 1024 * 1024
API_HOST = "api.github.com"
TOKEN_VARIABLE = "GITHUB_TOKEN"
RATE_LIMITED = {403, 429}


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


def _download(url: str, destination: Path, limit: int) -> None:
    for _ in range(6):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.port not in (None, 443):
            raise ValueError("downloads require HTTPS on the standard port")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("download URLs must not contain credentials")
        host = parsed.hostname.encode("idna").decode("ascii")
        addresses = _public_addresses(host)
        connection = None
        for address in addresses:
            candidate = _PinnedHTTPSConnection(host, address)
            try:
                candidate.connect()
                connection = candidate
                break
            except OSError:
                candidate.close()
        if connection is None:
            raise OSError("cannot connect to a verified public destination")
        try:
            target = quote(parsed.path or "/", safe="/%:@-._~!$&'()*+,;=")
            if parsed.query:
                target += "?" + quote(parsed.query, safe="=&%:+,;/?@-._~")
            connection.request("GET", target, headers=_request_headers(host))
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location:
                    raise ValueError("redirect is missing its destination")
                url = urljoin(url, location)
                continue  # the next target is resolved, checked and pinned again
            if response.status != 200:
                raise _failure(host, response)
            with destination.open("xb") as stream:
                size = 0
                while chunk := response.read(64 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise ValueError("remote asset exceeds its allowed byte limit")
                    stream.write(chunk)
            return
        finally:
            connection.close()
    raise ValueError("download exceeded the redirect limit")


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
        if not isinstance(assets, list) or len(assets) != len(expected) or not all(isinstance(asset, dict) for asset in assets) or {asset.get("name") for asset in assets} != expected:
            raise ValueError(f"release must contain exactly the {len(expected)} declared assets")
        for asset in assets:
            if asset.get("state") != "uploaded" or asset.get("browser_download_url") != prefix + asset["name"]:
                raise ValueError("release asset is incomplete or has a mixed-release URL")
        _download(release["checksums_url"], root / CHECKSUMS, 2 * 1024 * 1024)
        for entry in entries:
            if entry["bytes"] > MAX_DOWNLOAD:
                raise ValueError("release payload exceeds the online verification size limit")
            _download(prefix + entry["path"], root / entry["path"], entry["bytes"])
        integrity = verify_publication(root)
        if not integrity.ok:
            raise ValueError("remote integrity failure: " + "; ".join(map(str, integrity.issues)))
        for entry in entries:
            issues = inspect_payload(root / entry["path"], entry["role"], source_commit=commit)
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
