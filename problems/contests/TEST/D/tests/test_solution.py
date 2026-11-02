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
        sample_in = (ROOT / "data" / "sample" / "1.in").read_text(encoding="utf-8")
        sample_ans = (ROOT / "data" / "sample" / "1.ans").read_text(encoding="utf-8")
        self.assertEqual(run(sample_in).split(), sample_ans.split())


if __name__ == "__main__":
    unittest.main()
