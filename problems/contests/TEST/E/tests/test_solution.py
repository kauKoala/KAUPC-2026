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
        self.assertEqual(run(sample_in), sample_ans)

    def test_prints_one_to_n_stars_per_line(self):
        self.assertEqual(run("3\n"), "*\n**\n***\n")

    def test_single_line(self):
        self.assertEqual(run("1\n"), "*\n")

    def test_largest_input_has_n_lines(self):
        lines = run("100\n").splitlines()
        self.assertEqual(len(lines), 100)
        self.assertEqual(lines[-1], "*" * 100)


if __name__ == "__main__":
    unittest.main()
