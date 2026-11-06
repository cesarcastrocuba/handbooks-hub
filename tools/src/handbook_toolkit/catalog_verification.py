"""Online release gate: verify remote bytes before a catalog can be deployed."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import quote, urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile

from .artifacts import inspect_payload
from .catalog import validate_catalog
from .publication import CHECKSUMS, MANIFEST, verify_publication
from .validation import CheckResult, Issue, load_document, load_packaged_schema, schema_issues

MAX_DOWNLOAD = 512 * 1024 * 1024


def _download(url: str, destination: Path, limit: int) -> None:
    headers = {"User-Agent": "handbook-toolkit-release-verifier"}
    if urlsplit(url).hostname == "api.github.com":
        headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    request = Request(url, headers=headers)
    with urlopen(request, timeout=60) as response, destination.open("xb") as stream:
        size = 0
        while chunk := response.read(64 * 1024):
            size += len(chunk)
            if size > limit:
                raise ValueError("remote asset exceeds its allowed byte limit")
            stream.write(chunk)


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
        if len(set(names)) != 4 or {MANIFEST, CHECKSUMS} & set(names):
            raise ValueError("remote manifest has duplicate or reserved payload names")
        expected = set(names) | {MANIFEST, CHECKSUMS}
        assets = published.get("assets", [])
        if not isinstance(assets, list) or len(assets) != 6 or not all(isinstance(asset, dict) for asset in assets) or {asset.get("name") for asset in assets} != expected:
            raise ValueError("release must contain exactly the six declared assets")
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
        except (OSError, ValueError, UnicodeError, KeyError, TypeError) as error:
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
