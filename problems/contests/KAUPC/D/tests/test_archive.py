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
            samples = sorted((PACKAGE / "data" / "sample").glob("*.in"))
            self.assertTrue(samples)
            for sample in samples:
                self.assertIn(f"data/sample/{sample.name}", package.namelist())
                self.assertIn(f"data/sample/{sample.stem}.ans", package.namelist())
            self.assertFalse(any(chr(92) in name for name in package.namelist()))


if __name__ == "__main__":
    unittest.main()
