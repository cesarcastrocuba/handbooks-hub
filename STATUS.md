# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-14
**Phase:** Phases 1 to 5 complete. Every work package of change `0027` (WP0 to WP5) is merged: the
Word-index release is published (toolkit `0.10.2`, template `1.5.1`) and the Quarto portal is
deployed. The fix reaches readers in sample `v0.5.1`, which is pending. Phase 6 has not started and
needs an owner decision.
**State:** The sample book is published at `v0.5.0`, and the catalog lists it with download links;
`v0.4.2` and older published editions remain available (`HUB-DEC-031`). `v0.4.2` and `v0.5.0` show
empty Contents, List of Tables and List of Figures in desktop Word until the reader presses F9, and
captioned tables show no banding (change `0038`); `v0.5.1` will carry the fix. The Owner tested the
CI-built `book.docx` in desktop Word twice on 2026-11-14 (`sdd/changes/0038-word-indexes/owner-test.md`)
and accepted the build of PR 70, so toolkit `0.10.2` is tagged `toolkit-v0.10.2`; template `1.5.1`
is on `main` and pins it, and the mirror tag `template-v1.5.1` is pending. The sample's upgrade to toolkit
`0.10.2` is pending. The Quarto portal is deployed (`HUB-DEC-041`). Changes reach `main` only through
pull requests (`HUB-DEC-018`), with up-to-date branches (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `efc4c40c9c22fb5e5d2f50bf4cde189f304d0146`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). Change `0027` merged as PR 47 (audit record and decisions 036 to 040), PR 48 (documentation truth), PR 49 (toolkit release), PR 50 (edition preview in CI), PR 51 (documentation currency check), PR 52 (retrospective design record and font rights review), PR 53 (template release), PR 54 (catalog `v0.4.2`), PR 55 (native theme and list pages), PR 56 (authenticated release verification), PR 57 (release status), PR 58 (cover page, parts and reading experience, reviewed and merged by the independent reviewer), PR 59 (template release), PR 60 (figure paths in the print editions), PR 61 (catalog `v0.5.0`), PR 62 (release status), PR 63 (Quarto portal as an opt-in engine), PR 64 (deploy the Quarto portal, `HUB-DEC-041`), PR 65 (Word index caches), PR 66 (pinned actions and development dependencies, closes S2), PR 67 (Markdown figure and table numbering), PR 68 (interim status) and PR 70 (Word list markers) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.5.0` at `6e864d3`; tag `template-v1.5.1` is pending the export after this release |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.5.0` is the current release, published by run 43601118599 from `ba6666e` (sample `DEC-028`, `DEC-029`). It is the first published edition with a figure (Figure 1.1) and a List of Figures. `v0.5.0` and `v0.4.2` carry the Word index defect recorded in change `0038`; `v0.5.1` will carry the fix. Its upgrade to toolkit `0.10.2` is pending. `v0.4.2` and older published editions remain available (`HUB-DEC-031`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.10.2`, tag `toolkit-v0.10.2` at `efc4c40`, 411 unit tests. It ships the theme generated from design tokens with one base in light and dark and no `!important`, native Quarto table, figure and listing pages, the split build modules, the generated cover page, reading-order parts, the edition footer, figures and List of Figures, the favicon and social metadata, native CSS motion and accessibility fixes, the figure-path fix for the print editions, cached page numbers for the Word indexes with no forced field update and direct cell banding (change `0038`), and Markdown figure and table numbering aligned with the other editions (change `0041`) |
| Template | `1.5.1`, on `main`; pins toolkit `0.10.2` at `efc4c40`, and the mirror tag `template-v1.5.1` is pending. Its content is unchanged beyond the pin and the version statements: `publishing/_quarto.yml` already selects `dark: cosmo` and has no legacy navbar Tables entry, and the release workflow installs LibreOffice and passes `--require-page-numbers`, so the `0.10.1` to `0.10.2` upgrade note requires no further template change |
| CI | Sample `v0.5.0` release run 43601118599 succeeded from `ba6666e` and deployed the reading site. Catalog real run 43601281045 verified the published bytes and pushed the branch merged as PR 61 (`a9aa01c`). `portal-pages` run 43601714414 deployed `v0.5.0` with the legacy portal on its first attempt, the first deployment after change `0035` (PR 56), which authenticates the GitHub API requests of `catalog_verification`; run 43617800145 (manual dispatch with `deploy=true`) deployed the Quarto portal (`HUB-DEC-041`). The template release workflow installs LibreOffice and passes `--require-page-numbers` (change `0038`). Every pull request that changes the toolkit or the template builds an edition preview (`HUB-DEC-036`) |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. The published sample names Franz César Castro Cuba and includes a third-party notices page (`HUB-DEC-023`) |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.5.0` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-028`, `DEC-029`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.5.0` |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ as the Quarto website with the guide pages and the Design page; it shows `v0.5.0` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source), and `llms.txt` lists the `book.md` of `v0.5.0` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. After this merge, export `template/book/` with `python3 tools/scripts/export_template.py`, push it to `cesarcastrocuba/handbooks-template` and tag `template-v1.5.1`.
2. Upgrade the sample to toolkit `0.10.2` and publish `v0.5.1`, which carries the Word index fix; then update the catalog.
3. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Phase 6 has not started and needs an owner decision.
