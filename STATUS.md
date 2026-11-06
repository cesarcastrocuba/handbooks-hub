# Status

**This file is the single source of current status for the hub.** Decisions and their rationale live
only in [`docs/decisions.md`](docs/decisions.md); the plan lives in
[`docs/implementation-plan.md`](docs/implementation-plan.md).

**Updated:** 2026-11-06
**Phase:** Phase 1 integrated; Phase 2 in progress — manuscript validation
**State:** Phase 1 foundation, dual-license defaults, standard profile `0.2.0` and the setup docs are
integrated on `main`. The `feat/manuscript-validation` branch adds structural section-pilot and
chapter validation. Pilot approval, publication and release are **not** authorized.

## Current facts

| Item | State |
| --- | --- |
| `main` | `80c90dccacaedfde59a31bc4ba48fdf351035357`; Phase 1 and setup docs integrated |
| Manuscript branch | `feat/manuscript-validation`; structural validator `0.2.0` |
| GitHub repositories | [hub](https://github.com/cesarcastrocuba/handbooks-hub) and [sample](https://github.com/cesarcastrocuba/handbook-sample-01), both public |
| Reference handbook | Read-only at `6a15cc211f65e148afdaa75c71a063a8084d1910` |
| Sample repository | Branch `feat/pinned-toolkit-integration`; separate lane; no writes from this session |
| Toolkit | `0.2.0`, 83 unit tests; manuscript, catalog, profile and book validators; bundled schemas |
| CI | Hub `ci` passed on integrated `main` at `80c90dc`; branch CI is reported for the manuscript branch after push |
| Standard profile | `0.2.0`, **Approved** 2026-11-06 |
| Licensing | CC BY-SA 4.0 content, MIT code; approved 2026-11-06 |
| Catalog | Empty; no approved release exists |
| Publication | Not implemented; no pilot approval or release authorized |
| Migration of existing handbook | Deferred; separate owner decision (`HUB-DEC-012`) |

## Next actions

1. Root independently reviews and integrates `feat/manuscript-validation`.
2. Then agree the small Phase 4 publication CLI interfaces with root before implementation.
3. Await explicit owner authorization before pilot approval, publication or release.

## Blockers and open owner decisions

- Pilot approval is not authorized.
- Release and publication are not authorized.
- Phase 4 publication interfaces are not yet agreed.
