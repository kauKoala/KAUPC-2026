import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StatementMarkupTests(unittest.TestCase):
    def test_contest_statements_do_not_use_italic_variable_markup(self) -> None:
        statements = sorted((ROOT / "problems" / "contests").glob("*/*/problem_statement/problem.html"))
        self.assertTrue(statements)
        offenders = [path.relative_to(ROOT) for path in statements if "<var>" in path.read_text(encoding="utf-8")]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
