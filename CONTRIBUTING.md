# Contributing

Read [`AGENTS.md`](AGENTS.md) first. It applies to people and AI agents alike.

## Local setup

See [`docs/setup.md`](docs/setup.md) for supported platforms, prerequisites, troubleshooting and the
independent-book toolkit install.

```bash
git clone https://github.com/cesarcastrocuba/handbooks-hub.git
cd handbooks-hub
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-dev.txt
```

The checks need only Python, `jsonschema` and `PyYAML`. Rendering runs through
`handbook-toolkit build-book` and needs Quarto `1.11.9` and Poppler `pdfinfo`; the checks above do not
run it.

## Checks

```bash
make check    # unit tests + fast validators
make full     # fast checks + full repository validators
```

`make check` must pass before every commit. `make full` must pass before review. If a check cannot
run, say so in the change record; do not claim it passed.

## Pull requests and changes

- Keep one concern per change and one writer per file.
- Use conventional commits, for example `feat(toolkit): add catalog validator` or
  `docs(plan): record phase gates`.
- Substantive work and decisions need a change record under `sdd/changes/<id>/`. Small typo fixes do
  not.
- The pull-request description states purpose, files, commands run with results, checks not run,
  licensing impact and open owner decisions.
- Reviewers post `APPROVE` or `CHANGES_REQUESTED` with findings classified Critical, Major, Minor or
  Optional. The reviewer must differ from the implementer.
- The owner merges after review. Do not merge your own pull request.
- `main` is protected (`HUB-DEC-018`): every change arrives through a pull request with passing CI,
  and direct pushes are rejected, including for administrators. Branch protection enforces
  `HUB-DEC-026`: a branch must be up to date with `main` before merge; update it with
  `gh api -X PUT repos/<owner>/<repo>/pulls/<number>/update-branch` (or `gh pr update-branch`
  where the installed `gh` provides it) and let CI re-run. The update changes the head commit, so the merge command
  must name the new head.
- A trailer naming the contributing tool, such as `Co-Authored-By`, is allowed and records
  provenance only (`HUB-DEC-025`).
- Use a merge commit when a pinned commit lives on the branch; squashing would orphan the pin.

## Changing shared contracts

Changes to `tools/src/handbook_toolkit/schemas/`, `profiles/`, the toolkit CLI or `catalog/` affect every book. Treat them as
versioned API changes:

1. Record a proposal and update the plan or change record.
2. Keep backward compatibility or state the migration explicitly.
3. Update tests and fixtures for both accepted and rejected input.
4. Bump the toolkit and profile versions according to the compatibility rules in
   [`docs/implementation-plan.md`](docs/implementation-plan.md).
5. Obtain owner approval for profile or licensing changes.

## Adding a book

Books are independent public repositories created from `template/book/`. The generated mirror
`cesarcastrocuba/handbooks-template` provides **Use this template**, and
[`docs/author-guide.md`](docs/author-guide.md) describes the whole path from creation to listing. The
template copy is owned by the book: it pins an exact `handbook-toolkit` version, keeps its tests with
its content, and runs its own `make check` and release workflows.

A book is listed only after an approved release. The first listing and every withdrawal are manual
catalog pull requests reviewed and merged by the Owner; the `catalog-update` workflow only moves an
already listed book to a newer release. Do not add a book entry as part of implementing a book
repository.
