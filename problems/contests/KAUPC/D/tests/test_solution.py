import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOLUTION = ROOT / "submissions" / "accepted" / "solution.py"


def run(problem_input: str) -> str:
    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        input=problem_input,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


class ReferenceSolutionTest(unittest.TestCase):
    def test_sample(self):
        samples = sorted((ROOT / "data" / "sample").glob("*.in"))
        self.assertTrue(samples)
        for sample in samples:
            with self.subTest(sample=sample.name):
                self.assertEqual(run(sample.read_text(encoding="utf-8")).split(), sample.with_suffix(".ans").read_text(encoding="utf-8").split())


if __name__ == "__main__":
    unittest.main()
