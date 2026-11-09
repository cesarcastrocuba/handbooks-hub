# Evidence — Automatic portal deployment on catalog changes

**Decision:** `HUB-DEC-024`. **Branch:** `ci/portal-auto-deploy`.

## Change

- `.github/workflows/portal-pages.yml` now also runs on a push to `main` whose paths match
  `catalog/**`. `workflow_dispatch` and its `deploy` input are unchanged.
- `configure-pages` and the `deploy` job run when
  `github.ref == 'refs/heads/main' && (github.event_name == 'push' || inputs.deploy)`. A dispatch
  with `deploy: false`, or from any non-`main` ref, builds only.
- The build job, verification steps, action pins, permissions and concurrency group are unchanged;
  no action was added.
- `docs/catalog-automation.md` documents automatic deployment and keeps manual dispatch as the
  fallback and rollback path. `docs/operations-runbook.md` records the automatic redeploy and the
  branch-freshness rule under `HUB-DEC-026`.
- `tools/tests/test_portal_pages_workflow.py` proves the trigger, the unchanged dispatch input, the
  shared deploy condition and its truth table, the unchanged permissions and concurrency, and the
  pinned action set.

## Verification

```bash
make check
make full
```

- `make check`: 209 tests, 5 repository checks, 0 problems.
- `make full`: 209 tests, 6 repository checks, documentation links OK.

## Not proven

- The push trigger can only be exercised on GitHub after this branch is merged and a catalog change
  reaches `main`; no workflow run was dispatched from this branch.
- No portal deployment was performed from this change.
- Branch protection that requires branches to be up to date is a repository setting; this change
  records the rule under `HUB-DEC-026` and does not change that setting.
