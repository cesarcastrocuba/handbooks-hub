# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-11
**Phase:** Phases 1 to 5 complete. The plan recorded in change `0018` (Phases 0 to D) is complete:
withdrawal of `v0.2.2`, Markdown edition, author onboarding, template mirror, library portal and
sample `v0.2.5`. Phase 6 has not started and needs an owner decision.
**State:** The sample book is published at `v0.2.5`, and the catalog lists it with download links;
the portal deployed the library design from that catalog change (`portal-pages` run 42990936743).
Toolkit `0.6.0` adds a fifth payload, `book.md`, and publication manifest schema `1.1`; template
`1.1.0` is published as the generated mirror `cesarcastrocuba/handbooks-template`. `v0.2.4` stays
published as the previous edition, and `v0.2.2` is withdrawn with its tag kept (`HUB-DEC-027`).
`HUB-DEC-028`, `HUB-DEC-029` and `HUB-DEC-030` are merged but still **Proposed**: only the Owner
approves a decision, so their confirmation is open. Changes reach `main` only through pull requests
(`HUB-DEC-018`), and a branch must be up to date with `main` before merge (`HUB-DEC-026`).

## Current facts

| Item | State |
| --- | --- |
| `main` | `b0f148bf1898aef19f0316e96ff2ffd6fef88097`; protected by pull request and CI, also for administrators (`HUB-DEC-018`), and requires up-to-date branches (`strict=true`, `HUB-DEC-026`). The plan's increments merged as PR 15 (decision, withdrawal), PR 18 (template `1.1.0`), PR 19 (toolkit `0.6.0`) and PR 20 (catalog `v0.2.5`) |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub), [sample](https://github.com/cesarcastrocuba/handbook-sample-01) and [template](https://github.com/cesarcastrocuba/handbooks-template), all public. The template repository is a generated mirror of `template/book/`, marked as a template and tagged `template-v1.1.0` |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | `v0.2.5` is the current release; `v0.2.4` stays published as the previous edition. `v0.2.2` is withdrawn and keeps its tag (`HUB-DEC-027`). `v0.2.3` is withdrawn and keeps its tag (sample `DEC-019`). `v0.1.0` to `v0.2.0` are withdrawn and keep their tags (`HUB-DEC-021`). `v0.2.1` is withdrawn and keeps its tag (`HUB-DEC-023`). Introduction, 8 chapters, 3 appendices and References |
| Toolkit | `0.6.0`, tag `toolkit-v0.6.0` at `c200fd2`, 264 unit tests. Sample `v0.2.5` was built with it and is the first release with the Markdown edition and manifest schema `1.1` |
| Template | `1.1.0`, tag `template-v1.1.0`; pins toolkit `0.6.0` at `c200fd2` and ships the CI, release and Initialize-book workflows |
| CI | Sample `v0.2.5` release run 42989074637 succeeded from `c8c8703` and deployed the reading site. Catalog dry run 42989439736 reported `v0.2.4` to `v0.2.5` and `release verification: OK`; real run 42989589682 pushed the catalog branch merged as PR 20. `portal-pages` run 42990936743 started on the `push` at `b0f148b` and its build and deploy jobs succeeded |
| Standard profile | `1.0.0`, **Approved** 2026-11-06; `0.2.0` remains resolvable |
| Licensing | CC BY-SA 4.0 content, MIT code. Bundled third-party render resources reviewed and replaced where in doubt (`HUB-DEC-020`). Sample `v0.2.5` names Franz César Castro Cuba and includes a third-party notices page |
| Catalog | `schema_version` `1.1`, 1 approved release: `handbook-authoring-and-publishing` `v0.2.5` with download links for `pdf`, `html`, `docx`, `markdown` and `source` (sample `DEC-021`) |
| Publication | Reading site live at https://cesarcastrocuba.github.io/handbook-sample-01/ and serving `v0.2.5` |
| Portal | Library design live at https://cesarcastrocuba.github.io/handbooks-hub/, with a generated cover per category and five edition buttons (PDF, HTML, DOCX, Markdown, Source); `llms.txt` lists the `book.md` of `v0.2.5` |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Owner confirmation of `HUB-DEC-028`, `HUB-DEC-029` and `HUB-DEC-030`: their rows stay **Proposed** until the Owner approves them.
2. Owner deletes the throwaway repository `cesarcastrocuba/handbook-template-dryrun-delete-me` with `gh repo delete cesarcastrocuba/handbook-template-dryrun-delete-me --yes`; the delegated token has no `delete_repo` scope.
3. Sample manuscript follow-up: Chapter 7, Appendix B and Appendix C still describe a six-file release with six assets; changing them is an editorial change in the book repository.
4. `initialize-book` rewrites `book.yaml` through a YAML dump, so it drops the comments and quotes of the template descriptor; keeping them is a follow-up in `template/book/`.
5. Phase 6: migration evaluation of `solutions-architecture-handbook`, including its copies of the replaced fonts and DOCX reference; needs an owner decision.

## Blockers and open owner decisions

- `HUB-DEC-028`, `HUB-DEC-029` and `HUB-DEC-030` are **Proposed**. They were merged under the delegation in `HUB-DEC-027`, but only the Owner approves a decision, so the Owner must confirm each one before it changes status.
- Phase 6 has not started and needs an owner decision.
