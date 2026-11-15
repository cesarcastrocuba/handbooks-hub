# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-15
**Phase:** Phases 1 to 5 complete. Every work package of change `0027` (WP0 to WP5) is merged: the
native reading-experience release is published (toolkit `0.10.1`, template `1.5.0`, sample `v0.5.0`)
and the Quarto portal is deployed. Toolkit `0.10.3` is on `main`, not tagged; the Owner accepted
its Word edition in desktop Word on 2026-11-14. Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.5.0`, and the catalog lists it with download links;
`v0.4.2` and older published editions remain available (`HUB-DEC-031`). The Owner's first desktop
Word test found a defect in `v0.5.0` and `v0.4.2`: Contents, List of Tables and List of Figures are
empty on open until the reader updates the field with F9, and captioned tables show no banding
(change `0038`). The fix is on `main` and the Owner accepted the CI-built `book.docx` in desktop
Word (`sdd/changes/0038-word-indexes/owner-test.md`); `main` also numbers Markdown figures and
tables like the other editions (change `0041`). The deployed Quarto portal (`HUB-DEC-041`) renders
**without styles**: its stylesheets sat in a hidden directory that Pages does not publish, and a
book deployed with the template's Pages action would have the same defect (change `0042`). Toolkit
`0.10.3` fixes it on `main`; tag `toolkit-v0.10.2` exists and is not pinned by any template or
book. Toolkit `0.10.1` remains the released pin and template `1.5.0` pins it; the mirror
`cesarcastrocuba/handbooks-template` is tagged `template-v1.5.0`. Changes reach `main`
only through pull requests (`HUB-DEC-018`), with up-to-date branches (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `a170e65af9644f66bdc653ae63d796ef181ea44e`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). Change `0027` merged as PR 47 (audit record and decisions 036 to 040), PR 48 (documentation truth), PR 49 (toolkit release), PR 50 (edition preview in CI), PR 51 (documentation currency check), PR 52 (retrospective design record and font rights review), PR 53 (template release), PR 54 (catalog `v0.4.2`), PR 55 (native theme and list pages), PR 56 (authenticated release verification), PR 57 (release status), PR 58 (cover page, parts and reading experience, reviewed and merged by the independent reviewer), PR 59 (template `1.5.0`), PR 60 (figure paths in the print editions), PR 61 (catalog `v0.5.0`), PR 62 (release status), PR 63 (Quarto portal as an opt-in engine), PR 64 (deploy the Quarto portal, `HUB-DEC-041`), PR 65 (Word index caches), PR 66 (pinned actions and development dependencies, closes S2) and PR 67 (Markdown figure and table numbering) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.5.0` at `6e864d3` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.5.0` is the current release, published by run 43601118599 from `ba6666e` (sample `DEC-028`, `DEC-029`). It is the first published edition with a figure (Figure 1.1) and a List of Figures. `v0.5.0` and `v0.4.2` carry the Word index defect recorded in change `0038`. `v0.4.2` and older published editions remain available (`HUB-DEC-031`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.10.1`, tag `toolkit-v0.10.1` at `d4480f9`, 384 unit tests, is the released pin. It ships the theme generated from design tokens with one base in light and dark and no `!important`, native Quarto table, figure and listing pages, the split build modules, the generated cover page, reading-order parts, the edition footer, figures and List of Figures, the favicon and social metadata, native CSS motion and accessibility fixes, and the figure-path fix that lets the PDF and DOCX build a figure outside the first page. `main` carries `0.10.3`, not tagged: cached page numbers for the Word indexes, no forced field update, caption markers Word can rebuild a list from, direct cell banding, Markdown figure and table numbering aligned with the other editions, and site resources in a path static hosts publish (changes `0038`, `0041` and `0042`). Tag `toolkit-v0.10.2` exists and is not pinned |
| Template | `1.5.0`, merged as PR 59 (`972f835`); pins toolkit `0.10.1` at `d4480f9`, and the mirror tag `template-v1.5.0` is at `6e864d3`. Its content is unchanged beyond the pin and the version statements: `publishing/_quarto.yml` already selects `dark: cosmo` and has no legacy navbar Tables entry, so the `0.9.2` to `0.10.0` upgrade note requires no further template change |
| CI | Sample `v0.5.0` release run 43601118599 succeeded from `ba6666e` and deployed the reading site. Catalog real run 43601281045 verified the published bytes and pushed the branch merged as PR 61 (`a9aa01c`). `portal-pages` run 43601714414 deployed `v0.5.0` with the legacy portal on its first attempt, the first deployment after change `0035` (PR 56), which authenticates the GitHub API requests of `catalog_verification`; run 43617800145 (manual dispatch with `deploy=true`) deployed the Quarto portal (`HUB-DEC-041`). Every pull request that changes the toolkit or the template builds an edition preview (`HUB-DEC-036`) |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. The published sample names Franz César Castro Cuba and includes a third-party notices page (`HUB-DEC-023`) |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.5.0` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-028`, `DEC-029`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.5.0` |
| Portal | Live at https://cesarcastrocuba.github.io/handbooks-hub/ as the Quarto website with the guide pages and the Design page, **currently rendered without styles until it is redeployed from toolkit `0.10.3`** (change `0042`); it shows `v0.5.0` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source), and `llms.txt` lists the `book.md` of `v0.5.0` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Tag `toolkit-v0.10.3`, redeploy the portal and confirm its stylesheets are served.
2. Release template 1.5.1 and sample v0.5.1 pinned to it, and update the catalog.
3. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Phase 6 has not started and needs an owner decision.
