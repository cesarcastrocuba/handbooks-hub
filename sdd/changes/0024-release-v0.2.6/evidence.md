# Evidence — Release `v0.2.6`, template `1.1.1` and the template release dry run

**Authorization:** Owner instruction 2026-11-11, "Ejecuta 1,2,3 y4 por favor", answering the four
follow-ups listed after Phase D: (1) correct the six-file description in the sample manuscript,
(2) keep comments when `initialize-book` rewrites `book.yaml`, (3) run the template release
workflow on GitHub, (4) remove the leftover worktree. Sample decision `DEC-022`.
**Recorded:** 2026-11-11.

## What happened

- **Template release dry run.** In the private throwaway repository
  `cesarcastrocuba/handbook-template-dryrun-delete-me` the initialization pull request was merged
  and the template `release.yml` was dispatched for `0.1.0`. Run 43041194049 failed in "Validate the
  request": the workflow checks out without persisted credentials and then ran
  `git fetch --tags`, which a private repository refuses. With the tag check moved to the API, run
  43041314185 built, published seven assets and deployed Pages.
- **Template `1.1.1`** (hub PR 22, `a3543fa`): `initialize_book.py` edits the three YAML files as
  text and keeps comments and quoting, and `release.yml` carries the tag check verified above. The
  export was pushed to `cesarcastrocuba/handbooks-template` and tagged `template-v1.1.1`.
- **Sample `v0.2.6`** (sample PR 14, `1d73db9`): Chapter 7, Appendix B and Appendix C now describe
  a seven-file release. Release run 43063144576 published it.
- **Catalog**: `catalog-update` moved the entry from `v0.2.5` to `v0.2.6`.

## Verified

| Check | Result |
| --- | --- |
| Throwaway release `v0.1.0` | Seven assets; `sha256sum -c` OK for the six listed files; `book.md` opens with the control header of "Dry Run Handbook" `0.1.0`; Pages URL HTTP 200 |
| Hub PR 22 by the reviewer | `make full`: 268 tests OK; an exported copy initialized with a title containing a colon, quotes and `#` differs from the template `book.yaml` only in the six value lines; `validate-book --full` OK |
| Template mirror | `export_template.py` from `a3543fa`: 18 files, `diff -r` against the pushed tree empty; tags `template-v1.1.0` and `template-v1.1.1` |
| Sample PR 14 by the reviewer | No "six-file", "six files" or "six assets" left in `manuscript/`; `make check` and `make full` pass with the pinned toolkit; local build seven files. Review record in the book: `docs/editorial/reviews/v0.2.6-reviews.md` |
| Release `v0.2.6` assets | Seven files; `sha256sum -c SHA256SUMS.txt` OK for the six listed files; manifest schema `1.1`, toolkit `0.6.0`, commit `1d73db9d4784ce31424f25892f647b0cc974c0e0`; `book.md` has no six-file wording |
| Catalog dry run 43063528094 | `updated: handbook-authoring-and-publishing v0.2.5 -> v0.2.6 (published 2026-11-11)`; `release verification: OK` |
| Catalog real run 43063675117 | Success; pushed `catalog/handbook-authoring-and-publishing-v0.2.6` |
| `catalog_verification` on this branch | First local run `FAILED`, second run minutes later `OK`. The first failure was not captured; the likely cause is the reading site still propagating after the release |

## Incidents

- Sample release runs 43044978372 and 43046711504 and five attempts of the `publication-build` job
  of hub PR 22 failed in `apt-get install poppler-utils` with
  `Temporary failure resolving 'azure.archive.ubuntu.com'`. Nothing was published and no tag was
  created by the failed runs. Both succeeded once the runner network recovered.

## Known gaps

- The throwaway repository and its public Pages site still exist; the Owner deletes it with
  `gh repo delete cesarcastrocuba/handbook-template-dryrun-delete-me --yes`.
- The fixed `release.yml` was verified on GitHub as a patch in the throwaway repository; the
  `template-v1.1.1` tree itself was not used to create a second repository.
- `v0.2.4` and `v0.2.5` stay published; no decision withdraws them.
