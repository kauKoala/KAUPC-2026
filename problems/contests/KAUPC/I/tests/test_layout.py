import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PACKAGE = Path(__file__).resolve().parents[1]


class ContestPackageLayoutTests(unittest.TestCase):
    def test_contest_problem_directory_is_the_single_source(self) -> None:
        self.assertTrue((PACKAGE / "problem.yaml").is_file())
        self.assertTrue((PACKAGE / "problem_statement" / "problem.html").is_file())
        self.assertFalse((ROOT / "problems" / "addingbridges").exists())

    def test_time_limit_allows_per_query_dijkstra_in_every_language(self) -> None:
        # 서버 실측: 자바 다익스트라 1.96~4.26초, 파이썬(PyPy) 1.58초. 1.5배 여유를 두고 5초.
        config = (PACKAGE / "domjudge-problem.ini").read_text(encoding="utf-8")
        self.assertIn("timelimit = 5", config)
        self.assertIn("time_limit: 5", (PACKAGE / "problem.yaml").read_text(encoding="utf-8"))
        statement = (PACKAGE / "problem_statement" / "problem.html").read_text(encoding="utf-8")
        self.assertIn("<dt>시간 제한</dt><dd>5초</dd>", statement)
        self.assertIn("1 ≤ N ≤ 300", statement)
        self.assertIn("0 ≤ M ≤ 50,000", statement)
        self.assertIn("M &lt; N<sup>2</sup>", statement)
        self.assertIn("1 ≤ Q ≤ 1,000", statement)

    def test_reference_solutions_cover_all_judged_languages(self) -> None:
        accepted = PACKAGE / "submissions" / "accepted"
        self.assertTrue((accepted / "solution.c").is_file())
        self.assertTrue((accepted / "solution.cpp").is_file())
        self.assertTrue((accepted / "Main.java").is_file())
        self.assertEqual(sorted({path.suffix for path in accepted.iterdir()}), [".c", ".cpp", ".java", ".py"])
        # 쿼리마다 다익스트라를 도는 풀이도 정답으로 통과해야 한다.
        for name in ("dijkstra_per_query.cpp", "DijkstraPerQuery.java", "dijkstra_python.py", "dijkstra_heap_python.py"):
            self.assertTrue((accepted / name).is_file(), name)

    def test_slow_and_wrong_submissions_exist(self) -> None:
        slow = PACKAGE / "submissions" / "time_limit_exceeded"
        wrong = PACKAGE / "submissions" / "wrong_answer"
        self.assertTrue((slow / "floyd_every_query.cpp").is_file())
        self.assertTrue(any(wrong.iterdir()))

    def test_statement_has_component_sections_and_paired_example(self) -> None:
        statement = (PACKAGE / "problem_statement" / "problem.html").read_text(encoding="utf-8")
        self.assertIn('class="problem-statement"', statement)
        self.assertIn('class="sample-card"', statement)
        self.assertIn('data-sample-input', statement)
        self.assertIn('data-sample-output', statement)


if __name__ == "__main__":
    unittest.main()
