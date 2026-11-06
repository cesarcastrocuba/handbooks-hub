# Evidence — packaged schemas

**Change:** `0002-toolkit-packaged-schemas`
**Status:** Implemented, pending independent review
**Date:** 2026-11-06
**Fix commit:** pending (recorded by the follow-up evidence commit)
**Starting point reviewed:** `46b78cc4e5e7e4d82586012526ae604273490cfc`

## Environment

| Item | Value |
| --- | --- |
| OS | Linux, `/home/ubuntu/github/handbooks-hub` |
| Python | 3.12.3 |
| `jsonschema` | 4.10.3 |
| `PyYAML` | 6.0.1 |
| `pip` / `ensurepip` | Not available |
| `build` / `wheel` modules | Not available |
| Network | Not used |

**Packaging limitation:** a real wheel could not be built or installed locally. The integration tests
therefore simulate the installed layout two ways: a package-only filesystem copy and a zip-imported
package. Both use only the copied package and a temporary book, with a deliberately invalid decoy
`schemas/` directory in the book root. CI can perform the real editable install; a wheel-install job
remains a follow-up when packaging tools are present.

## Changes

| Area | Change |
| --- | --- |
| Schema location | Moved `schemas/*.json` to `tools/src/handbook_toolkit/schemas/*.json`; removed the top-level directory |
| Package data | `[tool.setuptools.package-data] handbook_toolkit = ["schemas/*.json"]` |
| Resolution | `load_packaged_schema()` uses `importlib.resources.files`; `load_schema_source()` honours an explicit override only |
| Validators | `validate_catalog`, `validate_profile`, `validate_book` accept a loaded schema mapping |
| Repository checks | `verify_repository` loads packaged schemas by default and reports `packaged schemas: OK`; `--schemas` still works |
| Tests | Added isolated package-copy, zip-import, package-data and override tests |
| Docs | Updated paths, architecture rule, status, changelog and this record |

## Commands and results

### 1. Fast checks

```bash
make check
```

Result: **PASS**

- 46 unit tests; `OK`.
- 5 checks, 0 problems.
- `packaged schemas: OK`.

### 2. Full checks

```bash
make full
```

Result: **PASS**

- 46 unit tests; `OK`.
- 6 checks, 0 problems.
- Documentation links resolve after the schema path move.

### 3. Isolated installed-package simulation

The test suite includes:

```text
test_isolated_package_copy_uses_bundled_schemas
test_zip_imported_package_uses_bundled_schemas
test_pyproject_ships_schemas_as_package_data
test_schema_directory_override
```

Result: **PASS**. The package copy and the zip import both validate `template/book` in a temporary
directory. Each test places `schemas/{book,catalog,profile}.schema.json` under the book root with an
impossible required field. Passing proves the CLI did not read the book-root schemas. The probe also
confirms `handbook_toolkit.__file__` resolves inside the isolated package path, not the hub.

### 4. Compilation

```bash
python3 -m compileall -q tools
```

Result: **PASS** (exit 0).

### 5. No top-level schema directory

```bash
find . -maxdepth 1 -type d -name schemas
git ls-files | grep 'schemas/'
```

Result: no top-level `schemas/` directory. The only tracked schema files are under
`tools/src/handbook_toolkit/schemas/`.

### 6. Hub behavior preserved

```bash
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . validate-book template/book/book.yaml --full
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify --full
```

Result: **PASS**. The book validates and the hub full verify reports 6 checks, 0 problems. The
`--schemas` override test also passes with a copied schema directory.

### 7. Source distribution inspection

A source distribution was built from a temporary copy of `tools/` with
`setuptools.build_meta.build_sdist`:

```text
handbook-toolkit-0.1.0/src/handbook_toolkit/schemas/book.schema.json
handbook-toolkit-0.1.0/src/handbook_toolkit/schemas/catalog.schema.json
handbook-toolkit-0.1.0/src/handbook_toolkit/schemas/profile.schema.json
```

Result: **PASS**; the package data declaration includes the schemas in the distribution. A wheel
could not be built because `bdist_wheel`/the `wheel` module is absent in this environment.

## Negative and boundary coverage

- A book-root `schemas/` directory cannot override the packaged schemas by accident.
- A package loaded from a zip archive resolves its schemas.
- A missing or unreadable packaged schema is reported as an issue, not silently ignored.
- An explicit `--schemas` directory still takes precedence when supplied.
- The hub required-file check now points at the packaged schema paths.

## Checks not run

| Check | Reason |
| --- | --- |
| Build and install a wheel | No `pip`, `ensurepip`, `build` or `wheel` locally |
| GitHub Actions | No GitHub remote by scope |
| A published toolkit release | No release or gate approval authorized |
| Quarto/PDF/DOCX | Phase 4 |

## Review handoff

Review the fix commit (recorded above after the evidence commit), then re-run:

```bash
make check
make full
```

Point the reviewer at `tools/tests/test_installed_package.py` and
`tools/src/handbook_toolkit/validation.py`. The decoy schema test is the key control: if it passes,
the book cannot be using a hub-relative schema directory.
