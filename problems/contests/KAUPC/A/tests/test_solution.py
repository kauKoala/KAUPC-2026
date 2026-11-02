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
    def test_sample_uses_dots_for_empty_cells(self):
        sample_in = "0 1 0 -1 0\n"
        expected = "..AA......\nKKAAUU..CC\nKKAAUUPPCC\nKK..UUPPCC\n......PP..\n"
        self.assertEqual(run(sample_in), expected)

    def test_all_committed_outputs_have_five_ten_character_rows(self):
        cases = sorted((ROOT / "data").rglob("*.in"))
        self.assertEqual(len(cases), 42)
        for input_path in cases:
            expected = input_path.with_suffix(".ans").read_text(encoding="utf-8")
            self.assertEqual(run(input_path.read_text(encoding="utf-8")), expected)
            rows = expected.splitlines()
            self.assertEqual(len(rows), 5, input_path.name)
            self.assertTrue(all(len(row) == 10 for row in rows), input_path.name)
            self.assertLessEqual(set("".join(rows)), set(".KAUPC"))


if __name__ == "__main__":
    unittest.main()
