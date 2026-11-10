# Author guide

This guide is for the person who writes and publishes a handbook on the platform. It explains what
the platform is, the five steps from an empty repository to a listed book, what a release contains,
how listing and withdrawal are approved, how to upgrade the toolkit pin, and the questions authors
ask most often.

The short version for a first book is
[the template quickstart](../template/book/docs/AUTHOR_QUICKSTART.md). Come back here for the rules
behind each step.

## What the platform is

The Hub is a small, agent-neutral platform for independent handbooks:

- **The hub** owns shared contracts, the versioned `handbook-toolkit` package, the standard editorial
  profile, the template, the catalog and the static portal. See the
  [catalog contract](catalog-contract.md) and the [publication contract](publication-contract.md).
- **The book** is a separate public repository created from the template. It owns its manuscript,
  its release and its repository settings. It pins an exact toolkit version and never copies shared
  scripts or imports a parent checkout.
- **The catalog** lists approved releases only. The portal is generated from that catalog and links
  to immutable release assets; it never hosts manuscript content.

You do not need access to the hub to write or release a book. You do need the Owner to approve the
catalog listing and any withdrawal.

## The five steps

### 1. Create the repository from the template

Create a public repository from `cesarcastrocuba/handbooks-template` with **Use this template**. The
template is a generated mirror of the hub's `template/book/`; never edit the mirror. The
[template distribution guide](template-distribution.md) explains how the mirror is produced.

### 2. Configure the repository once

Set **Settings → Pages → Source** to **GitHub Actions**, and protect `main` with a pull-request rule
that requires the `ci` status check. The release workflow deploys the HTML edition; branch protection
keeps the released commit clean.

The default `GITHUB_TOKEN` of a new repository can create branches, commits and releases. It cannot
open pull requests and cannot change workflow files. The template workflows are designed around that
limit.

### 3. Initialize the book identity

Run **Actions → initialize-book → Run workflow** with the title, identifier, author, summary and
category. The workflow:

- refuses to run from a branch other than the default branch;
- validates the identifier against `^[a-z][a-z0-9-]{1,63}$`, the summary length and the category;
- refuses to run once `book.yaml` no longer has the identifier `template-book`;
- rewrites `book.yaml`, `publishing/_quarto.yml`, `publishing/metadata.yaml`, `NOTICE.md`,
  `LICENSE-CODE` and the README title with a Python step that handles YAML safely;
- runs `make check`, commits to `init/<id>`, pushes the branch and prints the compare URL.

It does not open a pull request. Open the pull request from the compare link, wait for `ci` and merge.

### 4. Write, check and release

Write chapters under `manuscript/chapters/` and list each file exactly once in `manuscript/book.yml`.
Run `make check` on every change; it validates the descriptor, the reading order and the
cross-reference gate without Quarto. `make full` also renders and verifies the editions locally.

When the manuscript is ready, merge to `main` and run **Actions → release → Run workflow** with a
stable `X.Y.Z` version. The release workflow refuses to run outside the default branch, refuses an
existing tag or release, and refuses a book whose identifier is still `template-book`. It runs
`make check`, builds once from the exact commit, verifies the output and publishes it.

### 5. Request catalog listing

Open the listing form:
<https://github.com/cesarcastrocuba/handbooks-hub/issues/new?template=request-listing.yml>.

Give the repository URL, the release tag and URL, the reading site URL, the summary and the
categories, and confirm the licensing, the third-party rights review and that the release was built
by the pinned toolkit. The Owner reviews the request and merges a manual catalog pull request. After
the merge, the portal rebuilds automatically from the catalog.

## What a release contains

A release is built once, from the exact commit, by `handbook-toolkit build-book`. The toolkit
currently produces six files:

| File | Content |
| --- | --- |
| `book-html.zip` | The HTML edition; the same bytes are deployed to GitHub Pages |
| `book.pdf` | The PDF edition |
| `book.docx` | The DOCX edition |
| `book-source.zip` | The tracked source at the released commit |
| `publication-manifest.json` | Identity, toolkit and profile versions and per-file SHA-256 |
| `SHA256SUMS.txt` | Checksums for every payload and the manifest |

A newer toolkit may add files, for example a Markdown edition. The release workflow publishes every
file in the verified output directory, so such an addition needs no workflow change. The manifest
and the checksums are the audit trail: a withdrawn release keeps its tag, and the tag still points at
the released commit.

Do not edit release assets by hand. Do not attach extra files. A release that must change is
withdrawn and replaced.

## How listing approval works

The catalog is not filled automatically.

1. You submit the listing issue form.
2. The Owner checks the release, the reading site, the licenses and the categories.
3. An implementer opens a manual pull request that adds your entry to `catalog/catalog.json`, with a
   change record.
4. The hub checks validate the catalog and verify the published bytes; an independent reviewer checks
   the links and the evidence.
5. The Owner merges. The portal rebuilds from the merged catalog.

The **first listing of a book is always a manual, reviewed pull request merged by the Owner**. The
`catalog-update` workflow is not a listing path: it only moves a book that is already listed to a
newer release, and it also leaves a branch for human review. It never adds a book, changes a title or
summary, or withdraws an entry. See [catalog automation](catalog-automation.md).

## How withdrawal works

Every withdrawal is a manual catalog pull request reviewed and merged by the Owner. There are two
orders, described in [the operations runbook, section 4](operations-runbook.md#4-procedure-release-withdrawal):

- **No clean replacement yet** (defect, licensing or rights problem, security issue): withdraw the
  catalog entry first so the portal stops linking to the release, then delete the release assets.
- **A verified replacement is ready**: publish the replacement, update the catalog to it, verify the
  portal, then delete the obsolete release assets.

In both orders the Git tag is kept. The tag keeps the commit provenance auditable even after the
release page and its files are deleted. Use the withdrawal form:
<https://github.com/cesarcastrocuba/handbooks-hub/issues/new?template=request-withdrawal.yml>.

Deleting a release never happens from a book workflow. It is an Owner-approved operation.

## Upgrade the toolkit pin

Books upgrade deliberately. The full procedure is in [the book upgrade guide](book-upgrade.md).
The short form:

1. Read the hub `CHANGELOG.md` for every version between the current pin and the target.
2. Set `toolkit` in `book.yaml` to the exact target version, and change `profile.version` only when
   the target toolkit ships an approved profile change.
3. Replace the full commit SHA in `requirements.txt` with the reviewed hub commit.
4. Reinstall in the book's own virtual environment and run `make check`, then `make full`.
5. Review the rendered HTML, PDF and DOCX before merging and before the next release.

Never use a range, a parent checkout or a copied copy of the hub's scripts.

## Frequently asked questions

**Do I need a personal access token?** No. The book workflows use the repository's own
`GITHUB_TOKEN` with the permissions they declare. The hub stores no cross-repository credential, so
no workflow pushes into your book and none is needed.

**Why does the book workflow not open the pull request?** GitHub does not let the default token of a
new repository create pull requests or change workflow files. The initialize workflow pushes a branch
and prints the compare URL; a person opens the pull request.

**Why did the release workflow refuse to run?** It refuses when it is not dispatched from the default
branch, when the tag or the release already exists, and when `book.yaml` still has the identifier
`template-book`. Fix the cause; never delete an existing release to retry.

**Can I list a book before it has a release?** No. The catalog points to immutable release assets and
to a live reading site; both are verified before listing.

**Can I change the categories later?** Yes. Categories are catalog metadata, so a change is a manual
catalog pull request reviewed by the Owner. Use the same listing form and say what changes.

**Can I publish a pre-release?** The release workflow accepts stable `X.Y.Z` versions because the
catalog requires stable release tags. Use a temporary branch or a local `make full` build for
previews; do not attach preview assets to a catalog release.

**Can the reading site use a custom domain?** Yes. `reading_url` in the catalog is explicit, so a
custom domain is allowed. Keep it HTTPS and keep it live for as long as the book is listed.

**Why is there no sync workflow from the template?** The mirror is generated from the hub template
and books never import it. A sync workflow would need a cross-repository credential that the platform
does not store, and it would overwrite changes that belong to the book. Template changes reach a book
only through a deliberate upgrade pull request.

## Related documents

- [Template quickstart](../template/book/docs/AUTHOR_QUICKSTART.md)
- [Template README](../template/book/README.md)
- [Template distribution](template-distribution.md)
- [Catalog contract](catalog-contract.md)
- [Catalog automation](catalog-automation.md)
- [Publication contract](publication-contract.md)
- [Book upgrade procedure](book-upgrade.md)
- [Operations runbook](operations-runbook.md)
