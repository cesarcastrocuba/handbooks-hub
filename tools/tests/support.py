"""Test helpers shared by the toolkit test modules."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import yaml

TOOLS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = TOOLS_ROOT / "src"
SCHEMAS = TOOLS_ROOT / "src" / "handbook_toolkit" / "schemas"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def write_yaml(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def catalog_document() -> dict:
    return {
        "schema_version": "1.0",
        "books": [
            {
                "id": "example-book",
                "slug": "example-book",
                "title": "Example Book",
                "summary": "An example book used by the toolkit tests.",
                "categories": ["authoring"],
                "status": "published",
                "latest_release": {
                    "version": "1.0.0",
                    "tag": "v1.0.0",
                    "url": "https://github.com/example/example-book/releases/tag/v1.0.0",
                    "published_at": "2026-12-01",
                    "manifest_url": "https://github.com/example/example-book/releases/download/v1.0.0/publication-manifest.json",
                    "checksums_url": "https://github.com/example/example-book/releases/download/v1.0.0/SHA256SUMS.txt",
                },
            }
        ],
    }


def profile_document() -> dict:
    return yaml.safe_load((REPO_ROOT / "profiles/standard/profile.yaml").read_text(encoding="utf-8"))


def book_document() -> dict:
    return yaml.safe_load((REPO_ROOT / "template/book/book.yaml").read_text(encoding="utf-8"))


def copy_document(document: dict) -> dict:
    return copy.deepcopy(document)


def make_book_tree(root: Path, document: dict | None = None, chapter_names: tuple[str, ...] = ("chapters/01-example.qmd",)) -> Path:
    """Create a minimal book tree and return the descriptor path."""

    data = copy.deepcopy(document or book_document())
    data["id"] = "fixture-book"
    data["catalog"]["slug"] = "fixture-book"
    data["manuscript"]["root"] = "manuscript"
    data["manuscript"]["reading_order"] = "manuscript/book.yml"

    manuscript = root / "manuscript"
    for name in chapter_names:
        chapter = manuscript / name
        chapter.parent.mkdir(parents=True, exist_ok=True)
        chapter.write_text("# 1. Fixture\n\nPlaceholder.\n", encoding="utf-8")

    reading_order = {
        "front": [],
        "chapters": list(chapter_names),
        "back": [],
        "appendices": [],
        "references": [],
    }
    write_yaml(manuscript / "book.yml", reading_order)
    return write_yaml(root / "book.yaml", data)
