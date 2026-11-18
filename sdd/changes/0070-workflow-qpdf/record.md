# Change 0070 — qpdf in every workflow that runs the toolkit tests

Implementer OpenCode 2; reviewer and merger Claude. Branch `fix/0070-workflow-qpdf` from main
`b58e76d`. No version bump or tag: the workflows run from hub main.

## Defect

Change `0062` made qpdf 11 or later mandatory for a release build and installed it only in
`ci.yml` (publication and edition-preview jobs) and the template workflows. `portal-pages.yml` runs
`make full` before it builds the portal with only `poppler-utils`; the deployment after the catalog
merge (PR 111, run 44345418383) failed:

```text
BuildError: qpdf 11 or later is required to compact a release PDF; install qpdf or run an explicit preview build
FAILED (failures=2, errors=17, skipped=8)
```

`catalog-update.yml` runs the same `make full` with only `poppler-utils` and would fail the same way.
`clean-clone.yml` runs `make check` and `make full` on Ubuntu and macOS with only `poppler`; its
scheduled run 43901145283 already failed because three `test_numbering_parity` fixtures ran a plain
`git commit` without a git identity on a clean runner. That test bug is fixed here as well; the
remaining macOS-only failures are recorded under Known gaps.

## Fix

Every workflow that runs `make check`/`make full`, `build-book` or the real build tests now installs
qpdf 11 and verifies its version. Jobs that run the build tests also install LibreOffice.

| Workflow | Job | Change |
| --- | --- | --- |
| `ci.yml` | `checks` | Installs `poppler-utils qpdf` and verifies the qpdf version before `make check`/`make full`. LibreOffice is not installed here: this job has no Quarto, so build tests skip; LibreOffice alone would enable the soffice-only smoke test, which then needs Quarto. |
| `ci.yml` | `quickstart` | Same as `checks`; it runs the documented commands in a fresh venv. |
| `ci.yml` | `publication-build` | Already installed `poppler-utils qpdf libreoffice-writer`; gains the missing `Verify the qpdf version` step. |
| `ci.yml` | `edition-preview` | Already installed the three and verified qpdf; unchanged. |
| `ci.yml` | `template-install` | Validates a copied template and installs the pinned toolkit; no book build; unchanged. |
| `ci.yml` | `wheel-install` | Builds and imports the wheel; no book build; unchanged. |
| `catalog-update.yml` | `prepare` | Installs `poppler-utils qpdf libreoffice-writer` and verifies qpdf before `make full`. |
| `catalog-update.yml` | `publish` | Runs no repository code; unchanged. |
| `portal-pages.yml` | `build` | Installs `poppler-utils qpdf libreoffice-writer` and verifies qpdf before `make full`. |
| `portal-pages.yml` | `deploy`, `verify` | Page deployment and site check only; unchanged. |
| `clean-clone.yml` | `clean-clone` (Linux) | Installs `poppler-utils qpdf libreoffice-writer` and verifies qpdf. |
| `clean-clone.yml` | `clean-clone` (macOS) | `brew install poppler qpdf`, `brew install --cask libreoffice`, adds the LibreOffice `soffice` directory to `GITHUB_PATH`, and verifies qpdf. The no-skip gate needs LibreOffice: the real build tests do not skip without it, they fail. |

Permissions, triggers, concurrency and pinned action SHAs are unchanged.

The first dispatched `portal-pages` run (44350752598) showed the qpdf errors were gone but the build
still failed on an unrelated test bug: three `test_numbering_parity` tests run a plain `git commit`
in their fixture, and a clean runner has no git identity (`exit status 128`). They now pass
`-c user.name=Fixture -c user.email=fixture@example.invalid` exactly as
`tools/tests/test_edition_preview.py` already does.

## Tests

`tools/tests/test_workflow_system_dependencies.py` loads every workflow, finds each job whose steps
run `make check`/`make full`, `build-book`, `edition_preview.py` or `test_build.py`, and asserts that
job installs qpdf (`apt-get` or `brew`) and runs the `qpdf --version … -ge 11` check. It also pins the
expected job set and asserts that no workflow installs qpdf without the version check.

```text
$ .venv/bin/python -m unittest discover -s tools/tests -p test_workflow_system_dependencies.py -v
Ran 3 tests in 0.078s
OK
$ .venv/bin/python -m unittest discover -s tools/tests -p test_portal_pages_workflow.py -v
Ran 8 tests in 0.047s
OK
$ .venv/bin/python -m unittest discover -s tools/tests -p test_workflow_pins.py -v
Ran 3 tests in 0.003s
OK
$ EMPTY_HOME=$(mktemp -d) HOME=$EMPTY_HOME GIT_CONFIG_NOSYSTEM=1 \
    .venv/bin/python -m unittest discover -s tools/tests -p test_numbering_parity.py -v
Ran 16 tests in 41.587s
OK
```

The last command runs with an empty `HOME` and no system git config, which reproduces the clean
runner without a global identity.

## Evidence

```text
$ make full PYTHON=.venv/bin/python
Ran 571 tests in 632.694s

OK (skipped=3)
...
VERIFY (full): 7 check(s), 0 problem(s)
```

Dispatched runs on the branch (no deploy):

```text
DISPATCHES
```

## Known gaps

- The macOS leg of `clean-clone` fails on pre-existing macOS path handling unrelated to system
  dependencies. `test_build.BuildTests.test_local_path_in_the_markdown_fails_the_build` fails in both
  `('plain')` and `('under_score')` with
  `AssertionError: BuildError not raised : a local path must fail the build: /var/folders/…`, and
  `test_figure_layout.FigureLayoutTests.test_stages_attributes_not_pixels_or_code_or_svg` errors with
  `ValueError: '/private/var/…/figure.png' is not in the subpath of '/var/folders/…'` because macOS
  resolves the temporary directory through `/private`. Those are out of scope for this change.
- The workflows without Quarto (`ci.yml` `checks` and `quickstart`) install qpdf and poppler but not
  LibreOffice: build tests skip without Quarto, while LibreOffice alone would enable the
  soffice-only smoke test, which then needs Quarto.
- The macOS LibreOffice cask and `soffice` path are exercised only by the dispatched clean-clone run,
  not by local checks.
