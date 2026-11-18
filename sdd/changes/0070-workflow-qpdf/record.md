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

The re-dispatched portal run (44355804489) then passed `make full` and failed while downloading the
live reading site with `solutions-architecture-handbook: remote asset returned HTTP 503 from
cesarcastrocuba.github.io`. `_download` now retries a transient status for the same pinned request:
429/500/502/503/504 from a non-API host and 429/5xx from the API host, up to three more attempts with
2/4/8 s backoff, or a numeric `Retry-After` capped at 30 s. Redirects keep their six-hop cap, other
4xx responses are not retried, and the destination is opened only on a 200, so no partial file is
written.

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
$ .venv/bin/python -m unittest discover -s tools/tests -p test_catalog_verification.py
Ran 27 tests in 0.397s
OK
```

The catalog-verification tests add: a 503 followed by a 200 writes the file after one 2 s sleep; a
numeric `Retry-After: 7` is honoured; four 503s fail with the same message after three sleeps and no
file; a 404 is requested once and not retried. The sleep is patched, so the tests stay fast.

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
44350746376  clean-clone   f76cb8c  failure  qpdf installed and verified; Ubuntu failed on the three
                                              numbering-parity git identity errors (fixed later)
44350752598  portal-pages  f76cb8c  failure  make full failed only on those three errors; qpdf errors gone
44355799123  clean-clone   5c2c312  failure  Ubuntu make check/full passed (571 tests OK, 3 Playwright
                                              skips); the "no test may be skipped" gate failed on those
                                              skips; macOS failed on the path tests below
44355804489  portal-pages  5c2c312  failure  make full passed; catalog verification failed on a transient
                                              HTTP 503 from cesarcastrocuba.github.io (retry added)
NEW_PORTAL
```

## Known gaps

- The macOS leg of `clean-clone` fails on pre-existing macOS path handling unrelated to system
  dependencies. `test_build.BuildTests.test_local_path_in_the_markdown_fails_the_build` fails in both
  `('plain')` and `('under_score')` with
  `AssertionError: BuildError not raised : a local path must fail the build: /var/folders/…`, and
  `test_figure_layout.FigureLayoutTests.test_stages_attributes_not_pixels_or_code_or_svg` errors with
  `ValueError: '/private/var/…/figure.png' is not in the subpath of '/var/folders/…'` because macOS
  resolves the temporary directory through `/private`. Those are out of scope for this change.
- The Ubuntu `clean-clone` leg now passes `make check` and `make full` but its "no test may be
  skipped" gate fails on three Playwright browser tests that skip by design
  (`Playwright is installed by the edition-preview job`). Installing Playwright in `clean-clone` is
  out of scope for this change.
- The workflows without Quarto (`ci.yml` `checks` and `quickstart`) install qpdf and poppler but not
  LibreOffice: build tests skip without Quarto, while LibreOffice alone would enable the
  soffice-only smoke test, which then needs Quarto.
- The macOS LibreOffice cask and `soffice` path are exercised only by the dispatched clean-clone run,
  not by local checks.
