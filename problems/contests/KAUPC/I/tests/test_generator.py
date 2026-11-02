import subprocess
import sys
import tempfile
import unittest
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generators" / "generate_tests.py"
STATEMENT = ROOT / "problem_statement" / "problem.html"


def assert_well_formed_case(test: unittest.TestCase, text: str, case: str) -> None:
    lines = [line.split() for line in text.splitlines() if line.strip()]
    test.assertTrue(lines, case)
    test.assertEqual(len(lines[0]), 3, case)
    n, m, q = map(int, lines[0])
    test.assertTrue(1 <= n <= 300, case)
    test.assertTrue(0 <= m <= 50_000 and m < n * n, case)
    test.assertTrue(1 <= q <= 1_000, case)
    test.assertEqual(len(lines), 1 + m + q, case)
    for edge in lines[1 : 1 + m]:
        test.assertEqual(len(edge), 3, case)
        a, b, weight = map(int, edge)
        test.assertTrue(1 <= a <= n and 1 <= b <= n and 1 <= weight <= 100_000, case)
    for query in lines[1 + m :]:
        test.assertIn(query[0], ("1", "2"), case)
        test.assertEqual(len(query), 4 if query[0] == "1" else 3, case)
        values = list(map(int, query[1:]))
        test.assertTrue(all(1 <= vertex <= n for vertex in values[:2]), case)
        if query[0] == "1":
            test.assertTrue(1 <= values[2] <= 100_000, case)


class GeneratorTest(unittest.TestCase):
    def test_committed_cases_match_the_declared_input_shape(self):
        for input_file in sorted((ROOT / "data").rglob("*.in")):
            with self.subTest(case=input_file.relative_to(ROOT / "data")):
                assert_well_formed_case(self, input_file.read_text(encoding="utf-8"), str(input_file))

    def test_all_generated_cases_limit_queries_to_one_thousand(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            subprocess.run(
                [sys.executable, str(GENERATOR), "--output", str(output_dir)],
                check=True,
                text=True,
                capture_output=True,
            )
            for input_file in output_dir.rglob("*.in"):
                with self.subTest(case=input_file.name):
                    assert_well_formed_case(self, input_file.read_text(encoding="utf-8"), str(input_file))

    def test_statement_example_matches_the_committed_sample(self):
        statement = STATEMENT.read_text(encoding="utf-8")
        sample_input = re.search(r'<pre data-sample-input>(.*?)</pre>', statement, re.DOTALL)
        sample_output = re.search(r'<pre data-sample-output>(.*?)</pre>', statement, re.DOTALL)
        self.assertIsNotNone(sample_input)
        self.assertIsNotNone(sample_output)
        self.assertEqual(sample_input.group(1).strip(), (ROOT / "data/sample/1.in").read_text(encoding="utf-8").strip())
        self.assertEqual(sample_output.group(1).strip(), (ROOT / "data/sample/1.ans").read_text(encoding="utf-8").strip())

    def test_statement_does_not_limit_update_queries(self):
        self.assertNotIn("500개 이하", STATEMENT.read_text(encoding="utf-8"))

    def test_some_case_has_more_than_five_hundred_update_queries(self):
        def update_count(path: Path) -> int:
            lines = path.read_text(encoding="utf-8").splitlines()
            m = int(lines[0].split()[1])
            return sum(line.split()[0] == "1" for line in lines[1 + m :] if line.strip())

        self.assertGreater(max(update_count(path) for path in (ROOT / "data").rglob("*.in")), 500)

    def test_generates_input_and_matching_answer_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            subprocess.run(
                [sys.executable, str(GENERATOR), "--output", str(output_dir)],
                check=True,
                text=True,
                capture_output=True,
            )
            input_file = output_dir / "secret" / "max-dense.in"
            answer_file = output_dir / "secret" / "max-dense.ans"
            self.assertTrue(input_file.is_file())
            self.assertTrue(answer_file.read_text(encoding="utf-8").strip())


if __name__ == "__main__":
    unittest.main()
