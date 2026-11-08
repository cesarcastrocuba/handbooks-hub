# Proposal — Post-Phase-4 remediation

**Status:** Approved
**Change:** `0010-post-phase4-remediation`
**Branch:** `fix/post-phase4-remediation`
**Base:** `main` at `1635e69`

## Context

A status review on 2026-11-08 found that work integrated after the Phase 4 close was not reflected in
the status documents, had no change record, added third-party files without a rights review and kept
toolkit version `0.4.0` while its behavior changed.

## Scope

- Record a third-party rights review, replace the resources in doubt and update the notices.
- Remove vendor references from packaged style comments.
- Release toolkit `0.5.0` and pin the template to it.
- Bring `STATUS.md`, the plan and the changelog in line with the verified state.
- Record the owner's branch-protection instruction and propose the open decisions.

## Non-goals

- No book release and no catalog change.
- No change to `solutions-architecture-handbook`.
- No change to published releases.
- The sample-book pin moves to `0.5.0` in a later change, after this one lands on `main`.

## Integration constraint

`template/book/requirements.txt` pins a commit on this branch. Integrate with a merge commit; a squash
or rebase merge would orphan that commit and require a new pin.
