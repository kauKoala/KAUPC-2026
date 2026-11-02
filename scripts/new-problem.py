"""템플릿을 복사해 새 문제 패키지를 만든다.

저장소가 문제의 유일한 원본이므로, 새 문제는 항상 이 스크립트(또는 같은 구조의 폴더)로 만든다.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "problems" / "templates" / "standard"
TEXT_SUFFIXES = {".py", ".html", ".yaml", ".ini", ".md", ".txt", ".in", ".ans", ".c", ".java", ".cpp"}

DEFAULT_COLORS = [
    ("SteelBlue", "#4682B4"),
    ("Tomato", "#FF6347"),
    ("MediumSeaGreen", "#3CB371"),
    ("Goldenrod", "#DAA520"),
    ("MediumPurple", "#9370DB"),
    ("Chocolate", "#D2691E"),
    ("CadetBlue", "#5F9EA0"),
    ("IndianRed", "#CD5C5C"),
]


def contest_name_of(contest_dir: Path) -> str:
    contest_yaml = contest_dir / "contest.yaml"
    if not contest_yaml.is_file():
        return contest_dir.name
    for line in contest_yaml.read_text(encoding="utf-8").splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return contest_dir.name


def used_labels(problems_yaml: Path):
    if not problems_yaml.is_file():
        return set(), set()
    labels = set()
    ids = set()
    for line in problems_yaml.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            ids.add(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("label:"):
            labels.add(stripped.split(":", 1)[1].strip())
    return labels, ids


def pick_color(problems_yaml: Path):
    taken = set()
    if problems_yaml.is_file():
        for line in problems_yaml.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("color:"):
                taken.add(stripped.split(":", 1)[1].strip())
    for color, rgb in DEFAULT_COLORS:
        if color not in taken:
            return color, rgb
    return DEFAULT_COLORS[0]


def fill_placeholders(target: Path, replacements) -> None:
    for path in sorted(target.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        replaced = text
        for old, new in replacements.items():
            replaced = replaced.replace(old, new)
        if replaced != text:
            path.write_text(replaced, encoding="utf-8", newline="\n")


def append_problem_entry(problems_yaml: Path, problem_id: str, label: str, name: str, color: str, rgb: str) -> None:
    entry = (
        f"- id: {problem_id}\n"
        f"  label: {label}\n"
        f"  name: {name}\n"
        f"  color: {color}\n"
        f"  rgb: '{rgb}'\n"
    )
    existing = problems_yaml.read_text(encoding="utf-8") if problems_yaml.is_file() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    problems_yaml.write_text(existing + entry, encoding="utf-8", newline="\n")


def create(contest: str, label: str, problem_id: str, name: str, color: str, rgb: str) -> Path:
    contest_dir = REPO_ROOT / "problems" / "contests" / contest
    if not contest_dir.is_dir():
        raise ValueError(f"대회 폴더가 없다: {contest}")

    target = contest_dir / label
    if target.exists():
        raise ValueError(f"이미 있는 라벨이다: {contest}/{label}")

    problems_yaml = contest_dir / "problems.yaml"
    labels, ids = used_labels(problems_yaml)
    if label in labels:
        raise ValueError(f"{contest}에 {label}번이 이미 있다")
    if problem_id in ids:
        raise ValueError(f"{contest}에 영문 ID {problem_id}가 이미 있다")
    for ini in (REPO_ROOT / "problems" / "contests").glob("*/*/domjudge-problem.ini"):
        for line in ini.read_text(encoding="utf-8").splitlines():
            if line.startswith("externalid") and line.split("=", 1)[1].strip() == problem_id:
                raise ValueError(f"영문 ID {problem_id}는 이미 {ini.parent.parent.name}/{ini.parent.name}에서 씁니다.")

    if not color or not rgb:
        color, rgb = pick_color(problems_yaml)

    shutil.copytree(TEMPLATE, target)
    fill_placeholders(
        target,
        {
            "__문제 이름__": name,
            "__problem-id__": problem_id,
            "__CONTEST_NAME__": contest_name_of(contest_dir),
            "__CONTEST__": contest,
            "__LABEL__": label,
        },
    )
    # PHP INI treats parentheses and several other characters as syntax unless quoted.
    ini_path = target / "domjudge-problem.ini"
    lines = ini_path.read_text(encoding="utf-8").splitlines()
    lines = ["name = " + json.dumps(name, ensure_ascii=False) if line.startswith("name =") else line for line in lines]
    ini_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    append_problem_entry(problems_yaml, problem_id, label, name, color, rgb)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="템플릿에서 새 문제 패키지를 만든다.")
    parser.add_argument("contest", help="대회 폴더 이름 (예: KAUPC)")
    parser.add_argument("label", help="문제 라벨 (예: C)")
    parser.add_argument("problem_id", help="DOMjudge externalid (예: botmaintenance)")
    parser.add_argument("name", help="문제 이름")
    parser.add_argument("--color", default="", help="스코어보드 색 이름")
    parser.add_argument("--rgb", default="", help="스코어보드 색 RGB (예: #FF6347)")
    args = parser.parse_args()

    try:
        target = create(args.contest, args.label, args.problem_id, args.name, args.color, args.rgb)
    except ValueError as error:
        raise SystemExit(str(error))
    relative = target.relative_to(REPO_ROOT)
    print(f"만들었다: {relative}")
    print("다음 순서:")
    print(f"  1. {relative}/problem_statement/problem.html 작성")
    print(f"  2. {relative}/submissions/accepted/ 에 정답 코드")
    print(f"  3. python {relative}/generators/gen.py <시드> 로 입력을 확인")
    print(f"  4. python -m unittest discover {relative}/tests -v")
    print("  5. docker compose up -d")


if __name__ == "__main__":
    sys.exit(main())
