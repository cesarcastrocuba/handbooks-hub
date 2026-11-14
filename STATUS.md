# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-14
**Phase:** Phases 1 to 5 complete. The native reading-experience release is published: toolkit
`0.10.0` and template `1.5.0` (change `0027`, work packages WP3 and WP4); the sample is still
published at `v0.4.2`. Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.4.2`, and the catalog and portal list it with download
links; `v0.4.1` and older published editions remain available (`HUB-DEC-031`). The two failed
`portal-pages` attempts for `v0.4.2` were the GitHub API anonymous rate limit in
`catalog_verification`, which change `0035` (PR 56) now authenticates. Toolkit `0.10.0` is tagged
`toolkit-v0.10.0` and ships the native reading site: token-generated light and dark theme, native
Quarto list pages, a cover page, parts, edition footer, figures and List of Figures, favicon and
social metadata, native CSS motion and the split build modules. Template `1.5.0` is on `main` and
pins toolkit `0.10.0`; the mirror tag `template-v1.5.0` is pending the export that follows this
release. The sample's upgrade to toolkit `0.10.0` is pending. Changes reach `main` only through pull
requests (`HUB-DEC-018`), with up-to-date branches (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `dcfd8c86a616c931ae68450c60dbd220cfd49a08`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). Change `0027` merged as PR 47 (audit record and decisions 036 to 040), PR 48 (documentation truth), PR 49 (toolkit release), PR 50 (edition preview in CI), PR 51 (documentation currency check), PR 52 (retrospective design record and font rights review), PR 53 (template release), PR 54 (catalog `v0.4.2`), PR 55 (native theme and list pages), PR 56 (authenticated release verification), PR 57 (release status) and PR 58 (cover page, parts and reading experience) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.4.2` at `b7ca872`; tag `template-v1.5.0` is pending the export after this release |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.4.2` is the current release, published by run 43579133589 from `a59185e` (sample `DEC-027`). `v0.4.1` and older published editions remain available (`HUB-DEC-031`). `v0.2.2`, `v0.2.3` and earlier withdrawn editions keep their tags. Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.10.0`, tag `toolkit-v0.10.0` at `dcfd8c8`, 378 unit tests. It ships the theme generated from design tokens with one base in light and dark and no `!important`, native Quarto table, figure and listing pages, the split build modules, the generated cover page, reading-order parts, the edition footer, figures and List of Figures, the favicon and social metadata, native CSS motion and accessibility fixes |
| Template | `1.5.0`, on `main`; pins toolkit `0.10.0` at `dcfd8c8`. Its content is unchanged beyond the pin and the version statements: `publishing/_quarto.yml` already selects `dark: cosmo` and has no legacy navbar Tables entry, so the `0.9.2` to `0.10.0` upgrade note requires no further template change. Mirror tag `template-v1.5.0` is pending |
| CI | Sample `v0.4.2` release run 43579133589 succeeded from `a59185e` and deployed the reading site. Catalog real run 43579293962 verified the published bytes and pushed the branch merged as PR 54 (`66a6a0a`). `portal-pages` run 43579566245 deployed `v0.4.2` on its third attempt; the first two failed with `remote asset returned HTTP 403`, the GitHub API anonymous rate limit in `catalog_verification`, which change `0035` (PR 56) now authenticates. Every pull request that changes the toolkit or the template builds an edition preview (`HUB-DEC-036`) |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. The published sample names Franz César Castro Cuba and includes a third-party notices page (`HUB-DEC-023`) |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.4.2` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-027`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.4.2` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.4.2` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.4.2` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner opens `book.docx` of `v0.4.2` in desktop Word and runs the acceptance checklist of the operations runbook, because no agent could do it (`HUB-DEC-040`).
2. Work package WP5 of change `0027` is in progress.
3. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Desktop Word acceptance of `v0.4.2` is pending an owner action (`HUB-DEC-040`).
- Phase 6 has not started and needs an owner decision.
