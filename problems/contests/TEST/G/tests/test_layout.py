import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PACKAGE = ROOT / "problems" / "contests" / "TEST" / "G"


class ContestPackageLayoutTests(unittest.TestCase):
    def test_contest_problem_directory_is_the_single_source(self) -> None:
        self.assertTrue((PACKAGE / "problem.yaml").is_file())
        self.assertTrue((PACKAGE / "domjudge-problem.ini").is_file())
        self.assertTrue((PACKAGE / "problem_statement" / "problem.html").is_file())
        self.assertTrue((PACKAGE / "generators" / "gen.py").is_file())

    def test_statement_has_component_sections_and_paired_example(self) -> None:
        statement = (PACKAGE / "problem_statement" / "problem.html").read_text(encoding="utf-8")
        self.assertIn('class="problem-statement"', statement)
        self.assertIn('class="sample-card"', statement)
        self.assertIn("data-sample-input", statement)
        self.assertIn("data-sample-output", statement)

    def test_statement_has_no_template_placeholder(self) -> None:
        statement = (PACKAGE / "problem_statement" / "problem.html").read_text(encoding="utf-8")
        self.assertNotIn("__", statement)

    def test_every_input_has_an_answer(self) -> None:
        inputs = sorted((PACKAGE / "data").rglob("*.in"))
        self.assertTrue(inputs, "테스트 입력이 하나도 없다")
        for path in inputs:
            self.assertTrue(path.with_suffix(".ans").is_file(), f"{path.name}에 짝이 되는 .ans가 없다")


if __name__ == "__main__":
    unittest.main()
