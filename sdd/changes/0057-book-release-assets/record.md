# Change 0057 — Book-Owned Extra Release Assets (Gap G6)

Provide a generic, opt-in mechanism in the template release workflow (`release.yml`) for
book-owned generated release deliverables (such as checklist exports, data templates, and assessment
spreadsheets) without violating **HUB-DEC-003** (generated files are never committed) or mutating
the publication manifest and `SHA256SUMS.txt` contracts.

Closes Gap **G6** identified in the Change 0048 Solutions Architecture Handbook inventory.

## Design

1. **Opt-in Detection**:
   - In `release.yml`, after the verified toolkit build and before `gh release create`, the workflow checks
     whether the book's `Makefile` defines a `release-assets` target using `make -n release-assets`.
   - If not defined (`make -n` exits 2), the workflow prints an informational message and skips extra asset
     generation. Books without the target behave identically to today.
   - If defined (`make -n` exits 0), the workflow creates an empty `$RUNNER_TEMP/extra-assets` directory and runs:
     ```bash
     make release-assets RELEASE_ASSETS_DIR="$RUNNER_TEMP/extra-assets"
     ```

2. **Clean Working Tree Requirement**:
   - The working tree must remain clean after `make release-assets` runs (`test -z "$(git status --porcelain)"`).
   - Any generated files must reside in ignored directories (such as `_build/`) or directly in `$RELEASE_ASSETS_DIR`.

3. **Validation & Security Constraints**:
   - Files must be regular files directly inside `$EXTRA_ASSETS_DIR` (no subdirectories, no symlinks).
   - Filenames must match `^[A-Za-z0-9][A-Za-z0-9._-]*$`.
   - Filenames must not collide with publication files:
     `book-html.zip`, `book-source.zip`, `book.docx`, `book.md`, `book.pdf`, `book-extras.zip`,
     `publication-manifest.json`, `SHA256SUMS.txt`, `EXTRAS-SHA256SUMS.txt`.
   - Sensible size and count caps:
     - Count: 1 to 100 files
     - Single file size: max 10 MiB (10,485,760 bytes)
     - Total uncompressed size: max 50 MiB (52,428,800 bytes)

4. **Deterministic Packaging**:
   - The validated files are packed into ONE asset: `book-extras.zip` in `$RELEASE_DIR`.
   - Deterministic packaging: entries sorted by name, normalized POSIX file permissions (`0o100644`),
     fixed timestamps derived from `SOURCE_DATE_EPOCH` (or fallback `1980-01-01 00:00:00`), and zlib Deflate level 9.
   - A separate checksum file `EXTRAS-SHA256SUMS.txt` is written in `$RELEASE_DIR` with the SHA256 of `book-extras.zip`.
   - Core `publication-manifest.json` and `SHA256SUMS.txt` remain untouched, preserving toolkit release verification
     and the catalog contract.
   - Both `book-extras.zip` and `EXTRAS-SHA256SUMS.txt` are included in the release upload via `"$RELEASE_DIR"/*`.

## Dry Run Proof (Solutions Architecture Checklist Deliverables)

Dry run executed against a scratch checkout of `cesarcastrocuba/handbook-solutions-architecture` (at `a5426bc`, `main`) by extracting and executing the exact `run:` shell script of the `Build book-owned extra release assets (opt-in)` workflow step from `template/book/.github/workflows/release.yml`.

- **Scratch Target in Makefile**:
  ```makefile
  release-assets: checklist-exports
  	@mkdir -p "$(RELEASE_ASSETS_DIR)"
  	cp _build/checklists/exports/* "$(RELEASE_ASSETS_DIR)/"
  ```
- **Step Execution Output**:
  ```
  Building book-owned extra release assets...
  /tmp/scratch-runner-temp/toolkit-venv/bin/python scripts/checklists.py --check --export
  CHECKLISTS_OK: 145 active items in 19 domains
  EXPORT_OK: 145 items, 4 files updated
  /tmp/scratch-runner-temp/toolkit-venv/bin/python scripts/export_checklists_csv.py --all
  CHECKLIST_EXPORT_OK: items=96 files=17
  cp _build/checklists/exports/* "/tmp/scratch-runner-temp/extra-assets/"
  packaged 21 extra release assets into book-extras.zip (75184 bytes)
  ```
- **Working Tree Cleanliness**: `git status --porcelain` is clean (0 changes).
- **Packaged Asset**: `book-extras.zip` (75,184 bytes).
- **Checksum File `EXTRAS-SHA256SUMS.txt`**:
  ```
  55ef3341ec88f719c9ad8dfb46255db379ce87b1ac3c99c107bb251757896de4  book-extras.zip
  ```

### Member Verification Against Frozen v3.0.0 Exports

All 21 files inside `book-extras.zip` match the frozen v3.0.0 release exports byte-for-byte:

| Zip Member | SHA256 Checksum | v3.0.0 Match |
| --- | --- | :---: |
| `all-checklists.csv` | `bd92d046553fa0c3b0eb1c58d2e85e30ea38037fdeac8b18aa41c5e22938ef5c` | Yes |
| `appendix-c-source-checklist.csv` | `4f2d73ab4d14dbd22d55d52e3a8b1c1234e6a6550df9198e8823eea97119f813` | Yes |
| `architecture-review-assessment-template.csv` | `896981f51e2e14d78144a8f63eaf9e94bc6d4fa692a5b2570d5012c3a76712e9` | Yes |
| `architecture-review-checklist.csv` | `e4f9609b7c1571e3cd42585102ec34f2540db970179cd451be4c5be89c10adb8` | Yes |
| `architecture-review-checklist.json` | `a0f902c0aa644e7f13f4d2ea346cc53d3265c5f8cbd8a87c45c28d226deab8fd` | Yes |
| `architecture-review-checklist.md` | `448462498f6d59b12c52e403349e86f2c4ca75cd2adb29147d36532eb9e03f0a` | Yes |
| `ch01-source-checklist.csv` | `bb754ab5c30cee55d56fcfd60ddecc89e91a144dae7f92674b351c6581745d2a` | Yes |
| `ch02-source-checklist.csv` | `ff5b2d7616bc2e34d9ad98c42ab33d625d6e03811420166ff7ee100a096841a2` | Yes |
| `ch03-source-checklist.csv` | `4d7abd0ff630b7d0100d7136827d72185cb5cb3591817bb15d22abafe0ecf4da` | Yes |
| `ch04-source-checklist.csv` | `f1ea94eae151af58662e9339fde9b3a34294b708e045413b6225a3408630f706` | Yes |
| `ch05-source-checklist.csv` | `e75fae9e98f996f27d7ac4fb1dea6f636fea442501436fc7195ef25f4c8728c1` | Yes |
| `ch06-integration-checklist.csv` | `e6c420c26417ec304d6e5dd6495e00943012967bb6738c805c73ce1299c9c3f4` | Yes |
| `ch07-source-checklist.csv` | `3107b312da9653e96ad9588e011b0c4b595078955f38b5b25bc137ebdd2ec710` | Yes |
| `ch08-source-checklist.csv` | `be2b69146cf46b1b842abe759449ecd74338d5b6c15f773aef10d8b67d043e9a` | Yes |
| `ch09-source-checklist.csv` | `abe31e734fcaaef49e5e447e5643b5c54ea1ada65361bfdbf63803874a4277b9` | Yes |
| `ch10-source-checklist.csv` | `91b3681091fe9abb80ceaa2c57b087a21d5a86ffca17dcf2de5955fabb778a59` | Yes |
| `ch11-source-checklist.csv` | `1342ac9c68d52f77970bb25e0eb27e5e1f4b34753101ee0ccddbbbc2f7acf2c4` | Yes |
| `ch12-source-checklist.csv` | `32c257dcc15a2eef42f8ad7d2d02fef8ae9a2123076c71c75437e34e49661efe` | Yes |
| `ch13-source-checklist.csv` | `e5e735717f5ebce743a7a97ffe7437a3ad7a33e80804e029476f3240e77046a7` | Yes |
| `ch14-source-checklist.csv` | `24f4eff73ecf68950c8e580e17e8924ecde8aad2cdd004465ba3712b4f68a291` | Yes |
| `ch15-source-checklist.csv` | `cebe6dcaab1dea5912cfee052a2295c6caa30f388c83f3bcc0d86b3f3c4094e2` | Yes |

Result: `All 21 files match v3.0.0 frozen exports: True`.
