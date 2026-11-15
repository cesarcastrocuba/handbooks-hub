"""Check a deployed site from the outside: every local asset a page loads must be served.

A build can be complete on disk and still be published without some of its files; a host may
leave out hidden paths, for example. The pages then answer 200 and load without styles. This
check fetches each page as a reader's browser would and requests every stylesheet, script and
image it references on the same origin.

Usage::

    python3 -m handbook_toolkit.site_check URL [--page PATH ...] [--attempts N] [--wait SECONDS]
"""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ASSET_ATTRIBUTES = {"link": "href", "script": "src", "img": "src"}
LOOPBACK = {"127.0.0.1", "localhost"}
USER_AGENT = "handbook-toolkit-site-check"


class SiteCheckError(Exception):
    """The check itself could not run: a bad URL or a page that cannot be read."""


class _SameOriginRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if _origin(newurl) != _origin(request.full_url):
            raise HTTPError(newurl, code, "redirect to another origin", headers, fp)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


class _Assets(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attribute = ASSET_ATTRIBUTES.get(tag)
        value = dict(attrs).get(attribute) if attribute else None
        if value:
            self.targets.append(value)


def _origin(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    return parts.scheme, parts.netloc


def _require_allowed(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme == "https" and parts.hostname:
        return
    if parts.scheme == "http" and parts.hostname in LOOPBACK:
        return
    raise SiteCheckError(f"site URL must use HTTPS: {url}")


def _status(url: str, timeout: float) -> tuple[int, bytes]:
    opener = build_opener(_SameOriginRedirects)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, b""
    except (URLError, TimeoutError, OSError) as error:
        raise SiteCheckError(f"cannot reach {url}: {error}") from error


def local_assets(page_url: str, html: str) -> list[str]:
    """Absolute URLs of the stylesheets, scripts and images a page loads from its own origin."""

    parser = _Assets()
    parser.feed(html)
    found: list[str] = []
    for target in parser.targets:
        absolute = urldefrag(urljoin(page_url, target)).url
        if _origin(absolute) == _origin(page_url) and absolute not in found:
            found.append(absolute)
    return found


def missing_assets(base_url: str, pages: list[str], *, timeout: float = 20.0) -> tuple[int, list[str]]:
    """Return how many assets were requested and a line for each page or asset that is not served."""

    _require_allowed(base_url)
    base = base_url if base_url.endswith("/") else base_url + "/"
    requested: dict[str, int] = {}
    failures: list[str] = []
    for page in pages:
        page_url = urljoin(base, page)
        status, body = _status(page_url, timeout)
        if status != 200:
            failures.append(f"{status} {page_url}")
            continue
        for asset in local_assets(page_url, body.decode("utf-8", errors="replace")):
            if asset not in requested:
                requested[asset] = _status(asset, timeout)[0]
            if requested[asset] != 200:
                failures.append(f"{requested[asset]} {asset} (loaded by {page_url})")
    return len(requested), failures


def check_site(
    base_url: str, pages: list[str], *, attempts: int = 5, wait: float = 10.0, timeout: float = 20.0
) -> tuple[int, list[str]]:
    """Check the site, allowing a new deployment a bounded time to be served."""

    if attempts < 1:
        raise SiteCheckError("attempts must be at least 1")
    for attempt in range(1, attempts + 1):
        count, failures = missing_assets(base_url, pages, timeout=timeout)
        if not failures or attempt == attempts:
            return count, failures
        time.sleep(wait)
    raise AssertionError("unreachable")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that a deployed site serves every local asset its pages load.")
    parser.add_argument("url", help="base URL of the deployed site (HTTPS)")
    parser.add_argument("--page", action="append", default=[], help="page path to check besides the root; repeatable")
    parser.add_argument("--attempts", type=int, default=5, help="how many times to check before failing (default: 5)")
    parser.add_argument("--wait", type=float, default=10.0, help="seconds between attempts (default: 10)")
    args = parser.parse_args(argv)
    pages = ["", *args.page]
    try:
        count, failures = check_site(args.url, pages, attempts=args.attempts, wait=args.wait)
    except SiteCheckError as error:
        print(f"site-check: {error}", file=sys.stderr)
        return 2
    if failures:
        print("site-check: the deployed site does not serve everything its pages load:", file=sys.stderr)
        for failure in failures:
            print("  " + failure, file=sys.stderr)
        return 1
    print(f"site-check: {len(pages)} page(s), {count} asset(s), all 200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
