# Third-party rights review — bundled font binaries

**Status:** Open review written after the fact on 2026-11-14 for toolkit `0.9.1` and later.
**Scope:** every font binary shipped under `tools/src/handbook_toolkit/`: ten WOFF2 subsets and nine
TTF files in three family directories. This is an engineering record, not legal advice. It records
what the repository and its pull requests say about origin; where they say nothing, it says "not
recorded".

**Why it exists:** finding D6 in [`sdd/changes/0027-audit-plan/record.md`](../0027-audit-plan/record.md)
recorded that no rights review with hashes existed for Source Sans 3 and Source Serif 4, and that the
step from the original files to the renamed ones was not scripted.

## Families and licences

The three families and their upstream releases are the ones named in
[`NOTICE.md`](../../../NOTICE.md). The copyright and Reserved Font Name statements below were read
from each font's own name table (name ID 0) and from the `OFL.txt` stored beside it.

| Family | Files | Version (name ID 5) | Copyright (name ID 0) | Reserved Font Name | Licence file |
| --- | --- | --- | --- | --- | --- |
| Handbook Sans (Source Sans 3) | 4 TTF, 4 WOFF2 | `Version 3.052;hotconv 1.1.0;makeotfexe 2.6.0` | `© 2023 Adobe (http://www.adobe.com/), with Reserved Font Name ‘Source’` | `Source` | `fonts/source-sans3/OFL.txt` |
| Handbook Serif (Source Serif 4) | 3 TTF, 3 WOFF2 | `Version 4.005;hotconv 1.1.0;makeotfexe 2.6.0` | `© 2014 - 2023 Adobe (http://www.adobe.com/), with Reserved Font Name ‘Source’.` | `Source` | `fonts/source-serif4/OFL.txt` |
| Handbook Mono (JetBrains Mono) | 3 TTF, 3 WOFF2 | `Version 2.304; ttfautohint (v1.8.4.7-5d5b)` | `Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono)` | none declared | `fonts/jetbrains-mono/OFL.txt` |

All three `OFL.txt` files contain the SIL Open Font License 1.1 text. Their SHA-256 values:

| Licence file | SHA-256 |
| --- | --- |
| `fonts/source-sans3/OFL.txt` | `937d1985d2d6d003b6efdfa47e098b96c69d55395175f154d7f56410c942f978` |
| `fonts/source-serif4/OFL.txt` | `c21d7293d87b6d7ab1d0229a2f55b77f33a7613a6a4e66f6693d68d7d8d09464` |
| `fonts/jetbrains-mono/OFL.txt` | `30f0c136e3c88e422d0791acd97238870f9054a9729bc34cf2ff0d4ed8cac4ad` |

## File inventory

Paths are relative to `tools/src/handbook_toolkit/render_data/fonts/`. Hashes were produced with
`sha256sum`; family, full name and version were read with `fontTools.ttLib.TTFont` name IDs 1, 4 and 5.

| File | SHA-256 | Name ID 1 (family) | Name ID 4 (full name) | Licence beside it |
| --- | --- | --- | --- | --- |
| `source-sans3/HandbookSans-Regular.ttf` | `960a7c9de9cad40d8b0402065bb3785e8b3ac2c20277352475fe71000265b96d` | Handbook Sans | Handbook Sans Regular | `source-sans3/OFL.txt` |
| `source-sans3/HandbookSans-Bold.ttf` | `8d62b52f2ee3cd5919b4566fe9a065fbb45f84cb8e2854c25b3a5393a3c5fa23` | Handbook Sans | Handbook Sans Bold | `source-sans3/OFL.txt` |
| `source-sans3/HandbookSans-Italic.ttf` | `446cc67ad984b443a2c6caa5fa1b74d84ba3bdc6cbd31c3e68edb083d7941361` | Handbook Sans | Handbook Sans Italic | `source-sans3/OFL.txt` |
| `source-sans3/HandbookSans-BoldItalic.ttf` | `d788e95665ef3bff9656e0447c7465fd83cdf673d2a173f5468b1f4b34fefbea` | Handbook Sans | Handbook Sans Bold Italic | `source-sans3/OFL.txt` |
| `source-sans3/HandbookSans-Regular.woff2` | `bc5af694bd761ce4da5d3ef1022f20802a51c8da719ced52a1181b1555a8fa6b` | Handbook Sans | Handbook Sans Regular | `source-sans3/OFL.txt` |
| `source-sans3/HandbookSans-Bold.woff2` | `311b1c3a4fb941b00f0329324bd2b1f0056aa5817cf37886b49116c813b982f8` | Handbook Sans | Handbook Sans Bold | `source-sans3/OFL.txt` |
| `source-sans3/HandbookSans-Italic.woff2` | `71f69bb961e3ca9e50df1f8dffae7e0502a56b5002313e23dce6a9c4176e3144` | Handbook Sans | Handbook Sans Italic | `source-sans3/OFL.txt` |
| `source-sans3/HandbookSans-BoldItalic.woff2` | `dac1bab9b04d1db747be1640bc7a84991da25508fb54fa6f94847440c84faa27` | Handbook Sans | Handbook Sans Bold Italic | `source-sans3/OFL.txt` |
| `source-serif4/HandbookSerif-Regular.ttf` | `e105807be7339c09c4069f48f69413486cff9b2e57fb0c777a7b763d3125961a` | Handbook Serif | Handbook Serif Regular | `source-serif4/OFL.txt` |
| `source-serif4/HandbookSerif-Semibold.ttf` | `e661c7efc84b6ffefa682e89a322c33f85d1c2e2b06733ff9e1b2dcb1e468a88` | Handbook Serif | Handbook Serif Semibold | `source-serif4/OFL.txt` |
| `source-serif4/HandbookSerif-Bold.ttf` | `10100fbe5407903b001afc4e67948ff99d3547e75ebd2c1073d28f91c9f6ace4` | Handbook Serif | Handbook Serif Bold | `source-serif4/OFL.txt` |
| `source-serif4/HandbookSerif-Regular.woff2` | `451f94fe67f2c8eaea8a3366f8d0d34b0b8c2b71328b57cd3a64c7efe1b76619` | Handbook Serif | Handbook Serif Regular | `source-serif4/OFL.txt` |
| `source-serif4/HandbookSerif-Semibold.woff2` | `25112860717d1e4ca4e3697c40bd4390c00d32f57c984b5f0120ee635b950a87` | Handbook Serif | Handbook Serif Semibold | `source-serif4/OFL.txt` |
| `source-serif4/HandbookSerif-Bold.woff2` | `3b5a0e64b98cb0c43cce5b57067e50a692ec092cf4852a2c898eacc0724163b3` | Handbook Serif | Handbook Serif Bold | `source-serif4/OFL.txt` |
| `jetbrains-mono/JetBrainsMono-Regular.ttf` | `a0bf60ef0f83c5ed4d7a75d45838548b1f6873372dfac88f71804491898d138f` | JetBrains Mono | JetBrains Mono Regular | `jetbrains-mono/OFL.txt` |
| `jetbrains-mono/JetBrainsMono-Bold.ttf` | `5590990c82e097397517f275f430af4546e1c45cff408bde4255dad142479dcb` | JetBrains Mono | JetBrains Mono Bold | `jetbrains-mono/OFL.txt` |
| `jetbrains-mono/JetBrainsMono-Italic.ttf` | `9d0a1f7a708e6af183f1193b7e81d40da294f5c67682c085d8401c60aac8ded4` | JetBrains Mono | JetBrains Mono Italic | `jetbrains-mono/OFL.txt` |
| `jetbrains-mono/HandbookMono-Regular.woff2` | `261e9d78afecaa7cfb1846f52eafb4f09c14bbca44c4415bc3e7621681d95d5a` | Handbook Mono | Handbook Mono Regular | `jetbrains-mono/OFL.txt` |
| `jetbrains-mono/HandbookMono-Bold.woff2` | `8589ecc3d7bb010964470480f26c60207c81ea1823086034994b954d198f6c54` | Handbook Mono | Handbook Mono Bold | `jetbrains-mono/OFL.txt` |
| `jetbrains-mono/HandbookMono-Italic.woff2` | `402e6e1ab92c4e0af00903b0f8a999db2c1e84a9c9b702753af13cebf3c44ec5` | Handbook Mono | Handbook Mono Italic | `jetbrains-mono/OFL.txt` |

The three JetBrains Mono TTF hashes match the values recorded for toolkit `0.5.0` in
[`sdd/changes/0010-post-phase4-remediation/rights-review.md`](../0010-post-phase4-remediation/rights-review.md)
(R1 replacement). No earlier hash record exists for any Source Sans 3 or Source Serif 4 file.

## Where the files came from

| Family | Upstream project, as recorded | What is recorded | What is not recorded |
| --- | --- | --- | --- |
| Source Sans 3 | <https://github.com/adobe-fonts/source-sans/releases/tag/3.052R> (version `3.052R`) in `NOTICE.md` | Project, release tag and version | The archive or URL actually downloaded, its hash, the command that renamed the TTF files, and when that happened |
| Source Serif 4 | <https://github.com/adobe-fonts/source-serif/releases/tag/4.005R> (version `4.005R`) in `NOTICE.md` | Project, release tag and version | The archive or URL actually downloaded, its hash, the command that renamed the TTF files, and when that happened |
| JetBrains Mono | <https://github.com/JetBrains/JetBrainsMono/releases/tag/v2.304> (version `2.304`) in `NOTICE.md`; the `0010` review records the TTFs as byte-identical to `fonts/ttf/` in the upstream `JetBrainsMono-2.304.zip` | Project, release tag, version, archive name and byte-identity of the TTF files | The download command and its date are not recorded; they are not needed because the hashes match the `0010` record |

The ten WOFF2 files are subsets generated from the committed TTF files by
`tools/scripts/subset_web_fonts.py`. The script and its source files are recorded in commits
`a4949a9` and `9be5eba`; the WOFF2 files are committed, not rebuilt during a book build. The script's
module docstring describes the same path and names the manual step that it does not perform.

The Source Sans 3 and Source Serif 4 TTF files were already renamed when they entered the repository
in commit `9be5eba` (2026-11-13). No script in the repository produces those renamed TTF files, and no
commit message, pull request body or change record documents the command that did. That step is a
recorded gap, not a verified reproduction.

## Reserved Font Name check

The OFL text of Source Sans 3 and Source Serif 4 declares `Source` as a Reserved Font Name; the
JetBrains Mono OFL declares none. A modified font may not use a Reserved Font Name as its font name
without written permission.

What was verified in every one of the 19 binaries, by reading the name table with FontTools:

- Name IDs 1, 2, 3, 4, 6, 16 and 17 — family, style, unique identifier, full name, PostScript name and
  typographic family/subfamily — contain `Handbook Sans`, `Handbook Serif` or `Handbook Mono`; none
  of them contains `Source`, `JetBrains`, `Liberation`, `Selawik` or `Cascadia`.
- The ten WOFF2 subsets additionally set name ID 13 to the OFL 1.1 statement and name ID 14 to
  `https://openfontlicense.org`, and their unique identifier (name ID 3) reads, for example,
  `Handbook Sans Regular subset; 2026; OFL-1.1`.
- Name ID 0 keeps the upstream copyright and the Reserved Font Name phrase as copyright text, and
  name ID 7 keeps Adobe's or JetBrains' trademark statement. Neither is an identifying font name, and
  neither is removed by the subsetting script.
- The three `OFL.txt` files are packaged in the toolkit, copied beside the fonts by the build, linked
  from the generated portal footer, and shipped in the HTML ZIP, so a copy of the modified fonts
  travels with the licence text.

Not verified, and outside what a local check can establish: whether Adobe or JetBrains would accept
this renaming as sufficient in every jurisdiction, and whether the committed TTFs are unmodified
upstream glyph data apart from naming. The repository records no upstream hash for the two Adobe
families, so their glyph content cannot be compared with a named upstream archive from here.

## Known gaps

1. **The TTF rename is not scripted.** The renamed Source Sans 3 and Source Serif 4 TTF files have no
   reproducible source in the repository: no download step, no hash check and no rename command. Only
   the WOFF2 step is scripted. D6 recorded this; it remains open.
2. **No upstream hash for the Adobe families.** The `0010` review could compare Selawik, Cascadia,
   Liberation Sans and JetBrains Mono with named archives. No equivalent record exists for the two
   Adobe families.
3. **The `NOTICE.md` entries are the only provenance record** for the Adobe families. They name the
   project and release but not the file actually taken from it.

## Commands run

```bash
find tools/src \( -name '*.woff2' -o -name '*.ttf' -o -name '*.otf' \) | sort
find tools/src \( -name '*.woff2' -o -name '*.ttf' \) -print0 | sort -z | xargs -0 sha256sum
find tools/src/handbook_toolkit/render_data/fonts -name '*.txt' -print0 | sort -z | xargs -0 sha256sum
.venv/bin/python  # FontTools: read name IDs 0, 1, 4, 5, 13 and 14 from every binary
```

The FontTools step ran in a venv created in the worktree from `requirements-dev.txt` (`fonttools
4.68.0`). No font was modified by this review.
