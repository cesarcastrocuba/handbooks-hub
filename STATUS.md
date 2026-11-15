# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-15
**Phase:** Phases 1 to 5 complete. Every work package of change `0027` (WP0 to WP5) is merged: the
Word-index release is published (toolkit `0.10.3`, template `1.5.1` with its mirror tag
`template-v1.5.1`, and sample `v0.5.1`). Toolkit `0.11.0` is in review (change `0046`, PR 77) and
not tagged: it folds in the untagged 0.10.4 work (changes `0043`, `0044`, `0045`) and aligns the
portal and every edition with the design preview (`HUB-DEC-042`). A release round (toolkit, template and
sample `v0.5.2`) follows. Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.5.1`, and the catalog and portal list it with download
links; `v0.5.0` and older published editions remain available (`HUB-DEC-031`). `v0.4.2` and `v0.5.0`
show empty Contents, List of Tables and List of Figures in desktop Word until the reader presses F9,
and captioned tables show no banding (change `0038`); sample `v0.5.1` carries the fix, with cached
page numbers verified against LibreOffice destinations. The Owner tested the CI-built `book.docx` in
desktop Word twice on 2026-11-14 (`sdd/changes/0038-word-indexes/owner-test.md`) and accepted the
build of PR 70. Toolkit `0.10.3` is the released pin and template `1.5.1` pins it; the development
version is toolkit `0.11.0`, not tagged, which books do not pin yet: the release-gate fix (change
`0044`) and the deployed-site check (change `0045`) act in the hub, and the preview alignment
(change `0046`) reaches the books only after a toolkit tag and a template release. Tags `toolkit-v0.10.0` and
`toolkit-v0.10.2` exist and are not pinned. The Quarto portal is deployed and serves `v0.5.1` with
its styles. Changes reach `main` only through pull requests (`HUB-DEC-018`), with up-to-date
branches (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `b59e8d3c67c51f8c7d109f1cdb70121447b821e1`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). Change `0027` merged as PR 47 (audit record and decisions 036 to 040), PR 48 (documentation truth), PR 49 (toolkit release), PR 50 (edition preview in CI), PR 51 (documentation currency check), PR 52 (retrospective design record and font rights review), PR 53 (template release), PR 54 (catalog `v0.4.2`), PR 55 (native theme and list pages), PR 56 (authenticated release verification), PR 57 (release status), PR 58 (cover page, parts and reading experience, reviewed and merged by the independent reviewer), PR 59 (template release), PR 60 (figure paths in the print editions), PR 61 (catalog `v0.5.0`), PR 62 (release status), PR 63 (Quarto portal as an opt-in engine), PR 64 (deploy the Quarto portal, `HUB-DEC-041`), PR 65 (Word index caches), PR 66 (pinned actions and development dependencies, closes S2), PR 67 (Markdown figure and table numbering), PR 68 (interim status), PR 70 (Word list markers), PR 71 (site resources in a published path), PR 72 (release gate levels), PR 73 (catalog `v0.5.1`), PR 74 (native motion polish, change `0043`) and PR 75 (deployed-site check, change `0045`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.5.1` at `514f66c` (template `1.5.1` with toolkit `0.10.3`); `template-v1.5.0` remains at `6e864d3` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.5.1` is the current release, published by run 43686973539 from `77e7216` (sample `DEC-030`) with seven assets and toolkit `0.10.3`; its cached page numbers were verified against LibreOffice destinations. It is the first published edition with a figure (Figure 1.1) and a List of Figures, and it fixes the Word indexes of `v0.5.0` and `v0.4.2` (change `0038`). `v0.5.0` and older published editions remain available (`HUB-DEC-031`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.10.3`, tag `toolkit-v0.10.3` at `58384af`, 415 unit tests, is the released pin. It ships the theme generated from design tokens with one base in light and dark and no `!important`, native Quarto table, figure and listing pages, the split build modules, the generated cover page, reading-order parts, the edition footer, figures and List of Figures, the favicon and social metadata, native CSS motion and accessibility fixes, the figure-path fix for the print editions, cached page numbers for the Word indexes with no forced field update and direct cell banding (change `0038`), Markdown figure and table numbering aligned with the other editions (change `0041`), and site resources in a directory static hosts publish (change `0042`). The development version, toolkit `0.11.0` (PR 77, not tagged; the 0.10.4 number was never tagged), adds: the release gate no longer applies build rules newer than a published edition (change `0044`); once-only reveals, reading progress and hover, focus, details and theme micro-interactions in native CSS inside the reduced-motion guard (change `0043`, `HUB-DEC-038`), without the cross-document page transition, which change `0046` removes; `site_check`, which requests every local stylesheet, script and image of a deployed site (change `0045`); and the preview alignment (change `0046`, `HUB-DEC-042`): Bootstrap scale and radii from the tokens, compact portal card, chips and controls, whole-card guide links, and tables without stripes in the web, PDF and DOCX editions, with `#DDD3C0` rules between rows. Tags `toolkit-v0.10.0` and `toolkit-v0.10.2` exist and are not pinned |
| Template | `1.5.1`, on `main` and published as mirror tag `template-v1.5.1`; pins toolkit `0.10.3` at `58384af`. Its content is unchanged beyond the pin and the version statements: `publishing/_quarto.yml` already selects `dark: cosmo` and has no legacy navbar Tables entry, and the release workflow installs LibreOffice and passes `--require-page-numbers`, so the `0.10.1` to `0.10.2` upgrade note requires no further template change |
| CI | `portal-pages` run 43711965613 (manual dispatch from `b59e8d3`) deployed the portal from `main` (version 0.10.4, never tagged) and passed its first `verify` job: `site-check: 3 page(s), 27 asset(s), all 200` (change `0045`). Sample `v0.5.1` release run 43686973539 succeeded from `77e7216` and deployed the reading site; catalog real run 43687167357 verified the published bytes and pushed the branch merged as PR 73 (`9a15882`); `portal-pages` run 43687529695 deployed `v0.5.1` on its first attempt. Sample `v0.5.0` release run 43601118599 succeeded from `ba6666e` and deployed the reading site. Catalog real run 43601281045 verified the published bytes and pushed the branch merged as PR 61 (`a9aa01c`). `portal-pages` run 43601714414 deployed `v0.5.0` with the legacy portal on its first attempt, the first deployment after change `0035` (PR 56), which authenticates the GitHub API requests of `catalog_verification`; run 43617800145 (manual dispatch with `deploy=true`) deployed the Quarto portal (`HUB-DEC-041`); run 43666966237 failed because the release gate applied the new Word rules to the published `v0.5.0` (change `0044`); run 43686618540 redeployed the portal with its stylesheets served. The template release workflow installs LibreOffice and passes `--require-page-numbers` (change `0038`). Every pull request that changes the toolkit or the template builds an edition preview (`HUB-DEC-036`) |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. The published sample names Franz César Castro Cuba and includes a third-party notices page (`HUB-DEC-023`) |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.5.1` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-030`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.5.1` |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ as the Quarto website with the guide pages and the Design page; it serves every stylesheet and shows `v0.5.1` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source), and `llms.txt` lists the `book.md` of `v0.5.1` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Finish PR 77 (change `0046`): independent review, Owner acceptance of the localhost previews and of the edition-preview `book.docx` in desktop Word, merge.
2. Release round, each tag approved by the Owner: tag toolkit `0.11.0`; the next template release pins it and runs `site_check` in its release workflow (follow-up of change `0045`), mirror tag `template-v1.6.0`; sample `v0.5.2` after the Owner's Word check of its CI-built `book.docx`; catalog and portal deployment.
3. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Phase 6 has not started and needs an owner decision.
