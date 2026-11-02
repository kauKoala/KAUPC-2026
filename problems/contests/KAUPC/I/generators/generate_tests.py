import argparse
import random
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "submissions" / "accepted" / "floyd_python.py"

MAX_WEIGHT = 100000

CASES = {
    "sample/1": """4 2 6
1 2 5
2 3 5
2 1 3
1 3 4 2
2 1 4
1 1 4 3
2 1 4
2 2 4
""",
    "secret/disconnected": """5 1 6
1 2 8
2 1 3
1 2 3 4
2 1 3
1 4 5 1
2 1 5
2 4 5
""",
    "secret/parallel-edges": """2 1 3
1 2 7
2 1 2
1 1 2 4
2 1 2
""",
    "secret/irrelevant-bridge": """4 4 5
1 2 1
2 3 1
3 4 1
1 4 10
2 1 4
1 1 4 20
2 1 4
1 1 4 2
2 1 4
""",
    "secret/repeated-updates": """6 0 9
2 1 6
1 1 2 3
1 2 3 3
1 3 4 3
2 1 4
1 1 4 4
2 1 4
1 4 6 2
2 1 6
""",
    "secret/single-vertex": """1 0 3
2 1 1
1 1 1 7
2 1 1
""",
    "secret/self-loops": """3 3 5
1 1 4
2 2 9
1 2 6
2 1 2
1 1 1 1
2 1 1
2 1 3
2 3 3
""",
}


def random_case(seed, n, m, queries, updates, weight=MAX_WEIGHT, components=1):
    """Random graph; with components > 1 the vertices split into that many blocks."""
    rng = random.Random(seed)
    lines = [f"{n} {m} {queries}"]
    block = max(1, n // components)
    for _ in range(m):
        a = rng.randint(1, n)
        group = (a - 1) // block
        low = group * block + 1
        high = min(n, (group + 1) * block)
        b = rng.randint(low, high)
        lines.append(f"{a} {b} {rng.randint(1, weight)}")
    update_slots = set(rng.sample(range(queries), min(updates, queries)))
    for index in range(queries):
        if index in update_slots:
            lines.append(f"1 {rng.randint(1, n)} {rng.randint(1, n)} {rng.randint(1, weight)}")
        else:
            lines.append(f"2 {rng.randint(1, n)} {rng.randint(1, n)}")
    return "\n".join(lines) + "\n"


def path_case(seed, n, queries, updates, weight=MAX_WEIGHT):
    """Line graph with maximal weights: distances are large and every update is a shortcut."""
    rng = random.Random(seed)
    edges = [(i, i + 1, weight) for i in range(1, n)]
    lines = [f"{n} {len(edges)} {queries}"]
    lines += [f"{a} {b} {c}" for a, b, c in edges]
    update_slots = set(rng.sample(range(queries), min(updates, queries)))
    for index in range(queries):
        if index in update_slots:
            lines.append(f"1 1 {rng.randint(2, n)} {rng.randint(1, weight)}")
        else:
            lines.append(f"2 {rng.randint(1, n)} {rng.randint(1, n)}")
    return "\n".join(lines) + "\n"


def parallel_case(seed, n, m, queries):
    """Many parallel edges while keeping M below N squared."""
    rng = random.Random(seed)
    lines = [f"{n} {m} {queries}"]
    for index in range(m):
        lines.append(f"1 2 {1 + (index % MAX_WEIGHT)}")
    for index in range(queries):
        if index % 100 == 0:
            lines.append(f"1 1 2 {rng.randint(1, 10)}")
        else:
            lines.append(f"2 {rng.randint(1, n)} {rng.randint(1, n)}")
    return "\n".join(lines) + "\n"


def build_cases():
    cases = dict(CASES)
    cases["secret/max-dense"] = random_case(seed=20260921, n=300, m=5000, queries=1000, updates=500)
    cases["secret/max-two-components"] = random_case(
        seed=20260922, n=300, m=5000, queries=1000, updates=500, components=2
    )
    cases["secret/max-path-graph"] = path_case(seed=20260923, n=300, queries=1000, updates=500)
    cases["secret/max-parallel-edges"] = parallel_case(seed=20260924, n=300, m=50000, queries=100)
    # 쿼리마다 다익스트라를 도는 풀이가 가장 오래 걸리는 모양: 간선 50,000개, 조회 1,000개.
    cases["secret/max-dijkstra-queries"] = random_case(seed=20261022, n=300, m=50000, queries=1000, updates=0)
    cases["secret/max-dijkstra-updates"] = random_case(seed=20261023, n=300, m=50000, queries=1000, updates=500)
    # 1번 쿼리 수에는 제한이 없다. 간선을 추가할 때마다 O(N²)로 갱신하는 플로이드 풀이가 가장 오래 걸리는 모양.
    cases["secret/max-updates"] = random_case(seed=20261029, n=300, m=50000, queries=1000, updates=950)
    cases["secret/small-edge-heavy"] = random_case(seed=20261024, n=100, m=9000, queries=800, updates=300)
    cases["secret/updates-only"] = random_case(seed=20260925, n=300, m=1000, queries=520, updates=500)
    cases["secret/mid-random"] = random_case(seed=20260926, n=80, m=3000, queries=1000, updates=100)
    cases["secret/mid-sparse"] = random_case(seed=20260927, n=300, m=400, queries=1000, updates=50)
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
    cases = build_cases()
    for name, problem_input in cases.items():
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
