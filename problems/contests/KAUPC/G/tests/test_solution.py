import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOLUTION = ROOT / "submissions" / "accepted" / "solution.py"


def run(problem_input: str) -> str:
    return subprocess.run(
        [sys.executable, str(SOLUTION)],
        input=problem_input,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


class ReferenceSolutionTest(unittest.TestCase):
    def test_reports_lowest_usage_with_lexicographic_tie_break(self):
        self.assertEqual(run("6\nfeat rank 3\nfeat mod 3\nissue\nfix 1\nissue\nissue\n"), "mod 3\nrank 3\nrank 3\n")

    def test_ignores_operations_on_missing_or_duplicate_features(self):
        self.assertEqual(run("7\nhotfix ghost 5\ndeprecate ghost\nfeat poll 4\nfeat poll 99\nissue\nfix 2\nissue\n"), "poll 4\npoll 6\n")

    def test_stale_heap_entries_do_not_resurrect_removed_features(self):
        self.assertEqual(run("6\nfeat tts 1\nhotfix tts 5\ndeprecate tts\nissue\nfeat tts 9\nissue\n"), "-1\ntts 9\n")

    def test_reports_minus_one_when_no_feature_exists(self):
        self.assertEqual(run("3\nissue\nfix 7\nissue\n"), "-1\n-1\n")


    def test_matches_naive_simulation_on_small_random_inputs(self):
        import random

        rng = random.Random(7)
        for _ in range(300):
            problem_input = small_random_input(rng)
            self.assertEqual(run(problem_input), naive(problem_input), problem_input)


def small_random_input(rng) -> str:
    pool = ["a", "b", "c", "ab", "b_", "a0"]
    lines = []
    count = rng.randint(1, 40)
    for _ in range(count):
        command = rng.choice(["feat", "fix", "hotfix", "deprecate", "issue"])
        if command == "feat":
            lines.append(f"feat {rng.choice(pool)} {rng.randint(0, 6)}")
        elif command == "fix":
            lines.append(f"fix {rng.randint(0, 6)}")
        elif command == "hotfix":
            lines.append(f"hotfix {rng.choice(pool)} {rng.randint(0, 6)}")
        elif command == "deprecate":
            lines.append(f"deprecate {rng.choice(pool)}")
        else:
            lines.append("issue")
    lines.append("issue")
    return f"{len(lines)}\n" + "\n".join(lines) + "\n"


def naive(problem_input: str) -> str:
    tokens = problem_input.split()
    usage = {}
    output = []
    position = 1
    for _ in range(int(tokens[0])):
        command = tokens[position]
        position += 1
        if command == "feat":
            name, amount = tokens[position], int(tokens[position + 1])
            position += 2
            usage.setdefault(name, amount)
        elif command == "fix":
            amount = int(tokens[position])
            position += 1
            if usage:
                name = min(usage, key=lambda key: (usage[key], key))
                usage[name] += amount
        elif command == "hotfix":
            name, amount = tokens[position], int(tokens[position + 1])
            position += 2
            if name in usage:
                usage[name] += amount
        elif command == "deprecate":
            usage.pop(tokens[position], None)
            position += 1
        else:
            if usage:
                name = min(usage, key=lambda key: (usage[key], key))
                output.append(f"{name} {usage[name]}")
            else:
                output.append("-1")
    return "".join(line + "\n" for line in output)


if __name__ == "__main__":
    unittest.main()
