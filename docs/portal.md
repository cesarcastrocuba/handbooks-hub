# Static handbook catalog

Build a fresh static portal from the Git-tracked approved-release catalog:

```sh
python3 -m handbook_toolkit.portal catalog/catalog.json --output /tmp/handbook-portal
```

The output is a single responsive HTML file with embedded styles and JavaScript.
It provides category filters, title/release sorting and direct reading, release,
manifest and checksum links. It contains no book manuscript or download proxy.
Empty catalogs show an honest preparation message; planned topics are marked as
planned rather than populated with fictitious books.

Catalog entries require an explicit HTTPS `reading_url`: Pages URLs cannot be
reliably inferred from a release URL or a custom domain. The category vocabulary
is now enforced by the schema. This tightens the initial, unreleased catalog
contract; the live catalog is still empty. New categories require a deliberate
schema and portal vocabulary update.

The generator is offline and deterministic. It validates catalog shape/invariants,
escapes untrusted text and refuses to overwrite an existing output directory.
Before generation/deployment, the workflow runs:

```sh
python3 -m handbook_toolkit.catalog_verification catalog/catalog.json
```

For each entry this online gate requires a published stable GitHub release,
resolves its tag to the exact source commit, verifies manifest identity and all
six assets, checks their formats, and compares every live reading-site file with
the released HTML archive. Missing/mixed-release assets and changed bytes fail.
An empty catalog makes no network requests. Payload downloads are limited to
512 MiB each; API/identity responses to 2 MiB. Public GitHub API rate limits apply.
Editorial approval remains a human decision recorded before catalog acceptance;
neither checksums nor a published GitHub release prove that decision.

The Pages workflow is manual and builds from the checked-out catalog. Deployment
requires Pages configured with the GitHub Actions build type. Reading-site and
book-release publication remain independent workflows.

Verification: `python3 -m unittest discover -s tools/tests -p test_portal.py`.
Rollback removes portal generation/tests/workflow and reverts the unreleased
reading-URL/category schema changes; existing book sources are unaffected.
