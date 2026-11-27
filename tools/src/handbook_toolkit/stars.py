"""GitHub star counts, read once at build time and written into the page (issue 141).

Readers' browsers make no request to a third-party host: the count is part of the generated HTML.
The count comes from ``HANDBOOK_STAR_COUNTS`` (a JSON object ``{"owner/name": count}`` that a
release workflow fills with ``gh api``, so the build never holds a write token) or, when the build
is asked to (``HANDBOOK_STARS=fetch``, the portal workflow), from the GitHub API. Without either,
local builds, tests and reproducibility checks stay offline and byte-stable. Any failure gives ``None`` and the
page shows the star link without a number; it never fails the build.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from html import escape
import json
import os
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

FETCH_VARIABLE = "HANDBOOK_STARS"
COUNTS_VARIABLE = "HANDBOOK_STAR_COUNTS"
API = "https://api.github.com/repos/"
TIMEOUT = 10


def github_repository(url: str | None) -> str | None:
    """Return ``owner/name`` for an https GitHub repository URL, else None."""

    if not url:
        return None
    parts = urlsplit(str(url))
    if parts.scheme != "https" or parts.hostname != "github.com":
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if len(segments) < 2 or "OWNER" in segments[:2]:
        return None
    name = segments[1].removesuffix(".git")
    return f"{segments[0]}/{name}"


def fetch_enabled(environ: Mapping[str, str] | None = None) -> bool:
    return (os.environ if environ is None else environ).get(FETCH_VARIABLE) == "fetch"


def star_count(repository: str | None, *, environ: Mapping[str, str] | None = None,
               opener: Callable = urlopen) -> int | None:
    """Read ``stargazers_count`` of ``owner/name``; None when disabled or on any failure."""

    environ = os.environ if environ is None else environ
    if not repository:
        return None
    given = _given_count(repository, environ.get(COUNTS_VARIABLE))
    if given is not None or not fetch_enabled(environ):
        return given
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "handbook-toolkit"}
    token = environ.get("GITHUB_TOKEN") or environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with opener(Request(API + repository, headers=headers), timeout=TIMEOUT) as response:
            count = json.load(response).get("stargazers_count")
    except Exception:  # noqa: BLE001 - an unreachable API must never fail a build
        return None
    return _valid(count)


def _valid(count: object) -> int | None:
    return count if isinstance(count, int) and not isinstance(count, bool) and count >= 0 else None


def _given_count(repository: str, counts: str | None) -> int | None:
    if not counts:
        return None
    try:
        mapping = json.loads(counts)
    except ValueError:
        return None
    if not isinstance(mapping, dict):
        return None
    wanted = repository.casefold()
    return next((_valid(count) for name, count in mapping.items()
                 if isinstance(name, str) and name.casefold() == wanted), None)


def compact(count: int) -> str:
    """1234 -> "1.2k", 12000 -> "12k", as GitHub shows large counts."""

    if count < 1000:
        return str(count)
    if count < 10000:
        return f"{count / 1000:.1f}".rstrip("0").rstrip(".") + "k"
    return f"{count // 1000}k"


def label(repository: str, count: int | None) -> str:
    """Accessible name of a star link."""

    if count is None:
        return f"Star {repository} on GitHub"
    return f"Star {repository} on GitHub, {count} {'star' if count == 1 else 'stars'}"


def navbar_text(count: int | None) -> str:
    return "★ Star" if count is None else f"★ Star · {compact(count)}"


def star_link(url: str, repository: str, count: int | None, *, css: str = "star") -> str:
    """A real link with the count baked in; the star glyph is hidden from assistive technology."""

    from .portal_markup import icon as svg
    icon = svg("star")
    number = "" if count is None else f'<span class="star-count">{compact(count)}</span>'
    return (f'<a class="{escape(css, quote=True)}" href="{escape(url, quote=True)}" '
            f'aria-label="{escape(label(repository, count), quote=True)}">'
            f'{icon}Star{number}</a>')
