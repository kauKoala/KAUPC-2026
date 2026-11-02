import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generators" / "generate_tests.py"


class GeneratorTest(unittest.TestCase):
    def test_generates_input_and_matching_answer_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            subprocess.run(
                [sys.executable, str(GENERATOR), "--output", str(output_dir)],
                check=True,
                text=True,
                capture_output=True,
            )
            input_file = output_dir / "secret" / "tie-break.in"
            answer_file = output_dir / "secret" / "tie-break.ans"
            self.assertTrue(input_file.is_file())
            self.assertEqual(
                answer_file.read_text(encoding="utf-8"),
                "autorole 3\nmod 3\nmod 3\nmod 3\n",
            )

    def test_large_case_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            subprocess.run(
                [sys.executable, str(GENERATOR), "--output", str(output_dir)],
                check=True,
                text=True,
                capture_output=True,
            )
            generated = (output_dir / "secret" / "large-random.in").read_text(encoding="utf-8")
            committed = (ROOT / "data" / "secret" / "large-random.in").read_text(encoding="utf-8")
            self.assertEqual(generated, committed)


if __name__ == "__main__":
    unittest.main()
