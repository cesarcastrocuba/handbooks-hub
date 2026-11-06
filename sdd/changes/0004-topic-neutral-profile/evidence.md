# Evidence — topic-neutral standard profile

**Change:** `0004-topic-neutral-profile`
**Status:** Implemented, pending independent review
**Date:** 2026-11-06
**Branch:** `feat/topic-neutral-profile`
**Starting HEAD:** `0e8d897acae67d55eb09bf06a6e890d07d187779`
**Commit:** `5e626375c11b516052424be4e9cbc4f8f4beb357`

## Environment

| Item | Value |
| --- | --- |
| Python | 3.12.3 |
| `jsonschema` | 4.10.3 |
| `PyYAML` | 6.0.1 |
| Quarto | Not required for this change |
| Repository state | Hub clean at branch creation; sample and reference untouched |

## Changes

| Area | Change |
| --- | --- |
| Checklist | `architecture-review-checklist` / “Architecture Review Checklist” became `review-checklist` / “Review Checklist” |
| Figures | Removed from `section.required_elements`; `required: false`, `min_per_section: 0` |
| Tables | Removed from `section.required_elements`; `required: false`, `min_per_section: 0` |
| Validation | Reject an optional figure/table with a positive minimum; retain required-element minimum check |
| Tests | Added profile-contract and optional/required minima regressions |
| Docs | Updated editorial contract, implementation plan and publication example |
| Template | Profile pin moved from `0.1.0` to `0.2.0` |
| Governance | `STATUS.md`, `CHANGELOG.md` and this change record updated |

The profile remains `status: proposed`. No gate is approved.

## Commands and results

### 1. Fast checks

```bash
make check
```

Result: **PASS**

- 52 unit tests; `OK`.
- 5 checks, 0 problems.

### 2. Full checks

```bash
make full
```

Result: **PASS**

- 52 unit tests; `OK`.
- 6 checks, 0 problems.
- Documentation links resolve.

### 3. Profile and template validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/src python3 -B -m handbook_toolkit \
  --root . validate-profile profiles/standard/profile.yaml
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/src python3 -B -m handbook_toolkit \
  --root . validate-book template/book/book.yaml --full
```

Result: both report `OK`.

### 4. Compilation

```bash
python3 -m compileall -q tools
```

Result: **PASS** (exit 0).

### 5. Clean clone

```bash
git clone --branch feat/topic-neutral-profile /home/ubuntu/github/handbooks-hub /tmp/opencode/hub-clone-0004
cd /tmp/opencode/hub-clone-0004
make full
```

Result: **PASS**; 52 tests, 5 fast checks and 6 full checks with 0 problems. The clone remained
clean.

## Tests added

- `test_standard_profile_is_topic_neutral_and_visuals_are_optional`
- `test_required_figure_needs_a_minimum`
- `test_optional_figure_cannot_have_a_minimum`
- `test_required_table_needs_a_minimum`
- `test_optional_table_cannot_have_a_minimum`

The existing profile checks for duplicate ids/titles, closing order, labels, word ranges, upscaling and schema conformance continue to pass.

## Tradeoffs for review

- Worked example and chapter-level Review Checklist remain required. A book without a natural worked example still needs a profile or an explicit exception; this change does not remove that requirement.
- Figures and tables are optional, but quality rules still apply when used: alt text, source, proportional sizing, print readability, caption placement and adaptive widths.
- Profile `0.2.0` is a contract version change. Books pinned to `0.1.0` must update when adopting it; the hub template is updated.
- The toolkit validates profile structure and minima, not manuscript content. The Phase 2 manuscript validator is still needed before automated pilot conformance.
- The sample repository was not changed. Its own profile decision and descriptor work remain outside this change.

## Checks not run

| Check | Reason |
| --- | --- |
| Sample repository checks | Out of scope; this is a hub profile correction |
| Manuscript/profile content validation | Not implemented; Phase 2 |
| Artifact build | Not relevant to this contract change |
| GitHub Actions | No remote/CI execution from this environment |

## Review handoff

Review branch `feat/topic-neutral-profile` at the commit recorded above. Confirm:

1. The common profile no longer names an architecture-specific checklist.
2. Figures and tables are optional, while their quality rules remain.
3. Required section closure and the other handoff elements are preserved.
4. `exceptions` still require owner approval.
5. The profile remains `proposed` and no gate was approved.
