"""GitHub star counts, read once at build time and written into the page (issue 141).

Readers' browsers make no request to a third-party host: the count is part of the generated HTML.
The count comes from ``HANDBOOK_STAR_COUNTS`` (a JSON object ``{"owner/name": count}`` that a
release workflow fills with ``gh api``, so the build never holds a write token) or, when the build
is asked to (``HANDBOOK_STARS=fetch``, the portal workflow), from the GitHub API. Without either,
local builds, tests and reproducibility checks stay offline and byte-stable. Any failure gives ``None`` and the
page shows the star link without a number; it never fails the build.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
from html import escape
import json
import os
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

FETCH_VARIABLE = "HANDBOOK_STARS"
COUNTS_VARIABLE = "HANDBOOK_STAR_COUNTS"
API = "https://api.github.com/repos/"
TIMEOUT = 5
# A large catalog must not wait for one repository at a time; eight lookups in flight keeps a
# daily portal build short without opening an unbounded number of connections.
WORKERS = 8


class _NoRedirect(HTTPRedirectHandler):
    """Refuse redirects, so the token is only ever sent to api.github.com."""

    def redirect_request(self, *args, **kwargs):  # noqa: D401 - urllib hook
        return None


def _open(request: Request, timeout: float):
    return build_opener(_NoRedirect).open(request, timeout=timeout)


# One lookup per repository and build process: the daily portal build reads each count once.
_CACHE: dict[str, int | None] = {}


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
               opener: Callable | None = None) -> int | None:
    """Read ``stargazers_count`` of ``owner/name``; None when disabled or on any failure."""

    environ = os.environ if environ is None else environ
    if not repository:
        return None
    given = _given_count(repository, environ.get(COUNTS_VARIABLE))
    if given is not None or not fetch_enabled(environ):
        return given
    key = repository.casefold()
    if opener is None and key in _CACHE:
        return _CACHE[key]
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "handbook-toolkit"}
    token = environ.get("GITHUB_TOKEN") or environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with (opener or _open)(Request(API + repository, headers=headers), timeout=TIMEOUT) as response:
            count = _valid(json.load(response).get("stargazers_count"))
    except Exception:  # noqa: BLE001 - an unreachable API must never fail a build
        count = None
    if opener is None:
        _CACHE[key] = count
    return count


def prefetch_counts(repositories: Iterable[str | None], *,
                    environ: Mapping[str, str] | None = None,
                    workers: int = WORKERS,
                    opener: Callable | None = None) -> dict[str, int | None]:
    """Read distinct repositories concurrently, one lookup each, in the given order.

    The portal calls this before it renders cards, so a large catalog reads its counts in
    parallel instead of one request per book. Duplicates compare case-insensitively, and the
    returned mapping follows the first-seen order so a rebuild stays deterministic. A failed or
    slow lookup is still just ``None`` in that position (``star_count`` catches every error), so
    the page keeps its link without a number and the other lookups finish.
    """

    environ = os.environ if environ is None else environ
    if not fetch_enabled(environ):
        return {}
    unique: dict[str, str] = {}
    for repository in repositories:
        if repository:
            unique.setdefault(repository.casefold(), repository)
    if not unique:
        return {}
    ordered = list(unique.values())
    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(ordered)))) as pool:
        futures = {pool.submit(star_count, repository, environ=environ, opener=opener): repository
                   for repository in ordered}
        return {futures[future]: future.result() for future in futures}


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


def navbar_markup(count: int | None) -> str:
    """Navbar label with a class Quarto keeps, so CSS can size the star as a touch target.

    Quarto parses a navbar item's text as Markdown, so ``[text]{.star-link}`` becomes a span
    inside the link; the item itself cannot carry a class.
    """

    return f"[{navbar_text(count)}]{{.star-link}}"


def star_link(url: str, repository: str, count: int | None, *, css: str = "star") -> str:
    """A real link with the count baked in; the star glyph is hidden from assistive technology."""

    from .portal_markup import icon as svg
    icon = svg("star")
    number = "" if count is None else f'<span class="star-count">{compact(count)}</span>'
    return (f'<a class="{escape(css, quote=True)}" href="{escape(url, quote=True)}" '
            f'aria-label="{escape(label(repository, count), quote=True)}">'
            f'{icon}Star{number}</a>')
