"""Prepare cover, navigation and edition metadata for the native Quarto reading site."""
from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

import yaml

from .build_types import BuildError
from .print_layout import document_control_table, license_label
from . import design

PARTS = (("front", "Front matter"), ("chapters", "Chapters"),
         ("back", "Back matter"), ("appendices", "Appendices"), ("references", "References"))
EDITION_LABELS = {"pdf": "PDF", "html": "HTML", "docx": "Word", "markdown": "Markdown", "source": "Source"}


def _https(value: Any, field: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise BuildError(f"{field} must be an HTTPS URL")
    try:
        parts = urlsplit(value)
        _ = parts.port
    except ValueError as exc:
        raise BuildError(f"{field} must be a valid HTTPS URL") from exc
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or any(c.isspace() for c in value):
        raise BuildError(f"{field} must be an HTTPS URL without credentials")
    return value


def site_url(book: dict[str, Any], metadata: dict[str, Any], config: dict[str, Any]) -> str | None:
    """Prefer explicit publication URL; GitHub books use the pipeline's Pages convention."""
    explicit = metadata.get("site_url") or config.get("book", {}).get("site-url")
    if explicit:
        return _https(explicit, "site_url")
    repo = urlsplit(book.get("repository", {}).get("url") or "")
    parts = repo.path.strip("/").removesuffix(".git").split("/")
    if repo.hostname == "github.com" and len(parts) == 2 and all(parts) and not {"OWNER", "REPOSITORY"}.intersection(parts):
        owner, name = parts
        return f"https://{owner}.github.io/" + ("" if name.lower() == f"{owner.lower()}.github.io" else name + "/")
    return None


def _literal(value: Any) -> str:
    """Metadata is text; it cannot introduce Markdown, raw HTML or shortcodes."""
    text = str(value).replace("\n", " ").replace("\r", " ")
    punctuation = "[]{}*_`\\~#!|"
    return "".join(f"&#{ord(character)};" if character in punctuation else escape(character, quote=True)
                   for character in text)


def release_links(metadata: dict[str, Any], preview: bool) -> tuple[str | None, dict[str, str]]:
    """Only explicit, known publication URLs are offered; preview never implies a release."""
    if preview:
        return None, {}
    release = _https(metadata.get("release_url"), "release_url")
    urls = metadata.get("edition_urls") or {}
    if not isinstance(urls, dict):
        raise BuildError("edition_urls must map edition names to known HTTPS asset URLs")
    checked = {}
    for role, url in urls.items():
        if role not in EDITION_LABELS:
            raise BuildError(f"unknown edition_urls role: {role}")
        value = _https(url, "edition_urls." + role)
        if value:
            checked[role] = value
    return release, checked


def _write_cover(workspace: Path, book: dict[str, Any], metadata: dict[str, Any],
                 first_chapter: str, author: str, version: str, date: str,
                 status: str, license_text: str, downloads: dict[str, str]) -> None:
    front = {"title": "# " + book["title"] + " {.unnumbered}", "subtitle": str(metadata.get("subtitle") or ""),
             "author": author, "date": date, "numbered": False, "number-sections": False, "toc": False}
    lines = ["---", yaml.safe_dump(front, sort_keys=True).strip(), "---", "", "::: {.handbook-cover}",
             _literal(book["catalog"]["summary"]), "",
             f"**Edition {_literal(version)}** · {_literal(date)} · {_literal(status)}", "",
             _literal(license_text), "", "::: {.cover-actions}",
             f'<a class="btn btn-primary" href="{escape(quote(first_chapter.removesuffix(".qmd") + ".html", safe="/"), quote=True)}">Start reading</a>']
    for role, url in downloads.items():
        lines.append(f'<a class="btn btn-outline-primary" href="{escape(url, quote=True)}">{EDITION_LABELS[role]}</a>')
    lines += [":::", ":::", ""]
    (workspace / "index.qmd").write_text("\n".join(lines), encoding="utf-8")


def restore_first_source(workspace: Path, entries: list[str]) -> None:
    """Undo the print-only index alias before native web references are collected."""
    (workspace / entries[0]).write_text((workspace / "index.qmd").read_text(), encoding="utf-8")


def prepare_reading_site(workspace: Path, config: dict[str, Any], book: dict[str, Any],
                         metadata: dict[str, Any], groups: dict[str, list[str]],
                         entries: list[str], lists: list[str], fields: list[tuple[str, str]],
                         author: str, version: str, date: str, preview: bool) -> dict[str, Any]:
    """Switch only HTML staging to cover + original pages grouped as native parts."""
    config.pop("handbook-index-source-dir", None)
    front = list(groups["front"])
    has_control = any(any(line.lower().startswith("# document control")
                          for line in (workspace / entry).read_text().splitlines()) for entry in front)
    if not has_control:
        name = "document-control.qmd"
        if (workspace / name).exists():
            raise BuildError(f"generated control page would replace source file: {name}")
        (workspace / name).write_text("# Document Control {.unnumbered}\n\n" + document_control_table(fields), encoding="utf-8")
        front.insert(0, name)
    # The native lists follow Document Control, ahead of other front matter.
    front[1:1] = lists
    chapters: list[Any] = ["index.qmd"]
    for group, title in PARTS:
        files = front if group == "front" else groups[group]
        if files:
            chapters.append({"part": title, "chapters": files})
    license_text = license_label(book["license"]["content"])
    status = "Preview — not a released edition" if preview else str(metadata.get("status") or book["status"])
    release, downloads = release_links(metadata, preview)
    _write_cover(workspace, book, metadata, groups["chapters"][0], author, version, date,
                 status, license_text, downloads)
    bc = config["book"]
    bc["chapters"] = chapters
    bc["description"] = str(book["catalog"]["summary"])
    config["format"]["html"]["description-meta"] = bc["description"]
    bc["open-graph"] = True
    bc["twitter-card"] = {"card-style": "summary"}
    canonical = site_url(book, metadata, config)
    if canonical:
        bc["site-url"] = canonical
        config["format"]["html"]["canonical-url"] = True
    favicon = workspace / ".handbook-render/html/favicon.svg"
    favicon.write_text(design.favicon_svg(), encoding="utf-8")
    bc["favicon"] = favicon.relative_to(workspace).as_posix()
    footer = f"{_literal(book['title'])} · {_literal(version)} · {_literal(date)} · {_literal(license_text)}"
    if release:
        footer += f' · <a href="{escape(release, quote=True)}">Release</a>'
    bc["page-footer"] = {"center": footer}
    return config
