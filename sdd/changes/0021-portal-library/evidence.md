# Evidence — Change 0021, library portal

**Implementer:** coordinator (Claude). **Recorded:** 2026-11-10. Commands were run in a worktree of
the hub on branch `feat/portal-library`.

## Commands run

| Command | Result |
| --- | --- |
| `make check` | 226 unit tests, OK; `verify` OK (before the rebase on toolkit `0.6.0`; the final count is in the pull request) |
| `make full` | `VERIFY (full)`: 6 checks, 0 problems |
| `python3 -m handbook_toolkit.portal catalog/catalog.json --output <tmp>` on the live catalog (`1.0`, no `assets`) | `index.html` and `llms.txt` written; the card shows no edition buttons; `llms.txt` links the reading site |
| Same build on a three-book test catalog (`1.1`, all five roles) | Five buttons per card; `llms.txt` links each `book.md` |
| Headless Chromium screenshots of that build at 1280 px and 390 px, light and dark | Reviewed by eye: no horizontal scroll at 390 px, covers, buttons and guide sections legible in both themes |

## Files

`tools/src/handbook_toolkit/{portal.py,catalog.py,catalog_verification.py}`,
`tools/src/handbook_toolkit/schemas/catalog.schema.json`, `tools/scripts/update_catalog.py`,
`tools/tests/{test_portal.py,test_catalog.py,test_catalog_verification.py,test_update_catalog.py}`,
`docs/{portal.md,catalog-contract.md,catalog-automation.md}`, `CHANGELOG.md`.

## Not run

- No assistive-technology or real-device test.
- No deployment: the portal deploys only when a catalog change lands on `main`.
- Online `catalog_verification` of a release that lists `assets`: no such release exists until the
  sample `v0.2.5` is published with toolkit `0.6.0`. The check is covered by a unit test with a
  mocked release.
