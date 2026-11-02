import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"feat": 3, "fix": 2, "hotfix": 3, "deprecate": 2, "issue": 1}

def validate(case, text):
    lines = text.splitlines()
    if not 1 <= int(lines[0]) <= 200000 or int(lines[0]) != len(lines) - 1:
        raise AssertionError(f"{case}: wrong operation count")
    if "issue" not in lines[1:]:
        raise AssertionError(f"{case}: missing issue")
    for line in lines[1:]:
        words = line.split()
        if words[0] not in ALLOWED or len(words) != ALLOWED[words[0]]:
            raise AssertionError(f"{case}: invalid command {line}")
        if words[0] in ("feat", "fix", "hotfix") and not 0 <= int(words[-1]) <= 10000:
            raise AssertionError(f"{case}: p out of range {line}")
        if words[0] in ("feat", "hotfix", "deprecate"):
            name = words[1]
            if not (1 <= len(name) <= 20 and name.isascii() and name.isalpha() and name.islower()) or name in ALLOWED:
                raise AssertionError(f"{case}: invalid name {name}")

class FiveCommandContractTest(unittest.TestCase):
    def test_all_committed_inputs_use_the_five_commands(self):
        for path in (ROOT / "data").rglob("*.in"):
            with self.subTest(case=path.stem):
                validate(path, path.read_text(encoding="utf-8"))

    def test_generated_cases_use_the_same_contract(self):
        spec = importlib.util.spec_from_file_location("bot_generator", ROOT / "generators/generate_tests.py")
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        for name, text in generator.build_cases().items():
            with self.subTest(case=name):
                validate(name, text)

    def test_statement_does_not_offer_split(self):
        self.assertNotIn("<code>split", (ROOT / "problem_statement/problem.html").read_text(encoding="utf-8"))
