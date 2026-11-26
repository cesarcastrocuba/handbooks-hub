#!/usr/bin/env python3
"""Audit a published edition for split table bodies and heading/caption-only pages.

Reads the tagged Typst PDF and the HTML list of tables from one publication directory
(``book.pdf`` and ``book-html.zip``). A table is *split* when its body lands on more than one
page. A *orphan caption* is a caption whose pages are not all body pages of its table. A
*heading/caption-only page* has no body content other than headings or captions.

Usage::

    python3 tools/scripts/pdf_float_audit.py EDITION_DIRECTORY OUTPUT_JSON [--expect-clean]

``--expect-clean`` fails when any orphan caption or heading/caption-only page is found.
Requires qpdf 11 or later.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile


class Lists(HTMLParser):
    """Collect the text of every HTML list item (the list of tables)."""

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.items: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.stack.append("")

    def handle_endtag(self, tag):
        if tag == "li" and self.stack:
            self.items.append(self.stack.pop())

    def handle_data(self, data):
        for index in range(len(self.stack)):
            self.stack[index] += data


def inspect(directory: Path) -> dict:
    """Return table pages, orphan captions and heading/caption-only pages."""
    qpdf = json.loads(
        subprocess.check_output(["qpdf", "--json", str(directory / "book.pdf")])
    )
    objects = qpdf["qpdf"][1]
    page_order = {page["object"]: index for index, page in enumerate(qpdf["pages"], 1)}

    def resolve(value):
        return (
            objects["obj:" + value]["value"]
            if isinstance(value, str) and re.fullmatch(r"\d+ \d+ R", value)
            else value
        )

    def pages(value, page=None) -> set[int]:
        value = resolve(value)
        if isinstance(value, int):
            return {page_order[page]} if page in page_order else set()
        if isinstance(value, list):
            return set().union(*(pages(item, page) for item in value))
        if isinstance(value, dict):
            page = value.get("/Pg", page)
            return pages(value.get("/K", value.get("/MCID")), page)
        return set()

    roots = []
    for obj in objects.values():
        value = obj.get("value", {})
        if isinstance(value, dict) and value.get("/Type") == "/Catalog":
            roots.append(resolve(value["/StructTreeRoot"]))
    captions: dict[int, set[int]] = {}

    def data_tables(value) -> list[dict]:
        value = resolve(value)
        if isinstance(value, list):
            return [table for item in value for table in data_tables(item)]
        if not isinstance(value, dict):
            return []
        if value.get("/S") == "/Table":
            return [value]
        return data_tables(value.get("/K"))

    for obj in objects.values():
        value = obj.get("value")
        if isinstance(value, dict) and value.get("/S") == "/Caption":
            parent = resolve(value["/P"])
            if parent.get("/S") == "/Table":
                target = parent
            else:
                kids = parent.get("/K", [])
                kids = kids if isinstance(kids, list) else [kids]
                body = [item for item in kids if resolve(item) is not value]
                targets = data_tables(body)
                if not targets:
                    continue
                assert len(targets) == 1, targets
                target = targets[0]
            captions[id(target)] = pages(value)
    tables = []

    def visit(value):
        value = resolve(value)
        if isinstance(value, list):
            for item in value:
                visit(item)
        if not isinstance(value, dict):
            return
        if value.get("/S") == "/Table":
            kids = value.get("/K", [])
            kids = kids if isinstance(kids, list) else [kids]
            cap = [
                item
                for item in kids
                if isinstance(resolve(item), dict)
                and resolve(item).get("/S") == "/Caption"
            ]
            body = [item for item in kids if item not in cap]
            tables.append(
                {
                    "ordinal": len(tables) + 1,
                    "body_pages": sorted(pages(body, value.get("/Pg"))),
                    "caption_pages": sorted(
                        captions.get(id(value), pages(cap, value.get("/Pg")))
                    ),
                }
            )
        visit(value.get("/K"))

    assert roots, "PDF must have a semantic structure tree"
    for root in roots:
        visit(root)
    kinds = {page: set() for page in page_order.values()}

    def classify(value, page=None, kind="body"):
        value = resolve(value)
        if isinstance(value, int):
            if page in page_order:
                kinds[page_order[page]].add(kind)
        elif isinstance(value, list):
            for item in value:
                classify(item, page, kind)
        elif isinstance(value, dict):
            page = value.get("/Pg", page)
            role = value.get("/S")
            if role and re.fullmatch(r"/H[1-6]", role):
                kind = "heading"
            elif role == "/Caption":
                kind = "caption"
            classify(value.get("/K", value.get("/MCID")), page, kind)

    for root in roots:
        classify(root)
    only = {
        str(page): sorted(kind)
        for page, kind in kinds.items()
        if kind and kind <= {"heading", "caption"}
    }
    with ZipFile(directory / "book-html.zip") as archive:
        name = next((n for n in archive.namelist() if n == "tables.html"), None)
        labels: list[str] = []
        if name is not None:
            html = Lists()
            html.feed(archive.read(name).decode())
            labels = [
                match[1]
                for item in html.items
                if (match := re.match(r"^\s*Table\s+([A-Z0-9]+\.\d+)\b", item))
            ]
    captioned = [table for table in tables if table["caption_pages"]]
    if name is not None:
        assert len(captioned) == len(labels), (len(captioned), len(labels))
    else:
        labels = ["unlisted-" + str(table["ordinal"]) for table in captioned]
    for table, label in zip(captioned, labels):
        table["id"] = "Table " + label
    for table in tables:
        table.setdefault("id", "uncaptioned-" + str(table["ordinal"]))
        assert table["body_pages"], table
    split = [table for table in tables if len(table["body_pages"]) > 1]
    orphans = [
        table
        for table in captioned
        if not set(table["caption_pages"]) <= set(table["body_pages"])
    ]
    return {
        "all_tables": len(tables),
        "captioned_tables": len(captioned),
        "split_tables": split,
        "orphan_captions": orphans,
        "all_table_pages": tables,
        "pdf_pages": len(page_order),
        "heading_or_caption_only": only,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="publication directory")
    parser.add_argument("output", type=Path, help="JSON evidence file to write")
    parser.add_argument(
        "--expect-clean",
        action="store_true",
        help="fail on an orphan caption or a heading/caption-only page",
    )
    args = parser.parse_args(argv)
    result = inspect(args.directory)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in {"all_table_pages", "split_tables", "orphan_captions"}
            },
            indent=2,
        )
    )
    print(
        "split tables:",
        len(result["split_tables"]),
        "orphan captions:",
        len(result["orphan_captions"]),
    )
    if args.expect_clean:
        assert not result["orphan_captions"], result["orphan_captions"]
        assert not result["heading_or_caption_only"], result["heading_or_caption_only"]
    return 1 if result["orphan_captions"] or result["heading_or_caption_only"] else 0


if __name__ == "__main__":
    sys.exit(main())
