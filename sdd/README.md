# Specification-driven delivery

Substantive work and decisions use a small change record under `sdd/changes/<id>/`. Small typo,
formatting or dependency-bump changes do not need one; the commit and pull request are enough.

## Lifecycle

1. **Proposal** — problem, goals, non-goals, constraints, alternatives and owner decisions needed.
2. **Spec** — deliverables, interfaces, acceptance criteria, invariants and out-of-scope items.
3. **Tasks** — work packages with exclusive write sets, dependencies and status.
4. **Evidence** — exact commit, commands, results, checks not run and review findings.

A change record is closed when the owner merges it and the evidence names the reviewed commit. Keep
it as durable history; do not rewrite it after closure. A later change supersedes it with a new ID.

## Naming

`NNNN-short-slug`, for example `0001-hub-scaffold`, `0002-profile-v1`, `0003-sample-brief`.

## Status

| Status | Meaning |
| --- | --- |
| Draft | Being written; no owner approval |
| Proposed | Ready for review; owner decision pending |
| Approved | Owner approved; implementation may proceed |
| Implemented | Merged with evidence |
| Superseded | Replaced by a later change record |

Status lives in the change record's `tasks.md` and in [`STATUS.md`](../STATUS.md); decisions live in
[`docs/decisions.md`](../docs/decisions.md).

## What does not belong here

- A second status file.
- A second decision log.
- Copied manuscript content.
- Generated build artifacts.
