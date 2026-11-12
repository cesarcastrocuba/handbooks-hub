# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-12
**Phase:** Phases 1 to 5 complete. The plan recorded in change `0018` (Phases 0 to D) is complete,
and the unified design was released on 2026-11-12 (`HUB-DEC-032`): toolkit `0.7.0`, template `1.2.0`
and sample `v0.2.7`. Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.2.7`, and the catalog and portal list it with download
links; `portal-pages` deployed `v0.2.7` from the catalog change. `v0.2.6`, `v0.2.5` and `v0.2.4` stay
published as previous editions. Template `1.2.0` is published as the generated mirror
`cesarcastrocuba/handbooks-template`, tagged `template-v1.2.0`. Toolkit `0.7.0` is tagged
`toolkit-v0.7.0` and ships the design contract, the brand typeface and the generated web/PDF/DOCX
surfaces. `HUB-DEC-031` keeps every published release available, and a release is withdrawn only for
a recorded reason and by an explicit Owner decision. Changes reach `main` only through pull requests
(`HUB-DEC-018`), and a branch must be up to date with `main` before merge (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `7e11f4427d5fe6fa9c14cbcf285e52588dad1bd7`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). The design and release increments merged as PR 27 (design, `3ee1bd0`), PR 28 (toolkit `0.7.0`, `b2de280`), PR 29 (changelog, `e34ec02`) and PR 30 (catalog `v0.2.7`, `7e11f44`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.2.0` at `24e8f0d` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.7` is the current release, published by run 43290998984 from `49f2209` (sample `DEC-023`). `v0.2.6`, `v0.2.5` and `v0.2.4` remain published as previous editions. `v0.2.2` is withdrawn and keeps its tag (`HUB-DEC-027`). `v0.2.3` is withdrawn and keeps its tag (sample `DEC-019`). `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). `v0.2.1` is withdrawn and keeps its tag (`HUB-DEC-023`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.7.0`, tag `toolkit-v0.7.0` at `e34ec02`, 303 unit tests. It ships the design contract, the self-hosted brand fonts, generated portal/book/PDF/DOCX values and the Markdown leak-guard fix |
| Template | `1.2.0`, tag `template-v1.2.0` at `24e8f0d`; pins toolkit `0.7.0` at `12dc655`. It adds search, report-an-issue, source/downloads links, a light/dark theme and correction/proposal issue forms. The earlier `template-v1.1.1` end-to-end run remains recorded in this table's history and in change `0020` |
| CI | Sample `v0.2.7` release run 43290998984 succeeded from `49f2209` and deployed the reading site. Catalog dry run 43291318492 and real run 43291520986 verified the published bytes and pushed the branch merged as PR 30 (`7e11f44`). `portal-pages` run 43292300649 deployed `v0.2.7`. Design CI on PR 27 and release CI on PR 28 and PR 30 passed |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. Sample `v0.2.7` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.2.7` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-023`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.2.7` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.2.7` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.2.7` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner deletes the throwaway repository and its public Pages site: `gh repo delete cesarcastrocuba/handbook-template-dryrun-delete-me --yes`; the delegated token has no `delete_repo` scope.
2. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- The throwaway repository `cesarcastrocuba/handbook-template-dryrun-delete-me` and its public Pages site still exist and need the Owner's deletion.
- Phase 6 has not started and needs an owner decision.
