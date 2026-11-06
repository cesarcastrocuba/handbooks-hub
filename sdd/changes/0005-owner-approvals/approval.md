# Owner approval — Phase 1 foundation and standard profile

**Status:** Approved
**Decision date:** 2026-11-06
**Decision:** `HUB-DEC-015`
**Branch:** `feat/topic-neutral-profile`

## Approved scope

The owner approved:

1. **Phase 1 foundation** — the hub scaffold, repository split, contracts, toolkit skeleton, template,
   catalog placeholder, CI and the proposed phased plan.
2. **Dual-license defaults** — CC BY-SA 4.0 for handbook content and repository documentation; MIT
   for software and build configuration. See `HUB-DEC-009` and `NOTICE.md`.
3. **Standard profile `0.2.0`** — the topic-neutral review checklist and optional figures/tables
   correction. See `HUB-DEC-004` and `profiles/standard/profile.yaml`.
4. **Audience clarification** — the platform and sample book target a broad technical/software
   audience, not only architects.
5. **Integration authorization** — root may independently review and integrate the reviewed
   `feat/topic-neutral-profile` branch. The implementer does not merge it.

## Not authorized

- Pilot approval.
- Any release or publication.
- Deployment, Pages publication or artifact publication.
- Migration of `solutions-architecture-handbook`.
- A merge performed by the implementer.

## Historical evidence

Existing evidence files remain historical. Earlier statements that the repositories did not exist or
that CI had not run describe the initial local scaffold and are not current status. Current facts are
recorded in [`STATUS.md`](../../../STATUS.md) and [`evidence.md`](evidence.md).

## Next step

Root independently reviews the branch at the exact commit and integrates it. After integration, the
next scoped Phase 2 task may begin. Pilot and release work wait for explicit owner authorization.
