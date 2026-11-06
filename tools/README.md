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
handbook-toolkit verify --root .
handbook-toolkit verify --root . --full
handbook-toolkit validate-catalog catalog/catalog.json
handbook-toolkit validate-profile profiles/standard/profile.yaml
handbook-toolkit validate-book template/book/book.yaml --full
```

`--schemas` overrides the schema directory. The default is `<root>/schemas`.

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

Tests use only the standard library runner and cover both accepted and rejected input.
