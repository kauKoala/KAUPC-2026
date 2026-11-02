"""Regression tests for the bounded problem-editor generation and checks."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EDITOR_PATH = ROOT / "tools" / "problem-editor" / "app.py"


def load_editor_module():
    spec = importlib.util.spec_from_file_location("problem_editor_under_test", EDITOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDITOR = load_editor_module()


class ProblemEditorTests(unittest.TestCase):
    def test_authoring_header_does_not_expose_repository_controls(self):
        source = EDITOR_PATH.read_text(encoding="utf-8")

        self.assertNotIn("원격과 맞추기", source)
        self.assertNotIn("barright=bar_right", source)

    def make_package(self, root: Path) -> Path:
        package = root / "contest" / "A"
        (package / "data" / "sample").mkdir(parents=True)
        (package / "data" / "secret").mkdir()
        (package / "submissions" / "accepted").mkdir(parents=True)
        (package / "submissions" / "wrong_answer").mkdir()
        (package / "submissions" / "time_limit_exceeded").mkdir()
        (package / "problem.yaml").write_text("name: Test\ntime_limit: 1\nmemory: 512\n", encoding="utf-8")
        (package / "submissions" / "accepted" / "solution.py").write_text(
            "import sys\nprint(int(sys.stdin.read()) * 2)\n", encoding="utf-8"
        )
        return package

    def test_integer_generation_writes_secret_cases_and_returns_visible_seed_records(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            # The bounded generator has no example-data mode: every seed is judging data.
            generator = getattr(EDITOR, "generate_integer_cases", None)
            self.assertIsNotNone(generator, "bounded integer generation is not available")
            result = generator(package, minimum=10, maximum=20, seeds=["11", "29"])

            records = result["cases"]
            self.assertEqual([record["seed"] for record in records], ["11", "29"])
            self.assertEqual(len(records), 2)
            for index, record in enumerate(records, start=1):
                self.assertEqual(record["input"], (package / "data" / "secret" / f"{index}.in").read_text(encoding="utf-8"))
                self.assertEqual(record["answer"], (package / "data" / "secret" / f"{index}.ans").read_text(encoding="utf-8"))
                self.assertNotEqual(record["input"], record["answer"], "MAIN 정답 코드의 출력이 정답 파일이어야 한다")
            self.assertEqual(list((package / "data" / "sample").glob("*")), [])

    def test_generated_case_log_keeps_only_seed_and_name(self):
        # 입력과 정답은 data/에 이미 있다. 기록에 또 넣으면 저장소가 수십 MB씩 불어난다.
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            EDITOR.generate_integer_cases(package, minimum=10, maximum=20, seeds=["11", "29"])

            saved = json.loads((package / "generators" / "generated-cases.json").read_text(encoding="utf-8"))

            self.assertEqual(saved, [{"seed": "11", "name": "1"}, {"seed": "29", "name": "2"}])
            self.assertEqual([record["seed"] for record in EDITOR.generated_cases(package)], ["11", "29"])

    def test_replacing_generated_case_log_drops_stored_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            EDITOR.replace_generated_case_records(package, [{"seed": "5", "name": "3", "input": "x" * 1000, "answer": "y"}])

            saved = json.loads((package / "generators" / "generated-cases.json").read_text(encoding="utf-8"))

            self.assertEqual(saved, [{"seed": "5", "name": "3"}])

    def test_integer_generation_does_not_write_partial_cases_when_a_seed_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))

            with self.assertRaises(ValueError):
                EDITOR.generate_integer_cases(package, minimum=10, maximum=20, seeds=["11", "bad"])

            self.assertEqual(list((package / "data" / "secret").glob("*")), [])
            self.assertFalse((package / "generators" / "generated-cases.json").exists())

    def test_verification_rows_include_explicit_serial_execution_order(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            for name in ("b.py", "a.py"):
                (package / "submissions" / "accepted" / name).write_text("print()\n", encoding="utf-8")
            (package / "submissions" / "wrong_answer" / "wrong.py").write_text("print()\n", encoding="utf-8")
            (package / "data" / "secret" / "1.in").write_text("input\n", encoding="utf-8")
            (package / "data" / "secret" / "1.ans").write_text("answer\n", encoding="utf-8")

            calls = []
            original_verify_one = EDITOR.verify_one
            try:
                def verify_one(path, tests, time_limit):
                    calls.append(path.name)
                    return {"verdict": "AC", "detail": "ok", "slowest": 0.01}

                EDITOR.verify_one = verify_one
                result = EDITOR.verify_package(package)
            finally:
                EDITOR.verify_one = original_verify_one

            self.assertEqual(calls, ["a.py", "b.py", "solution.py", "wrong.py"])
            self.assertTrue(
                all("order" in row for row in result["rows"]),
                "verification rows must expose their serial execution order",
            )
            self.assertEqual([row["order"] for row in result["rows"]], list(range(1, len(calls) + 1)))
            self.assertEqual([row["file"] for row in result["rows"]], calls)

    def test_preview_document_embeds_statement_without_a_second_authenticated_request(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            (package / "problem_statement").mkdir()
            (package / "problem_statement" / "problem.html").write_text(
                "<article><h1>미리보기 확인</h1></article>", encoding="utf-8"
            )

            preview = getattr(EDITOR, "preview_document", None)
            self.assertIsNotNone(preview, "same-page preview document is not available")
            document = preview(package)

            self.assertIn("미리보기 확인", document)
            self.assertIn(EDITOR.PREVIEW_STYLE, document)



class CommitSizeGuardTests(unittest.TestCase):
    # GitHub은 100MB가 넘는 파일을 거부한다. 한 번 커밋되면 이후 푸시가 전부 막혀서 미리 막는다.
    def test_oversized_files_lists_only_files_over_the_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "big.in").write_bytes(b"x" * 2048)
            (root / "data" / "small.in").write_bytes(b"x" * 10)
            original = EDITOR.MAX_COMMIT_BYTES
            EDITOR.MAX_COMMIT_BYTES = 1024
            try:
                found = EDITOR.oversized_files([root])
            finally:
                EDITOR.MAX_COMMIT_BYTES = original
            self.assertEqual([path.name for path, _ in found], ["big.in"])

    def test_git_save_refuses_oversized_files_before_committing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "big.in").write_bytes(b"x" * 2048)
            original_limit, original_git = EDITOR.MAX_COMMIT_BYTES, EDITOR.git
            calls = []
            EDITOR.MAX_COMMIT_BYTES = 1024
            EDITOR.git = lambda *args, **kwargs: calls.append(args) or (0, "")
            try:
                with self.assertRaises(ValueError) as caught:
                    EDITOR.git_save([root], "test")
            finally:
                EDITOR.MAX_COMMIT_BYTES, EDITOR.git = original_limit, original_git
            self.assertIn("big.in", str(caught.exception))
            self.assertEqual(calls, [])


class SubmissionDeleteTests(unittest.TestCase):
    def make_package(self, root: Path) -> Path:
        return ProblemEditorTests.make_package(self, root)

    def test_delete_removes_only_the_named_file(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            wrong = package / "submissions" / "time_limit_exceeded" / "solution.cpp"
            wrong.write_text("int main(){}\n", encoding="utf-8")

            removed = EDITOR.delete_submission(package, "time_limit_exceeded", "solution.cpp")

            self.assertEqual(removed, wrong)
            self.assertFalse(wrong.exists())
            self.assertTrue((package / "submissions" / "accepted" / "solution.py").is_file())

    def test_delete_rejects_unknown_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            with self.assertRaises(ValueError):
                EDITOR.delete_submission(package, "data", "solution.py")

    def test_delete_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            (package / "problem.yaml").touch()
            with self.assertRaises(ValueError):
                EDITOR.delete_submission(package, "accepted", "../../problem.yaml")
            self.assertTrue((package / "problem.yaml").is_file())

    def test_delete_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            with self.assertRaises(ValueError):
                EDITOR.delete_submission(package, "wrong_answer", "nope.py")

    def test_main_falls_back_after_deleting_the_chosen_main(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            (package / "submissions" / "accepted" / "fast.cpp").write_text("int main(){}\n", encoding="utf-8")
            (package / "generators").mkdir()
            (package / "generators" / "main.txt").write_text("fast.cpp\n", encoding="utf-8")

            EDITOR.delete_submission(package, "accepted", "fast.cpp")

            self.assertEqual(EDITOR.main_solution_name(package), "solution.py")

    def test_code_rows_have_a_delete_button_wired_to_the_route(self):
        source = EDITOR_PATH.read_text(encoding="utf-8")
        self.assertIn('"/submission-delete": self.post_submission_delete', source)
        self.assertIn("link('/submission-delete')", source)
        self.assertIn('"/submission-delete": "code"', source)


class DataPanelLayoutTests(unittest.TestCase):
    def test_editor_has_no_collapsed_sections_and_a_sample_toggle(self):
        source = (ROOT / "tools/problem-editor/app.py").read_text(encoding="utf-8")
        self.assertNotIn("<details", source)
        self.assertIn('"/testcase-sample": self.post_testcase_sample', source)
        self.assertNotIn("id='manual'", source)


    def test_rename_updates_every_file_that_holds_the_problem_name(self):
        with tempfile.TemporaryDirectory() as directory:
            contests = Path(directory)
            package = contests / "MAIN" / "A"
            package.mkdir(parents=True)
            (package / "problem.yaml").write_text(
                "name: 옛 이름\nlimits:\n  time_limit: 2\n  memory: 512\n", encoding="utf-8"
            )
            (package / "domjudge-problem.ini").write_text(
                "name = 옛 이름\nshort-name = sample\nexternalid = sample\ntimelimit = 2\n", encoding="utf-8"
            )
            entry = "- id: other\n  label: B\n  name: 다른 문제\n- id: sample\n  label: A\n  name: 옛 이름\n  color: Red\n"
            (contests / "MAIN" / "problems.yaml").write_text(entry, encoding="utf-8")
            (contests / "REUSE").mkdir()
            (contests / "REUSE" / "problems.yaml").write_text(
                "- id: sample\n  label: C\n  name: 옛 이름\n", encoding="utf-8"
            )
            original = EDITOR.CONTESTS
            EDITOR.CONTESTS = contests
            try:
                changed = EDITOR.rename_problem(package, "  새 이름: (개정)  ")
            finally:
                EDITOR.CONTESTS = original

            self.assertEqual(EDITOR.problem_meta(package)["name"], "새 이름: (개정)")
            self.assertEqual(EDITOR.problem_meta(package)["time_limit"], 2.0)
            self.assertIn('name = "새 이름: (개정)"', (package / "domjudge-problem.ini").read_text(encoding="utf-8"))
            main = (contests / "MAIN" / "problems.yaml").read_text(encoding="utf-8")
            self.assertIn("  name: 다른 문제\n", main)
            self.assertIn('  name: "새 이름: (개정)"\n  color: Red', main)
            self.assertIn('name: "새 이름: (개정)"', (contests / "REUSE" / "problems.yaml").read_text(encoding="utf-8"))
            self.assertEqual(len(changed), 4)

    def test_rename_rejects_empty_name_and_keeps_plain_names_unquoted(self):
        with self.assertRaises(ValueError):
            EDITOR.clean_problem_name("   ")
        self.assertEqual(EDITOR.yaml_scalar("트리플(Triple)"), "트리플(Triple)")

    def test_statement_form_has_an_editable_name_field(self):
        source = EDITOR_PATH.read_text(encoding="utf-8")
        self.assertIn("id='s-name' name='name'", source)

if __name__ == "__main__":
    unittest.main()
