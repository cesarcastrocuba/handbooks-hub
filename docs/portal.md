# Static handbook catalog

Build a fresh static portal from the Git-tracked approved-release catalog:

```sh
python3 -m handbook_toolkit.portal catalog/catalog.json --output /tmp/handbook-portal
```

The output directory holds `index.html`, a single responsive page with embedded
styles and JavaScript, `llms.txt`, a plain-text index for AI tools, and a
`fonts/` directory with the self-hosted WOFF2 files the page requests.

`index.html` contains:

- **The library.** One card per book with a cover generated from its title and first category,
  category filters, title/release sorting, a text search over the cards, and reading, release,
  manifest and checksum links. A release whose catalog entry lists `assets` also gets one download
  button per edition (PDF, HTML, DOCX, Markdown, Source); other releases keep only the "Release
  downloads" link.
- **Guide sections.** How the platform works, how to create a handbook in five steps, how a book
  is published and withdrawn, how to contribute to a book, and questions and answers. They are
  static text and link to the template repository, the author guide and the hub issue forms.

The page loads no external script, style, font or image, follows the reader's light or dark
preference and contains no book manuscript or download proxy. Empty catalogs show an honest
preparation message; planned topics are marked as planned rather than populated with fictitious
books.

`llms.txt` follows the llms.txt convention: a title, a summary and one link per book. The link is
the Markdown edition when the release lists one and the reading site otherwise.

Catalog entries require an explicit HTTPS `reading_url`: Pages URLs cannot be
reliably inferred from a release URL or a custom domain. The category vocabulary
is now enforced by the schema. This tightens the initial, unreleased catalog
contract. New categories require a deliberate
schema and portal vocabulary update.
Reading URLs use port 443 and contain no query string or credentials; a fragment
may identify a section of the landing page.

The generator is offline and deterministic. It validates catalog shape/invariants,
escapes untrusted text and refuses to overwrite an existing output directory.
Before generation/deployment, the workflow runs:

```sh
python3 -m handbook_toolkit.catalog_verification catalog/catalog.json
```

For each entry this online gate requires a published stable GitHub release,
resolves its tag to the exact source commit, verifies manifest identity and every
release asset, checks each catalog download link against the manifest, checks their formats, and verifies that every released HTML-site file
is present and byte-identical live. Extra live files are not enumerated.
Missing/mixed-release assets and changed bytes fail.
An empty catalog makes no network requests. Payload downloads are limited to
512 MiB each; API/identity responses to 2 MiB. Public GitHub API rate limits apply.
Editorial approval remains a human decision recorded before catalog acceptance;
neither checksums nor a published GitHub release prove that decision.
All requests and redirects require HTTPS on port 443 and public unicast IPs.
Connections are pinned to the checked IP while TLS verifies the original hostname;
DNS rebinding cannot substitute a second unchecked address during connection.
Internal, loopback, link-local and reserved destinations fail before fetching.

The Pages workflow builds from the checked-out catalog; it deploys on a catalog change on `main`
or by manual dispatch (`HUB-DEC-024`). Deployment
requires Pages configured with the GitHub Actions build type. Reading-site and
book-release publication remain independent workflows.

Verification: `python3 -m unittest discover -s tools/tests -p test_portal.py`.
Rollback removes portal generation/tests/workflow and reverts the unreleased
reading-URL/category schema changes; existing book sources are unaffected.
