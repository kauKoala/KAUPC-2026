import subprocess
import sys
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BUILD = ROOT / "scripts" / "build-problem.py"
PACKAGE = ROOT / "problems" / "contests" / "KAUPC" / "A"
ARCHIVE = PACKAGE / "build" / "problem.zip"


class ProblemArchiveTest(unittest.TestCase):
    def test_archive_uses_domjudge_forward_slash_testcase_paths(self):
        subprocess.run([sys.executable, str(BUILD), "KAUPC", "A"], check=True)
        with zipfile.ZipFile(ARCHIVE) as package:
            self.assertIn("data/sample/1.in", package.namelist())
            self.assertIn("data/sample/1.ans", package.namelist())
            self.assertFalse(any(chr(92) in name for name in package.namelist()))

    def test_archive_contains_custom_output_validator(self):
        subprocess.run([sys.executable, str(BUILD), "KAUPC", "A"], check=True)
        with zipfile.ZipFile(ARCHIVE) as package:
            self.assertIn("output_validators/exact_output/run", package.namelist())

    def test_archive_marks_custom_validator_as_executable(self):
        subprocess.run([sys.executable, str(BUILD), "KAUPC", "A"], check=True)
        with zipfile.ZipFile(ARCHIVE) as package:
            mode = package.getinfo("output_validators/exact_output/run").external_attr >> 16
            self.assertNotEqual(mode & 0o111, 0)


if __name__ == "__main__":
    unittest.main()
