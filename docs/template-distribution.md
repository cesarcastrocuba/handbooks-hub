# Template distribution

The book template has one canonical source and one generated mirror:

| Location | Role |
| --- | --- |
| `template/book/` in this hub | Canonical source, changed only by a reviewed hub pull request |
| `cesarcastrocuba/handbooks-template` | Generated mirror used by authors with **Use this template** |

The mirror is never edited directly. Every file in it comes from an export of the tracked template
tree, so a review of the hub pull request is a review of everything the mirror will contain.

## Export the template

The export script copies the tracked files of `template/book/`, dotfiles included, into a new
directory. It adds nothing else, refuses an existing non-empty directory, makes no network requests
and produces the same file list every time.

```bash
python3 tools/scripts/export_template.py --output /tmp/handbooks-template
```

The output contains `book.yaml`, `Makefile`, `README.md`, the licenses, `manuscript/`,
`publishing/`, `docs/AUTHOR_QUICKSTART.md`, `.gitignore`, `.github/workflows/` and
`.github/scripts/initialize_book.py`.

## Publish the mirror

Run this from a clean hub clone with the template change already merged. Replace `1.1.1` with the
template version recorded in the change.

```bash
python3 tools/scripts/export_template.py --output /tmp/handbooks-template
git clone https://github.com/cesarcastrocuba/handbooks-template.git /tmp/handbooks-template-mirror
find /tmp/handbooks-template-mirror -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a /tmp/handbooks-template/. /tmp/handbooks-template-mirror/
diff -r /tmp/handbooks-template /tmp/handbooks-template-mirror --exclude .git
git -C /tmp/handbooks-template-mirror add -A
git -C /tmp/handbooks-template-mirror commit -m "chore(template): publish template 1.1.1"
git -C /tmp/handbooks-template-mirror push origin HEAD:main
git -C /tmp/handbooks-template-mirror tag -a template-v1.1.1 -m "Template 1.1.1"
git -C /tmp/handbooks-template-mirror push origin template-v1.1.1
```

`diff -r` must print nothing. A mirror commit that differs from the export is a defect: discard it
and export again from the reviewed hub commit.

The tag is the template release identity. Books created from a tagged mirror can record which
template they started from in their own history; the platform does not rewrite book repositories.

## Mark the repository as a template

Marking `cesarcastrocuba/handbooks-template` as a GitHub template is an **Owner** action. It is a
repository setting, not repository content, so no pull request can perform it.

The Owner enables it in **Settings → General → Template repository**, or with an authenticated
command:

```bash
gh api --method PATCH repos/cesarcastrocuba/handbooks-template -F is_template=true
```

Until the setting is enabled, an author can still receive the tree from the Owner, but **Use this
template** is unavailable.

## Why there is no sync workflow

There is no workflow that pushes the template into the mirror, and none that pushes a template update
into existing books:

- **No cross-repository credential.** A workflow in the hub cannot write to another repository with
  its own `GITHUB_TOKEN`, and the platform stores no personal access token. This is the same reason
  catalog updates are dispatched by hand (see [catalog automation](catalog-automation.md)).
- **The mirror is generated.** A sync workflow would be a second writer of the same bytes; the export
  from a reviewed commit is simpler and verifiable with `diff -r`.
- **Books are independent.** Rewriting an existing book from the template would overwrite the
  author's manuscript, identity and catalog metadata. Books adopt template changes through a
  deliberate upgrade pull request, as described in [the book upgrade guide](book-upgrade.md).

## Verification

A template distribution is complete when:

1. `python3 tools/scripts/export_template.py` succeeds and reports the expected file count.
2. `diff -r` between the export and the mirror prints nothing.
3. The mirror commit is tagged `template-vX.Y.Z` and the tag is pushed.
4. The mirror is marked as a template by the Owner.
5. A throwaway repository created from the mirror passes `make check`; the initialize workflow is
   exercised there before the template is announced.

The hub's own tests copy `template/book/` and run its `make check`, so a broken template fails the
hub before it reaches the mirror.
