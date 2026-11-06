"""Resolve exact approved profile snapshots from the installed toolkit."""

from importlib.resources import files
import re

import yaml

from .validation import DocumentError, load_packaged_schema, schema_issues


def load_profile(profile_id: str, version: str) -> dict:
    """Load an approved profile by identity; never upgrade or use a parent checkout."""
    if not isinstance(profile_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", profile_id):
        raise DocumentError("profile id must be a lowercase slug")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise DocumentError("profile version must be exact MAJOR.MINOR.PATCH")
    name = f"{profile_id}-{version}.yaml"
    resource = files("handbook_toolkit").joinpath("profile_data", name)
    try:
        document = yaml.safe_load(resource.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise DocumentError(
            f"approved profile {profile_id}@{version} is unavailable in this toolkit; install its reviewed toolkit pin"
        ) from error
    issues = schema_issues(document, load_packaged_schema("profile.schema.json"), name)
    if issues:
        raise DocumentError("invalid packaged profile: " + "; ".join(map(str, issues)))
    if document["id"] != profile_id or document["version"] != version or document["status"] != "approved":
        raise DocumentError("packaged profile identity or approval status does not match the requested pin")
    return document
