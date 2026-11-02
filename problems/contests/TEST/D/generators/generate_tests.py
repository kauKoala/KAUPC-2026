"""테스트 데이터 생성기.

`data/`에 결정론적으로 입력을 쓰고, 정답 코드를 돌려 같은 이름의 `.ans`를 만든다.
난수를 쓸 때는 반드시 시드를 고정한다. 시드나 케이스를 바꾸면 커밋된 `data/`도 갱신해야 한다.
"""

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "submissions" / "accepted" / "solution.py"

GENERATOR = ROOT / "generators" / "gen.py"


def seeded_case(seed: int) -> str:
    completed = subprocess.run(
        [sys.executable, str(GENERATOR), str(seed)],
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout


def build_cases():
    return {
        "sample/1": seeded_case(1),
        **{f"secret/{seed - 1}": seeded_case(seed) for seed in range(2, 8)},
    }


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
