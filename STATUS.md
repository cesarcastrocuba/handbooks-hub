# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-14
**Phase:** Phases 1 to 5 complete. The Word-field release is published: toolkit `0.9.2`, template
`1.4.2` and sample `v0.4.2` (change `0027`, `HUB-DEC-040`). Phase 6 has not started and needs an
owner decision.
**State:** The sample book is published at `v0.4.2`, and the catalog and portal list it with download
links; `portal-pages` deployed `v0.4.2` on its third attempt after two transient asset `403` failures
in `catalog_verification`. `v0.4.1` and older published editions remain available (`HUB-DEC-031`).
Toolkit `0.9.2` is tagged `toolkit-v0.9.2` and fixes the Word callout styles, the native Contents and
caption-list fields, table banding, font fallbacks, the DOCX validators and the List of Tables page
rule. Template `1.4.2` is on `main` and pins toolkit `0.9.2`; the mirror
`cesarcastrocuba/handbooks-template` is tagged `template-v1.4.2`. Changes reach `main` only through
pull requests (`HUB-DEC-018`), with up-to-date branches (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `66a6a0a94a22904b1eb832e99d1d147797478861`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). Change `0027` merged as PR 47 (audit record and decisions 036 to 040), PR 48 (documentation truth), PR 49 (toolkit `0.9.2`), PR 50 (edition preview in CI), PR 51 (documentation currency check), PR 52 (retrospective design record and font rights review), PR 53 (template `1.4.2`) and PR 54 (catalog `v0.4.2`); the merged branches were deleted, leaving six remote branches |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.4.2` at `b7ca872` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.4.2` is the current release, published by run 43579133589 from `a59185e` (sample `DEC-027`). `v0.4.1` and older published editions remain available (`HUB-DEC-031`). `v0.2.2`, `v0.2.3` and earlier withdrawn editions keep their tags. Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.9.2`, tag `toolkit-v0.9.2` at `2e29438`, 359 unit tests. It ships Word callout styles with one definition each, native Contents and caption-list fields with cached entries, table banding from reference styles, font fallbacks, the DOCX validators and the List of Tables page rule |
| Template | `1.4.2`, merged as PR 53 (`2b679f5`); pins toolkit `0.9.2` at `2e29438`, and the mirror tag `template-v1.4.2` is at `b7ca872`. Its content is unchanged beyond the pin and the version statements, because the `0.9.1` to `0.9.2` upgrade note requires no manuscript or configuration edit |
| CI | Sample `v0.4.2` release run 43579133589 succeeded from `a59185e` and deployed the reading site. Catalog real run 43579293962 verified the published bytes and pushed the branch merged as PR 54 (`66a6a0a`). `portal-pages` run 43579566245 deployed `v0.4.2` on its third attempt; the first two failed with `remote asset returned HTTP 403` in `catalog_verification`. Every pull request that changes the toolkit or the template builds an edition preview (`HUB-DEC-036`) |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. The published sample names Franz César Castro Cuba and includes a third-party notices page (`HUB-DEC-023`) |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.4.2` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-027`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.4.2` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.4.2` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.4.2` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner opens `book.docx` of `v0.4.2` in desktop Word and runs the acceptance checklist of the operations runbook, because no agent could do it (`HUB-DEC-040`).
2. Work packages WP3, WP4 and WP5 of change `0027` are in progress.
3. Add a bounded retry to `catalog_verification` for the transient asset HTTP `403` seen in `portal-pages` for `v0.4.1` and `v0.4.2`.
4. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Desktop Word acceptance of `v0.4.2` is pending an owner action (`HUB-DEC-040`).
- Phase 6 has not started and needs an owner decision.
