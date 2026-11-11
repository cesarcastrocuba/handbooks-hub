# Change 0021 — Library portal, catalog download links and `llms.txt`

**Decisions:** `HUB-DEC-030` and the catalog and `llms.txt` parts of `HUB-DEC-028` (Proposed until the
Owner merges). **Plan:** Phase B, items 2 and 3, of the plan summarised in change `0018`.

## Problem

The portal is a plain card grid. It does not explain the platform, the author path or how a book is
approved and withdrawn. It cannot offer a button per edition, because the catalog stores only the
release, manifest and checksum URLs and the portal is generated offline.

## Change

1. **Catalog schema `1.1`**: optional `latest_release.assets`, a direct download URL per artifact
   role (`pdf`, `html`, `docx`, `markdown`, `source`). A `1.0` catalog stays valid.
   - The validator requires schema `1.1` for `assets` and pins each URL to the canonical file of its
     role under the same release as `manifest_url`.
   - `tools/scripts/update_catalog.py` records a link for each canonical file uploaded to a newly
     listed release. A release that is already listed never gains or changes links.
   - Online verification requires each link to be an artifact of the release manifest with the same
     role.
2. **Portal** (`tools/src/handbook_toolkit/portal.py`): generated covers by category, one button per
   listed edition, text search, guide sections and `llms.txt` next to `index.html`. The
   `build_portal(catalog, output)` entry point, the atomic staged write and the offline build stay.
3. **Docs**: `docs/portal.md`, `docs/catalog-contract.md`, `docs/catalog-automation.md`.

## Compatibility

The live catalog (`1.0`, sample `v0.2.4`, no `assets`) builds unchanged and shows no edition
buttons. The buttons and the Markdown link in `llms.txt` appear when `catalog-update` lists a release
built with toolkit `0.6.0`.

## Known limits

- The guide sections link to the template repository, the author guide and the issue forms, which
  arrive with change `0020`. The portal is deployed only on a catalog change, which follows it.
- Visual review was done on a local build in a headless browser; no assistive-technology test ran.

Evidence is recorded in this folder by the implementing pull request.
