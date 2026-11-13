# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-13
**Phase:** Phases 1 to 5 complete. The plan recorded in change `0018` (Phases 0 to D) and the design
refinement are released: toolkit `0.8.0`, template `1.3.0` and sample `v0.3.0` (`HUB-DEC-033`).
Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.3.0`, and the catalog and portal list it with download
links; `portal-pages` deployed `v0.3.0` from the catalog change. `v0.2.7`, `v0.2.6`, `v0.2.5` and
`v0.2.4` remain published as previous editions. Template `1.3.0` is published as the generated mirror
`cesarcastrocuba/handbooks-template`, tagged `template-v1.3.0`. Toolkit `0.8.0` is tagged
`toolkit-v0.8.0` and ships Source Sans 3/Source Serif 4, the compact portal, the book chrome and the
unified table/document styles. `HUB-DEC-031` keeps every published release available. Changes reach
`main` only through pull requests (`HUB-DEC-018`), and a branch must be up to date before merge
(`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `40fb2d7acfd630a5fdaf8b2e0f546345cbbf28ed`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). The refinement and release merged as PR 32 (design, `3c5a7d9`), PR 33 (toolkit `0.8.0`, `9921dbe`) and PR 34 (catalog `v0.3.0`, `40fb2d7`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.3.0` at `5974fc2` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.3.0` is the current release, published by run 43342066827 from `3322411` (sample `DEC-024`). `v0.2.7`, `v0.2.6`, `v0.2.5` and `v0.2.4` remain published as previous editions. `v0.2.2` is withdrawn and keeps its tag (`HUB-DEC-027`). `v0.2.3` is withdrawn and keeps its tag (sample `DEC-019`). `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). `v0.2.1` is withdrawn and keeps its tag (`HUB-DEC-023`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.8.0`, tag `toolkit-v0.8.0` at `9921dbe`, 303 unit tests. It ships Source Sans 3/Source Serif 4, the compact portal, book chrome, a single table caption/List of Tables system and the rebuilt DOCX |
| Template | `1.3.0`, tag `template-v1.3.0` at `5974fc2`; pins toolkit `0.8.0` at `b01a4c6`. It carries the refined type, compact scale, search, report-an-issue, source/downloads links, light/dark theme and correction/proposal issue forms |
| CI | Sample `v0.3.0` release run 43342066827 succeeded from `3322411` and deployed the reading site. Catalog dry run 43342284030 and real run 43342419259 verified the published bytes and pushed the branch merged as PR 34 (`40fb2d7`). `portal-pages` run 43342897423 deployed `v0.3.0`. Design CI on PR 32 and release CI on PR 33/34 passed |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. Sample `v0.2.7` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.3.0` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-024`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.3.0` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.3.0` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.3.0` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner deletes the throwaway repository and its public Pages site: `gh repo delete cesarcastrocuba/handbook-template-dryrun-delete-me --yes`; the delegated token has no `delete_repo` scope.
2. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- The throwaway repository `cesarcastrocuba/handbook-template-dryrun-delete-me` and its public Pages site still exist and need the Owner's deletion.
- Phase 6 has not started and needs an owner decision.
