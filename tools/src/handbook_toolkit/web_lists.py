"""Generate native Quarto list pages before HTML rendering only."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
import re

from .indexes import LISTS
from .references import LABEL, _visible_lines
from .build_types import BuildError

PAGE_NAMES = {"tbl": "tables.qmd", "fig": "figures.qmd", "lst": "listings.qmd"}


def caption_references(text: str) -> list[tuple[str, str]]:
    """Reuse source-label parsing; code contents never declare captions."""
    result = []
    for _, line in _visible_lines(text, fence_attributes=True):
        for match in LABEL.finditer(line):
            label = match.group(1)
            if label.split("-", 1)[0] not in PAGE_NAMES:
                continue
            caption = line[:match.start()].strip()
            if caption.startswith("!["):
                caption = caption[2:].split("](", 1)[0]
            elif caption.startswith((":", "Table:")):
                caption = caption.removeprefix("Table:").lstrip(": ")
            else:
                listing = re.search(r'lst-cap=["\'](.*?)["\']', line)
                caption = listing.group(1) if listing else ""
            result.append((label, caption))
    return result


def generate_list_pages(workspace: Path, entries: list[str]) -> list[str]:
    """Generate nonempty registry lists; Quarto resolves numbers and destinations."""
    references = []
    for entry in entries:
        try:
            references.extend((label, caption, entry) for label, caption in caption_references((workspace / entry).read_text(encoding="utf-8")))
        except OSError as exc:
            raise BuildError(f"cannot collect caption references from {entry}: {exc}") from exc
    pages = []
    for kind, _, title, _ in LISTS:
        items = [(label, caption, entry) for label, caption, entry in references if label.startswith(kind + "-")]
        if not items:
            continue
        name = PAGE_NAMES[kind]
        page = workspace / name
        if page.exists():
            raise BuildError(f"generated list page would replace source file: {name}")
        body = [f"# {title} {{.unnumbered}}", "", "::: {.list-of-tables}"]
        for label, caption, entry in items:
            target = quote(entry, safe="/") + "#" + label
            caption = caption.replace("[", "\\[").replace("]", "\\]")
            m = re.match(r"^(tbl|fig)-(0|bm)-(\d+)$", label)
            if m:
                prefix = "Table" if m.group(1) == "tbl" else "Figure"
                group_pfx = "0" if m.group(2) == "0" else "BM"
                num_label = f"{prefix} {group_pfx}.{m.group(3)}"
                body.append(f"- [{num_label}](<{target}>)" + (f": [{caption}](<{target}>)" if caption else ""))
            else:
                body.append(f"- @{label}" + (f": [{caption}](<{target}>)" if caption else ""))
        body += [":::", ""]
        page.write_text("\n".join(body), encoding="utf-8")
        pages.append(name)
    return pages
