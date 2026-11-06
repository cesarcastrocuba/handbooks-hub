# Tasks — topic-neutral standard profile

**Status:** Proposed
**Change:** `0004-topic-neutral-profile`

| ID | Task | Write set | Status |
| --- | --- | --- | --- |
| T1 | Rename the architecture-specific checklist | `profiles/standard/profile.yaml` | Done |
| T2 | Make figures and tables optional | `profiles/standard/profile.yaml` | Done |
| T3 | Add optional/required minima consistency checks | `tools/src/handbook_toolkit/profiles.py` | Done |
| T4 | Add profile contract regressions | `tools/tests/test_profile.py` | Done |
| T5 | Update editorial contract and version references | `docs/`, `template/book/book.yaml` | Done |
| T6 | Update status and changelog | `STATUS.md`, `CHANGELOG.md` | Done |
| T7 | Run fast and full checks | None | Done |
| T8 | Commit and record exact HEAD | `.git/`, this record | Done after commit |
| T9 | Independent review | Review comments | Pending |
| T10 | Owner approval of profile `0.2.0` | Decision record | **Not requested by this change** |

## Verification mapping

| Criterion | Evidence |
| --- | --- |
| Profile schema valid | `test_repository_profile_is_valid`; `handbook-toolkit validate-profile` |
| Topic-neutral checklist | `test_standard_profile_is_topic_neutral_and_visuals_are_optional` |
| Optional figures/tables | same test; `make check` |
| Minima consistency | `test_required_*` and `test_optional_*` tests |
| Template pin | `template/book/book.yaml`; `validate-book` |
| Full checks | `make full` |
| No approval | `STATUS.md`; `profile.yaml status: proposed` |
