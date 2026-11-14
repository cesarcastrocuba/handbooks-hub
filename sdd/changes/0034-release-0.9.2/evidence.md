# Evidence — Release `0.9.2`, template `1.4.2` and sample `v0.4.2`

**Change:** `0034-release-0.9.2`. **Recorded:** 2026-11-14. This is the status record after the
release; the pins and the post-merge steps are in [`record.md`](record.md).

## Facts, with the commands that verified them

| Fact | Command | Result |
| --- | --- | --- |
| Toolkit `0.9.2` is merged as hub PR 49 at `2e294388ea4e4039744b14e4164301f6c085f587` | `gh pr view 49 --json state,mergeCommit`; `git rev-list -n1 toolkit-v0.9.2`; `gh api repos/cesarcastrocuba/handbooks-hub/git/ref/tags/toolkit-v0.9.2` | `MERGED`, merge `2e29438…`; the tag object `609d884` peels to the same commit |
| Template `1.4.2` is merged as hub PR 53 at `2b679f50ad396922b616bef16f9a4b32951e9942` | `gh pr view 53 --json state,mergeCommit` | `MERGED`, merge `2b679f5…` |
| The mirror `main` and tag `template-v1.4.2` are at `b7ca872ab03fdd344ae892d78aea316c82cef7bd` | `gh api repos/cesarcastrocuba/handbooks-template/commits/main`; `git ls-remote --tags https://github.com/cesarcastrocuba/handbooks-template template-v1.4.2 'template-v1.4.2^{}'` | `main` `b7ca872…`; tag object `7953894` peels to `b7ca872…` |
| Sample PR 25 is merged as `a59185ee91820d9f9c379e352ff6ebbaee84ba6c` (sample `DEC-027`) | `gh pr view 25 -R cesarcastrocuba/handbook-sample-01 --json state,mergeCommit`; `gh api repos/cesarcastrocuba/handbook-sample-01/contents/DECISIONS.md?ref=a59185e` | `MERGED`, `a59185e…`; `DEC-027` present |
| Release run 43579133589 published `v0.4.2` from `a59185e` | `gh run view 43579133589 -R cesarcastrocuba/handbook-sample-01 --json workflowName,conclusion,headSha`; `gh release view v0.4.2 … --json assets` | `release` success, `Build, verify and release` and `Deploy the verified HTML` succeeded; seven assets |
| `v0.4.2` is the tag commit and the reading site serves it | `gh api repos/cesarcastrocuba/handbook-sample-01/git/ref/tags/v0.4.2`; `curl -s https://cesarcastrocuba.github.io/handbook-sample-01/` | tag → commit `a59185e…`; HTTP 200 and the page names `0.4.2` |
| Catalog run 43579293962 verified the bytes and pushed the branch merged as PR 54 (`66a6a0a94a22904b1eb832e99d1d147797478861`) | `gh run view 43579293962 --log`; `gh pr view 54 --json state,mergeCommit`; `catalog/catalog.json` | `updated: … v0.4.1 -> v0.4.2 (published 2026-11-14)`, `release verification: OK`; PR 54 `MERGED`, merge `66a6a0a…`; catalog schema `1.1`, one release `v0.4.2` with five download links |
| Portal run 43579566245 deployed `v0.4.2` on its third attempt | `gh api …/actions/runs/43579566245/attempts/{1,2,3}`; both failed jobs' logs | attempts 1 and 2 `failure`, attempt 3 `success`; logs show `remote asset returned HTTP 403` and `release verification: FAILED` |
| The live portal shows `v0.4.2` and `llms.txt` lists its `book.md` | `curl -s https://cesarcastrocuba.github.io/handbooks-hub/`; `curl -s …/llms.txt` | HTTP 200; ten `v0.4.2` URLs; `v0.4.2/book.md` |
| Other work of change `0027` merged | `gh pr view 47/48/50/51/52 --json state,mergeCommit,title` | PR 47 `979a6d6`, PR 48 `1be5d6a`, PR 50 `e544a05`, PR 51 `5c775ea`, PR 52 `f075e27`, all `MERGED` |
| The branch cleanup left six remote branches | `gh api repos/cesarcastrocuba/handbooks-hub/branches` | six: `main`, `docs/design-contract-record`, `feat/documentation-drift-guard`, `fix/docx-native-fields`, `refactor/native-reading-site`, `release/template-1.4.2` |
| `v0.4.1` and older published editions remain available | `gh release list -R cesarcastrocuba/handbook-sample-01` | `v0.4.2` Latest, then `v0.4.1`, `v0.4.0`, `v0.3.0` |

## Repository checks

- `python3 -m unittest discover -s tools/tests` in a venv with `requirements-dev.txt`:
  `Ran 359 tests in 101.324s` — `OK`.
- `PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify --full`: `VERIFY (full): 7 check(s),
  0 problem(s)`.

## Not verified

- **Desktop Word acceptance of `v0.4.2`.** No agent can open the DOCX in desktop Word; the Owner runs
  the acceptance checklist of the operations runbook, as `HUB-DEC-040` records.
- The coordinator reports that 57 merged remote branches were deleted. After deletion the count
  cannot be re-derived from the API; only the six remaining branches can be verified.
- The visual result of the Word fields (Contents, caption lists) is structural evidence only: the
  suite and CI validate structure, not a Word viewer's rendering.
