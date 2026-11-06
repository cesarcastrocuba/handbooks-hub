# Proposal — hub scaffold and phased plan

**Status:** Proposed
**Date:** 2026-11-06
**Owner decision:** Gate 1 (pending)

## Context

`IMPLEMENTATION-HANDOFF.md` and the Engram handoff summary #6795 describe a reusable handbook
platform: independent book repositories, a hub for shared contracts and a static portal, versioned
tooling, an editorial contract, reproducible publication and an agent-neutral workflow.

The existing `solutions-architecture-handbook` is a released, working book. It is useful as a source
of editorial and build lessons but must remain read-only until a separate owner decision. The sample
repository path exists but is empty.

## Problem

There is no hub repository, no shared contract, no versioned toolkit, no template, no catalog and no
agreed phase plan. Without those, a sample book would either copy the existing scripts or invent its
own rules, and the two repositories would drift before the first release.

## Goals

- Initialize the hub as a local Git repository with reviewable, conventional commits.
- Record the repository boundaries, editorial contract, publication contract, catalog contract,
  decisions and assumptions.
- Provide a proposed standard profile, JSON schemas, a minimal template and an empty catalog.
- Provide a small, deterministic, tested toolkit slice rather than an untested framework.
- Define the six phases, work packages, gates, owner decisions and evidence.
- Keep the sample and reference repositories untouched.

## Non-goals

- Scaffolding `handbook-sample-01` in this session.
- Creating GitHub repositories, Pages, releases or deployments.
- Migrating the existing handbook.
- Building the full manuscript validator, Quarto pipeline or portal.
- Merging or self-reviewing the scaffold.

## Constraints

- Work only inside `handbooks-hub`.
- English artifacts; conventional commits; no AI attribution.
- No secrets, personal data or unlicensed third-party material.
- The reference repository is read-only.
- Owner approval is required for editorial gates, licensing, repositories, deployments and releases.

## Alternatives considered

| Alternative | Why not now |
| --- | --- |
| One monorepo for hub and all books | Couples releases and content ownership; the handoff explicitly separates them. |
| Copy the reference scripts into the template | Creates two implementations and guarantees drift; the handoff forbids copied shared scripts. |
| Build the full toolkit, profile, template and book in one batch | Too large to review, violates the "small useful vertical slice" instruction and delays the first gate. |
| Defer the scaffold until GitHub repositories exist | The owner wants local, reviewable artifacts first; remote creation is a separate authorization. |

## Owner decisions requested

1. Approve the hub/book split and the deferred sample scaffold (`HUB-DEC-001`, `HUB-DEC-012`).
2. Approve the proposed standard profile direction and exceptions model (`HUB-DEC-004`).
3. Confirm the licensing and notice scope (`HUB-DEC-009`).
4. Authorize Phase 2 after independent review; do not infer authorization for deployment or
   repository creation.
