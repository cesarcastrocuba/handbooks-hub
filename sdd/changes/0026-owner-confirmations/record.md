# Record — Owner confirmations and release retention

**Decisions:** `HUB-DEC-028`, `HUB-DEC-029`, `HUB-DEC-030` (Proposed → Approved), `HUB-DEC-031`
(new). **Recorded:** 2026-11-11. **Change:** `0026-owner-confirmations`.

## Owner words, verbatim, 2026-11-11

- "Confirmo las decisiones, hay que actualziar."
- "Creo que es mejor que todas las versiones sigan publicadas verdad? por qué debemos borrar las antiguas, tal vez como refrencia la gente quiere buscar anntiguas versiones"

### Translation (not verbatim)

- "I confirm the decisions; they have to be updated."
- "I think it is better that all versions stay published, right? Why should we delete the old ones? Maybe people want to look up old versions as a reference."

## What was recorded

- `HUB-DEC-028` (Markdown edition), `HUB-DEC-029` (author onboarding) and `HUB-DEC-030` (library
  portal) move from **Proposed** to **Approved**. They were merged under the delegation in
  `HUB-DEC-027`; the Owner's confirmation is the approval.
- `HUB-DEC-031` records the retention rule: published releases stay published as previous editions,
  and a release is withdrawn only for a recorded reason (licensing or rights, integrity or security,
  or an edition published by mistake) by an explicit Owner decision. The catalog and portal list only
  the latest approved release.

## Consequences

- Sample `v0.2.4` and `v0.2.5` stay published as previous editions. Both describe a six-file release,
  which `v0.2.6` corrects; the historical editions are not rewritten.
- The earlier withdrawals (`HUB-DEC-021`, `HUB-DEC-023`, `HUB-DEC-027`, sample `DEC-019`) each had
  their own recorded decision and are not reversed.

## Not changed

- `docs/decisions.md` rows `HUB-DEC-028` to `HUB-DEC-030` keep their text; only the status and the
  closing sentence changed. No catalog, release or manuscript change is part of this record.
