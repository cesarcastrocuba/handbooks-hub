# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-14
**Phase:** Phases 1 to 5 complete. Toolkit `0.9.2` and template `1.4.2` are released; the sample is
still published at `v0.4.1`, and its upgrade to toolkit `0.9.2` is pending. Phase 6 has not started
and needs an owner decision.
**State:** The sample book is published at `v0.4.1`, and the catalog and portal list it with download
links; `v0.4.0` and older published editions remain available. Toolkit `0.9.2` is tagged
`toolkit-v0.9.2` and fixes the Word callout styles, the native Contents and caption-list fields, table
banding, font fallbacks, the DOCX validators and the List of Tables page rule. Template `1.4.2` is on
`main` and pins toolkit `0.9.2`; its mirror tag `template-v1.4.2` is pending the export that follows
this release. The sample's upgrade to toolkit `0.9.2` is pending. Changes reach `main` only through
pull requests (`HUB-DEC-018`), with up-to-date branches (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | Release state `2e294388ea4e4039744b14e4164301f6c085f587`, the merge of PR 49; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). The Word-field fixes merged as PR 49 (change `0029`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.4.1` at `9238849`; tag `template-v1.4.2` is pending the export after this release |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.4.1` is the current release, published by run 43472781256 from `e1ca349` (sample `DEC-026`). `v0.4.0` and older published editions remain available. `v0.2.2`, `v0.2.3` and earlier withdrawn editions keep their tags. Its upgrade to toolkit `0.9.2` is pending. Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.9.2`, tag `toolkit-v0.9.2` at `2e29438`, 359 unit tests. It ships Word callout styles with one definition each, native Contents and caption-list fields with cached entries, table banding from reference styles, font fallbacks, the DOCX validators and the List of Tables page rule |
| Template | `1.4.2`, on `main`; pins toolkit `0.9.2` at `2e29438`. Its content is unchanged beyond the pin and the version statements, because the `0.9.1` to `0.9.2` upgrade note requires no manuscript or configuration edit. Mirror tag `template-v1.4.2` is pending |
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
