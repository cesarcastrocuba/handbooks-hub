# Catalog contract

The catalog is the only data source for the hub portal. It is deliberately small: it lists books and
their approved releases; it does not mirror manuscript content.

Machine-readable contract: [`catalog/catalog.json`](../catalog/catalog.json) and
[`catalog.schema.json`](../tools/src/handbook_toolkit/schemas/catalog.schema.json). Current state:
one approved book; see [`STATUS.md`](../STATUS.md).

## Entry model

```json
{
  "schema_version": "1.0",
  "books": [
    {
      "id": "handbook-authoring-and-publishing",
      "slug": "handbook-authoring-and-publishing",
      "title": "Handbook Authoring and Publishing",
      "summary": "A practical guide to writing, reviewing and publishing a handbook.",
      "categories": ["authoring", "publishing"],
      "status": "published",
      "reading_url": "https://OWNER.github.io/REPO/",
      "latest_release": {
        "version": "1.0.0",
        "tag": "v1.0.0",
        "url": "https://github.com/OWNER/REPO/releases/tag/v1.0.0",
        "published_at": "2026-12-01",
        "manifest_url": "https://github.com/OWNER/REPO/releases/download/v1.0.0/publication-manifest.json",
        "checksums_url": "https://github.com/OWNER/REPO/releases/download/v1.0.0/SHA256SUMS.txt"
      }
    }
  ]
}
```

The example is illustrative and is not listed in the catalog.

### Direct download links (schema 1.1)

`latest_release` may carry an optional `assets` object that maps an artifact role to the direct URL
of that edition. It requires `schema_version` `"1.1"`; a `1.0` catalog without `assets` stays valid.

```json
"assets": {
  "pdf": "https://github.com/OWNER/REPO/releases/download/v1.0.0/book.pdf",
  "html": "https://github.com/OWNER/REPO/releases/download/v1.0.0/book-html.zip",
  "docx": "https://github.com/OWNER/REPO/releases/download/v1.0.0/book.docx",
  "markdown": "https://github.com/OWNER/REPO/releases/download/v1.0.0/book.md",
  "source": "https://github.com/OWNER/REPO/releases/download/v1.0.0/book-source.zip"
}
```

Roles are `pdf`, `html`, `docx`, `markdown` and `source`. A release lists only the editions it
has: a release built before the Markdown edition existed has no `markdown` link. The portal shows
one button per listed role and `llms.txt` links the Markdown edition when it is listed.

## Required invariants

The toolkit enforces these deterministically:

| Invariant | Reason |
| --- | --- |
| `id` and `slug` are unique and match `^[a-z][a-z0-9-]{1,63}$` | Stable URLs and joins |
| `status` is `published` or `archived` | No drafts in the public catalog |
| `latest_release.version` is exact semver `MAJOR.MINOR.PATCH` | Immutable, comparable releases |
| `tag` is exactly `v` + `version` | One naming rule across books |
| Release, manifest and checksums URLs are HTTPS and share the same tag | No mutable or mixed-release links |
| `published_at` is an ISO date (`YYYY-MM-DD`) | Deterministic rendering |
| Categories are unique controlled lowercase slugs | Stable portal grouping |
| `reading_url` is explicit HTTPS | Reading sites may use custom domains and cannot be inferred from release URLs |
| Each `assets` URL is the canonical file of its role under the same release as `manifest_url` | No link to another release, host or file |
| Online verification: each `assets` URL is an artifact of the release manifest with the same role | The link downloads verified bytes |
| The JSON document is valid against the catalog schema | One validated interface |

A catalog entry is rejected if it points to a branch, a pull request, a draft release or a build
artifact that is not attached to the release.

## Update flow

1. The book owner approves a release and the book publishes the artifact set.
2. The book release is verified: tag, manifest, checksums and artifact hashes.
3. A hub change updates `catalog/catalog.json` and the change record.
4. `handbook-toolkit validate-catalog` and `handbook-toolkit verify --full` pass.
5. An independent reviewer verifies the links and the release evidence.
6. The owner merges; the portal rebuilds from the catalog.

The catalog is append-mostly. Removing an entry is reserved for withdrawal (for example a licensing
or integrity defect) and must be recorded with the reason and the replacement version.

## Categories

Categories are portal facets, not a taxonomy of every topic. Start with a small controlled set and
extend it only when a book cannot be described by the existing values:

`architecture`, `authoring`, `cloud`, `data`, `engineering`, `governance`, `publishing`, `security`.

The catalog schema enforces this vocabulary. The portal exposes filters only for populated
categories; empty categories are explicitly marked as planned facets.

## Portal behavior

- One card per book: a generated cover, title, summary, categories, latest version, links to the
  reading site and release downloads, and one button per edition listed under `assets`.
- Filter by category, sort by title or release date, and search the text of the cards in the browser.
- Static guide sections explain the platform, the author path, publishing and withdrawal.
- `llms.txt` is written next to `index.html` and lists every book for AI tools.
- The portal is static HTML generated from the catalog and deployed to Pages.
- The portal never proxies or hosts book downloads; it links to immutable release assets.
- Broken or missing release assets fail the portal build, not the reader's browser.
- The deployment workflow runs online release/tag/hash/reading-site verification before generating
  the static portal. Offline HTML generation alone does not establish those external facts.

## Non-goals

- Full-text search inside books.
- Hosting canonical manuscript content in the hub.
- Automatic ingestion from a branch or a pull request.
- Ratings, comments or user accounts.
