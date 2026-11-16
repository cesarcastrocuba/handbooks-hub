# Change 0056 — Template 1.7.0

Prepare template `1.7.0` pinned to toolkit `0.12.0` (change `0054`, PR 89) and standard profile
`1.1.0` (`HUB-DEC-044 (2)`: "the standard profile becomes `1.1.0` with toolkit `0.12.0`"). It
carries the template work of change `0049` (PR 84): pre-release versions `X.Y.Z-rc.N` in the
release workflow (G1), the tailored README written by `initialize_book.py` (G11) and the `Fast
checks` documentation (G10). The coordinator publishes the mirror and the tag `template-v1.7.0`
after review, merge and the Owner's approval.

## Pins and scope

- Toolkit pin: `0824ddfaebd28f170f157fcb38641c7dc65d6c20`, the merge commit of PR 89. The tag
  `toolkit-v0.12.0` is created on this same commit after the Owner's approval; requirements pin the
  peeled commit, never the tag object or a branch.
- Template: `book.yaml` (toolkit `0.12.0`, profile `1.1.0`), `requirements.txt`, the README heading
  and pin sentence, and the tests that read them.
- Hub: README status and versions (the profile line was stale at `1.0.0`), CHANGELOG, the upgrade
  example for `0.11.0` → `0.12.0`, and STATUS.
- CI: the `edition-preview` job also builds `cesarcastrocuba/handbook-solutions-architecture`, so every
  hub pull request previews the platform's first full-size book (18 chapters, 10 appendices, 121
  figures, 263 tables) and the Owner's Word check of this round uses a CI-built DOCX of it. The job
  timeout rises from 20 to 45 minutes for that build. The runbook and the workflow test name the
  third artifact, `edition-preview-solutions-architecture`.

## Owner gates (not part of the merge)

One desktop Word round over the three CI-built DOCX files of this pull request (template, sample,
Solutions Architecture Handbook), then the Owner's approval of the tags `toolkit-v0.12.0`,
`template-v1.7.0` and the book's `v3.1.0-rc.1`, plus confirmation of the fourth relaxation of profile
`1.1.0` (change `0050` record, line 54).

## Verification evidence

Pasted in the pull request from commands run on its exact HEAD.

Rollback boundary: revert this change. No mirror, tag, catalog entry or book release is changed here.
