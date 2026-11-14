"""Build html."""

from __future__ import annotations
from pathlib import Path
import shutil
from . import design
from .docx_post import (
    prepare_docx,
)
from .artifacts import archive_tree

from .build_types import BuildError, PAYLOADS

def _one_file(directory: Path, suffix: str) -> Path:
    matches = sorted(directory.rglob(f"*{suffix}"))
    if len(matches) != 1:
        raise BuildError(
            f"expected exactly one {suffix} output under {directory}, found {len(matches)}"
        )
    return matches[0]

def _payload_paths(workspace: Path, dist: Path, epoch: int) -> dict[str, Path]:
    output = workspace / "_output"
    if not (output / "index.html").is_file():
        raise BuildError("Quarto did not produce _output/index.html")
    site = dist.parent / "site"
    shutil.copytree(
        output,
        site,
        ignore=shutil.ignore_patterns("*.pdf", "*.docx", "*.typst"),
    )
    # Quarto copies only the font files referenced by the stylesheet. The OFL
    # notices must travel with them, so they are added explicitly before the
    # exact tree is archived and deployed.
    for relative, data in design.font_licenses().items():
        target = site / ".handbook-render" / "fonts" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    archive_tree(site, dist / PAYLOADS["html"], epoch)
    pdf = _one_file(output, ".pdf")
    docx = _one_file(output, ".docx")
    shutil.copy2(pdf, dist / PAYLOADS["pdf"])
    shutil.copy2(docx, dist / PAYLOADS["docx"])
    prepare_docx(dist / PAYLOADS["docx"])
    return {
        "html": dist / PAYLOADS["html"],
        "pdf": dist / PAYLOADS["pdf"],
        "docx": dist / PAYLOADS["docx"],
        "source": dist / PAYLOADS["source"],
    }
