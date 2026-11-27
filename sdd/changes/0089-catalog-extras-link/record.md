# Change 0089 — Link a release's optional extras from the catalog and the portal

Implementer: oc7 (OpenCode). Reviewer and merger: a different agent. Branch
`feat/catalog-extras-link` from `main` `d432bfa`. No version bump or tag: the change ships in the
next toolkit release.

Closes issue 142 (last open item). The catalog already verified the optional
`book-extras.zip` + `EXTRAS-SHA256SUMS.txt` pair, but no catalog field or portal link exposed it.
The Solutions Architecture Handbook `v6.0.0` publishes the pair; the sample does not.

## Write set

- `tools/src/handbook_toolkit/schemas/catalog.schema.json`
- `tools/src/handbook_toolkit/catalog.py`
- `tools/src/handbook_toolkit/catalog_verification.py`
- `tools/scripts/update_catalog.py`
- `tools/src/handbook_toolkit/portal.py`
- `tools/src/handbook_toolkit/portal_markup.py`
- `tools/src/handbook_toolkit/render_data/portal/card.html`
- `tools/scripts/portal_preview.py`
- `docs/catalog-contract.md`, `docs/catalog-automation.md`, `CHANGELOG.md`
- `tools/tests/test_catalog.py`, `test_catalog_verification.py`, `test_update_catalog.py`,
  `test_portal.py`
- this record

`catalog/catalog.json` and `STATUS.md` are deliberately untouched: entries come only from the
catalog-update workflow for approved releases, and the coordinator owns the status file.

## Design

`latest_release.extras` is an optional object with exactly `archive` and `checksums_url`, both
HTTPS URLs. It is not a new `assets` role: `assets` keeps the fixed publication payloads and the
verifier continues to keep the extras pair out of them.

**No `schema_version` bump.** The design asked for an optional, backward-compatible field and did
not ask for a new schema version. The field is valid in every supported version, entries without it
stay valid, and readers that do not know it ignore it. This follows the precedent of change `0072`,
which added optional/required catalog data without a new decision row, so `docs/decisions.md` has no
new entry. `STATUS.md` stays at catalog schema `1.2`; the coordinator can restate the catalog shape
after merge if needed.

`update_catalog.release_extras` reads the release asset list. Both uploaded, canonical extras files
produce `extras`; neither omits the field; one without the other raises the existing
"release extras must carry both book-extras.zip and EXTRAS-SHA256SUMS.txt" error before the catalog
is written.

`catalog.py` checks that each extras URL is the release's own canonical file, using the manifest
URL as the base. `catalog_verification._verify_book` repeats the check against the release URL
prefix, requires the release asset set to contain the pair when the catalog entry has `extras`,
and then runs the existing `_verify_extras` checksum and archive checks. A release with the pair and
a catalog entry without `extras` **passes**: an older entry is not forced to add the optional field.

Both portal engines show an `Extras` button in the formats row and an `Extras checksums` link in the
assets row when `extras` is present. The links use the existing `.fmt` and `.assets` styles, so the
44 px Quarto target and the phone layout are unchanged. `portal_preview.py` rebases the extras URLs
for its fixture book, like the assets.

## Tests

- `test_catalog.py`: valid extras, entry without extras, wrong tag/name/host for each URL, and a
  missing required URL.
- `test_update_catalog.py`: pair detection, no extras, one-without-the-other, starter/foreign
  assets, plan output with and without the field, and the CLI apply path.
- `test_catalog_verification.py`: catalog extras match the release, a wrong URL is rejected by
  `_verify_book`, an entry with extras but no release pair fails, and a release pair without a
  catalog entry passes.
- `test_portal.py`: the legacy card shows the `Extras` button and `Extras checksums` link; a card
  without extras has neither; the Quarto card renders both links and their labels.

## Known gaps

- `catalog/catalog.json` still lists the Solutions Architecture Handbook `v6.0.0` without
  `extras`; the field appears the next time the catalog-update workflow lists a release that
  publishes the pair. This change deliberately does not edit an approved catalog entry.
- The legacy portal's `.fmt` buttons were already below 44 px; the new link reuses that existing
  style, and the Quarto engine keeps its 44 px target. No CSS was changed.
- `STATUS.md` still states catalog schema `1.2`, which remains accurate because no schema version
  changed.

## Evidence

Commands run with the scratchpad venv
`/tmp/claude-1001/-home-ubuntu-github-handbooks-hub/7b4fb8a3-4711-43a8-8238-6b2394596453/scratchpad/hubvenv`:

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tools/tests -p 'test_catalog.py'` | 18 tests, OK |
| `python -m unittest discover -s tools/tests -p 'test_update_catalog.py'` | 38 tests, OK |
| `python -m unittest discover -s tools/tests -p 'test_catalog_verification.py'` | 35 tests, OK |
| `python -m unittest discover -s tools/tests -p 'test_portal.py'` | 30 tests, OK (Quarto included) |
| `make check` | 670 tests, OK (1908.306 s); `verify`: 5 checks, 0 problems |
| `python -m unittest test_reading_site.NativeMotionBrowserTests` (known flake, rerun alone) | 3 tests, OK (26.883 s) |
| `make verify-full` | 7 checks, 0 problems |

No check is claimed before it is run.
