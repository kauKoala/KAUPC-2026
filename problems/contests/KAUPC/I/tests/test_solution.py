import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOLUTION = ROOT / "submissions" / "accepted" / "floyd_python.py"


class ReferenceSolutionTest(unittest.TestCase):
    def test_handles_disconnected_graph_bridge_and_parallel_edge(self):
        problem_input = """4 1 6
1 2 10
2 1 2
1 2 3 4
2 1 3
1 1 2 2
2 1 2
2 2 4
"""
        result = subprocess.run(
            [sys.executable, str(SOLUTION)],
            input=problem_input,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout, "10\n14\n2\n-1\n")


if __name__ == "__main__":
    unittest.main()
