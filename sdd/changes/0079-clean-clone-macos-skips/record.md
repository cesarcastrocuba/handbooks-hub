# Change 0079 — clean-clone: symlinked temporary paths and Playwright

Fixes hub issue 113. Implementer Claude; reviewer and merger a different agent. Branch
`fix/clean-clone-macos-skips` from main `57e7350`. No version bump or tag: the toolkit fix ships with
the next toolkit release, which needs its own Owner approval.

## Defect

The scheduled `clean-clone` workflow has failed since 2026-11-16 (run 43901145283). Change `0070`
fixed the system dependencies and the git identity of the fixtures. Two causes remained.

1. **macOS (`macos-15`).** The temporary directory `/var/folders/…` is a symlink to
   `/private/var/folders/…`. Two toolkit functions mixed the given and the resolved spelling:
   - `build_book` resolved the repository and output paths and gave only the resolved spellings to
     `_reject_local_paths`. A manuscript that contained the given spelling of its own repository
     path passed the leak check. `test_local_path_in_the_markdown_fails_the_build` caught this on
     macOS (`BuildError not raised`). This was a real gap in the leak check, not only a test
     problem.
   - `stage_figures` resolved each raster path but recorded it relative to the unresolved
     workspace, so `relative_to` raised `ValueError` for a workspace reached through a symlink
     (`test_stages_attributes_not_pixels_or_code_or_svg`). A real build always passes a resolved
     workspace, so release builds were not affected.
2. **Ubuntu (`ubuntu-24.04`).** `make check` and `make full` passed, but the gate "Hub: no test may
   be skipped" failed on the Playwright browser tests, which skip when Playwright is not installed.

## Fix

| File | Change |
| --- | --- |
| `tools/src/handbook_toolkit/build.py` | Keeps the given (absolute, unresolved) spelling of the repository, the output and its staging directory, and the resolved home directory, and passes them to `_reject_local_paths` with the resolved ones. |
| `tools/src/handbook_toolkit/figure_layout.py` | Records a staged raster path relative to the resolved workspace, the same base the escape check already used. |
| `.github/workflows/clean-clone.yml` | New step "Hub: install the screenshot browser": installs `tools/scripts/requirements-edition-preview.txt` (Playwright `1.60.0`) and Chromium (`--with-deps` on Linux), so the browser tests run and the no-skip gate stays strict. Allow-listing the skips was rejected: it would weaken the gate. |
| `docs/clean-clone.md` | Step 3 names the Playwright install. |

## Tests

- `test_figure_layout.test_workspace_reached_through_a_symlink_is_staged`: stages a figure through a
  symlinked workspace.
- `test_build.test_local_path_in_the_markdown_fails_the_build` gains a `symlinked` case: the book
  directory is reached through a symlink, as on macOS, and the given spelling must fail the build.

Both reproduce the macOS failures on Linux: without the fix they fail with
`ValueError: '…/real/figure.png' is not in the subpath of '…/link'` and
`BuildError not raised … (directory='symlinked')`; with the fix they pass.

## Verification evidence

The pull request records the commands and results on its exact HEAD. The `clean-clone` workflow runs
on the pull request because it changes `.github/workflows/clean-clone.yml`; both legs are the proof
for issue 113.

Rollback boundary: revert this commit.
