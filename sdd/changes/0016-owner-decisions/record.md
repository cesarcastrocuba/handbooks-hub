# Change 0016 — Portal auto-deploy, provenance trailers and up-to-date branches

**Decisions:** `HUB-DEC-024`, `HUB-DEC-025`, `HUB-DEC-026`. **Recorded:** 2026-11-09.

## Context

On 2026-11-09 the Owner asked for three improvements after the `v0.2.2` release, translated here:

1. Deploy the portal automatically when a catalog change merges to `main` (`HUB-DEC-024`).
2. Decide whether hub commits keep the tool attribution trailer. An independent reviewer had twice
   noted it against the tool-neutral roles in `AGENTS.md` (`HUB-DEC-025`).
3. Decide whether `main` requires branches to be up to date before merge (`HUB-DEC-026`).

The Owner asked the coordinator to recommend items 2 and 3 and to complete them the same night. They
are recorded as **Proposed**; the Owner's merge of this change confirms them, and a follow-up record
marks them **Approved** when the branch-protection setting is applied.

## Alternatives considered

| Decision | Chosen | Rejected alternative and why |
| --- | --- | --- |
| `HUB-DEC-024` | Deploy on push to `main` under `catalog/**` | Deploy on every push to `main`: rebuilds the portal for unrelated changes |
| `HUB-DEC-025` | Allow provenance trailers in the hub | Remove them: loses the record of which tool produced a change, which cross-tool review relies on |
| `HUB-DEC-026` | Require up-to-date branches | Keep `strict=false`: two green branches can combine into a broken `main` |

## Consequences

- The workflow change for `HUB-DEC-024` is change `0015` (hub PR 11), merged after this record. Until
  it merges, the portal deploys only by manual dispatch, which remains the fallback afterwards.
- Reviewers stop reporting the trailer as a finding. The sample book keeps the ban in its own
  [`CONTRIBUTING.md`](https://github.com/cesarcastrocuba/handbook-sample-01/blob/main/CONTRIBUTING.md).
- After merge, branch protection in both repositories is switched to `strict=true`, and the result
  is recorded below.

## Verification

- `make full` before review: recorded in the pull request.
- The Owner merged hub PR 10 as `80e8438` on 2026-11-10, which confirmed `HUB-DEC-025` and
  `HUB-DEC-026`; both are now **Approved**.
- Branch protection after merge, by
  `gh api -X PATCH repos/cesarcastrocuba/<repo>/branches/main/protection/required_status_checks -F strict=true`:
  the hub returned `strict: true` with `checks`, `quickstart`, `template-install`,
  `publication-build` and `wheel-install`; the sample returned `strict: true` with `check`.
- The first use of the rule: hub PR 11 was behind `main` after PR 10 merged, was updated through the
  `update-branch` API to `3c2febc` (bringing in only PR 10's files) and its five checks passed again.
  The installed `gh` 2.45.0 has no `gh pr update-branch`, so `CONTRIBUTING.md` names the API call.
