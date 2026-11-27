# Change 0088 — Template 1.10.0

Template `1.10.0` pins toolkit `0.16.1`: hub commit `0c89c38c9375d39cc9f2747469f545ee5dd7b561`,
the merge of PR 149 (change `0087`), tagged `toolkit-v0.16.1`. The standard profile stays `1.1.0`.
It is a minor release because the template itself changed since `1.9.2`: the release workflow reads
the repository star count before the build (change `0085`), the README describes the star link, and
`NOTICE.md` names Inter and JetBrains Mono (change `0083`). Prepared by the coordinator (Claude);
reviewed by a different agent.

## Write set

- `template/book/requirements.txt`, `template/book/book.yaml` and `template/book/README.md`: the pin
  and the version.
- `README.md`: the template and toolkit versions.
- `tools/tests/test_template.py`: the descriptor pin.
- `docs/book-upgrade.md`: the example "toolkit 0.14.2 to 0.16.1".
- `STATUS.md`, `CHANGELOG.md` (`[1.10.0]`) and this record.

## Owner gates

1. The toolkit 0.16.1 print editions are content-identical to 0.16.0 (change `0087`), so no new
   desktop Word check is needed for the template pin. The `edition-preview (template)` job of this
   PR builds the template with toolkit `0.16.1`.
2. The Owner approved the tag `template-v1.10.0` in the chat on 2026-11-27 ("si a 1,2,3 por favor
   dale caña") and authorized the coordinator to merge after another agent approves and CI is
   green. The coordinator then exports the mirror (`docs/template-distribution.md`) and pushes the
   tag.

## Verification evidence

The pull request records the evidence, from commands run on its exact HEAD.

Rollback boundary: revert this commit. The tag, the mirror and book releases are separate steps.
