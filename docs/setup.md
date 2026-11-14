# Setup and local checks

This guide is for people who want to run the hub's checks or work on an independent book. Reading a
published handbook needs no installation.

## 1. Who needs what

| Role | Needs | Does not need |
| --- | --- | --- |
| Reader of a published handbook | A browser and the book's reading site or release downloads | Python, Git, Quarto |
| Contributor to this hub | Git, Python 3.11+, pip, venv; `make` unless using the no-make path | Quarto, Poppler, PDF/DOCX tools |
| Hub maintainer | The contributor setup plus CI and toolkit knowledge | A local publication toolchain |
| Independent book author | Python, venv, Git and the pinned `handbook-toolkit` | A hub checkout, copied toolkit code or schemas |

The current validators check contracts, catalog/profile/book descriptors and repository files. The
render toolchain (Quarto, Poppler `pdfinfo`, PDF/DOCX rendering) is the optional build described in
section 7. It is not required for validator-only work. When Quarto is installed, `make full` also runs real renderer tests.

## 2. Tested platforms and prerequisites

| Item | Tested state |
| --- | --- |
| OS | Ubuntu 24.04 (GitHub Actions `ubuntu-24.04`) and a Linux workstation |
| Python | 3.12 (3.11+ required by the toolkit) |
| Git | 2.43+ |
| pip | Installed with the Python environment |
| venv | Python's `venv` module; `ensurepip` must be available |
| make | GNU make; optional if using the no-make path |

macOS and native Windows are **not tested**. The POSIX shell commands below work on Linux. If you
use PowerShell on Windows, the venv activation command is:

```powershell
.venv\Scripts\Activate.ps1
```

That activation line is provided for accuracy only; no native Windows command sequence is claimed as
tested. Use WSL or a Linux environment if you need the tested path.

## 3. Prerequisites on Debian/Ubuntu

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv make
```

If `python3 -m venv` reports that `ensurepip` is missing, install the venv package for the exact
Python minor version, for example:

```bash
sudo apt install -y python3.12-venv
```

Substitute your installed version. Then delete and recreate `.venv`.

Verify the basics:

```bash
git --version
python3 --version
python3 -m pip --version
make --version
```

## 4. Hub contributor or maintainer quickstart

These are the exact commands in the README quickstart. They create `.venv` **inside the clone**, not
in an external temporary directory.

```bash
git clone https://github.com/cesarcastrocuba/handbooks-hub.git
cd handbooks-hub
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-dev.txt
make check
make full
```

`requirements-dev.txt` installs the editable local toolkit (`-e ./tools`) with its
`jsonschema`/`PyYAML` dependencies, plus `fonttools` and `brotli` for the font tests.

- `make check` runs the unit tests and the fast validators.
- `make full` runs the same checks plus documentation-link, documentation-currency and full
  template checks.
- `.venv/` is ignored by Git. The hub's checks do not scan it.

The critical path note: an **external** temporary venv is not proof that this in-repo `.venv`
quickstart works. Test the commands above in the clone, or use CI, which creates `.venv` in the
checkout.

## 5. No-make path

Use this when GNU make is unavailable. It is the same environment and the same checks.

```bash
git clone https://github.com/cesarcastrocuba/handbooks-hub.git
cd handbooks-hub
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-dev.txt

PYTHONPATH=tools/src python3 -m unittest discover -s tools/tests -v
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify
PYTHONPATH=tools/src python3 -m handbook_toolkit --root . verify --full
```

The last command is the full current-scope check. It does not build HTML, PDF or DOCX.

## 6. Troubleshooting

### `No module named venv` or `ensurepip is not available`

Install the distro venv package for your Python version, then recreate the environment:

```bash
sudo apt install -y python3-venv
rm -rf .venv
python3 -m venv .venv
```

If a version-specific package is required, use `python3.12-venv` or the matching minor version.

### `pip: command not found`

Use the interpreter-bound form inside the activated environment:

```bash
python3 -m pip --version
```

If that fails, install `python3-pip`, activate the venv and try:

```bash
python3 -m ensurepip --upgrade
```

If `ensurepip` is still unavailable, install the distro venv package and recreate `.venv`.

### `externally-managed-environment` when installing

The system Python refuses global installs. Activate the venv and install there:

```bash
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

### `make: command not found`

Install `make` or use the [no-make path](#5-no-make-path).

### `python3` is too old

The toolkit requires Python 3.11 or newer. Check `python3 --version`; install or select a supported
interpreter and recreate `.venv` with that interpreter.

### The environment or scanner rejects an in-repo `.venv`

The hub's `.gitignore` excludes `.venv/` and the hub checks do not scan it. A different tool may
still scan ignored directories. If that tool is part of your workflow, configure its exclusion or
use its documented external-environment mode; that is a different setup path and does not establish
that the in-repo quickstart above works. Do not describe an external temp venv as proof of the
in-repo path.

## 7. Independent book authors and the pinned toolkit

A book repository owns its manuscript and installs the shared toolkit from a pinned hub commit. It
must not import a parent checkout or copy the hub's `tools/`, schemas or scripts.

The template contains a `requirements.txt` with a direct, non-editable VCS pin:

```text
handbook-toolkit @ git+https://github.com/cesarcastrocuba/handbooks-hub.git@<FULL_HUB_COMMIT_SHA>#subdirectory=tools
```

Use a full 40-character commit SHA, never a branch name or a range. The template's committed value
is a working example; replace it with the hub commit the book has reviewed.

```bash
git clone https://github.com/OWNER/BOOK.git
cd BOOK
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
handbook-toolkit --root . validate-book
```

After the reading order and pilot exist, run the full descriptor/reading-order check:

```bash
handbook-toolkit --root . validate-book --full
```

Structural manuscript validation requires an explicit reviewed profile until packaged profile
resolution is implemented:

```bash
handbook-toolkit --root . validate-manuscript manuscript/chapters/pilot.qmd --mode section-pilot --profile /path/to/standard-profile.yaml

handbook-toolkit --root . validate-manuscript manuscript/chapters/ch01.qmd --mode chapter --profile /path/to/standard-profile.yaml
```

The validator checks structure only: labels, opening callouts, worked example, review checklist
placement, closing order, actual paragraph/callout forms, non-empty bodies, duplicates, malformed or
unclosed callouts, and delimiter-length-aware fenced-code exclusion. In chapter mode it applies the
section/unit rules to each ordinary content section; Worked Example and Further Reading are exempt. It
does not judge meaning, factual accuracy, prose quality or visual usefulness, and it never requires a
diagram or table. The explicit `--profile` path is a current limitation of profile distribution; an absolute path is
simplest for an independent book. Do not silently substitute a different profile.

The toolkit validates descriptor, catalog/profile/book schema, reading-order and structural
manuscript form. Chapter mode applies the section/unit rules to each ordinary content section;
Worked Example and Further Reading are special sections. The profile is referenced in `book.yaml`
but is not yet resolved from the installed package; an explicit `--profile` is required, and prose
quality, factual accuracy and visual usefulness remain review responsibilities.

### Optional publication build

The separate `handbook-toolkit build-book` command renders HTML/Typst/DOCX, creates source and HTML
ZIPs, inspects payloads, writes the manifest/checksums and atomically exposes a verified seven-file
directory. It requires Quarto `1.11.9`, Poppler `pdfinfo` and a clean source commit; the profile resolves from
the installed package by default, with `--profile` as an explicit override. None of that is installed
by `requirements-dev.txt` or `requirements.txt` and none is required for the checks above. See [`publication-build.md`](publication-build.md). It does not
publish, deploy or release anything.

## 8. Portal and design preview

The deployed single-page portal needs only the toolkit. Building the opt-in Quarto candidate or
living Design page additionally requires Quarto **1.11.9**; no PDF or Word tool is needed for the
portal itself. Use new output directories:

```sh
handbook-toolkit build-portal --catalog catalog/catalog.json --output /tmp/hub-portal
handbook-toolkit build-portal --catalog catalog/catalog.json --output /tmp/hub-portal-quarto --engine quarto
handbook-toolkit design-preview --output /tmp/hub-design
```

For screenshots, activate the contributor venv, then:

```sh
python3 -m pip install -r tools/scripts/requirements-edition-preview.txt
python3 -m playwright install chromium
python3 tools/scripts/portal_preview.py --output /tmp/hub-portal-preview
```

On a machine missing browser system libraries, Playwright's `install --with-deps chromium` installs
those operating-system dependencies too. The preview uses a temporary loopback HTTP server and
rejects external browser resources. See [portal.md](portal.md) for the parity/deployment gate and
online catalog verification. Neither preview command deploys or releases anything.

## 9. Where to go next

- Hub contributors: [`../CONTRIBUTING.md`](../CONTRIBUTING.md), [`../AGENTS.md`](../AGENTS.md)
- Book authors: [`../template/book/README.md`](../template/book/README.md)
- Current status and approvals: [`../STATUS.md`](../STATUS.md)
