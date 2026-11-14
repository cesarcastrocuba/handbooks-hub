# Record — Pinned CI actions and development dependencies

**Change:** `0040-pinned-ci-and-dev-dependencies`. **Finding:** S2 of the audit plan in change
`0027`. **Recorded:** 2026-11-14. Implementer pull request; independent review and merge by another
agent.

## What was pinned

Every `uses:` under `.github/workflows/` and `template/book/.github/workflows/` now names a full
40-character commit with the version in a trailing comment. `ci.yml` was the last file using tags;
it now uses the commits the other workflows already pinned:

| Action | Commit | Version |
| --- | --- | --- |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7.0.1 |
| `actions/setup-python` | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | v7.1.0 |
| `quarto-dev/quarto-actions/setup` | `8a96df13519ee81fd526f2dfca5962811136661b` | v2.2.0 |

The other actions were already pinned: `actions/configure-pages`, `actions/upload-pages-artifact`,
`actions/deploy-pages`, `actions/upload-artifact` and `actions/download-artifact`. Checkout steps that
never push now set `persist-credentials: false`, as the `edition-preview` job already did: the five
`ci.yml` jobs, `portal-pages`, the template `ci` and `release` workflows. The `catalog-update`
publish job and `initialize-book` keep credentials because they push a branch.

`tools/tests/test_workflow_pins.py` fails when a workflow uses an action that is not pinned to a
40-character commit with a version comment, or when one action is pinned to two different commits.

## Development dependencies

`requirements-dev.txt` now pins the packages it names, at the versions its old ranges resolved to on
2026-11-14 (`pip freeze` in a fresh venv):

| Package | Old range | Pinned |
| --- | --- | --- |
| `fonttools` | `>=4.40,<5` | `==4.68.0` |
| `brotli` | `>=1.0,<2` | `==1.2.1` |
| `tinycss2` | `>=1.4,<2` | `==1.5.1` |

`-e ./tools` stays. `tools/scripts/requirements-edition-preview.txt` already pinned
`playwright==1.60.0`. The toolkit's own ranges in `tools/pyproject.toml` stay ranges, because the
toolkit is a library that books install and must resolve against their environment.

No document quotes the old ranges, so no prose changed. Transitive dependencies are not pinned: the
files name only their direct packages, as the finding asks.

## Why no hashes

`--hash` would force pip's hash-checking mode, which rejects the editable `-e ./tools` install; the
documented `pip install -r requirements-dev.txt` command would fail unless it were split in two.
That is out of scope and would weaken the documented quickstart. Exact versions give reproducible
depending without breaking the editable toolkit.

## How to bump

One reviewed pull request per bump. For an action, change the commit and its trailing version
comment everywhere it appears; the new test fails until every occurrence agrees. For a Python
package, update the version in `requirements-dev.txt` (or the preview file), install it in a fresh
venv, run `make full`, and record the new version here in the pull request.
