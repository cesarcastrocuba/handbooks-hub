# Change 0072 — Authors in the catalog and the portal

Owner request (2026-11-18): "Include the author in the filter and on the cover section, for example
below the cover; the publisher is independent: Handbooks Hub."

No version bump and no tag. The change ships in the next toolkit release.

## Scope

- `tools/src/handbook_toolkit/schemas/catalog.schema.json`, `catalog/catalog.json`
- `tools/src/handbook_toolkit/catalog_verification.py`, `tools/scripts/update_catalog.py`
- `tools/src/handbook_toolkit/portal.py`, `portal_markup.py`, `render_data/portal/*`
- `.github/ISSUE_TEMPLATE/request-listing.yml`
- `docs/catalog-contract.md`, `docs/catalog-automation.md`, `docs/author-guide.md`
- `tools/tests/test_schemas.py`, `test_catalog_verification.py`, `test_update_catalog.py`,
  `test_portal.py`
- `CHANGELOG.md` and this record

`render_data/html/*` and `design.py` are untouched; change `0071` runs there in parallel.

## Catalog schema 1.2

`authors` is a required array of one to ten unique, non-empty, trimmed strings (no leading or
trailing whitespace). A name cannot contain `|`: the portal keeps the authors in `data-authors`
joined by `" | "`, so the separator would split a name. `schema_version` accepts `1.2`; a `1.1`
document without `authors` remains valid and `1.2` requires the field. `catalog/catalog.json` moves to `1.2` and states
`"authors": ["Franz César Castro Cuba"]` for both books, the `author` of each book's
`publishing/metadata.yaml`.

## Verification

`catalog_verification._verify_authors` reads `publishing/metadata.yaml` from the release's
`book-source.zip` (already downloaded for the payload checks) and compares its `author` — a string
or a list of strings — with the catalog `authors`, after trimming. A mismatch names both values; a
source archive without the file cannot verify and fails with a clear error. Catalogs without
`authors` (schema `1.0`/`1.1`) skip the check, so a published legacy release is not held to a newer
rule.

`update_catalog.plan_update` rewrites only `latest_release`: a `1.0` catalog gains `1.1` when direct
downloads are added, while a `1.2` catalog keeps its authors and its schema version.

## Portal

- The Quarto engine card keeps `data-authors` (`" | "`-joined) and shows `By …` under the title,
  joined as "A", "A and B" or "A, B and C".
- The generated cover carries the author line under the title and `Handbooks Hub · vX.Y.Z` at its
  foot.
- The toolbar gains `Author <select>` (`All authors` plus each distinct author, case-insensitively
  sorted) next to the topic chips, the search and the sort. `filter.js` combines the three filters;
  the search text now includes `data-authors`, so a name finds its books. The filter runs only when
  the control exists.
- `footer.html` names the publisher once: "Handbooks Hub — an independent publisher of open
  handbooks."
- The legacy engine (`--engine legacy`) gets the same byline, cover line and Author select, because
  it shares `filter.js`; the legacy tests cover it.
- Author names are escaped in text, attributes and `<option>` values, including accents and `<`.

## Tests

- `test_schemas.CatalogSchemaTests`: `1.1` without authors valid, `1.2` requires authors, and empty,
  duplicate, padded, eleven-item or non-string lists are invalid.
- `test_catalog_verification`: a fake `book-source.zip` with matching metadata passes, a metadata
  list passes, a mismatch and a missing file fail with the expected messages.
- `test_update_catalog`: a `1.2` catalog keeps `authors` and `1.2` when it moves to a newer release.
- `test_portal`: card byline, cover author and publisher foot, the Author select options (distinct
  authors, `All authors` first), escaping, a catalog without authors rendering no byline, and a
  Playwright test that selects an author, resets it, and searches by a name.

## Evidence

```
$ make full PYTHON=.venv/bin/python
...
Ran 587 tests in 656.996s

OK
site-check: 1 page(s), 3 asset(s), all 200
PYTHONPATH=tools/src ./.venv/bin/python -m handbook_toolkit --root . verify
repository files: OK
packaged schemas: OK
.../catalog/catalog.json: OK
.../profiles/standard/profile.yaml: OK
.../template/book/book.yaml: OK
VERIFY: 5 check(s), 0 problem(s)
PYTHONPATH=tools/src ./.venv/bin/python -m handbook_toolkit --root . verify --full
repository files: OK
packaged schemas: OK
.../catalog/catalog.json: OK
.../profiles/standard/profile.yaml: OK
.../template/book/book.yaml: OK
documentation links: OK
documentation currency: OK
VERIFY (full): 7 check(s), 0 problem(s)
```

```
$ GITHUB_TOKEN=$(gh auth token) python -m handbook_toolkit.catalog_verification catalog/catalog.json
release verification: OK
```

The real catalog verifies online, which now includes the author comparison against both books'
`book-source.zip` metadata.

## Catalog move to v3.1.1

The Solutions Architecture book published `v3.1.1` (release run 44477761172 from `ed4d86b`) and its
reading site now serves that edition, so online verification of the listed `v3.1.0` failed with
`live reading asset differs from released HTML: analytic-index.html`. The entry moved with the same
core the catalog-update workflow uses, which rewrites only `latest_release` and kept `authors` and
schema `1.2`:

```
$ python3 tools/scripts/update_catalog.py apply --catalog catalog/catalog.json \
    --slug solutions-architecture-handbook --tag v3.1.1 \
    --source-repo cesarcastrocuba/handbook-solutions-architecture --release-json /tmp/rel.json
updated: solutions-architecture-handbook v3.1.0 -> v3.1.1 (published 2026-11-19)

$ python -m handbook_toolkit.cli validate-catalog catalog/catalog.json
.../catalog/catalog.json: OK

$ GITHUB_TOKEN=$(gh auth token) python -m handbook_toolkit.catalog_verification catalog/catalog.json
release verification: OK
```

## Screenshots

- `portal-library-light.png`
- `portal-library-dark.png`

Built with `python -m handbook_toolkit.portal catalog/catalog.json --output <dir> --engine quarto`
at 1280 px, reduced motion, light and dark.

## CI

`portal-pages.yml` was dispatched on `feat/0072-portal-authors` with `deploy=false` (run
`44401553490`): the `build` job succeeded and `deploy` and `verify` were skipped as requested.
