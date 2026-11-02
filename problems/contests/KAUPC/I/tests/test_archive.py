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
            self.assertIn("data/sample/1.in", package.namelist())
            self.assertIn("data/sample/1.ans", package.namelist())
            self.assertFalse(any("\\" in name for name in package.namelist()))


if __name__ == "__main__":
    unittest.main()
