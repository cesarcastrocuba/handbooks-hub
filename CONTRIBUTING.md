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

The current checks need only Python, `jsonschema` and `PyYAML`. Quarto and Graphviz are not needed
until the future publication setup.

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

Books are independent repositories created from `template/book/` (available in Phase 2). They pin an
exact `handbook-toolkit` version, keep their tests with their content and request catalog listing
only after an approved release.
