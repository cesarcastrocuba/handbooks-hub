# Change 0078 — Template 1.9.2

Template `1.9.2` pins toolkit `0.14.2`: hub commit `47c37e23819abb801b1c8635401d6b64e7e14fad`,
the merge of PR 123 (change `0077`). The standard profile stays `1.1.0`, and the workflows of
template `1.9.0` are unchanged. Prepared by the coordinator (Claude); reviewed and merged by a
different agent.

## Write set

- `template/book/requirements.txt`, `template/book/book.yaml` and `template/book/README.md`: the pin
  and the version.
- `README.md`: the template and toolkit versions.
- `tools/tests/test_template.py`: the descriptor pin.
- `docs/book-upgrade.md`: the example "toolkit 0.14.1 to 0.14.2".
- `STATUS.md`: toolkit 0.14.2 and template 1.9.2 merged and untagged.
- `CHANGELOG.md` (`[1.9.2] - Unreleased`) and this record.

## Owner gates

1. Desktop Word check: the Owner checked the CI-built Solutions Architecture 4.0.0 DOCX built with
   the 0.14.2 code (PR 122, run 44735543751) on 2026-11-20: "All good". The `edition-preview` job of
   this PR builds the template, the sample and the SA book again with toolkit `0.14.2`.
2. The Owner approves the tags `toolkit-v0.14.2` (at `47c37e2`) and `template-v1.9.2` in the chat.
   The coordinator then exports the template mirror and pushes the tag.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. Tags, the mirror and book releases are separate steps.
