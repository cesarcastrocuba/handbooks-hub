# Retrospective record — design contract work, `HUB-DEC-032` to `HUB-DEC-035`

**Status:** Written after the fact on 2026-11-14. This record reconstructs work that shipped without a
change record; it is not a contemporaneous account and it changes no decision.

**Scope:** the four design releases of 2026-11-12 and 2026-11-13 recorded in
[`docs/decisions.md`](../../../docs/decisions.md) as `HUB-DEC-032`, `HUB-DEC-033`, `HUB-DEC-034` and
`HUB-DEC-035`. It lists what shipped, the pull requests that carried it, the independent reviews
recorded on them, and the tags. Evidence was read from both repositories on 2026-11-14: `gh pr view`
for each pull request, `git ls-remote --tags` for tags, `gh release view` for the sample releases, and
`gh run list` for the release runs.

**Why it exists:** audit finding D6 in
[`sdd/changes/0027-audit-plan/record.md`](../0027-audit-plan/record.md) recorded that no change record
covered these four decisions. This file closes that gap; it does not re-approve the work.

## What shipped

Each decision released one toolkit and template version and published one sample edition. The sample
release is the immutable artifact set; the toolkit and template tags are the code identity a book
pins.

| Decision | Toolkit | Template | Sample | Sample release run | Sample release published |
| --- | --- | --- | --- | --- | --- |
| `HUB-DEC-032` | `0.7.0` | `1.2.0` | `v0.2.7` | 43290998984 | 2026-11-12T19:32:29Z |
| `HUB-DEC-033` | `0.8.0` | `1.3.0` | `v0.3.0` | 43342066827 | 2026-11-13T01:05:17Z |
| `HUB-DEC-034` | `0.9.0` | `1.4.0` | `v0.4.0` | 43428501092 | 2026-11-13T12:50:55Z |
| `HUB-DEC-035` | `0.9.1` | `1.4.1` | `v0.4.1` | 43472781256 | 2026-11-13T17:27:44Z |

What each release contained, as the decisions and their pull requests describe it:

- `HUB-DEC-032` — one packaged token document, a design schema, a loader with contrast checks, and
  generated values for the portal, book HTML, Typst/PDF and DOCX; the template gained full-book
  search, repository actions, a light/dark theme and correction and proposal issue forms.
- `HUB-DEC-033` — Source Sans 3 for text and Source Serif 4 for display headings; compact portal and
  book chrome; table captions and a List of Tables; rebuilt DOCX styles.
- `HUB-DEC-034` — compact chrome shared by hub and book, shared callout boxes, cream Word pages, table
  stripes and a static List of Tables in Word.
- `HUB-DEC-035` — the 1300 px hub/book column, the List of Tables in the sidebar, no stripes inside
  callout tables, a neutral `review` callout role, licence-block alignment and a rebuilt Word
  callout/list layout.

## Tags

Annotated tags in `cesarcastrocuba/handbooks-hub` peel to the commits below. The template repository
`cesarcastrocuba/handbooks-template` is the generated mirror of `template/book/` and carries its own
tags.

| Tag | Commit |
| --- | --- |
| `toolkit-v0.7.0` | `e34ec0272b696e7f1249ee5112124726777b75cd` |
| `toolkit-v0.8.0` | `9921dbe5150e28394d4cef0cebdf864d35f02e55` |
| `toolkit-v0.9.0` | `e6c18d019db1f8d24101eee994774a040c48b73b` |
| `toolkit-v0.9.1` | `298d7039e09f7ffbd102b8d1cd09ee01521c34f1` |
| `template-v1.2.0` | `24e8f0d5378aa4667dd3a3ec48bda2a8ea98fda0` |
| `template-v1.3.0` | `5974fc2b7f95781223ed6e6bda1a9bbb658804af` |
| `template-v1.4.0` | `d6c35f1ffc49e9c8c2949b1a644b2e2cbe32670e` |
| `template-v1.4.1` | `92388494dd178efeca432b0adb800fceffe822b7` |

Sample release tags `v0.2.7`, `v0.3.0`, `v0.4.0` and `v0.4.1` resolve to the sample merge commits
`49f22094bd6080271a2151a8f3507655742661e7`, `33224119b01c2be65ff820b0b9673e9d56253f03`,
`12f8d460fc364c21bf7ecfd3d0344207ef03ffb9` and `e1ca3497a0885bc7c3a7214e120de16265949972`.

## Hub pull requests

| PR | Title | Merge commit | Merged | Review record |
| --- | --- | --- | --- | --- |
| [27](https://github.com/cesarcastrocuba/handbooks-hub/pull/27) | feat(design): unify the portal, book, PDF and DOCX on one design contract | `3ee1bd04dd076846b8013fc03e18a22532336834` | 2026-11-12T19:08:53Z | Request changes at `e93919e` (two Critical, one Major, one Minor); approve at `a4949a9` |
| [28](https://github.com/cesarcastrocuba/handbooks-hub/pull/28) | release: toolkit 0.7.0 and template 1.2.0 | `b2de280c236affd0144d0b330da8b5b8163bbdb4` | 2026-11-12T19:17:32Z | Approve with two Minor follow-ups at `07e84f5` |
| [30](https://github.com/cesarcastrocuba/handbooks-hub/pull/30) | feat(catalog): list handbook-authoring-and-publishing release v0.2.7 | `7e11f4427d5fe6fa9c14cbcf285e52588dad1bd7` | 2026-11-12T19:38:52Z | Approve, no findings at `b0fdb63` |
| [32](https://github.com/cesarcastrocuba/handbooks-hub/pull/32) | feat(design): professional type, web chrome, tables and DOCX refinement | `3c5a7d9ee0613da46c4d5c51b3f871039d80a01c` | 2026-11-13T00:45:43Z | Request changes at `5184282` and `7209d52`; approve at `5cb88ed` |
| [33](https://github.com/cesarcastrocuba/handbooks-hub/pull/33) | release: toolkit 0.8.0 and template 1.3.0 | `9921dbe5150e28394d4cef0cebdf864d35f02e55` | 2026-11-13T00:54:40Z | Approve, no findings at `9698dc7` |
| [34](https://github.com/cesarcastrocuba/handbooks-hub/pull/34) | feat(catalog): list handbook-authoring-and-publishing release v0.3.0 | `40fb2d7acfd630a5fdaf8b2e0f546345cbbf28ed` | 2026-11-13T01:10:40Z | Approve, no findings at `3001476` |
| [36](https://github.com/cesarcastrocuba/handbooks-hub/pull/36) | feat(design): polish hub, book chrome, callouts and Word layout | `6e43a374dbe743d3c6341554e5f125139afb38b9` | 2026-11-13T12:17:25Z | Request changes at `2c668a7` (two Major, two Minor); approve at `39c184e` |
| [37](https://github.com/cesarcastrocuba/handbooks-hub/pull/37) | release: toolkit 0.9.0 and template 1.4.0 | `7d5313efe02f90eae71dca48823ac8245c5558c8` | 2026-11-13T12:25:52Z | Approve with two Minor follow-ups at `92f2bac` |
| [38](https://github.com/cesarcastrocuba/handbooks-hub/pull/38) | fix(book): let the note callout keep its shared border colour | `e6c18d019db1f8d24101eee994774a040c48b73b` | 2026-11-13T12:35:56Z | Request changes at `4bfe4ce` (one Minor); approve at `82a6f9a` |
| [39](https://github.com/cesarcastrocuba/handbooks-hub/pull/39) | fix(template): pin the reviewed 0.9.0 callout fix | `48a70c97ede8b17550f96ac73ca61b560f18c22a` | 2026-11-13T12:40:16Z | Approve, no findings at `6ac005e` |
| [40](https://github.com/cesarcastrocuba/handbooks-hub/pull/40) | feat(catalog): list handbook-authoring-and-publishing release v0.4.0 | `4635ea64f1ebfae776b0f4ea6dd8abb0acfc8da1` | 2026-11-13T12:57:13Z | Approve, no findings at `809e75f` |
| [42](https://github.com/cesarcastrocuba/handbooks-hub/pull/42) | fix(design): align hub/book widths, sidebar tables and Word callout boxes | `463bdb5c5d49b5c12c69264feff0fa1993315f2c` | 2026-11-13T16:58:22Z | Request changes at `962ec50` (one Major); approve at `201b12b` |
| [43](https://github.com/cesarcastrocuba/handbooks-hub/pull/43) | release: toolkit 0.9.1 and template 1.4.1 | `f1ffe9df696e26adac4666ab4c43ded133831403` | 2026-11-13T17:11:57Z | Approve with two Minor upgrade-note follow-ups at `a93f576` |
| [44](https://github.com/cesarcastrocuba/handbooks-hub/pull/44) | feat(catalog): list handbook-authoring-and-publishing release v0.4.1 | `97494ee2716ee28ae373c15d2685a6b1c3ebc666` | 2026-11-13T17:34:26Z | Approve, no findings at `722fbeb` |

## Sample pull requests

Repository: `cesarcastrocuba/handbook-sample-01`.

| PR | Title | Merge commit | Merged | Review record |
| --- | --- | --- | --- | --- |
| [16](https://github.com/cesarcastrocuba/handbook-sample-01/pull/16) | release: toolkit 0.7.0 design edition (v0.2.7) | `49f22094bd6080271a2151a8f3507655742661e7` | 2026-11-12T19:29:12Z | Approve with two Minor follow-ups at `1d7ccfd` |
| [19](https://github.com/cesarcastrocuba/handbook-sample-01/pull/19) | release: v0.3.0 with toolkit 0.8.0 | `33224119b01c2be65ff820b0b9673e9d56253f03` | 2026-11-13T01:02:10Z | Approve with one Minor follow-up at `35a2e3c` |
| [20](https://github.com/cesarcastrocuba/handbook-sample-01/pull/20) | docs(release): record v0.3.0 as published | `f4dbf011bd89a584b9d6a46d8ee66975512c8863` | 2026-11-13T01:23:58Z | One Minor at `5a52a79`, repeated, then approve at `10642c4` |
| [21](https://github.com/cesarcastrocuba/handbook-sample-01/pull/21) | release: v0.4.0 with toolkit 0.9.0 | `12f8d460fc364c21bf7ecfd3d0344207ef03ffb9` | 2026-11-13T12:47:40Z | Approve with one Minor follow-up at `5108415` |
| [23](https://github.com/cesarcastrocuba/handbook-sample-01/pull/23) | release: v0.4.1 with toolkit 0.9.1 | `e1ca3497a0885bc7c3a7214e120de16265949972` | 2026-11-13T17:23:16Z | Approve with two Minor follow-ups at `e7611f3` |

Adjacent status-document pull requests, not named by the decisions but part of the same releases:
[17](https://github.com/cesarcastrocuba/handbook-sample-01/pull/17) (`71ba91d`) and
[18](https://github.com/cesarcastrocuba/handbook-sample-01/pull/18) (`8c91b0c`) for `v0.2.7`,
[22](https://github.com/cesarcastrocuba/handbook-sample-01/pull/22) (`f1c5bc8`) for `v0.4.0`, and
[24](https://github.com/cesarcastrocuba/handbook-sample-01/pull/24) (`70383d1`) for `v0.4.1`.
Each was reviewed independently; reviewer findings on them were documentation corrections and were
fixed before merge, except where the review text records a remaining Minor follow-up.

## How the releases were evidenced

- Every book release is a stable GitHub release with seven assets (HTML ZIP, PDF, DOCX, `book.md`,
  source ZIP, `publication-manifest.json`, `SHA256SUMS.txt`). The catalog reviews of hub PR 30, 34, 40
  and 44 record the release date, tag, seven-asset membership, manifest identity and checksum check.
- The sample release workflow runs recorded above all completed successfully at the sample merge
  commit named in the tag table.
- The catalogue entries for `v0.2.7`, `v0.3.0`, `v0.4.0` and `v0.4.1` were merged in hub PR 30, 34,
  40 and 44. `portal-pages` deploys the portal from the catalog on `main`.
- The reviews are recorded as pull-request comments because the connected account owns the pull
  requests and GitHub does not accept a formal approval event from it. The review text names the
  exact reviewed commit.

## Known gaps

- This is a reconstruction. It cannot recover discussion that was never written on a pull request.
- The decisions do not record an owner approval comment for each individual release; they record the
  owner instruction that authorised the release line. The approval evidence is the decision row plus
  the clean independent review and green CI recorded on each pull request.
- Font provenance for `HUB-DEC-033` is covered separately in
  [`rights-review-fonts.md`](rights-review-fonts.md), which records what is and is not documented.
