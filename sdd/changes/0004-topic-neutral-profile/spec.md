# Spec — topic-neutral standard profile

**Status:** Proposed
**Change:** `0004-topic-neutral-profile`

## Deliverables

| ID | Deliverable | Location | State |
| --- | --- | --- | --- |
| D1 | Topic-neutral review checklist | `profiles/standard/profile.yaml` | Done |
| D2 | Optional figures and tables | `profiles/standard/profile.yaml` | Done |
| D3 | Profile semantic checks for optional/required minima | `tools/src/handbook_toolkit/profiles.py` | Done |
| D4 | Regression tests | `tools/tests/test_profile.py` | Done |
| D5 | Editorial contract and version references | `docs/editorial-contract.md`, `docs/implementation-plan.md`, `docs/publication-contract.md` | Done |
| D6 | Template profile pin | `template/book/book.yaml` | Done |
| D7 | Status and changelog | `STATUS.md`, `CHANGELOG.md` | Done |

## Profile contract

### Preserved chapter elements

- When to Use This Chapter
- Key Takeaway
- Worked Example
- Review Checklist
- Further Reading

### Preserved section closure

- Example
- Common Pitfall
- Decision & Trade-off

### Figures and tables

- Not required and not part of `section.required_elements`.
- `min_per_section: 0`.
- When present, the existing figure/table quality rules apply.
- Absence is not an exception.

### Exceptions

`exceptions.allowed` remains `true`; owner approval is required and the record location remains
`sdd/changes/<id>/profile-exceptions.md`.

## Acceptance criteria

1. The standard profile validates against `profile.schema.json`.
2. The profile has no architecture-specific element title.
3. A figure or table that is optional cannot declare a positive minimum.
4. A figure or table that is required must declare a minimum of at least one.
5. The template pins profile `0.2.0`.
6. `make check` and `make full` pass.
7. `STATUS.md` still marks the profile as Proposed.
8. No profile approval, merge or release occurs.

## Tradeoffs

- The worked example and chapter-level review checklist remain mandatory. A book without a natural
  worked example still needs a profile or exception decision; this change does not remove that
  requirement.
- Figures and tables remain governed by readability, caption and accessibility rules when used. The
  change removes compulsion, not quality control.
- The profile version moves to `0.2.0`; books pinning `0.1.0` must update when they adopt it. No book
  in this repository consumes `0.1.0` except the template, which is updated.
- At the time of this change the toolkit did not validate manuscript content. `0007` adds structural
  section-pilot/chapter validation; it still does not judge prose, facts or visual usefulness.

## Out of scope

- Sample repository changes.
- Profile approval.
- A new common profile id or a book-specific profile.
- Manuscript structural validators.
