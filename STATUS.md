# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-13
**Phase:** Phases 1 to 5 complete. The rendered-detail release is published: toolkit `0.9.1`,
template `1.4.1` and sample `v0.4.1` (`HUB-DEC-035`). Phase 6 has not started and needs an owner
decision.
**State:** The sample book is published at `v0.4.1`, and the catalog and portal list it with download
links; `portal-pages` deployed `v0.4.1`. `v0.4.0` and older published editions remain available.
Template `1.4.1` is published as the generated mirror `cesarcastrocuba/handbooks-template`, tagged
`template-v1.4.1`. Toolkit `0.9.1` is tagged `toolkit-v0.9.1` and ships the aligned hub/book column,
sidebar List of Tables, callout table tint, neutral review callouts and the rebuilt Word layout.
Changes reach `main` only through pull requests (`HUB-DEC-018`), with up-to-date branches
(`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | Release state `97494ee2716ee28ae373c15d2685a6b1c3ebc666`, status record merged as PR 45 (`f297f92`); protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). The rendered-detail fixes merged as PR 42 (design, `463bdb5`), PR 43 (toolkit `0.9.1`, `f1ffe9d`) and PR 44 (catalog `v0.4.1`, `97494ee`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.4.1` at `9238849` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.4.1` is the current release, published by run 43472781256 from `e1ca349` (sample `DEC-026`). `v0.4.0` and older published editions remain available. `v0.2.2`, `v0.2.3` and earlier withdrawn editions keep their tags. Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.9.1`, tag `toolkit-v0.9.1` at `298d703`, 308 unit tests. It ships the 1300 px hub/book column, sidebar List of Tables, callout table tint, neutral review callouts, code blocks and the rebuilt Word callout/list/licence layout |
| Template | `1.4.1`, tag `template-v1.4.1` at `9238849`; pins toolkit `0.9.1` at `298d703`. It carries the aligned chrome, sidebar Tables link, neutral review callouts and the rebuilt Word layout |
| CI | Sample `v0.4.1` release run 43472781256 succeeded from `e1ca349` and deployed the reading site. Catalog real run 43473399400 verified the published bytes and pushed the branch merged as PR 44 (`97494ee`). `portal-pages` run 43474125855 deployed `v0.4.1` after a transient asset 403 was retried. Design CI on PR 42 and release CI on PR 43/44 passed |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. The published sample names Franz César Castro Cuba and includes a third-party notices page (`HUB-DEC-023`) |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.4.1` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-026`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.4.1` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.4.1` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.4.1` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- Phase 6 has not started and needs an owner decision.
