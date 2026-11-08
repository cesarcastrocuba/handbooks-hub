# Evidence — Post-Phase-4 remediation

**Base:** `1635e69`. **Toolkit commit pinned by the template:** `bad47813b148687b1bfb148244874657e2e445c0`.

## Commands run on 2026-11-08

| Command | Result |
| --- | --- |
| `make check` after the version bump | Pass, 166 tests, 5 verify checks |
| `make full` at this change | Pass, 6 verify checks |
| `sha256sum -c SHA256SUMS.txt` on the `v0.2.0` release assets | Pass, 5 files |
| `make full` in the sample book with toolkit `5f96202` | Pass |
| `curl` on the portal, the reading site, and the `v0.2.0` manifest and checksums | HTTP 200 for all four |
| `cmp` of bundled fonts against upstream releases | See `rights-review.md` |

## Owner instruction

Given to the implementing session on 2026-11-08, verbatim: "Si por favor y pr9tege la rama main para
que desde aquí en adelante solo se realicen mejoras en ramas y luego se 8ntegren en main con
autorización, corrige todo lo antrrior". This is the basis for `HUB-DEC-018` and for this change. It
does not ratify earlier releases or accept the open license questions.

## Independent review

A separate agent reviewed `c0dea57` and requested changes: 2 Major and 6 Minor findings. All were
addressed in the next commit. A second review of `5a5b6a9` approved the hub with 3 Minor findings,
all addressed afterwards. A later commit requires a new review.

## Branch protection

Applied with `PUT /repos/{owner}/{repo}/branches/main/protection` on both repositories. Required hub
checks: `checks`, `quickstart`, `template-install`, `publication-build`, `wheel-install`. Required
sample check: `check`.

## Not run or not verified

- Independent review: pending.
- Rendered output of a book built with `0.5.0`: only the copied-template build in the test suite ran.
- `wheel-install`, `template-install` and the other CI jobs run on the pull request, not locally.
- Visual review of the published PDF.
- Whether the post-Phase-4 commits were reviewed outside GitHub: no record exists.
