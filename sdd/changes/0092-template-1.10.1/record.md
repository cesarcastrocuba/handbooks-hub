# Change 0092 — Template 1.10.1

Template `1.10.1` pins toolkit `0.16.2`: hub commit `25fb8010970f95e1d00afbff87f5657d1ce102ba`,
the merge of PR 153 (change `0091`). The standard profile stays `1.1.0`, and the template files
are otherwise unchanged from `1.10.0`. Prepared by the coordinator (Claude); reviewed by a
different agent.

## Write set

- `template/book/requirements.txt`, `template/book/book.yaml` and `template/book/README.md`: the pin
  and the version.
- `README.md`: the template and toolkit versions.
- `tools/tests/test_template.py`: the descriptor pin.
- `docs/book-upgrade.md`: the example "toolkit 0.16.1 to 0.16.2" (Optional 4 of the PR 153 review).
- `STATUS.md`, `CHANGELOG.md` (`[1.10.1]`) and this record.

## Owner gates

1. Desktop Word check of the toolkit 0.16.2 DOCX (the PR 152 previews): pending.
2. Approval of the tags `toolkit-v0.16.2` and `template-v1.10.1` in the chat: pending. The
   coordinator then exports the mirror (`docs/template-distribution.md`) and pushes the tag.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. The tag, the mirror and book releases are separate steps.
