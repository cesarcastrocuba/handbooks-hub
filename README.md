# Handbook Hub

A reusable, agent-neutral platform for publishing independent handbooks. The hub owns the shared
contracts, the versioned Python toolkit, the standard editorial profile, the book template, the
catalog and the static portal. Each book repository owns its canonical manuscript and publishes its
own reading site and release downloads.

Status: **Phases 1 to 5 complete, with the unified design released in toolkit `0.9.1`.** See
[`STATUS.md`](STATUS.md) and the [implementation plan](docs/implementation-plan.md).

## Who this is for

| Reader | Installation needed? | Start here |
| --- | --- | --- |
| Reader of a published handbook | **No** | Use the book's reading site or release downloads. The catalog currently lists `handbook-authoring-and-publishing` `v0.4.1`. |
| Contributor to this hub | **Yes** — Git, Python 3.11+, pip, venv | [Quick start](#quick-start-hub-contributors) or [`docs/setup.md`](docs/setup.md) |
| Hub maintainer | **Yes** — the contributor setup plus `make` and CI knowledge | [`docs/setup.md`](docs/setup.md) |
| Author of an independent book | **Yes** — Python, venv and the pinned toolkit | [`template/book/README.md`](template/book/README.md) |

Current validators need **Python only**. Rendering ships in the same toolkit: `handbook-toolkit
build-book` builds the HTML site, the PDF, the DOCX edition, the Markdown edition and the source
bundle, and needs Quarto `1.11.9` and Poppler `pdfinfo`. Those tools are **not** required to run the
checks described here.

## Quick start (hub contributors)

Tested on **Ubuntu 24.04 with Python 3.12**. Native Windows is not tested; see
[`docs/setup.md`](docs/setup.md) for platform notes.

```bash
git clone https://github.com/cesarcastrocuba/handbooks-hub.git
cd handbooks-hub
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-dev.txt
make check
make full
```

The documented path creates `.venv` **inside the clone**, which `.gitignore` excludes. CI runs this
exact path; an external temporary venv is a different setup and is not used as proof of this one.

If `make` is unavailable, use the no-make commands in
[`docs/setup.md`](docs/setup.md#5-no-make-path). For missing `pip`, missing `venv`, platform-specific
activation and troubleshooting, start with [`docs/setup.md`](docs/setup.md).

## What exists today

| Path | Purpose |
| --- | --- |
| `docs/` | Architecture, contracts, decisions, assumptions, setup guide and phased plan |
| `docs/design.md` | Design contract: colour roles, contrast floors, the brand typeface and per-surface mapping |
| `profiles/standard/` | Approved standard editorial profile `1.0.0` with per-rule validation classification |
| `tools/` | Versioned `handbook-toolkit` package with deterministic validators and tests |
| `tools/src/handbook_toolkit/schemas/` | JSON Schema contracts for books, profiles and the catalog, shipped inside the toolkit package |
| `template/book/` | Book template `1.4.1` with publishing config, licenses, workflows, search/contribution actions and `make check`/`build`/`full` |
| `catalog/` | Catalog of approved book releases |
| `docs/publication-build.md` | Local seven-file build with staging, payload inspection and atomic finalization |
| `docs/book-upgrade.md` | Supported toolkit/profile upgrade path for an independent book |
| `docs/operations-runbook.md` | Upgrade, rollback, release withdrawal and incident procedures |
| `docs/catalog-automation.md` | Manual catalog-update workflow, its rules and its limits |
| `docs/adapter-contract.md` | Agent adapters as thin projections of `AGENTS.md` |
| `docs/clean-clone.md` | Linux and macOS clean-clone matrix and its evidence |
| `sdd/` | Lightweight specification-driven delivery records |
| `.github/` | CI and the pull-request template |

## Scope and non-goals

The hub and sample repositories exist on GitHub and their CI has passed. Books own their manuscript,
their reading site and their release assets; publication runs in the book repository. This repository
deploys the portal: `portal-pages` builds and deploys the generated site after a catalog change on
`main`. `catalog-update` moves an already listed book to a newer release, verifies the published
bytes, pushes a `catalog/<slug>-<tag>` branch and triggers `ci.yml` on it; it cannot open the pull
request, so the Owner opens and merges it (see [`docs/catalog-automation.md`](docs/catalog-automation.md)).
The hub does not edit the sample book repository or migrate the existing handbook. Pilot approval and
any release remain owner-gated steps.

## Licensing

Documentation and editorial material in this hub are licensed under CC BY-SA 4.0
([`LICENSE`](LICENSE)); software under the MIT License ([`LICENSE-CODE`](LICENSE-CODE)). Scope and
attribution are recorded in [`NOTICE.md`](NOTICE.md).

## Contributing and agent use

Read [`AGENTS.md`](AGENTS.md) first. It applies to every contributor, human or AI, whatever tool
they use. [`CONTRIBUTING.md`](CONTRIBUTING.md) describes local checks and the pull-request workflow.
