import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PACKAGE = Path(__file__).resolve().parents[1]


class ContestPackageLayoutTests(unittest.TestCase):
    def test_contest_problem_directory_is_the_single_source(self) -> None:
        self.assertTrue((PACKAGE / "problem.yaml").is_file())
        self.assertTrue((PACKAGE / "domjudge-problem.ini").is_file())
        self.assertTrue((PACKAGE / "problem_statement" / "problem.html").is_file())
        self.assertTrue((PACKAGE / "submissions" / "accepted" / "solution.py").is_file())

    def test_reference_and_counterexample_submissions_exist(self) -> None:
        submissions = PACKAGE / "submissions"
        self.assertTrue((submissions / "accepted" / "solution.c").is_file())
        self.assertTrue((submissions / "accepted" / "solution.cpp").is_file())
        self.assertTrue((submissions / "accepted" / "solution.py").is_file())
        self.assertTrue((submissions / "accepted" / "Main.java").is_file())
        self.assertTrue((submissions / "time_limit_exceeded" / "sort_every_issue.py").is_file())
        self.assertTrue((submissions / "time_limit_exceeded" / "SortEveryIssue.java").is_file())
        self.assertTrue((submissions / "wrong_answer" / "stale_by_name_only.py").is_file())
        self.assertTrue((submissions / "wrong_answer" / "no_tie_break.py").is_file())
        self.assertTrue((submissions / "wrong_answer" / "feat_overwrites.py").is_file())

    def test_statement_has_component_sections_and_paired_example(self) -> None:
        statement = (PACKAGE / "problem_statement" / "problem.html").read_text(encoding="utf-8")
        self.assertIn('class="problem-statement"', statement)
        self.assertIn('class="sample-card"', statement)
        self.assertIn("data-sample-input", statement)
        self.assertIn("data-sample-output", statement)

    def test_test_contest_reuses_the_same_source(self) -> None:
        pointer = ROOT / "problems" / "contests" / "TEST" / "C" / "source.txt"
        self.assertEqual(pointer.read_text(encoding="utf-8").strip(), "../KAUPC/G")


if __name__ == "__main__":
    unittest.main()
