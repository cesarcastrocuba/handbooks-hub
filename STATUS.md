# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-13
**Phase:** Phases 1 to 5 complete. The 0.9 design polish is released: toolkit `0.9.0`, template `1.4.0`
and sample `v0.4.0` (`HUB-DEC-034`). Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.4.0`, and the catalog and portal list it with download
links; `portal-pages` deployed `v0.4.0`. `v0.3.0` and older published editions remain available.
Template `1.4.0` is published as the generated mirror `cesarcastrocuba/handbooks-template`, tagged
`template-v1.4.0`. Toolkit `0.9.0` is tagged `toolkit-v0.9.0` and ships the compact web chrome, shared
callout palette, cream Word page, table captions/lists and atomic callouts. Changes reach `main` only
through pull requests (`HUB-DEC-018`), with up-to-date branches (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `4635ea64f1ebfae776b0f4ea6dd8abb0acfc8da1`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). The polish merged as PR 36 (design, `6e43a37`), PR 37 (toolkit `0.9.0`, `7d5313e`), PR 38 (callout fix, `e6c18d0`), PR 39 (template pin, `48a70c9`) and PR 40 (catalog `v0.4.0`, `4635ea6`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.4.0` at `d6c35f1` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.4.0` is the current release, published by run 43428501092 from `12f8d46` (sample `DEC-025`). `v0.3.0` and older published editions remain available. `v0.2.2`, `v0.2.3` and earlier withdrawn editions keep their tags. Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.9.0`, tag `toolkit-v0.9.0` at `e6c18d0`, 304 unit tests. It ships the compact hub/book chrome, cream PDF/DOCX canvas, shared callouts, table stripes and the static Word List of Tables |
| Template | `1.4.0`, tag `template-v1.4.0` at `d6c35f1`; pins toolkit `0.9.0` at `e6c18d0`. It carries the polish, Pages library link, Tables navigation and the current design surfaces |
| CI | Sample `v0.4.0` release run 43428501092 succeeded from `12f8d46` and deployed the reading site. Catalog real run 43428892331 verified the published bytes and pushed the branch merged as PR 40 (`4635ea6`). `portal-pages` run 43429487649 deployed `v0.4.0`. Design CI on PR 36/38 and release CI on PR 37/39/40 passed |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). The web fonts are renamed OFL subsets, published with their `OFL.txt` notices. Sample `v0.2.7` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.4.0` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-025`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.4.0` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.4.0` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.4.0` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner deletes the throwaway repository and its public Pages site: `gh repo delete cesarcastrocuba/handbook-template-dryrun-delete-me --yes`; the delegated token has no `delete_repo` scope.
2. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- The throwaway repository `cesarcastrocuba/handbook-template-dryrun-delete-me` and its public Pages site still exist and need the Owner's deletion.
- Phase 6 has not started and needs an owner decision.
