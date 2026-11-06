"""Create and verify a publication identity without rebuilding its payloads.

This module establishes byte integrity, not editorial approval, format validity or
reproducibility. Those are separate publication gates.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .validation import CheckResult, DocumentError, Issue, load_packaged_schema, schema_issues

MANIFEST = "publication-manifest.json"
CHECKSUMS = "SHA256SUMS.txt"
MEDIA = {"html": "application/zip", "pdf": "application/pdf",
         "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         "source": "application/zip"}
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SUM_LINE = re.compile(r"([0-9a-f]{64})  ([A-Za-z0-9][A-Za-z0-9._-]*)\Z")
SUFFIX = {"html": ".zip", "source": ".zip", "pdf": ".pdf", "docx": ".docx"}


def _payload(directory: Path, name: str) -> Path:
    if not isinstance(name, str) or not SAFE_NAME.fullmatch(name):
        raise ValueError(f"artifact must be a plain filename: {name!r}")
    path = directory / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"artifact is missing, a symlink or not a file: {name}")
    return path


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_manifest(directory: Path, metadata: dict, artifacts: dict[str, str]) -> Path:
    """Write a new manifest and checksums for four already-built payloads.

    Metadata follows publication-manifest.schema.json. Refuse replacement of an
    existing manifest or checksum file; callers must use a fresh build directory.
    """
    directory = directory.resolve()
    if (directory / MANIFEST).exists() or (directory / CHECKSUMS).exists():
        raise ValueError("publication identity already exists; use a fresh output directory")
    if set(artifacts) != set(MEDIA):
        raise ValueError("exactly html, pdf, docx and source payloads are required")
    if len(set(artifacts.values())) != 4 or {MANIFEST, CHECKSUMS} & set(artifacts.values()):
        raise ValueError("payload filenames must be distinct and cannot be identity files")
    if {path.name for path in directory.iterdir()} != set(artifacts.values()):
        raise ValueError("fresh output directory must contain exactly the four payloads")
    document = deepcopy(metadata)
    document["schema_version"] = "1.0"
    document["artifacts"] = []
    for role, name in sorted(artifacts.items()):
        path = _payload(directory, name)
        if not name.endswith(SUFFIX[role]):
            raise ValueError(f"{role} payload must use the {SUFFIX[role]} extension")
        document["artifacts"].append({"role": role, "path": name,
                                      "sha256": _digest(path), "bytes": path.stat().st_size,
                                      "media_type": MEDIA[role]})
    issues = schema_issues(document, load_packaged_schema("publication-manifest.schema.json"), MANIFEST)
    if issues:
        raise ValueError("invalid manifest metadata: " + "; ".join(map(str, issues)))
    encoded = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    digests = {entry["path"]: entry["sha256"] for entry in document["artifacts"]}
    digests[MANIFEST] = hashlib.sha256(encoded).hexdigest()
    sums = "".join(f"{digests[name]}  {name}\n" for name in sorted(digests)).encode("utf-8")
    temporary: list[Path] = []
    created: list[Path] = []
    try:
        for contents in (encoded, sums):
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".publication-", delete=False) as stream:
                temporary.append(Path(stream.name))
                stream.write(contents)
                stream.flush()
                os.fsync(stream.fileno())
        for staged, name in zip(temporary, (MANIFEST, CHECKSUMS)):
            destination = directory / name
            os.link(staged, destination)  # exclusive creation; never replace another writer's identity
            created.append(destination)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)
    return directory / MANIFEST


def verify_publication(directory: Path) -> CheckResult:
    """Verify schema, required roles, exact asset membership, sizes and hashes.

    Checksums cannot establish trust in an author or source commit: a verifier must
    compare the manifest identity with the independently approved release commit.
    """
    directory = directory.resolve()
    issues: list[Issue] = []
    try:
        manifest_path = _payload(directory, MANIFEST)
        sums_path = _payload(directory, CHECKSUMS)
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        issues.extend(schema_issues(document, load_packaged_schema("publication-manifest.schema.json"), MANIFEST))
        if issues:
            return CheckResult(str(directory), tuple(issues))
        entries = document["artifacts"]
        roles = [entry["role"] for entry in entries]
        names = [entry["path"] for entry in entries]
        if len(set(roles)) != 4 or set(roles) != set(MEDIA):
            issues.append(Issue(MANIFEST, "exactly one payload for each required role is required"))
        if len(set(names)) != len(names) or {MANIFEST, CHECKSUMS} & set(names):
            issues.append(Issue(MANIFEST, "payload names must be unique and exclude identity files"))
        for entry in entries:
            path = _payload(directory, entry["path"])
            if path.stat().st_size != entry["bytes"] or _digest(path) != entry["sha256"]:
                issues.append(Issue(entry["path"], "payload size or SHA-256 differs from manifest"))
            if entry["media_type"] != MEDIA[entry["role"]]:
                issues.append(Issue(entry["path"], "media type does not match role"))
            if not entry["path"].endswith(SUFFIX[entry["role"]]):
                issues.append(Issue(entry["path"], "file extension does not match role"))
        expected = set(names) | {MANIFEST}
        sums: dict[str, str] = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            match = SUM_LINE.fullmatch(line)
            if not match or match[2] in sums:
                issues.append(Issue(CHECKSUMS, "malformed or duplicate checksum entry"))
                continue
            sums[match[2]] = match[1]
        if set(sums) != expected:
            issues.append(Issue(CHECKSUMS, "checksum membership must equal payloads plus manifest"))
        for name, digest in sums.items():
            if name in expected and _digest(_payload(directory, name)) != digest:
                issues.append(Issue(name, "SHA-256 differs from checksum file"))
        actual = {path.name for path in directory.iterdir()}
        if actual != expected | {CHECKSUMS}:
            issues.append(Issue(str(directory), "output directory must contain only the declared release assets"))
    except (OSError, UnicodeError, ValueError, DocumentError) as error:
        issues.append(Issue(str(directory), str(error)))
    return CheckResult(str(directory), tuple(issues))
