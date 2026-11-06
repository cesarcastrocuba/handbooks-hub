# Installed, versioned profiles

`handbook_toolkit.profile_resources.load_profile(id, version)` resolves an exact
approved profile from the installed toolkit. It does not access a parent checkout,
fetch the network, silently upgrade a version, or substitute a different profile.
An unavailable version fails with an actionable installation error.

The Hub's `profiles/standard/profile.yaml` is the maintained definition. The
package carries its approved, versioned distribution snapshot under
`profile_data/standard-1.0.0.yaml`; the approved `standard-0.2.0.yaml` snapshot remains in the package
for books that pin the previous version. Books do not copy either file. CI compares each current
snapshot byte-for-byte with the approved definition so the two cannot drift.
An intentional new profile version must add its own snapshot and update the
version-specific tests rather than silently replacing an adopted profile.

The package-data declaration includes YAML snapshots in source/wheel builds.
Resource loading works from a normal install or a ZIP package, independently of
the working directory. The profile schema and exact id/version/approved status
are checked on load. Prose quality and factual accuracy remain review concerns.

This unit supplies the distribution API. `build-book` uses it when no explicit profile override is
requested. `validate-manuscript` still requires an explicit profile path.

Verification: `python3 -m unittest discover -s tools/tests -p test_profile_resources.py`.
Rollback removes the snapshot, loader, tests, guide and package-data entry; existing
explicit-profile validation is unchanged.
