# Proposal — structural manuscript validation

**Status:** Proposed
**Change:** `0007-manuscript-validation`
**Branch:** `feat/manuscript-validation`

## Context

The toolkit can validate book descriptors, profiles and reading order, but it cannot check whether a
pilot section or chapter has the structure declared by the approved profile. Phase 2 needs a
deterministic structural check before publication work can consume it.

## Interface

```text
handbook-toolkit --root ROOT validate-manuscript PATH --mode section-pilot --profile PROFILE
```

- `--profile` is required until profile distribution/resolution is implemented.
- `--mode section-pilot` checks one section's required Definition/Purpose/What it includes/Why it is
  needed labels, closing Example/Common Pitfall/Decision & Trade-off order, non-empty bodies,
  heading and actual paragraph/callout forms.
- `--mode chapter` checks When to Use This Chapter, Key Takeaway, Worked Example, Review Checklist
  placement and Further Reading, then applies the section/unit rules to every ordinary content
  section. Worked Example and Further Reading are special sections and are exempt from the ordinary
  section shape.
- Fenced code is excluded with delimiter-length-aware fences. Unclosed or malformed callouts are
  errors, not silently accepted divs.
- Missing, duplicate, misordered and wrong-form elements are reported with line locations.

## Boundaries

The validator is structural only. It does not judge prose quality, meaning, factual accuracy,
whether a diagram or table is useful, or whether the profile matches the book. It does not require
visuals and does not enforce word quotas. It is not a semantic or publication validator.

## Tooling

- Toolkit version `0.2.0` adds the command; source installs remain exact.
- No scripts are copied from the existing handbook.
- Publication manifest/checksum work is a separate root slice; this change does not edit root-owned
  publication files.

## Acceptance

- Accepted section-pilot and chapter fixtures without visuals.
- Rejected missing/duplicate/misordered labels and closing elements.
- Rejected empty label/paragraph/callout bodies.
- Rejected wrong forms, wrong callout class, unclosed callouts, fake content inside fenced code and
  non-delimiter-aware fence boundaries.
- Rejected chapter content sections missing unit labels or closing elements, and single-subsection
  sections where the profile forbids them.
- `make check` and `make full` pass.
