# Proposal — topic-neutral standard profile

**Status:** Proposed
**Date:** 2026-11-06
**Change:** `0004-topic-neutral-profile`

## Context

The common standard profile was derived from the Solutions Architecture Handbook. Its chapter
checklist was named `Architecture Review Checklist`, and it required at least one figure and one
captioned table in every section. The sample repository review identified both as integration
blockers: the checklist name is domain-specific, and a diagram or table is not always the right
explanation.

The handoff requires a common profile that preserves the reader elements while allowing explicit
profiles and exceptions. It does not require every section to contain a diagram or table.

## Decision

- Rename the chapter element to `review-checklist` with the title `Review Checklist`.
- Make figures and tables optional: they are absent from `section.required_elements`, and both
  `figure.required` and `table.required` are `false` with `min_per_section: 0`.
- Keep the rules that apply when a figure or table is used: source/alt text, proportional sizing,
  readable print size, captions below tables and adaptive widths.
- Keep the rest of the handoff elements: When to Use This Chapter, Key Takeaway, worked example,
  Definition/Purpose/What it includes/Why it is needed, Example, Common Pitfall, Decision &
  Trade-off, Review Checklist and Further Reading.
- Keep explicit profiles and owner-approved exceptions.
- Bump the profile to `0.2.0` and update the template pin.

## Non-goals

- Approving the profile. It remains `proposed`.
- Changing the sample repository or writing its profile.
- Removing the worked-example section or chapter-level review checklist.
- Adding manuscript content validation; that remains Phase 2 work.
- Merging or releasing anything.

## Consequences

A book can omit a diagram or table without recording an exception, but any figure or table it does
include must still meet the readability and caption rules. A book that cannot provide a worked
example or a chapter-level review checklist still needs an explicit profile or recorded exception.
The sample repository will still need its own descriptor/profile decision; this change removes only
the architecture-specific name and the mandatory visual elements.

## Owner decision

The profile remains **Proposed**. Owner approval is required before it becomes the default; this
change record does not approve it.
