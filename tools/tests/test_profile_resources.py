"""Exact installed profile identity, distribution and drift regressions."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

import support
from handbook_toolkit.profile_resources import load_profile
from handbook_toolkit.validation import DocumentError


class ProfileResourceTests(unittest.TestCase):
    def test_exact_profile_is_approved_and_freshly_loaded(self):
        profile = load_profile("standard", "0.2.0")
        self.assertEqual(profile["status"], "approved")
        profile["title"] = "local mutation"
        self.assertNotEqual(load_profile("standard", "0.2.0")["title"], "local mutation")

    def test_packaged_snapshot_matches_canonical_approved_profile(self):
        source = support.REPO_ROOT / "profiles/standard/profile.yaml"
        packaged = support.SRC / "handbook_toolkit/profile_data/standard-0.2.0.yaml"
        self.assertEqual(source.read_bytes(), packaged.read_bytes())
        self.assertEqual(load_profile("standard", "0.2.0"), support.profile_document())

    def test_missing_version_ranges_and_traversal_fail_without_fallback(self):
        for identity, version in (("standard", "9.9.9"), ("standard", ">=0.2.0"),
                                  ("../standard", "0.2.0"), ("standard", "../../profile")):
            with self.subTest(identity=identity, version=version):
                with self.assertRaises(DocumentError):
                    load_profile(identity, version)

    def test_profile_loads_from_zip_package_outside_hub(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "toolkit.zip"
            package = support.SRC / "handbook_toolkit"
            with ZipFile(archive, "w") as bundle:
                for path in sorted(package.rglob("*")):
                    if path.is_file() and path.suffix in {".py", ".json", ".yaml"}:
                        bundle.write(path, path.relative_to(support.SRC).as_posix())
            environment = dict(os.environ, PYTHONPATH=str(archive))
            output = subprocess.check_output([
                sys.executable, "-c",
                "import handbook_toolkit; from handbook_toolkit.profile_resources import load_profile; "
                "assert '.zip/' in handbook_toolkit.__file__; "
                "p=load_profile('standard','0.2.0'); print(p['id'],p['version'],p['status'])",
            ], cwd=root, env=environment, text=True, timeout=30)
            self.assertEqual(output.strip(), "standard 0.2.0 approved")


if __name__ == "__main__":
    unittest.main()
