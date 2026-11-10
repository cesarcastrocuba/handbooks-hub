# Evidence — Release `v0.2.4` and catalog listing

**Decision:** sample `DEC-019` (Owner instruction 2026-11-10). **Recorded:** 2026-11-10.

## What happened

- Sample PR 8 prepared the corrections from the independent review of the `v0.2.0` front matter and
  appendices as `v0.2.3`. Release `v0.2.3` was dispatched before PR 8 merged and was built from
  `7b835a5`: it carried the `v0.2.2` manuscript under the `0.2.3` label.
- Release assets are never replaced under an existing tag. The Owner decided to withdraw `v0.2.3` and
  publish the corrections as `v0.2.4`. The `v0.2.3` release page and assets were deleted and its tag
  stays at `7b835a5`. A second dispatch for `v0.2.3` stopped at the "tag already exists" guard
  (run 42793137439) and published nothing.
- Sample PR 9 moved the prepared edition to `0.2.4`, and release run 42810374270 published it from
  `cd99d7a`.

## Verified

| Check | Result |
| --- | --- |
| Release assets | Six files; `sha256sum -c SHA256SUMS.txt` OK for the five listed files |
| PDF | 57 pages; title page "Version 0.2.4"; author Franz César Castro Cuba; contains the new Appendix B gate checklists and glossary entry |
| Manifest | commit `cd99d7ae4f940cdcde3dff309d02358d1c7899b1`, version `0.2.4` |
| Reading site | HTTP 200 |
| Catalog dry run 42810626248 | `updated: handbook-authoring-and-publishing v0.2.2 -> v0.2.4 (published 2026-11-10)`; `release verification: OK`; publish skipped |
| Catalog real run 42810762259 | Success; pushed `catalog/handbook-authoring-and-publishing-v0.2.4` at `fd1a617` |

## Still to happen

- After merge, `portal-pages` should deploy on its own (`HUB-DEC-024`, change `0015`). This is the
  first catalog change since that trigger landed; the result is recorded after merge.

## Not run

- No sample artifact build was run in this hub change.
- `v0.2.2` stays published; no withdrawal was decided for it.
