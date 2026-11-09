# Adapter contract

An adapter is an optional, thin file that points a specific agent tool at the repository's neutral
instructions in [`AGENTS.md`](../AGENTS.md). The neutral instructions are the only source of policy;
an adapter changes how a tool loads them, not what they say.

## Authority and scope

[`AGENTS.md`](../AGENTS.md) defines roles, workflow, source-of-truth rules, content rules and
verification commands for every contributor, human or agent. An adapter is a projection of that file
for one tool. It carries no independent authority, so a conflict is resolved by `AGENTS.md`.

Adapters are optional. Removing an adapter file and its row in the drift check leaves the repository
fully usable; no build target, toolkit module or validator reads an adapter.

## What an adapter may contain

- A pointer or import that causes the tool to load `AGENTS.md`.
- Tool-specific syntax only: import markers, file names and the small amount of prose needed to
  explain the pointer.
- A `make` target reference only when `AGENTS.md` already lists that target.

Keep an adapter short. The current limit is 12 lines, enforced by the drift check.

## What an adapter may not contain

- New rules, prohibitions, exceptions or role definitions.
- A checklist, review process or workflow that differs from `AGENTS.md`.
- A decision log, decision identifier or rationale.
- Current status, phase, release or ownership information.
- A copy of the neutral instructions or of repository documentation.

Status belongs in [`STATUS.md`](../STATUS.md), decisions in
[`docs/decisions.md`](decisions.md), and the plan in
[`docs/implementation-plan.md`](implementation-plan.md).

## Which tools need an adapter

OpenAI Codex documents `AGENTS.md` as its repository instruction file and reads it without an
adapter, so this repository adds no Codex adapter.

Claude Code's documented entry point is `CLAUDE.md`; the repository's `CLAUDE.md` imports
`AGENTS.md` with the `@AGENTS.md` syntax.

GitHub Copilot's documented repository entry point is `.github/copilot-instructions.md`; the
repository's adapter at that path points it at `AGENTS.md`.

For any other tool, native `AGENTS.md` support is unverified here. Do not claim it without that
tool's documentation.

## Add an adapter

1. Create the thin file at the path the tool documents.
2. Point it at `AGENTS.md` using that tool's native syntax.
3. Add the path to `ADAPTERS` in [`tools/tests/test_adapters.py`](../tools/tests/test_adapters.py).
4. Run `make check` and `make full`.

The drift check is part of the normal unit-test discovery, so no Makefile change is needed. It
rejects an adapter that is missing, does not reference `AGENTS.md`, names a `make` target absent
from `AGENTS.md`, exceeds the length limit, or carries normative or status content.
