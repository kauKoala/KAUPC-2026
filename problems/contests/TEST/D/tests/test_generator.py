import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generators" / "generate_tests.py"


class GeneratorTest(unittest.TestCase):
    def test_regenerating_reproduces_the_committed_data(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            subprocess.run(
                [sys.executable, str(GENERATOR), "--output", str(output_dir)],
                check=True,
                text=True,
                capture_output=True,
            )
            for generated in sorted(output_dir.rglob("*")):
                if not generated.is_file():
                    continue
                committed = ROOT / "data" / generated.relative_to(output_dir)
                self.assertTrue(committed.is_file(), f"{committed}가 커밋되어 있지 않다")
                self.assertEqual(
                    generated.read_text(encoding="utf-8"),
                    committed.read_text(encoding="utf-8"),
                    f"{committed.name}이 생성기 출력과 다르다",
                )


if __name__ == "__main__":
    unittest.main()
