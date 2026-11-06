# Tasks — packaged schemas

**Status:** Proposed
**Change:** `0002-toolkit-packaged-schemas`

| ID | Task | Write set | Status |
| --- | --- | --- | --- |
| T1 | Move schemas into the package | `tools/src/handbook_toolkit/schemas/` | Done |
| T2 | Declare package data | `tools/pyproject.toml` | Done |
| T3 | Add packaged-schema loader and package-first resolution | `validation.py`, `cli.py`, `repository.py` | Done |
| T4 | Remove top-level schema coupling | `schemas/`, repository required-file list | Done |
| T5 | Update validator signatures and tests | `tools/src/`, `tools/tests/` | Done |
| T6 | Add isolated package-copy and zip-import tests | `tools/tests/test_installed_package.py` | Done |
| T7 | Add `--schemas` override regression test | `tools/tests/test_cli.py` | Done |
| T8 | Update docs, status, changelog and this record | `README`, `docs/`, `STATUS.md`, `CHANGELOG.md`, `sdd/` | Done |
| T9 | Run fast, full, compile and clean-clone checks | None | Done |
| T10 | Commit and record the exact HEAD | `.git/`, this record | Done after commit |
| T11 | Independent review of the fix | Review comments | Pending |
| T12 | Owner Gate 1 (still open; this fix does not approve it) | Decision record | Pending |

## Verification mapping

| Criterion | Evidence |
| --- | --- |
| Package-copy validation | `test_isolated_package_copy_uses_bundled_schemas` |
| Zip-import validation | `test_zip_imported_package_uses_bundled_schemas` |
| Package data declared | `test_pyproject_ships_schemas_as_package_data` |
| Override still works | `test_schema_directory_override` |
| Hub verify works | `make check` / `make full` output |
| No top-level schemas | `find` / `git ls-files` |
| Clean tree | `git status --porcelain` |

## Deferred

| Task | Reason | Next step |
| --- | --- | --- |
| Real wheel build and install | No `pip`, `ensurepip`, `build` or `wheel` in this environment | CI installs the editable package; add a wheel job when packaging tools are available |
| Rotating the toolkit version | No release or gate approval in this change | Version bump belongs to the next release |
