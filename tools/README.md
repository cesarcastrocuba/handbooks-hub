# `handbook-toolkit`

The shared, versioned Python package for handbook repositories. It validates the contracts that
books and the catalog must honour. It contains no book prose and makes no network calls.

## Install

```bash
python3 -m pip install -e ./tools
```

Books install a published release at an exact version. They do not import this checkout or copy its
source.

## Commands

```bash
handbook-toolkit version
handbook-toolkit --root . verify
handbook-toolkit --root . verify --full
handbook-toolkit validate-catalog catalog/catalog.json
handbook-toolkit validate-profile profiles/standard/profile.yaml
# from a book repository root:
handbook-toolkit validate-book --full
# from the hub checkout:
handbook-toolkit validate-book template/book/book.yaml --full
```

`validate-book` defaults to `book.yaml` in the repository root, so a book can run it with no path.

Schemas are bundled inside the installed package. `--schemas` optionally overrides them with a
local directory; a book does not need a hub checkout or a vendored `schemas/` copy.

## Current scope

Version `0.1.0` validates:

- catalog schema, unique ids/slugs, exact tag/version agreement, immutable release URLs and real dates;
- profile schema, unique element ids, closing-order consistency, label style and figure/table
  constraints;
- book descriptor schema, pinned toolkit version and path safety;
- reading-order existence, duplicates and, in full mode, completeness against every `.qmd` file;
- repository-required files and, in full mode, relative documentation links.

The manuscript skeleton, reference resolver, artifact manifest and portal generator are Phase 2 and
Phase 4 work. This package does not claim to validate them yet.

## Tests

```bash
python3 -m unittest discover -s tools/tests -v
```

Tests use only the standard library runner and cover both accepted and rejected input. They also
parse every documented `handbook-toolkit` example, so a doc example with global options after the
subcommand fails the suite.

GitHub Actions additionally builds a wheel, verifies that the three schemas are inside it, installs
the wheel in an isolated virtual environment and validates a copy of the template book outside the
hub checkout. That job is not a publication step.
