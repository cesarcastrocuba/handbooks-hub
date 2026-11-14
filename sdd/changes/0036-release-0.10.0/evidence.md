# Evidence — Release `0.10.1`, template `1.5.0` and sample `v0.5.0`

**Change:** `0036-release-0.10.0`. **Recorded:** 2026-11-14. This is the status record after the
release; the pins and the post-merge steps are in [`record.md`](record.md).

## Facts, with the commands that verified them

| Fact | Command | Result |
| --- | --- | --- |
| WP3 (change `0031`) merged as hub PR 55 at `48816803069f38148de6bbfc4ef32c85bb38045f` | `gh pr view 55 --json state,mergeCommit` | `MERGED`, merge `4881680…` |
| WP4 (change `0032`) merged as hub PR 58 at `dcfd8c86a616c931ae68450c60dbd220cfd49a08` | `gh pr view 58 --json state,mergeCommit` | `MERGED`, merge `dcfd8c8…`; the independent reviewer reviewed and merged it because the coordinator wrote one of its commits |
| Tag `toolkit-v0.10.0` points to that commit and no template or book pins `0.10.0` | `git rev-list -n1 toolkit-v0.10.0`; `grep -rn 0.10.0 template/book/`; `gh api …/handbook-sample-01/contents/book.yaml?ref=ba6666e` | tag commit `dcfd8c8…`; no pin in `template/book/`; the sample pins `0.10.1`. `0.10.0` cannot build the PDF or DOCX of a book with a figure outside its first page (change `0037`) |
| Toolkit `0.10.1` (change `0037`) merged as hub PR 60 at `d4480f9e2bc897cbd69a8455abf00bb3b2a1e30b`; tag `toolkit-v0.10.1` points to it | `gh pr view 60 --json state,mergeCommit`; `git rev-list -n1 toolkit-v0.10.1` | `MERGED`, merge `d4480f9…`; tag commit `d4480f9…`; merged by the independent reviewer, the coordinator was its implementer |
| Template `1.5.0` merged as hub PR 59 at `972f83520e0418636db8a338c1201bcfb752d352` | `gh pr view 59 --json state,mergeCommit` | `MERGED`, merge `972f835…` |
| The mirror `main` and tag `template-v1.5.0` are at `6e864d3e07e9d7d78f9136d427c378a91a9ca637` | `gh api repos/cesarcastrocuba/handbooks-template/commits/main`; `git ls-remote --tags https://github.com/cesarcastrocuba/handbooks-template template-v1.5.0 'template-v1.5.0^{}'` | `main` `6e864d3…`; tag object `cab3ca4` peels to `6e864d3…` |
| Sample PR 27 is merged as `ba6666ea84731ca8aeffc04c3e60f2dfb26ba977` (sample `DEC-028`, `DEC-029`) | `gh pr view 27 -R cesarcastrocuba/handbook-sample-01 --json state,mergeCommit`; `gh api …/contents/DECISIONS.md?ref=ba6666e` | `MERGED`, `ba6666e…`; both decisions present |
| Release run 43601118599 published `v0.5.0` from `ba6666e` with seven assets | `gh run view 43601118599 -R cesarcastrocuba/handbook-sample-01 --json workflowName,conclusion,headSha,jobs`; `gh release view v0.5.0 … --json assets` | `release` success, build/verify/publish and Pages deploy succeeded; seven assets; tag `v0.5.0` → `ba6666e…` |
| `v0.5.0` is the first published edition with a figure and a List of Figures | `pdftotext book.pdf -` from the release; `curl https://cesarcastrocuba.github.io/handbook-sample-01/` | the PDF contains "Figure 1.1 …" and "List of Figures"; the site shows "List of Figures" |
| Catalog run 43601281045 verified the bytes and pushed the branch merged as PR 61 (`a9aa01cdee64b90326e8fe4039e26c48b5d4130d`) | `gh run view 43601281045 --log`; `gh pr view 61 --json state,mergeCommit`; `catalog/catalog.json` | `updated: … v0.4.2 -> v0.5.0 (published 2026-11-14)`, `release verification: OK`; PR 61 `MERGED`, merge `a9aa01c…`; catalog schema `1.1`, one release `v0.5.0` |
| Portal run 43601714414 deployed `v0.5.0` on its first attempt, the first after change `0035` | `gh api …/actions/runs/43601714414`; `curl https://cesarcastrocuba.github.io/handbooks-hub/`; `curl …/llms.txt` | `run_attempt = 1`, success; portal HTTP 200 showing `v0.5.0`; `llms.txt` links `v0.5.0/book.md`. Change `0035` (PR 56, merge `493e186`) authenticates the GitHub API requests of `catalog_verification` |
| `v0.4.2` and older published editions remain available | `gh release list -R cesarcastrocuba/handbook-sample-01` | `v0.5.0` Latest, then `v0.4.2`, `v0.4.1`, … |

## Process deviation

The coordinator merged two pull requests it had implemented itself: PR 51 (documentation currency
check) and PR 56 (verification authentication), each after an independent approval by a different
agent and green CI. `HUB-DEC-040` allows the coordinator to merge after independent review but keeps
the `AGENTS.md` rule that an implementer never merges their own work, so those two merges did not
respect it. From PR 58 on, the independent reviewer merged what the coordinator had implemented.

## Repository checks

- `PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify --full`: `VERIFY (full): 7
  check(s), 0 problem(s)`, including `documentation currency: OK`.
- The suite at the release of `0.10.1` ran 384 tests (recorded in `STATUS.md`).

## Not verified

- **Desktop Word.** Nobody has opened `book.docx` of `v0.4.2` or `v0.5.0` in desktop Word; the Owner
  runs the acceptance checklist of the operations runbook (`HUB-DEC-040`).
- **Markdown numbering.** The Markdown edition of `v0.5.0` numbers the figure sequentially
  (`*Figure 1: …*`) while the PDF and HTML editions number it by chapter (`Figure 1.1`). Both forms
  were observed in the released files; aligning them is an open action.
- The merge history shows who merged each pull request, not which agent wrote it; the deviation
  above is recorded from the coordinator's account.
