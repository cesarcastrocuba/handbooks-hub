# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-14
**Phase:** Phases 1 to 5 complete. The native reading-experience release is published: toolkit
`0.10.1`, template `1.5.0` and sample `v0.5.0` (change `0027`, work packages WP3 and WP4). Phase 6
has not started and needs an owner decision.
**State:** The sample book is published at `v0.5.0`, and the catalog and portal list it with download
links; `v0.4.2` and older published editions remain available (`HUB-DEC-031`). It is the first
published edition with a figure (Figure 1.1) and a List of Figures. Toolkit 0.10.0 was tagged but is
not pinned by any template or book, because it cannot build the PDF or DOCX of a book with a figure
outside its first page; `0.10.1` fixes that (change `0037`). Toolkit `0.10.1` is tagged
`toolkit-v0.10.1` and ships the native reading site: token-generated light and dark theme, native
Quarto list pages, a cover page, parts, edition footer, figures and List of Figures, favicon and
social metadata, native CSS motion and the split build modules. Template `1.5.0` is on `main` and
pins toolkit `0.10.1`; the mirror `cesarcastrocuba/handbooks-template` is tagged `template-v1.5.0`.
Changes reach `main` only through pull requests (`HUB-DEC-018`), with up-to-date branches
(`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `a9aa01cdee64b90326e8fe4039e26c48b5d4130d`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). Change `0027` merged as PR 47 (audit record and decisions 036 to 040), PR 48 (documentation truth), PR 49 (toolkit release), PR 50 (edition preview in CI), PR 51 (documentation currency check), PR 52 (retrospective design record and font rights review), PR 53 (template release), PR 54 (catalog `v0.4.2`), PR 55 (native theme and list pages), PR 56 (authenticated release verification), PR 57 (release status), PR 58 (cover page, parts and reading experience, reviewed and merged by the independent reviewer), PR 59 (template `1.5.0`), PR 60 (figure paths in the print editions) and PR 61 (catalog `v0.5.0`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.5.0` at `6e864d3` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.5.0` is the current release, published by run 43601118599 from `ba6666e` (sample `DEC-028`, `DEC-029`). It is the first published edition with a figure (Figure 1.1) and a List of Figures. `v0.4.2` and older published editions remain available (`HUB-DEC-031`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.10.1`, tag `toolkit-v0.10.1` at `d4480f9`, 384 unit tests. It ships the theme generated from design tokens with one base in light and dark and no `!important`, native Quarto table, figure and listing pages, the split build modules, the generated cover page, reading-order parts, the edition footer, figures and List of Figures, the favicon and social metadata, native CSS motion and accessibility fixes, and the figure-path fix that lets the PDF and DOCX build a figure outside the first page |
| Template | `1.5.0`, merged as PR 59 (`972f835`); pins toolkit `0.10.1` at `d4480f9`, and the mirror tag `template-v1.5.0` is at `6e864d3`. Its content is unchanged beyond the pin and the version statements: `publishing/_quarto.yml` already selects `dark: cosmo` and has no legacy navbar Tables entry, so the `0.9.2` to `0.10.0` upgrade note requires no further template change |
| CI | Sample `v0.5.0` release run 43601118599 succeeded from `ba6666e` and deployed the reading site. Catalog real run 43601281045 verified the published bytes and pushed the branch merged as PR 61 (`a9aa01c`). `portal-pages` run 43601714414 deployed `v0.5.0` on its first attempt; it is the first deployment after change `0035` (PR 56), which authenticates the GitHub API requests of `catalog_verification`. Every pull request that changes the toolkit or the template builds an edition preview (`HUB-DEC-036`) |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. The published sample names Franz César Castro Cuba and includes a third-party notices page (`HUB-DEC-023`) |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.5.0` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-028`, `DEC-029`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.5.0` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.5.0` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.5.0` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner opens `book.docx` of `v0.5.0` in desktop Word and runs the acceptance checklist of the operations runbook, because no agent could do it (`HUB-DEC-040`).
2. Work package WP5 of change `0027` (the portal as a Quarto website) is in progress.
3. Align the Markdown edition's figure and table numbering with the other editions: it numbers them sequentially ("Figure 1") while the print and HTML editions number them by chapter ("Figure 1.1").
4. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Desktop Word acceptance of `v0.4.2` and `v0.5.0` is pending an owner action (`HUB-DEC-040`).
- Phase 6 has not started and needs an owner decision.
