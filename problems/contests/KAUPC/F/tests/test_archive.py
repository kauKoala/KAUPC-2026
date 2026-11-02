import subprocess
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BUILD = ROOT / "scripts" / "build-problem.py"
PACKAGE = Path(__file__).resolve().parents[1]
ARCHIVE = PACKAGE / "build" / "problem.zip"


class ProblemArchiveTest(unittest.TestCase):
    def test_archive_uses_domjudge_forward_slash_testcase_paths(self):
        subprocess.run([sys.executable, str(BUILD), "KAUPC", PACKAGE.name], check=True)
        with zipfile.ZipFile(ARCHIVE) as package:
            names = package.namelist()
            samples = [name for name in names if name.startswith("data/sample/") and name.endswith(".in")]
            self.assertTrue(samples)
            for name in samples:
                self.assertIn(name[:-3] + ".ans", names)
            self.assertFalse(any(chr(92) in name for name in package.namelist()))


if __name__ == "__main__":
    unittest.main()
