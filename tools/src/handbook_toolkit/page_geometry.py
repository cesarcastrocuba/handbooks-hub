"""Shared print geometry used by native configuration and raster sizing."""

from __future__ import annotations
import re
from .build_types import BuildError

PAPER = "a4"
MARGINS = {"x": "2.2cm", "y": "2.4cm"}
PAPERS_CM = {"a4": (21.0, 29.7), "us-letter": (21.59, 27.94), "letter": (21.59, 27.94)}


def inches(value: str) -> float:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|in|pt|px)\s*", str(value))
    if not match:
        raise BuildError(f"unsupported print length: {value!r}")
    return (
        float(match[1])
        * {"cm": 1 / 2.54, "mm": 1 / 25.4, "in": 1, "pt": 1 / 72, "px": 1 / 96}[
            match[2]
        ]
    )


def text_width_inches(config: dict) -> float:
    fmt = config.get("format", {}).get("typst", {}) or {}
    paper = str(fmt.get("papersize", PAPER)).lower()
    if paper not in PAPERS_CM:
        raise BuildError(f"unsupported print paper for raster sizing: {paper}")
    margin = fmt.get("margin", MARGINS)
    if isinstance(margin, str):
        left = right = margin
    elif isinstance(margin, dict):
        left = margin.get("left", margin.get("x", MARGINS["x"]))
        right = margin.get("right", margin.get("x", MARGINS["x"]))
    else:
        raise BuildError("print margin must be a length or mapping")
    result = PAPERS_CM[paper][0] / 2.54 - inches(left) - inches(right)
    if result <= 0:
        raise BuildError("print margins leave no text width")
    return result
