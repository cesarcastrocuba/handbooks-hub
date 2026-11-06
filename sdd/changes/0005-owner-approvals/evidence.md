# Evidence — owner approval record

**Change:** `0005-owner-approvals`
**Status:** Approved
**Date:** 2026-11-06
**Branch:** `feat/topic-neutral-profile`
**Approval commit:** pending (recorded by the follow-up evidence commit)

## Actual repository and CI facts

| Item | Evidence |
| --- | --- |
| Hub repository | <https://github.com/cesarcastrocuba/handbooks-hub>, public, default branch `main` |
| Sample repository | <https://github.com/cesarcastrocuba/handbook-sample-01>, public, default branch `main` |
| Hub `main` CI | Run [42266553876](https://github.com/cesarcastrocuba/handbooks-hub/actions/runs/42266553876): `ci`, `push`, `0e8d897`, **success** |
| Hub branch CI | Run [42274376867](https://github.com/cesarcastrocuba/handbooks-hub/actions/runs/42274376867): `ci`, `workflow_dispatch`, `ebdb42e`, branch `feat/topic-neutral-profile`, **success** |
| Sample branch CI | Run [42276101707](https://github.com/cesarcastrocuba/handbook-sample-01/actions/runs/42276101707): `repository-check`, `push`, `e3b7f28`, branch `feat/pinned-toolkit-integration`, **success** |

The hub and sample repositories are public. Their default branch is `main`. The sample integration
work is on `feat/pinned-toolkit-integration` and was not merged or modified by this hub change.

## Local checks

```bash
make check
make full
```

Both are recorded at the approval commit after the follow-up evidence update. The current branch
contains the profile approval change and the approval record.

## Scope statement

No merge, release, deployment, Pages publication, pilot approval or sample-repository write was
performed. Root reviews and integrates the branch; the implementer does not merge it.

## Historical evidence

The following files retain their historical content and were not rewritten:

- `sdd/changes/0001-hub-scaffold/evidence.md`
- `sdd/changes/0002-toolkit-packaged-schemas/evidence.md`
- `sdd/changes/0003-cli-docs-and-wheel-ci/evidence.md`
- `sdd/changes/0004-topic-neutral-profile/evidence.md`

They record the state at their respective commits, including the earlier absence of GitHub
repositories and CI runs. Current state is in `STATUS.md`.
