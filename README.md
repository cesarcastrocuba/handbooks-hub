# Handbook Hub

A reusable, agent-neutral platform for publishing independent handbooks. The hub owns the shared
contracts, the versioned Python toolkit, the standard editorial profile, the book template, the
catalog and the static portal. Each book repository owns its canonical manuscript and publishes its
own reading site and release downloads.

Status: **Phase 1 foundation approved; Phase 2 next.** See [`STATUS.md`](STATUS.md) and the
[implementation plan](docs/implementation-plan.md).

## What exists today

| Path | Purpose |
| --- | --- |
| `docs/` | Architecture, contracts, decisions, assumptions and the phased plan |
| `profiles/standard/` | Approved standard editorial profile `0.2.0` |
| `tools/` | Versioned `handbook-toolkit` package with deterministic validators and tests |
| `tools/src/handbook_toolkit/schemas/` | JSON Schema contracts for books, profiles and the catalog, shipped inside the toolkit package |
| `template/book/` | Minimal book-repository template, intentionally incomplete until Phase 2 |
| `catalog/` | Catalog of approved book releases; empty until a release is approved |
| `sdd/` | Lightweight specification-driven delivery records |
| `.github/` | Basic CI and the pull-request template |

## Quick start

Requirements: Python 3.11 or newer, `jsonschema` and `PyYAML`. The checks are deterministic and do
not require Quarto, network access or a GitHub repository.

```bash
make check        # unit tests + fast validations
make full         # fast checks + full repository validations
```

Without `make`:

```bash
PYTHONPATH=tools/src python3 -m unittest discover -s tools/tests -v
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify --full
```

## Scope and non-goals

The hub and sample repositories now exist on GitHub and their CI has passed. This branch does not
merge, deploy a site, publish a release, edit the sample book repository or migrate the existing
handbook. Pilot approval and any release remain owner-gated steps.

## Licensing

Documentation and editorial material in this hub are licensed under CC BY-SA 4.0
([`LICENSE`](LICENSE)); software under the MIT License ([`LICENSE-CODE`](LICENSE-CODE)). Scope and
attribution are recorded in [`NOTICE.md`](NOTICE.md).

## Contributing and agent use

Read [`AGENTS.md`](AGENTS.md) first. It applies to every contributor, human or AI, whatever tool
they use. [`CONTRIBUTING.md`](CONTRIBUTING.md) describes local checks and the pull-request workflow.
