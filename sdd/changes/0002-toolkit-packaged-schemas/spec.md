# Spec — packaged schemas

**Status:** Proposed
**Change:** `0002-toolkit-packaged-schemas`

## Deliverables

| ID | Deliverable | Location | State |
| --- | --- | --- | --- |
| D1 | Canonical schemas inside the package | `tools/src/handbook_toolkit/schemas/*.json` | Done |
| D2 | Wheel/package data declaration | `tools/pyproject.toml` | Done |
| D3 | Packaged-schema loader | `tools/src/handbook_toolkit/validation.py` | Done |
| D4 | Package-first CLI and repository checks | `cli.py`, `repository.py` | Done |
| D5 | Explicit `--schemas` override | CLI + test | Done |
| D6 | Installed-layout integration tests | `tools/tests/test_installed_package.py` | Done |
| D7 | Documentation and decision-record updates | `README`, `docs/`, `tools/README.md`, SDD | Done |

## Resolution contract

1. If `--schemas <dir>` is supplied, load `<dir>/<name>` from the filesystem.
2. Otherwise load `handbook_toolkit/schemas/<name>` through `importlib.resources.files`.
3. A missing or unparsable packaged schema is a validation failure, not a silent fallback to the
   book root.
4. The toolkit must not read `<root>/schemas` by default.
5. The package data pattern is `handbook_toolkit = ["schemas/*.json"]`.

## API surface

```text
load_packaged_schema(name) -> dict
load_schema_source(name, override: Path | None = None) -> dict
verify_repository(root, full=False, schemas: Path | None = None)
```

Validators (`validate_catalog`, `validate_profile`, `validate_book`) now accept a loaded schema
mapping. This makes the schema source explicit and removes the accidental path coupling.

## Acceptance criteria

1. `make check` passes: 46 unit tests, 5 fast checks and 0 problems.
2. `make full` passes: 46 unit tests, 6 full checks and 0 problems.
3. The isolated package-copy test validates a book that contains a deliberately invalid
   `schemas/book.schema.json`.
4. The zip-imported package test validates the same book.
5. The package configuration test finds `schemas/*.json` under `handbook_toolkit` package data.
6. The hub's default `verify` reports `packaged schemas: OK`.
7. No top-level `schemas/` directory exists.
8. `--schemas` still works when a valid override directory is supplied.

## Invariants

- One canonical copy of each schema, inside the package.
- No book needs a hub checkout, a copied script or a vendored schema directory.
- No network access during schema resolution.
- Resource reading works from a normal filesystem package and from a zip archive.
- Hub verify output remains deterministic apart from absolute root paths.

## Out of scope

- A real wheel build in this environment (packaging tools unavailable).
- Publishing the toolkit.
- Profile content distribution beyond the pinned profile version.
- Any change to the schema contents themselves.
