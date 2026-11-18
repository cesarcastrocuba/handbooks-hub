# Change 0069 — Catalog verification accepts book extras

Implementer OpenCode 2; reviewer and merger Claude. Branch `fix/0069-catalog-extras` from main
`24d579d`. No version bump or tag: the verifier runs from hub main in CI, not from a book's pinned
toolkit.

## Defect

Change `0057` lets a book add a `release-assets` Makefile target; the template release workflow then
uploads `book-extras.zip` and `EXTRAS-SHA256SUMS.txt` next to the seven publication assets. The
Solutions Architecture `v3.1.0` release has those nine assets. `catalog_verification._verify_book`
required the published asset set to equal exactly the manifest names plus the manifest and checksums,
so any release with extras failed:

```text
solutions-architecture-handbook: release must contain exactly the 7 declared assets
```

`catalog-update.yml` and `portal-pages.yml` both run this verifier, so no book with extras could be
listed or deployed.

## Fix

`_verify_book` now accepts either the expected set exactly, as before, or that set plus both
`book-extras.zip` and `EXTRAS-SHA256SUMS.txt`. Exactly one of the pair, or any other asset name,
still fails with a clear message. Every asset must remain `uploaded` with a same-release
`browser_download_url`, including the extras.

When the pair is present, `_verify_extras` checks it in a sibling temporary directory, so the
published seven-file set is still verified by `verify_publication` unchanged:

- `EXTRAS-SHA256SUMS.txt` is downloaded with a 64 KiB limit and must contain exactly one
  `sha256sum` line naming `book-extras.zip` (`<64 lowercase hex>  book-extras.zip`).
- `book-extras.zip` is downloaded with the API asset `size` as its bound (and `MAX_DOWNLOAD`), and
  its SHA-256 must match the sums line.
- It must be a valid ZIP (`ZipFile.testzip()` returns `None`), and every member path must be
  relative: absolute paths, Windows drive paths and any `..` component are rejected.

Extras are not catalog `assets` roles; the catalog schema is unchanged. `tools/scripts/update_catalog.py`
needs no change: `release_roles` maps only the canonical files in `ASSET_FILES`, so the extras are
ignored when the catalog entry gains its download links. A live run of the updater is not part of this
change; the verifier is.

## Tests

```text
$ .venv/bin/python -m unittest discover -s tools/tests -p test_catalog_verification.py
Ran 23 tests in 0.361s
OK
```

New cases, using the file's existing fake-HTTP fixture: the pair passes; only the ZIP or only the
sums file fails; an unknown tenth asset fails; a checksum mismatch fails; a malformed sums file
(bad format, wrong name, two lines) fails; a `../` ZIP member fails; a non-ZIP file fails. The
existing exact-seven, legacy six-asset, hash, redirect and token tests still pass.

## Docs

`docs/publication-contract.md` now says a release may carry the optional pair and that catalog
verification accepts it alongside the required assets and checks the checksum and ZIP;
`docs/catalog-automation.md` and both `docs/book-upgrade.md` examples say the same. Extras remain
outside the catalog roles.

## Evidence

```text
$ make full PYTHON=.venv/bin/python
Ran 568 tests in 638.294s

OK (skipped=3)
...
VERIFY (full): 7 check(s), 0 problem(s)
```

A real online run against the published `v3.1.0`, with a temporary catalog that appends the Solutions
Architecture entry (not committed; the listing is a separate PR):

```text
$ GITHUB_TOKEN=$(gh auth token) .venv/bin/python -m handbook_toolkit.catalog_verification /tmp/opencode/0069-live/catalog-with-sa.json
release verification: OK
```

The release has nine uploaded assets: the seven publication files plus `book-extras.zip` (75,184 B)
and `EXTRAS-SHA256SUMS.txt` (82 B). The run downloaded and verified both, the seven files, the
manifest identity against the tag commit, and the live reading-site files.

## Known gaps

- The extras checksum is the release's own `EXTRAS-SHA256SUMS.txt`; it proves the ZIP matches that
  line, not who produced it. The manifest identity and tag commit still anchor the seven-file set.
- Only the exact pair is accepted; a book that uploads additional assets must publish them through
  the extras pair or not at all.
- The catalog schema and its roles are unchanged; extras never become catalog download links.
