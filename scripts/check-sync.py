"""저장소와 DOMjudge DB가 같은 문제 집합을 보고 있는지 확인한다.

저장소가 유일한 원본이므로, DB에만 있는 문제는 누군가 jury UI로 만든 것이고 커밋되지 않는다.
DB에만 있는 문제가 하나라도 있으면 종료 코드 1로 실패한다.
"""

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTESTS = REPO_ROOT / "problems" / "contests"

QUERY = (
    "SELECT c.shortname, p.externalid, cp.shortname "
    "FROM contestproblem cp "
    "JOIN contest c ON c.cid = cp.cid "
    "JOIN problem p ON p.probid = cp.probid "
    "ORDER BY c.shortname, cp.shortname;"
)


def problem_id_of(package: Path) -> str:
    ini = package / "domjudge-problem.ini"
    if not ini.is_file():
        return ""
    for line in ini.read_text(encoding="utf-8").splitlines():
        if line.startswith("externalid"):
            return line.split("=", 1)[1].strip()
    return ""


def contest_id_of(contest_dir: Path) -> str:
    contest_yaml = contest_dir / "contest.yaml"
    if not contest_yaml.is_file():
        return contest_dir.name
    for line in contest_yaml.read_text(encoding="utf-8").splitlines():
        if line.startswith("id:"):
            return line.split(":", 1)[1].strip()
    return contest_dir.name


def repository_state():
    """(대회 id, 라벨) -> 문제 id"""
    state = {}
    if not CONTESTS.is_dir():
        return state
    for contest_dir in sorted(p for p in CONTESTS.iterdir() if p.is_dir()):
        contest_id = contest_id_of(contest_dir)
        for label_dir in sorted(p for p in contest_dir.iterdir() if p.is_dir()):
            source = label_dir
            pointer = label_dir / "source.txt"
            if pointer.is_file():
                source = (contest_dir / pointer.read_text(encoding="utf-8").strip()).resolve()
            problem_id = problem_id_of(source)
            if problem_id:
                state[(contest_id, label_dir.name)] = problem_id
    return state


def database_state(compose_project_dir: Path):
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "mariadb",
        "sh",
        "-c",
        'exec mariadb -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -N -B -e "$1"',
        "sh",
        QUERY,
    ]
    result = subprocess.run(command, cwd=compose_project_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit("DB를 읽지 못했다. 스택이 떠 있는지 확인해라.\n" + result.stderr.strip())
    state = {}
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        contest_id, problem_id, label = parts
        state[(contest_id, label)] = problem_id
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=REPO_ROOT)
    args = parser.parse_args()

    repository = repository_state()
    database = database_state(args.project_dir)

    # 저장소가 관리하지 않는 대회(예: DOMjudge 데모)는 비교 대상이 아니다.
    managed = {contest_id for contest_id, _ in repository}
    database = {key: value for key, value in database.items() if key[0] in managed}

    only_in_db = {key: value for key, value in database.items() if key not in repository}
    only_in_repo = {key: value for key, value in repository.items() if key not in database}
    mismatched = {
        key: (repository[key], database[key])
        for key in repository.keys() & database.keys()
        if repository[key] != database[key]
    }

    print(f"저장소 {len(repository)}개, DB {len(database)}개")

    for (contest_id, label), problem_id in sorted(only_in_repo.items()):
        print(f"  [등록 안 됨] {contest_id}/{label} {problem_id} - docker compose up -d provisioner")
    for (contest_id, label), (expected, actual) in sorted(mismatched.items()):
        print(f"  [id 불일치] {contest_id}/{label} 저장소={expected} DB={actual}")
    for (contest_id, label), problem_id in sorted(only_in_db.items()):
        print(f"  [DB에만 있음] {contest_id}/{label} {problem_id} - 저장소에 없어서 공유되지 않는다")

    if only_in_db or only_in_repo or mismatched:
        print("실패: 저장소가 원본이다. DB에만 있는 문제는 커밋되지 않는다.")
        return 1
    print("동기화 정상")
    return 0


if __name__ == "__main__":
    sys.exit(main())
