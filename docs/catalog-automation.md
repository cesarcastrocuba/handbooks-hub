# Catalog automation

The `catalog-update` workflow prepares step 3 of the update flow in the
[catalog contract](catalog-contract.md): it moves an existing catalog entry to a newer published
release of its book, verifies the result and leaves a branch for review. A person still reviews and
merges every change.

## Why it is run by hand

Books live in other repositories, so a release event in a book cannot start a workflow here without
a stored personal access token. The hub stores no such credential; the workflow has a
`workflow_dispatch` trigger only.

## How to run it

Start with a dry run, which is the default. Dispatch from `main`:

```bash
gh workflow run catalog-update.yml --repo OWNER/handbooks-hub --ref main \
  -f slug=handbook-authoring-and-publishing -f tag=v0.2.1
```

Add `-f dry_run=false` to push a branch. The inputs are:

| Input | Meaning |
| --- | --- |
| `slug` | Slug of a book already in `catalog/catalog.json` |
| `tag` | Published stable release tag, exact `vMAJOR.MINOR.PATCH` |
| `dry_run` | Default `true`: validate and verify, push nothing |

## What it does

1. **`prepare` job (read-only token).** Refuses a real run outside `main`, reads the book's source
   repository from its current catalog entry, and fetches the release object for the tag.
2. `tools/scripts/update_catalog.py` applies the rules below and rewrites only `latest_release`.
3. `python -m handbook_toolkit.catalog_verification catalog/catalog.json` checks the published bytes
   of every listed release, and `make full` runs the repository checks. Both run on a dry run and
   on a no-op too.
4. **`publish` job (`contents: write`, `actions: write`).** Runs only when this is not a dry run and
   the catalog changed. It runs no repository code. It pushes branch `catalog/<slug>-<tag>`,
   triggers `ci.yml` on it and writes a compare URL to the job summary.

A push made with `GITHUB_TOKEN` starts no workflow, and GitHub Actions is not permitted to create
pull requests in this repository. The explicit `ci.yml` dispatch produces the required checks on the
commit, and the compare URL lets the owner open the pull request.

## Update rules

| Request | Result |
| --- | --- |
| Tag newer than the listed version (numeric comparison) | Entry updated |
| Tag already listed, identical release data | No-op, reported; nothing is pushed |
| Tag already listed, different release data | Rejected: a published release must not change |
| Older tag | Rejected as a downgrade |
| Slug not in the catalog | Rejected: adding a book is a human change |
| Archived book | Rejected: changing a book's status is a human change |
| Release from a different repository than the entry | Rejected: moving a book is a human change |
| Tag not exact `vMAJOR.MINOR.PATCH` | Rejected |
| Draft or prerelease, or no clear stable state | Rejected |

The toolkit's catalog validator runs on the catalog before and after the change.

## What it does not do

- It does not push to `main`, open or merge a pull request, or change repository settings.
- It does not publish, edit or delete a book release.
- It does not add a book, edit a book's title, summary, categories or reading site, or withdraw an
  entry. Those remain human changes under the catalog contract.
- It does not record evidence in a change record under `sdd/changes/`; the pull request does that.
- It does not support private book repositories or hosts other than GitHub Releases: online
  verification reads public release assets without credentials.

## Remaining human steps

1. Open the pull request from the compare URL in the job summary and confirm the required checks
   passed on its commit.
2. A reviewer who did not make the change verifies the links and the release evidence.
3. The owner merges. A push to `main` that changes `catalog/**` triggers `portal-pages` and deploys
   automatically (`HUB-DEC-024`).

## Portal deployment

A merge to `main` that touches `catalog/**` triggers `portal-pages` and deploys the generated site.
Manual dispatch remains the fallback and the rollback path: dispatch from `main` with `deploy: true`
to deploy, or from any ref with `deploy: false` to build only.

## Recovery

- **Branch already exists.** The run fails rather than overwriting it. Finish or delete the branch
  first, then dispatch again.
- **The `ci.yml` dispatch failed after the push.** Run
  `gh workflow run ci.yml --repo OWNER/handbooks-hub --ref catalog/<slug>-<tag>`.
- **Online verification failed with HTTP 403.** The verifier is unauthenticated and can hit GitHub's
  shared rate limit. Re-run the job later; do not bypass the check.
