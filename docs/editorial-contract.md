# Editorial contract

The machine-readable contract is [`profiles/standard/profile.yaml`](../profiles/standard/profile.yaml)
and [`schemas/profile.schema.json`](../schemas/profile.schema.json). This document explains the
intent; the profile is authoritative when the two differ.

The profile is **Proposed**. Owner approval at Gate 1 makes `0.1.0` the default for new books.

## Why a profile exists

The reference handbook converged on a repeatable reader experience, but not every chapter needs the
same shape. The platform therefore separates:

- **Required skeleton** — the reader must always know why a chapter matters, how to use it and what
  to remember.
- **Required section closure** — a section ends with a concrete example, a pitfall and a real
  trade-off, so it informs a decision rather than only describing a topic.
- **Profile exceptions** — a book may declare a different profile or a recorded exception, approved
  by the owner. Exceptions are explicit, versioned and reviewed; they are not silent omissions.

## Standard chapter skeleton

In order:

1. `# N. Title` and one or two opening paragraphs.
2. A `When to Use This Chapter` callout.
3. A `Key Takeaway` callout.
4. Numbered sections `N.1 … N.k`.
5. One worked-example section (the in-practice element).
6. The `Architecture Review Checklist — <topic>` callout, as the last element of the worked example.
7. `## N.k Further Reading` as the last numbered section.

Callouts use this shape:

```markdown
::: {.callout-note appearance="simple" icon=false title="When to Use This Chapter"}
- A concrete situation where the chapter changes a decision.
:::
```

## Section and unit shape

A section either has no numbered subsections or at least two. A single subsection is a defect: add a
real second unit or merge it into the section.

Every unit starts with a one- or two-sentence definition and then three labelled paragraphs, in this
order:

```markdown
### N.M.K Title

**Definition.** What the concept is, in one or two sentences.

**Purpose.** The decisions it informs and the outcomes it changes.

**What it includes.** Dimensions, characteristics and key aspects.

**Why it is needed.** The consequence of omitting it and the evidence that shows it is in place.
```

Labels are bold, followed by a period. They are paragraphs, not headings. A unit is normally
150–350 words; reuse and reorganize real material before writing new prose.

A section closes with, in order:

1. `**Example.**` — a short, concrete case.
2. A `Common Pitfall` callout — the mistake, its consequence and how to avoid it.
3. A `Decision & Trade-off` callout — a framing sentence and a numbered
   `| Option | Choose when | Consequences |` table with 2–4 options.

The worked-example section follows its own shape. It begins with `*In practice:*` and may use
numbered steps, a figure or a table.

## Figures

- At least one figure per section; it must explain a structure, flow, lifecycle, decision or
  relationship. Decorative images and word clouds are not figures.
- Graphviz is the default source format for diagrams. A rendered figure keeps its source in the book
  repository.
- Preserve aspect ratio. Do not upscale a small diagram to fill the text column.
- At least 10 pt effective text in print. The reference handbook's RC5 work showed that nominal font
  size is not enough; validate the rendered and placed size.
- Natural width at most 2000 px at 200 dpi, with short node labels. Wide chains use a different rank
  direction or two rows.
- Every figure has alt text and a stable `Figure N.F — Title` caption.

## Tables

- At least one captioned table per section, outside the `Decision & Trade-off` callout.
- The caption goes below the table as `: Title`. The build numbers it as `Table N.T — Title`.
- Tables use adaptive column widths based on visible content, not a fixed equal split.
- A table is never placed directly after a figure, or vice versa; add explanatory prose between them.
- Tables inside `Decision & Trade-off` are not numbered and do not carry a caption.

## Cross-references and glossary

- Write references explicitly: `Chapter 4`, `4.2`, `Figure 4.1`, `Table 4.2`.
- Automatic glossary-term linking is off by default. A link must be deliberate and resolve to a real
  target; indiscriminate term links make prose noisy and create stale anchors.
- An index or glossary is generated from a curated source, not from automatic term detection.

## Review gates

| Gate | What the owner approves | What the reviewer verifies |
| --- | --- | --- |
| Brief | Audience, scope, outcomes, non-goals and length | Brief is testable and consistent with the profile |
| Outline | Chapter and section structure, figures, tables and checklists | Coverage, dependencies and no duplicate ownership |
| Pilot | One written section | Editorial quality, factual accuracy, figure/table readability, profile conformance |
| Expansion | Batches of chapters | Cross-references, consistency, licensing and evidence |
| Publication | Artifact set and release | Exact artifact bytes, manifest, checksums and catalog entry |

No substantive chapter expansion starts before the pilot is approved.

## Exceptions

An exception record states:

- the profile element and version;
- why the default does not fit;
- what replaces it;
- the scope (book, chapter or section);
- the owner approval reference and expiry or review trigger.

Record it under `sdd/changes/<id>/profile-exceptions.md` in the book repository. A book-wide
alternative profile is a new profile version, not an exception list.

## Mechanical enforcement

Phase 2 turns the profile into deterministic validators for the chapter skeleton, section closure,
unit labels, figure constraints and table captions. Until those validators exist, reviewers enforce
this contract manually and must not claim automated conformance.
