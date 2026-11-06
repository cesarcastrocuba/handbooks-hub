"""Stage installed Quarto resources into a private build workspace."""

from importlib.resources import files
from pathlib import Path
import shutil

RESOURCE_NAMES = (
    "filters/table-layout.lua",
    "filters/task-checkbox.lua",
    "typst/callout-breakable.typ",
)


def stage_render_resources(destination: Path) -> dict[str, Path]:
    """Copy packaged resources to a new directory, including from zip installs.

    The caller owns a private build workspace. Existing paths are never replaced;
    a failed copy removes only the directory created by this call.
    """
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    try:
        package = files("handbook_toolkit").joinpath("render_data")
        staged = {}
        for name in RESOURCE_NAMES:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(package.joinpath(*name.split("/")).read_bytes())
            staged[name] = target
        return staged
    except Exception:
        shutil.rmtree(destination)
        raise
