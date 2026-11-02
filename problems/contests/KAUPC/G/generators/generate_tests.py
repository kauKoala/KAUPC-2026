import argparse
import random
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "submissions" / "accepted" / "solution.py"

MAX_VALUE = 10000
NAME_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
# 기능 이름은 작업 이름과 같지 않다.
COMMANDS = {"feat", "fix", "hotfix", "deprecate", "issue"}

LITERAL_CASES = {
    "sample/1": """13
feat music 5
feat ping 9
issue
fix 10
issue
hotfix music 1
feat tts 2
issue
deprecate tts
issue
deprecate ping
deprecate music
issue
""",
    "sample/2": """12
feat music 5
feat ping 5
issue
hotfix music 3
issue
deprecate ping
issue
feat ping 1
issue
fix 10
issue
issue
""",
    "secret/ignored-operations": """10
issue
fix 5
hotfix ghost 7
deprecate ghost
feat poll 4
feat poll 100
issue
hotfix poll 0
deprecate ghost
issue
""",
    "secret/tie-break": """9
feat rank 3
feat mod 3
feat autorole 3
issue
fix 1
issue
deprecate autorole
issue
issue
""",
    "secret/revive-after-deprecate": """11
feat tts 100
issue
deprecate tts
feat tts 1
issue
hotfix tts 4
issue
deprecate tts
issue
feat tts 0
issue
""",
    "secret/fix-chain": """12
feat aa 0
feat ab 1
feat ac 2
fix 5
issue
fix 5
issue
fix 5
issue
fix 100
fix 100
issue
""",
    "secret/all-deprecated": """9
feat ping 1
feat rank 2
deprecate ping
deprecate rank
issue
feat ping 7
issue
deprecate ping
issue
""",
    "secret/tie-break-prefix": """8
feat ab 5
feat aa 5
feat abc 5
feat a 5
issue
fix 0
issue
issue
""",
}


def make_names(rng, count, length=None):
    names = set()
    while len(names) < count:
        size = length if length else rng.randint(1, 12)
        name = "".join(rng.choice(NAME_ALPHABET) for _ in range(size))
        if name not in COMMANDS:
            names.add(name)
    return sorted(names)




def random_case(seed, operations, pool_size, weights, max_value=MAX_VALUE, name_length=None):
    rng = random.Random(seed)
    names = make_names(rng, pool_size, name_length)
    commands = list(weights)
    chances = [weights[command] for command in commands]

    def target():
        return rng.choice(names)

    lines = [str(operations)]
    for _ in range(operations):
        command = rng.choices(commands, weights=chances, k=1)[0]
        if command == "feat":
            lines.append("feat " + rng.choice(names) + " " + str(rng.randint(0, max_value)))
        elif command == "fix":
            lines.append("fix " + str(rng.randint(0, max_value)))
        elif command == "hotfix":
            lines.append("hotfix " + target() + " " + str(rng.randint(0, max_value)))
        elif command == "deprecate":
            lines.append("deprecate " + target())
        else:
            lines.append("issue")
    if "issue" not in lines[1:]:
        lines[-1] = "issue"
    return "\n".join(lines) + "\n"




def single_feature_max_total_case(operations):
    """한 기능에 최댓값만 더해 사용 지수를 가능한 한 크게 만든다. 200,000번이면 1,999,990,000이다."""
    lines = [str(operations), f"feat maxtotal {MAX_VALUE}"]
    lines += [f"hotfix maxtotal {MAX_VALUE}"] * (operations - 2)
    lines.append("issue")
    return "\n".join(lines) + "\n"


def stale_heap_case(seed, operations, pool_size):
    """같은 기능을 계속 갱신해 힙에 낡은 항목이 쌓이게 한다."""
    rng = random.Random(seed)
    names = make_names(rng, pool_size)
    lines = [str(operations)]
    written = 0
    for name in names:
        if written >= operations:
            break
        lines.append("feat " + name + " " + str(rng.randint(0, 1000)))
        written += 1
    while written < operations:
        target = names[0]
        lines.append("hotfix " + target + " " + str(rng.randint(0, 1000)))
        written += 1
        if written < operations:
            lines.append("issue")
            written += 1
    return "\n".join(lines) + "\n"


def fix_only_case(seed, operations, pool_size):
    """fix만 계속 호출해 최저 기능이 매번 바뀌게 한다."""
    rng = random.Random(seed)
    names = make_names(rng, pool_size)
    lines = [str(operations)]
    written = 0
    for name in names:
        if written >= operations:
            break
        lines.append("feat " + name + " " + str(rng.randint(0, 100)))
        written += 1
    while written < operations:
        lines.append("fix " + str(rng.randint(1, 100)))
        written += 1
        if written < operations:
            lines.append("issue")
            written += 1
    return "\n".join(lines) + "\n"


def feat_only_case(seed, operations):
    """대부분이 feat이고 조회는 끝에 몇 번만 있는 중간 크기 입력."""
    rng = random.Random(seed)
    names = make_names(rng, operations)
    lines = [str(operations)]
    for index in range(operations - 3):
        lines.append("feat " + names[index] + " " + str(rng.randint(0, MAX_VALUE)))
    lines.append("issue")
    lines.append(f"fix {MAX_VALUE}")
    lines.append("issue")
    return "\n".join(lines) + "\n"


def build_cases():
    cases = dict(LITERAL_CASES)
    cases["secret/large-random"] = random_case(
        seed=20260921,
        operations=150000,
        pool_size=40000,
        weights={"feat": 3, "fix": 2, "hotfix": 3, "deprecate": 1, "issue": 3},
    )
    cases["secret/lazy-stress"] = random_case(
        seed=20260922,
        operations=80000,
        pool_size=40,
        weights={"feat": 1, "fix": 1, "hotfix": 6, "deprecate": 1, "issue": 3},
    )
    cases["secret/churn"] = random_case(
        seed=20260923,
        operations=60000,
        pool_size=400,
        weights={"feat": 4, "fix": 1, "hotfix": 1, "deprecate": 4, "issue": 4},
        max_value=1000,
    )
    cases["secret/issue-heavy"] = random_case(
        seed=20260924,
        operations=150000,
        pool_size=40000,
        weights={"feat": 2, "fix": 1, "hotfix": 1, "deprecate": 1, "issue": 10},
    )
    cases["secret/long-names"] = random_case(
        seed=20260925,
        operations=60000,
        pool_size=30000,
        weights={"feat": 3, "fix": 2, "hotfix": 3, "deprecate": 1, "issue": 4},
        name_length=20,
    )
    cases["secret/equal-values"] = random_case(
        seed=20260926,
        operations=100000,
        pool_size=2000,
        weights={"feat": 4, "fix": 2, "hotfix": 2, "deprecate": 1, "issue": 6},
        max_value=3,
    )
    cases["secret/stale-heap"] = stale_heap_case(seed=20260927, operations=100000, pool_size=50)
    cases["secret/fix-only"] = fix_only_case(seed=20260928, operations=100000, pool_size=1000)
    cases["secret/max-total"] = single_feature_max_total_case(operations=200000)
    cases["secret/mid-random"] = random_case(
        seed=20260929,
        operations=20000,
        pool_size=5000,
        weights={"feat": 3, "fix": 2, "hotfix": 3, "deprecate": 1, "issue": 3},
    )
    cases["secret/mid-late-issue"] = random_case(
        seed=20260930,
        operations=20000,
        pool_size=3000,
        weights={"feat": 4, "fix": 3, "hotfix": 3, "deprecate": 2, "issue": 0},
    ).replace("20000\n", "20001\n", 1).rstrip("\n") + "\nissue\n"
    cases["secret/feat-only"] = feat_only_case(seed=20260931, operations=20000)
    cases["secret/max-random"] = random_case(
        seed=20261001, operations=200000, pool_size=40000,
        weights={"feat": 3, "fix": 2, "hotfix": 3, "deprecate": 1, "issue": 3},
    )
    cases["secret/max-fix"] = fix_only_case(seed=20261002, operations=200000, pool_size=2000)
    # 기능 100,000개를 살려 둔 채 fix와 issue를 100,000번 한다.
    # 정렬된 리스트에 넣고 빼는 O(N) 풀이는 여기서 시간 초과가 나야 한다.
    cases["secret/max-live-fix"] = fix_only_case(seed=20261022, operations=200000, pool_size=100000)
    return cases


def reference_command(reference: Path):
    if reference.suffix == ".py":
        return [sys.executable, str(reference)]
    return [str(reference)]


def answer_for(problem_input: str, reference: Path) -> str:
    completed = subprocess.run(
        reference_command(reference),
        input=problem_input,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout


def write_cases(output: Path, reference: Path) -> None:
    for name, problem_input in build_cases().items():
        input_path = output / f"{name}.in"
        answer_path = output / f"{name}.ans"
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(problem_input, encoding="utf-8", newline="\n")
        answer_path.write_text(answer_for(problem_input, reference), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    parser.add_argument(
        "--reference",
        type=Path,
        default=REFERENCE,
        help="정답 생성에 쓸 실행 파일. .py면 현재 파이썬으로 실행하고, 그 외에는 바로 실행한다.",
    )
    args = parser.parse_args()
    write_cases(args.output, args.reference)


if __name__ == "__main__":
    main()
