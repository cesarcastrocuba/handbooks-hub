# Evidence — Release `v0.2.5`, catalog listing with download links, template mirror

**Decisions:** `HUB-DEC-027` (delegation), `HUB-DEC-028`, `HUB-DEC-029`, sample `DEC-021`.
**Recorded:** 2026-11-11. This closes Phase D of the plan summarised in change `0018`.

## What happened

- Toolkit `0.6.0` merged as hub PR 19 (`c200fd2`) and was tagged `toolkit-v0.6.0` on that commit.
- Template `1.1.0` merged as hub PR 18 (`b33d309`), pinned to `c200fd2`.
- Sample PR 12 (`c8c8703`) moved the book to toolkit `0.6.0` and prepared `0.2.5`. Release run
  42989074637 published `v0.2.5` from `c8c8703` and deployed the reading site.
- The `catalog-update` workflow moved the catalog to `v0.2.5`. It is the first entry with
  `latest_release.assets`, so the catalog `schema_version` is now `1.1`.
- The exported template was pushed to `cesarcastrocuba/handbooks-template` and tagged
  `template-v1.1.0`; the repository was marked as a template under the delegation in `HUB-DEC-027`.

## Verified

| Check | Result |
| --- | --- |
| Release assets | Seven files: `book-html.zip`, `book.pdf`, `book.docx`, `book.md`, `book-source.zip`, `publication-manifest.json`, `SHA256SUMS.txt`; `sha256sum -c SHA256SUMS.txt` OK for the six listed files |
| Manifest | schema `1.1`, toolkit `0.6.0`, commit `c8c8703ac5109bc3c94c726db5c9177b18c6296b`, version `0.2.5`, roles `docx`, `html`, `markdown`, `pdf`, `source` |
| `book.md` | 2015 lines; control header with version `0.2.5`, status "Released edition" and the release commit |
| PDF | 57 pages (`pdfinfo`), title "Handbook Authoring and Publishing". The earlier note that `pdfinfo` printed "Suspects object is wrong type (boolean)" did not reproduce in the independent review; it is specific to that environment, not a property of the artifact |
| Reading site | HTTP 200 |
| Catalog dry run 42989439736 | `updated: handbook-authoring-and-publishing v0.2.4 -> v0.2.5 (published 2026-11-11)`; `release verification: OK`; publish skipped |
| Catalog real run 42989589682 | Success; pushed `catalog/handbook-authoring-and-publishing-v0.2.5` |
| `python3 -m handbook_toolkit.catalog_verification catalog/catalog.json` on this branch | `release verification: OK`, including the five download links against the manifest |
| Template export | `python3 tools/scripts/export_template.py` from `b33d309`: 18 files, `diff -r` against the pushed tree empty |
| Template mirror CI | `ci` succeeded on `main` of `handbooks-template` |
| Initialize dry run | Private throwaway repository `cesarcastrocuba/handbook-template-dryrun-delete-me` created from the mirror; `initialize-book` run 42989412165 succeeded and pushed `init/dry-run-handbook` changing `book.yaml`, `publishing/_quarto.yml`, `publishing/metadata.yaml`, `NOTICE.md`, `LICENSE-CODE` and `README.md` |

## Known gaps and follow-ups

- The throwaway repository still exists: the coordinator's token has no `delete_repo` scope. The
  Owner deletes it with `gh repo delete cesarcastrocuba/handbook-template-dryrun-delete-me --yes`.
- The template `release.yml` was not executed on GitHub: the dry run stopped after `initialize-book`.
  The sample book uses its own release workflow.
- `initialize-book` rewrites `book.yaml` through a YAML dump, which drops the comments and the quotes
  of the template descriptor. The result validates; keeping the comments is a follow-up.
- Chapter 7 and Appendices B and C of the sample book still describe a six-file release. That is
  manuscript content and needs its own editorial change in the book repository.
- `v0.2.4` stays published as the previous edition; no decision withdraws it.

## After merge

- A different agent reviewed PR 20 at `efc9f0c` and approved it with no Critical or Major findings;
  the review re-ran `make full`, the online `catalog_verification`, the portal build and the download
  of the seven assets. PR 20 merged as `b0f148b`.
- `portal-pages` run 42990936743 started on the `push` at `b0f148b`; its build and deploy jobs
  succeeded.
- Live checks after the deployment: the portal and its `llms.txt` return HTTP 200; the portal shows
  five edition buttons (PDF, HTML, DOCX, Markdown, Source) pointing at the `v0.2.5` assets and
  `llms.txt` lists `book.md` of `v0.2.5`; the reading site returns HTTP 200.
- `STATUS.md` records this state in the follow-up status change.
