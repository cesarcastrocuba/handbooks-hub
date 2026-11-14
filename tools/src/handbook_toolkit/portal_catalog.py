"""Read the approved-release catalog without fetching remote content."""
from pathlib import Path
from typing import Any

from .catalog import validate_catalog
from .validation import load_document, load_packaged_schema


def read_catalog(path: Path) -> list[dict[str, Any]]:
    result = validate_catalog(path, load_packaged_schema('catalog.schema.json'))
    if not result.ok:
        raise ValueError('invalid catalog: ' + '; '.join(map(str, result.issues)))
    return sorted(load_document(path)['books'], key=lambda book: book['title'].casefold())
