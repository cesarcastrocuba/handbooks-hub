# Change 0047 — Template 1.6.0

Prepare template 1.6.0 pinned to Owner-approved toolkit 0.11.0, with a read-only asset check after
Pages deployment. The coordinator publishes the mirror and tag after independent review and merge.
This Implementer does not merge, tag, publish the mirror, or edit STATUS/decisions.

## Pins and scope

- Baseline: `d4bef53af4c70f86fecdb13d1924c79353dde32f` (`origin/main`).
- Branch/worktree: `release/template-1.6.0`, `/home/ubuntu/github/handbooks-hub.worktrees/template160`,
  exactly as requested by the implementation brief.
- `git rev-parse 'toolkit-v0.11.0^{commit}'` resolves to that same commit. The annotated tag object
  has a different SHA; requirements pin the peeled commit, not the tag object or a mutable branch.
- Updated descriptor, pinned requirement, template README version, hub README, root CHANGELOG,
  upgrade guide and focused template tests, following PR 69's release pattern. The existing
  neutral Review Checklist source is already on main; no additional manuscript edit is needed.

The upgrade guide covers the exact pin, dependent site-check job and `.callout-note .review` role.
The release workflow exports the deploy action's actual `page_url`. Its dependent `verify` job
has only contents-read permission, checks out without stored credentials, installs the same pinned
toolkit and passes the deployment URL through an environment variable to `site_check`. A failed
asset request fails the workflow; the job neither publishes nor deploys a second time.

## Verification evidence

- `.venv/bin/python -m unittest discover -s tools/tests -p test_template.py -k Workflow -v`:
  **10 tests passed in 0.118 s**. This includes the deployment-output dependency, read-only job,
  credential-free checkout, requirement installation and exact environment-based invocation.
- `git diff --check`: passed.
- Runtime release deployment: not run; this PR changes a manually dispatched book-owned workflow,
  and does not authorize publishing a book or deploying its reading site.
- Documentation currency is checked before expensive full builds. The brief explicitly requires
  stopping and reporting exact STATUS lines if that gate needs coordinator-owned changes.
- `make full`, template-install CI and edition-preview CI remain required before the release PR
  can be handed off as green. No validation result is implied by a version or pin update.

Rollback boundary: revert the template pin/version, dependent verify job, their tests and release/
upgrade notes together. No published mirror, tag, catalog entry or book release is changed here.
