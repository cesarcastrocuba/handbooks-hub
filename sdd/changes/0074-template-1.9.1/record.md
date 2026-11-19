# Change 0074 — Template 1.9.1

Template `1.9.1` pins toolkit `0.14.1`: hub commit `9c4355e5174c41dbbaaae7fe6304c247768b69d2`,
the merge of PR 117 (change `0073`). The standard profile stays `1.1.0`, and the workflows of
template `1.9.0` are unchanged. Prepared by the coordinator (Claude); reviewed and merged by a
different agent.

## Write set

- `template/book/requirements.txt`, `template/book/book.yaml` and `template/book/README.md`: the pin
  and the version.
- `README.md`: the template and toolkit versions.
- `tools/tests/test_template.py`: the descriptor pin.
- `docs/book-upgrade.md`: the example "toolkit 0.14.0 to 0.14.1".
- `CHANGELOG.md` (`[1.9.1] - Unreleased`) and this record.

## Owner gates

1. The `edition-preview` job of this PR builds the Solutions Architecture `3.1.1` preview, the
   sample and the template with toolkit `0.14.1`. The Owner reads the web edition (light and dark)
   and opens the DOCX in desktop Word.
2. The Owner approves the tags `toolkit-v0.14.1` (at `9c4355e`) and `template-v1.9.1` in the chat.
   The coordinator then exports the template mirror and pushes the tag.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. Tags, the mirror and book releases are separate steps.
