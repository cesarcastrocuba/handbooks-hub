# Evidence — Release `v0.2.1` and withdrawal of earlier releases

**Decision:** `HUB-DEC-021`. **Book commit:** `0549762699a95764467ee75cba28d8a791480394`. **Toolkit:** `0.5.0`, tag `toolkit-v0.5.0`.

## Owner instructions, verbatim, 2026-11-08

- "1. actualiza el catálogo con lo nuevo y retira lo antiguo 2. solutions no toques, luego al migrar verémos estos trmas"
- Merges, answering a question that named the exception to `AGENTS.md`: "Delegar en Claude".
- Withdrawal, answering a question that warned deletion is irreversible: "Borrar releases, conservar tags".
- "sobre la integración autorizo 1 y 2"

## Sequence

1. Merge hub #1 and sample #1, tag `toolkit-v0.5.0`.
2. Merge sample #2 and run the release workflow on `main`.
3. Verify `v0.2.1`, then update the catalog through this change.
4. Redeploy the portal, then delete the release pages and assets of `v0.1.0` to `v0.2.0`, keeping tags.

## Results for `v0.2.1`

| Check | Result |
| --- | --- |
| Release workflow on `main` | Success, build and Pages deploy |
| `sha256sum -c SHA256SUMS.txt` | Pass, 5 files |
| Manifest | Commit above, toolkit `0.5.0`, profile `1.0.0` |
| PDF | 50 pages; `pdffonts` lists only Selawik, JetBrains Mono and Liberation Sans |
| Reading site, manifest and checksums URLs | HTTP 200 |
| `python3 -m handbook_toolkit.catalog_verification catalog/catalog.json` | `release verification: OK` |

## Not verified

- Full visual review of the PDF and rendering of the DOCX in Microsoft Word.
- Copies of withdrawn editions held outside GitHub cannot be recalled.
