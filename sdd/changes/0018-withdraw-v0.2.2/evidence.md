# Evidence — Withdrawal of sample `v0.2.2` and delegated execution of Phases 0 to D

**Decision:** `HUB-DEC-027` (Owner instruction 2026-11-10). **Recorded:** 2026-11-10.
**Plan:** `/home/ubuntu/.claude/plans/hazy-riding-map.md`, which supersedes `twinkly-chasing-castle.md`.

## Owner instructions, verbatim, 2026-11-10

- "Lee /home/ubuntu/.claude/plans/twinkly-chasing-castle.md, STATUS.md y docs/decisions.md para la decición retira la v.0.2.2 y ya creé un repositorio vacío https://github.com/cesarcastrocuba/handbooks-template"
- "Quiero que comiences y termines el plan de acción con todos los detalles por favor, dale caña, tienes toda la noche para subir e implementar los cambiso, tienes toda mi autorización para realizar los ajustes, no ahce falta que me preguntes nada puesto que me voy a dormir desde la Fase 0 a la Fase D, si hace falta abres otros agentes obreritos opencode"

### Translation (not verbatim)

- "Read /home/ubuntu/.claude/plans/twinkly-chasing-castle.md, STATUS.md and docs/decisions.md for the
  decision to withdraw v0.2.2, and I have already created an empty repository
  https://github.com/cesarcastrocuba/handbooks-template"
- "I want you to begin and finish the action plan with every detail please, go for it, you have all
  night to upload and implement the changes, you have all my authorization to make the adjustments,
  you do not need to ask me anything since I am going to sleep from Phase 0 to Phase D, if needed
  open other little opencode worker agents"

The second instruction is the delegation recorded in `HUB-DEC-027` (b): merges after independent
review and green CI, the `v0.2.2` deletion, the `toolkit-v0.6.0` tag, the sample `v0.2.5` dispatch and
catalog update, and the export to `cesarcastrocuba/handbooks-template`, for this sequence only.

## Preconditions verified 2026-11-10

| Check | Result |
| --- | --- |
| `catalog/catalog.json` | Lists `v0.2.4`, with `url`, `manifest_url` and `checksums_url` pointing at `v0.2.4`; no entry references `v0.2.2` |
| `gh release list -R cesarcastrocuba/handbook-sample-01` | `v0.2.4` marked **Latest** and `v0.2.2`; nothing else |
| Portal | Live and shows `v0.2.4` (`HUB-DEC-024`) |

The catalog therefore never links to a missing release once `v0.2.2` is deleted, which is the
condition the withdrawal order in the publication contract and the runbook Order B require.

## Plan scope, Phases 0 to D

- **Phase 0: withdraw sample `v0.2.2` (first, small)** — hub decision and evidence, sample
  documentation, independent review, then delete the release page and six assets keeping the tag.
- **Phase A: decisions and change records (hub, docs only)** — `HUB-DEC-028` Markdown edition,
  `HUB-DEC-029` author onboarding, `HUB-DEC-030` portal library; change records `0019` to `0021`.
- **Phase B: toolkit 0.6.0 (hub `tools/`)** — `book.md` payload, manifest schema 1.1, catalog schema
  1.1 with optional `assets`, portal library design and `llms.txt`, tests, tag `toolkit-v0.6.0`.
- **Phase C: template 1.1.0 and author path** — pin toolkit 0.6.0 in `template/book/`, export to
  `handbooks-template`, issue forms, author guide and `CONTRIBUTING` "Adding a book".
- **Phase D: prove it on the sample** — sample `v0.2.5` with seven verified files, catalog update
  carrying `assets`, portal auto-deploy with Markdown and `llms.txt`, dry run of
  `initialize-book.yml` in a throwaway repository.

## Withdrawal evidence

Recorded 2026-11-10, after hub PR 15 (`4c37598`) and sample PR 11 (`e4e3f82`) merged. Both were
implemented by a worker agent and reviewed by the coordinator on the pull-request HEAD.

| Step | Result |
| --- | --- |
| `gh release delete v0.2.2 -R cesarcastrocuba/handbook-sample-01 --yes` (no `--cleanup-tag`) | Release page and six assets deleted |
| `gh release list -R cesarcastrocuba/handbook-sample-01` | Only `v0.2.4`, marked **Latest** |
| `gh api repos/cesarcastrocuba/handbook-sample-01/git/ref/tags/v0.2.2` | `refs/tags/v0.2.2` still resolves to `c1485183ca1c52e28bdbd28c92c1f382b6603d55` |
| `python3 -m handbook_toolkit.catalog_verification catalog/catalog.json` | `release verification: OK` |
| `curl` of the portal URL | HTTP 200 |
| `curl -L` of the former `v0.2.2/book.pdf` asset URL | HTTP 404 |

## Process notes

- The plan file named at the top of this record is a local working file and is not part of the
  repository; the phase list above is the durable summary.
- The coordinator's first two merge attempts were refused by its tool permission layer. The Owner
  then wrote "autorizo a que fusiones" and "autorizo a todo lo que tengas que implementar relativo a
  este plan de acción" (2026-11-10), and the merges proceeded under `HUB-DEC-027` (b).

## Not run

- No sample artifact build was run, and no toolkit, template or portal code was changed by Phase 0.
