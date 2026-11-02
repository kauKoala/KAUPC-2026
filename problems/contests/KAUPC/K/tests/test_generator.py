"""생성기는 시드만으로 결정된다.

같은 시드가 다른 입력을 만들면 커밋된 data/를 다시 만들 수 없다.
"""

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "generators" / "gen.py"


class GeneratorTest(unittest.TestCase):
    def run_seed(self, seed: str) -> str:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), seed],
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout

    def test_the_same_seed_always_makes_the_same_input(self) -> None:
        self.assertEqual(self.run_seed("1"), self.run_seed("1"))

    def test_different_seeds_make_different_inputs(self) -> None:
        seen = {self.run_seed(str(seed)) for seed in range(1, 12)}
        self.assertGreater(len(seen), 1, "시드를 바꿔도 같은 입력만 나온다")


if __name__ == "__main__":
    unittest.main()
