# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-11
**Phase:** Phases 1 to 5 complete. The plan recorded in change `0018` (Phases 0 to D) is complete:
withdrawal of `v0.2.2`, Markdown edition, author onboarding, template mirror, library portal and the
sample `v0.2.6` follow-up. Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.2.6`, and the catalog and portal list it with download
links; `portal-pages` deployed `v0.2.6` from the catalog change. `v0.2.5` and `v0.2.4` stay published
as previous editions. Template `1.1.1` is published as the generated mirror
`cesarcastrocuba/handbooks-template`, tagged `template-v1.1.1`. Toolkit `0.6.0` is tagged and carries
one fix merged after the tag (the Markdown leak guard, PR 24), which ships with the next toolkit
version. `HUB-DEC-028`, `HUB-DEC-029` and `HUB-DEC-030` are still **Proposed**: only the Owner
approves a decision. Changes reach `main` only through pull requests (`HUB-DEC-018`), and a branch
must be up to date with `main` before merge (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `2dc324ec9fc1a8ad9b6e7c6ab6deb02229b52629`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). The plan's increments merged as PR 15 (decision, withdrawal), PR 18 (template `1.1.0`), PR 19 (toolkit `0.6.0`), PR 20 (catalog `v0.2.5`), PR 23 (catalog `v0.2.6`, merge `a5dc0c9`) and PR 24 (leak guard) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.1.1` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.6` is the current release, published by run 43063144576 from `1d73db9`. `v0.2.5` and `v0.2.4` remain published as previous editions. `v0.2.2` is withdrawn and keeps its tag (`HUB-DEC-027`). `v0.2.3` is withdrawn and keeps its tag (sample `DEC-019`). `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). `v0.2.1` is withdrawn and keeps its tag (`HUB-DEC-023`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.6.0`, tag `toolkit-v0.6.0` at `c200fd2`, 269 unit tests. One fix merged after the tag: the Markdown leak guard now detects escaped paths (PR 24, recorded under `Unreleased`); it ships with the next toolkit version, so books re-pin when that version is tagged |
| Template | `1.1.1`, tag `template-v1.1.1`; pins toolkit `0.6.0` at `c200fd2`. The `release.yml` tag check through the API was verified on GitHub in the throwaway repository (runs 43041194049 failure, then 43041314185 success). The comment- and quote-preserving `initialize_book.py` was verified locally only, through unit tests and a real initialization of an exported copy (review of PR 22); it has not run on GitHub from the `template-v1.1.1` tree |
| CI | Sample `v0.2.6` release run 43063144576 succeeded from `1d73db9` and deployed the reading site. Catalog dry run 43063528094 reported `v0.2.5` to `v0.2.6` and `release verification: OK`; real run 43063675117 pushed the catalog branch merged as PR 23 (`a5dc0c9`). `portal-pages` run 43069666080 started on the `push` at `a5dc0c9` and its build and deploy jobs succeeded |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). Sample `v0.2.6` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.2.6` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-022`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.2.6` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, showing `v0.2.6` with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.2.6` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner confirmation of `HUB-DEC-028`, `HUB-DEC-029` and `HUB-DEC-030`: their rows stay **Proposed** until the Owner approves them.
2. Owner deletes the throwaway repository and its public Pages site: `gh repo delete cesarcastrocuba/handbook-template-dryrun-delete-me --yes`; the delegated token has no `delete_repo` scope.
3. Owner decision on whether `v0.2.4` and `v0.2.5` stay published: no decision withdraws them, so they remain available as previous editions.
4. The next toolkit version ships the Markdown leak-guard fix; books re-pin when it is tagged.
5. End-to-end template check: create a new repository from the `template-v1.1.1` tree and run `initialize-book` there. It has not been done; only the `release.yml` tag check ran on GitHub, and `initialize_book.py` was verified locally.
6. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- `HUB-DEC-028`, `HUB-DEC-029` and `HUB-DEC-030` are **Proposed**. They were merged under the delegation in `HUB-DEC-027`, but only the Owner approves a decision, so the Owner must confirm each one before it changes status.
- The throwaway repository `cesarcastrocuba/handbook-template-dryrun-delete-me` and its public Pages site still exist and need the Owner's deletion.
- Whether `v0.2.4` and `v0.2.5` stay published is an open owner decision.
- Phase 6 has not started and needs an owner decision.
