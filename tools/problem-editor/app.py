"""문제 패키지 웹 에디터.

저장소의 `problems/contests/`를 직접 읽고 쓴다. DOMjudge DB는 건드리지 않는다.
무엇을 고치든 파일로 저장한 뒤 곧바로 커밋하고 푸시한다. 저장소가 원본이다.
표준 라이브러리만 쓴다.
"""

import base64
import html
import http.client
import http.server
import importlib.util
import json
import mimetypes
import os
import re
import random
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

REPO_ROOT = Path(os.environ.get("PROBLEM_REPO_ROOT") or Path(__file__).resolve().parents[2])
CONTESTS = REPO_ROOT / "problems" / "contests"
SCRIPTS = REPO_ROOT / "scripts"

# scripts/new-problem.py 를 그대로 재사용한다. 파일 이름에 하이픈이 있어 경로로 불러온다.
_spec = importlib.util.spec_from_file_location("new_problem", SCRIPTS / "new-problem.py")
new_problem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(new_problem)

# 리버스 프록시 뒤에서 하위 경로로 서비스할 때 쓴다. 예: /authoring
BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")


def link(path: str) -> str:
    """화면에 넣는 주소는 항상 접두사를 붙인다."""
    return BASE_PATH + path


SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_PROBLEM_ID = re.compile(r"^[a-z0-9]+$")
SAFE_FILE = re.compile(r"^[A-Za-z0-9_.-]+$")

# 폴더 이름이 곧 기대 판정이다. Polygon처럼 파일마다 기대 판정을 태그로 붙인다.
SUBMISSION_LABELS = (
    ("accepted", "AC", "맞았습니다"),
    ("wrong_answer", "WA", "틀렸습니다"),
    ("time_limit_exceeded", "TLE", "시간 초과"),
)
SUBMISSION_FOLDERS = tuple(folder for folder, _, _ in SUBMISSION_LABELS)

# 코드를 올릴 때 고르는 언어. 확장자가 곧 채점 언어다.
LANGUAGES = (
    ("py", "Python", "solution.py"),
    ("cpp", "C++", "solution.cpp"),
    ("c", "C", "solution.c"),
    ("java", "Java", "Main.java"),
)
DEFAULT_FILENAME = {key: filename for key, _, filename in LANGUAGES}
EXTENSION_LANGUAGE = {"py": "Python", "cpp": "C++", "cc": "C++", "c": "C", "java": "Java"}

PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
# 템플릿이 넣어 두는 자리 문구. 그대로 남아 있으면 아직 안 쓴 것으로 본다.
PLACEHOLDER_TEXT = ("문제 설명을 작성한다.", "입력 형식을 작성한다.", "출력 형식을 작성한다.", "내용을 작성한다.")
IMAGE_MARKUP = re.compile(r"!\[([^\]\n]*)\]\(([A-Za-z0-9_.-]+)\)")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")
MAX_IMAGE_BYTES = 1024 * 1024

# 화면을 다시 그릴 때 어느 칸의 결과인지 알아야 그 자리에 메시지를 띄운다.
SECTION_OF_ROUTE = {
    "/statement": "statement",
    "/image": "statement",
    "/testcase": "data",
    "/testcase-delete": "data",
    "/testcase-sample": "data",
    "/generator": "generator",
    "/generate": "generator",
    "/generate-legacy": "generator",
    "/submission": "code",
    "/submission-delete": "code",
    "/verify": "verify",
    "/publish": "publish",
}
SECTIONS = tuple(dict.fromkeys(SECTION_OF_ROUTE.values()))


def safe_image_name(filename: str, folder: Path) -> str:
    """한글이나 공백이 든 이름도 받는다. 지문 표기법이 읽을 수 있는 이름으로 바꿔 준다."""
    suffix = Path(filename).suffix.lower()
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", Path(filename).stem).strip("-")
    stem = stem or "image"
    candidate = stem + suffix
    number = 2
    while (folder / candidate).is_file():
        candidate = f"{stem}-{number}{suffix}"
        number += 1
    return candidate


def safe_part(value: str, pattern=SAFE_NAME) -> str:
    value = (value or "").strip()
    if not pattern.match(value):
        raise ValueError(f"쓸 수 없는 이름입니다: {value!r}")
    return value


def package_dir(contest: str, label: str) -> Path:
    path = CONTESTS / safe_part(contest) / safe_part(label)
    if not (path / "problem.yaml").is_file():
        raise ValueError(f"문제 패키지가 없습니다: {contest}/{label}")
    return path


def write_text(path: Path, text: str) -> None:
    """개행은 LF로 맞추고, 줄 끝 공백과 파일 끝 빈 줄을 정리한 뒤 마지막 개행 하나를 보장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = text.replace("\r\n", "\n").split("\n")
    normalized = "\n".join(line.rstrip() for line in lines).rstrip("\n")
    if normalized:
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


# ---- problem.yaml: 이름과 제한은 여기가 원본이다 ----


def problem_meta(package: Path):
    """이름, 시간 제한(초), 메모리 제한(MB). 채점에 실제로 쓰이는 값이다."""
    text = (package / "problem.yaml").read_text(encoding="utf-8")
    name = package.name
    for line in text.splitlines():
        if line.startswith("name:"):
            name = yaml_unquote(line.split(":", 1)[1].strip())
            break
    time_match = re.search(r"time_limit:\s*([0-9]+(?:\.[0-9]+)?)", text)
    memory_match = re.search(r"memory:\s*([0-9]+)", text)
    return {
        "name": name,
        "time_limit": float(time_match.group(1)) if time_match else 1.0,
        "memory": int(memory_match.group(1)) if memory_match else 512,
    }


def problem_name_of(package: Path) -> str:
    return problem_meta(package)["name"]


def pretty_seconds(value: float):
    return int(value) if float(value).is_integer() else value


PROBLEM_NAME_MAX_LENGTH = 100


def yaml_unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except ValueError:
            return value
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def yaml_scalar(value: str) -> str:
    """평범한 이름은 그대로 쓰고, YAML 문법과 겹치는 이름만 따옴표로 감싼다."""
    plain = (
        value == value.strip()
        and ": " not in value
        and " #" not in value
        and not value.endswith(":")
        and value[0] not in "-?:,[]{}#&*!|>'\"%@`"
    )
    return value if plain else json.dumps(value, ensure_ascii=False)


def clean_problem_name(raw) -> str:
    name = " ".join(str(raw or "").split())
    if not name:
        raise ValueError("제목을 입력하세요.")
    if len(name) > PROBLEM_NAME_MAX_LENGTH:
        raise ValueError(f"제목은 {PROBLEM_NAME_MAX_LENGTH}자 이하로 정하세요.")
    return name


def problem_id_of(package: Path) -> str:
    ini_path = package / "domjudge-problem.ini"
    if ini_path.is_file():
        for line in ini_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("externalid"):
                return line.split("=", 1)[1].strip()
    return ""


def rename_problem(package: Path, name: str):
    """이름은 problem.yaml, domjudge-problem.ini, 그리고 이 문제를 쓰는 모든 대회의 problems.yaml에 있다.
    바뀐 파일 목록을 돌려준다."""
    name = clean_problem_name(name)
    if name == problem_meta(package)["name"]:
        return []
    changed = []

    yaml_path = package / "problem.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    text = re.sub(r"^name:.*$", lambda _: "name: " + yaml_scalar(name), text, count=1, flags=re.M)
    write_text(yaml_path, text)
    changed.append(yaml_path)

    ini_path = package / "domjudge-problem.ini"
    if ini_path.is_file():
        ini = ini_path.read_text(encoding="utf-8")
        # PHP INI는 괄호 같은 문자를 문법으로 읽으므로 항상 따옴표로 감싼다.
        ini = re.sub(r"^name\s*=.*$", lambda _: "name = " + json.dumps(name, ensure_ascii=False), ini, count=1, flags=re.M)
        write_text(ini_path, ini)
        changed.append(ini_path)

    problem_id = problem_id_of(package)
    if problem_id and CONTESTS.is_dir():
        for problems_yaml in sorted(CONTESTS.glob("*/problems.yaml")):
            lines = problems_yaml.read_text(encoding="utf-8").split("\n")
            inside = False
            touched = False
            for index, line in enumerate(lines):
                if line.startswith("- "):
                    inside = re.fullmatch(r"- id:\s*" + re.escape(problem_id) + r"\s*", line) is not None
                elif inside and re.match(r"^  name:", line):
                    lines[index] = "  name: " + yaml_scalar(name)
                    touched = True
            if touched:
                write_text(problems_yaml, "\n".join(lines))
                changed.append(problems_yaml)
    return changed


def write_problem_meta(package: Path, time_limit: float, memory: int) -> None:
    """제한을 고치면 problem.yaml과 domjudge-problem.ini를 같이 고친다."""
    if time_limit <= 0 or time_limit > 60:
        raise ValueError("시간 제한은 0초보다 크고 60초 이하여야 합니다.")
    if memory < 16 or memory > 4096:
        raise ValueError("메모리 제한은 16MB 이상 4096MB 이하여야 합니다.")

    seconds = pretty_seconds(time_limit)
    yaml_path = package / "problem.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    text = re.sub(r"time_limit:\s*[0-9.]+", f"time_limit: {seconds}", text)
    text = re.sub(r"memory:\s*[0-9]+", f"memory: {memory}", text)
    write_text(yaml_path, text)

    ini_path = package / "domjudge-problem.ini"
    if ini_path.is_file():
        ini = ini_path.read_text(encoding="utf-8")
        ini = re.sub(r"timelimit\s*=\s*[0-9.]+", f"timelimit = {seconds}", ini)
        write_text(ini_path, ini)


def statement_path(package: Path) -> Path:
    return package / "problem_statement" / "problem.html"


def image_dir(package: Path) -> Path:
    return package / "problem_statement" / "images"


def accepted_dir(package: Path) -> Path:
    return package / "submissions" / "accepted"


def main_solution_name(package: Path) -> str:
    """데이터의 정답 파일을 만드는 코드. 직접 고른 값이 있으면 그것을 쓴다."""
    marker = package / "generators" / "main.txt"
    if marker.is_file():
        chosen = marker.read_text(encoding="utf-8").strip()
        if chosen and (accepted_dir(package) / chosen).is_file():
            return chosen
    legacy = package / "generators" / "generate_tests.py"
    if legacy.is_file():
        found = re.search(
            r'REFERENCE\s*=\s*ROOT\s*/\s*"submissions"\s*/\s*"[^"]+"\s*/\s*"([^"]+)"',
            legacy.read_text(encoding="utf-8"),
        )
        # 예전 생성기는 느린 참조 풀이를 쓰기도 한다. 정답 폴더에 있는 것만 인정한다.
        if found and (accepted_dir(package) / found.group(1)).is_file():
            return found.group(1)
    if accepted_dir(package).is_dir():
        for candidate in sorted(accepted_dir(package).glob("*.py")):
            return candidate.name
        for candidate in sorted(accepted_dir(package).iterdir()):
            if candidate.is_file() and candidate.name != ".gitkeep":
                return candidate.name
    return "solution.py"


def main_solution_path(package: Path) -> Path:
    path = accepted_dir(package) / main_solution_name(package)
    if path.is_file():
        return path
    raise ValueError("정답 코드가 없습니다. 정답 코드를 먼저 추가하세요.")


def delete_submission(package: Path, folder: str, filename: str) -> Path:
    """잘못 올린 코드 파일 하나를 지운다. MAIN을 지우면 main_solution_name이 다른 정답 코드로 넘어간다."""
    if folder not in SUBMISSION_FOLDERS:
        raise ValueError(f"허용하지 않는 종류입니다: {folder}")
    filename = (filename or "").strip()
    if not SAFE_FILE.match(filename) or filename in (".", ".."):
        raise ValueError(f"파일 이름을 확인하세요: {filename!r}")
    target = package / "submissions" / folder / filename
    if not target.is_file():
        raise ValueError(f"{folder}/{filename}을(를) 찾을 수 없습니다.")
    target.unlink()
    return target


def count_files(folder: Path, pattern: str = "*") -> int:
    if not folder.is_dir():
        return 0
    return len([p for p in folder.glob(pattern) if p.is_file() and p.name != ".gitkeep"])


def list_packages():
    rows = []
    if not CONTESTS.is_dir():
        return rows
    for contest_dir in sorted(p for p in CONTESTS.iterdir() if p.is_dir()):
        for label_dir in sorted(p for p in contest_dir.iterdir() if p.is_dir()):
            pointer = label_dir / "source.txt"
            if pointer.is_file():
                rows.append(
                    {
                        "contest": contest_dir.name,
                        "label": label_dir.name,
                        "name": "(다른 대회 문제 재사용)",
                        "source": pointer.read_text(encoding="utf-8").strip(),
                        "editable": False,
                    }
                )
                continue
            if not (label_dir / "problem.yaml").is_file():
                continue
            rows.append(
                {
                    "contest": contest_dir.name,
                    "label": label_dir.name,
                    "name": problem_name_of(label_dir),
                    "source": "",
                    "samples": count_files(label_dir / "data" / "sample", "*.in"),
                    "secrets": count_files(label_dir / "data" / "secret", "*.in"),
                    "accepted": count_files(accepted_dir(label_dir)),
                    "editable": True,
                }
            )
    return rows


# ---- 요청 읽기 ----


def parse_multipart(body: bytes, content_type: str):
    """텍스트 필드는 문자열로, 파일은 바이트도 같이 담아 둔다."""
    match = re.search(r"boundary=([^;]+)", content_type)
    if not match:
        return {}
    boundary = match.group(1).strip().strip('"').encode()
    fields = {}
    for part in body.split(b"--" + boundary):
        if not part.strip() or part.strip() == b"--":
            continue
        header_blob, _, value = part.partition(b"\r\n\r\n")
        headers = header_blob.decode("utf-8", "replace")
        name_match = re.search(r'name="([^"]*)"', headers)
        if not name_match:
            continue
        value = value.rstrip(b"\r\n")
        name = name_match.group(1)
        filename_match = re.search(r'filename="([^"]*)"', headers)
        if filename_match and filename_match.group(1):
            fields[name + "__filename"] = filename_match.group(1)
            fields[name + "__bytes"] = value
        fields[name] = value.decode("utf-8", "replace")
    return fields


def read_form(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length) if length else b""
    content_type = handler.headers.get("Content-Type", "")
    if content_type.startswith("multipart/form-data"):
        return parse_multipart(body, content_type)
    return {key: values[0] for key, values in parse_qs(body.decode("utf-8", "replace")).items()}


# ---- git: 고친 내용은 바로 커밋하고 푸시한다 ----

GIT_BRANCH = os.environ.get("GIT_BRANCH", "master")
GIT_SSH_KEY = os.environ.get("GIT_SSH_KEY", "").strip()


def git_env():
    env = dict(os.environ)
    if GIT_SSH_KEY and Path(GIT_SSH_KEY).is_file():
        env["GIT_SSH_COMMAND"] = (
            f"ssh -i {GIT_SSH_KEY} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
        )
    return env


def git(*args, check: bool = False):
    """저장소 루트에서 git을 돌린다. (종료코드, 출력)"""
    result = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=git_env(),
    )
    output = (result.stdout + result.stderr).strip()
    if check and result.returncode != 0:
        raise ValueError("git " + " ".join(args) + " 실패: " + output[-400:])
    return result.returncode, output


def git_available() -> bool:
    return (REPO_ROOT / ".git").exists()


def push_url() -> str:
    """배포 키로 밀 수 있는 ssh 주소. 키가 없으면 빈 문자열."""
    if not GIT_SSH_KEY or not Path(GIT_SSH_KEY).is_file():
        return ""
    code, remote = git("remote", "get-url", "origin")
    if code != 0 or not remote:
        return ""
    remote = remote.strip()
    if remote.startswith("git@") or remote.startswith("ssh://"):
        return remote
    match = re.match(r"https://([^/]+)/(.+?)(?:\.git)?$", remote)
    if not match:
        return ""
    return f"git@{match.group(1)}:{match.group(2)}.git"


def git_branch() -> str:
    if not git_available():
        return ""
    _, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    return branch.strip()


def git_pull() -> str:
    """원격을 먼저 따라잡는다. 충돌은 그대로 올려서 사람이 풀게 한다."""
    if not git_available():
        raise ValueError("git 저장소가 아니다")
    url = push_url()
    code, output = git("pull", "--rebase", url if url else "origin", GIT_BRANCH)
    if code != 0:
        git("rebase", "--abort")
        raise ValueError("원격과 합치지 못했다. 직접 해결해야 한다: " + output[-300:])
    return "원격과 맞췄다"


# GitHub은 100MB가 넘는 파일을 받지 않는다. 한 번 커밋되면 그 뒤 푸시가 전부 막혀서, 여유를 두고 미리 거른다.
MAX_COMMIT_BYTES = 50 * 1024 * 1024


def oversized_files(paths):
    """paths 아래에서 MAX_COMMIT_BYTES를 넘는 파일과 크기."""
    found = []
    for path in paths:
        path = Path(path)
        files = [path] if path.is_file() else (p for p in path.rglob("*") if p.is_file()) if path.is_dir() else []
        for file in files:
            size = file.stat().st_size
            if size > MAX_COMMIT_BYTES:
                found.append((file, size))
    return found


def git_save(paths, message: str) -> str:
    """바뀐 파일을 커밋하고 곧바로 푸시한다. 결과를 한 줄로 돌려준다."""
    too_big = oversized_files(paths)
    if too_big:
        listed = ", ".join(f"{file.name}({size // (1024 * 1024)}MB)" for file, size in too_big)
        raise ValueError(f"파일이 너무 커서 저장하지 않았습니다: {listed}. 한 파일은 {MAX_COMMIT_BYTES // (1024 * 1024)}MB 이하여야 합니다.")
    if not git_available():
        return "저장되었습니다."
    for path in paths:
        git("add", "--", str(path))
    code, staged = git("diff", "--cached", "--name-only")
    if code != 0 or not staged.strip():
        return "저장되었습니다."
    git("commit", "-m", message, check=True)
    url = push_url()
    if not url:
        return "저장되었습니다."
    code, output = git("push", url, f"HEAD:{GIT_BRANCH}")
    if code != 0:
        # 원격이 앞서 있으면(배포 등) 받아서 내 커밋을 그 위로 올린 뒤 다시 민다.
        pulled, pull_output = git("pull", "--rebase", "--autostash", url, GIT_BRANCH)
        if pulled != 0:
            git("rebase", "--abort")
            print(pull_output, file=sys.stderr)
            raise ValueError("원격 저장소와 충돌해 저장하지 못했습니다. 운영진에게 알려 주세요.")
        code, output = git("push", url, f"HEAD:{GIT_BRANCH}")
        if code != 0:
            print(output, file=sys.stderr)
            raise ValueError("저장하지 못했습니다. 잠시 후 다시 시도해 주세요.")
    return "저장되었습니다."


# ---- 채점 시스템 반영 ----

DOCKER_SOCKET = os.environ.get("DOCKER_SOCKET", "/var/run/docker.sock")
PROVISIONER_SERVICE = os.environ.get("PROVISIONER_SERVICE", "provisioner")


class DockerSocketConnection(http.client.HTTPConnection):
    """Docker 데몬은 유닉스 소켓으로 HTTP를 받는다. 표준 라이브러리만으로 붙는다."""

    def __init__(self, socket_path: str):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(300)
        self.sock.connect(self.socket_path)


def docker_request(method: str, path: str, body=None):
    connection = DockerSocketConnection(DOCKER_SOCKET)
    try:
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def find_provisioner() -> str:
    query = quote(json.dumps({"label": ["com.docker.compose.service=" + PROVISIONER_SERVICE]}), safe="")
    try:
        status, payload = docker_request("GET", f"/containers/json?all=1&filters={query}")
    except (OSError, AttributeError) as error:
        raise ValueError(f"채점 시스템에 연결하지 못했습니다. Docker 스택이 실행 중인지 확인하세요. ({error})")
    if status != 200:
        raise ValueError(f"채점 시스템에 연결하지 못했습니다. (status {status})")
    containers = json.loads(payload)
    if not containers:
        raise ValueError("provisioner 컨테이너를 찾지 못했습니다.")
    return containers[0]["Id"]


def run_provisioner() -> str:
    """provisioner를 다시 돌리고 끝날 때까지 기다린다."""
    container = find_provisioner()
    status, payload = docker_request("POST", f"/containers/{container}/start")
    if status not in (204, 304):
        raise ValueError(f"provisioner를 실행하지 못했습니다. (status {status}): {payload.decode('utf-8', 'replace')[:200]}")

    deadline = time.time() + 600
    exit_code = None
    while time.time() < deadline:
        status, payload = docker_request("GET", f"/containers/{container}/json")
        if status != 200:
            raise ValueError(f"provisioner 상태를 읽지 못했습니다. (status {status})")
        state = json.loads(payload)["State"]
        if not state.get("Running"):
            exit_code = state.get("ExitCode")
            break
        time.sleep(1)
    if exit_code is None:
        raise ValueError("반영이 제한 시간 안에 끝나지 않았습니다.")

    status, payload = docker_request("GET", f"/containers/{container}/logs?stdout=1&stderr=1&tail=40")
    logs = payload.decode("utf-8", "replace") if status == 200 else ""
    logs = "".join(ch for ch in logs if ch == "\n" or ch >= " ")
    if exit_code != 0:
        raise ValueError("반영에 실패했습니다. 마지막 로그: " + logs.strip()[-400:])
    return "채점 시스템에 반영했습니다."


# ---- 데이터 생성기 ----

# 생성기 파일은 그 자체로 돌아가야 한다. 시드를 받아 난수를 고정하는 앞부분은 항상 같으므로
# 에디터가 붙였다 뗐다 한다. 출제자는 표시 아래 본문만 쓴다.
GEN_MARKER = "# ---- 여기부터 출제자가 쓴다 ----"
GEN_PROLOGUE = f"""\"\"\"시드 하나를 받아 입력 하나를 표준 출력으로 내보낸다.

같은 시드면 항상 같은 입력이 나와야 한다. 그래야 데이터를 언제든 다시 만들 수 있다.
\"\"\"

import random
import sys

random.seed(int(sys.argv[1]))

{GEN_MARKER}
"""

GEN_TEMPLATE = """n = random.randint(1, 100)

print(n)
print(" ".join(str(random.randint(1, 1000)) for _ in range(n)))
"""


def generator_body(package: Path) -> str:
    """화면에 보여 줄 본문. 앞부분은 감춘다."""
    script = generator_path(package)
    if not script.is_file():
        return GEN_TEMPLATE
    text = script.read_text(encoding="utf-8")
    if GEN_MARKER in text:
        return text.split(GEN_MARKER, 1)[1].lstrip(chr(10))
    return text


def write_generator(package: Path, body: str) -> None:
    write_text(generator_path(package), GEN_PROLOGUE + chr(10) + body.strip() + chr(10))


def generator_path(package: Path) -> Path:
    return package / "generators" / "gen.py"


def seed_log_path(package: Path) -> Path:
    """어떤 시드로 무엇을 만들었는지 적어 두는 기록."""
    return package / "generators" / "seeds.txt"


def generated_cases_path(package: Path) -> Path:
    """출제 화면에서 다시 보여 줄 생성 데이터 기록."""
    return package / "generators" / "generated-cases.json"


def generated_case_records(package: Path):
    path = generated_cases_path(package)
    if not path.is_file():
        return []
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return saved if isinstance(saved, list) else []


def generated_cases(package: Path):
    """생성기로 만들어 지금도 data/secret에 남아 있는 테스트케이스 기록."""
    return [
        record
        for record in generated_case_records(package)
        if (package / "data" / "secret" / f"{record.get('name')}.in").is_file()
    ]


def case_log_entry(record) -> dict:
    """기록에는 시드와 파일 이름만 남긴다. 입력·정답은 data/에 있고, 여기 또 넣으면 저장소가 수십 MB씩 커진다."""
    return {"seed": str(record.get("seed")), "name": str(record.get("name"))}


def replace_generated_case_records(package: Path, records) -> None:
    entries = [case_log_entry(record) for record in records]
    write_text(generated_cases_path(package), json.dumps(entries, ensure_ascii=False, indent=2))


def sync_seeds(package: Path, wanted) -> str:
    """시드 목록을 저장한다. 새 시드는 테스트케이스를 만들고, 빠진 시드의 테스트케이스는 지운다."""
    order = []
    for seed in wanted:
        if seed not in order:
            order.append(seed)
    current = generated_cases(package)
    keep, removed, seen = [], [], set()
    for record in current:
        seed = str(record.get("seed"))
        # 목록에서 빠진 시드와, 같은 시드로 두 번 만든 사본은 지운다. 같은 시드는 같은 입력이다.
        if seed in order and seed not in seen:
            keep.append(record)
            seen.add(seed)
        else:
            removed.append(record)
    for record in removed:
        for suffix in (".in", ".ans"):
            target = package / "data" / "secret" / f"{record.get('name')}{suffix}"
            if target.is_file():
                target.unlink()
    replace_generated_case_records(package, keep)
    existing = {str(record.get("seed")) for record in keep}
    added = [seed for seed in order if seed not in existing]
    if added:
        generate_from_seeds(package, "secret", added)
    parts = []
    if added:
        parts.append(f"테스트케이스 {len(added)}개를 만들었습니다")
    if removed:
        parts.append(f"{len(removed)}개를 지웠습니다")
    return (", ".join(parts) + ".") if parts else "바뀐 시드가 없습니다."


def save_generated_case_records(package: Path, records) -> None:
    replace_generated_case_records(package, generated_case_records(package) + list(records))


def legacy_generator_path(package: Path) -> Path:
    """예전 방식. 파이썬 스크립트가 데이터를 전부 직접 만든다."""
    return package / "generators" / "generate_tests.py"


def next_test_number(package: Path, group: str) -> int:
    folder = package / "data" / group
    numbers = [0]
    if folder.is_dir():
        for path in folder.glob("*.in"):
            if path.stem.isdigit():
                numbers.append(int(path.stem))
    return max(numbers) + 1


def answers_from_main(package: Path, inputs):
    """MAIN 정답 코드를 한 번 빌드해 입력마다 기대 출력을 만든다."""
    solution = main_solution_path(package)
    answers = []
    with tempfile.TemporaryDirectory() as directory:
        workdir = Path(directory)
        run_cmd, build_cmd = run_and_build(solution, workdir)
        if run_cmd is None:
            raise ValueError(f"{solution.name}은(는) 이 서버에서 실행할 수 없습니다. 실행할 수 있는 정답 코드를 MAIN으로 지정하세요.")
        if build_cmd:
            built = subprocess.run(
                build_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180
            )
            if built.returncode != 0:
                raise ValueError(f"{solution.name} 컴파일 에러: " + (built.stderr or built.stdout).strip()[-300:])
        for seed, input_text in inputs:
            answered = subprocess.run(
                run_cmd,
                input=input_text,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            if answered.returncode != 0:
                raise ValueError(f"시드 {seed}의 정답을 만들지 못했습니다: " + (answered.stderr or answered.stdout).strip()[-300:])
            answers.append(answered.stdout)
    return answers


def generate_integer_cases(package: Path, minimum, maximum, seeds):
    """시드마다 범위 안의 정수 한 개를 채점 데이터로 만든다."""
    try:
        minimum = int(minimum)
        maximum = int(maximum)
    except (TypeError, ValueError):
        raise ValueError("최솟값과 최댓값은 정수여야 합니다.")
    if minimum > maximum:
        raise ValueError("최솟값은 최댓값보다 클 수 없습니다.")

    number = next_test_number(package, "secret")
    inputs = []
    for seed in seeds:
        seed = str(seed).strip()
        if not seed:
            continue
        try:
            value = random.Random(int(seed)).randint(minimum, maximum)
        except ValueError:
            raise ValueError(f"시드는 정수여야 합니다: {seed}")
        input_text = f"{value}\n"
        inputs.append((seed, input_text))

    if not inputs:
        raise ValueError("시드를 한 줄에 하나씩 입력하세요.")

    pending = [
        (seed, input_text, answer_text)
        for (seed, input_text), answer_text in zip(inputs, answers_from_main(package, inputs))
    ]

    cases = []
    metadata = []
    for seed, input_text, answer_text in pending:
        write_text(package / "data" / "secret" / f"{number}.in", input_text)
        write_text(package / "data" / "secret" / f"{number}.ans", answer_text)
        cases.append({"seed": seed, "input": input_text, "answer": answer_text})
        metadata.append({"seed": seed, "name": str(number), "input": input_text, "answer": answer_text})
        number += 1
    save_generated_case_records(package, metadata)
    return {"cases": cases}


def generate_from_seeds(package: Path, group: str, seeds) -> str:
    """시드마다 생성기를 돌려 데이터를 덧붙인다. 정답은 MAIN 코드가 만든다."""
    # 생성기로 만든 데이터는 예제가 아니라 항상 채점 데이터다.
    group = "secret"
    script = generator_path(package)
    if not script.is_file():
        raise ValueError("생성기 코드를 먼저 저장하세요.")
    solution = main_solution_path(package)

    number = next_test_number(package, group)
    made = []
    records = []
    pending = []
    # MAIN이 파이썬이 아닐 수 있다. 한 번 빌드해 두고 시드마다 다시 쓴다.
    with tempfile.TemporaryDirectory() as directory:
        workdir = Path(directory)
        run_cmd, build_cmd = run_and_build(solution, workdir)
        if run_cmd is None:
            raise ValueError(f"{solution.name}은(는) 이 서버에서 실행할 수 없습니다. 실행할 수 있는 정답 코드를 MAIN으로 지정하세요.")
        if build_cmd:
            built = subprocess.run(
                build_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180
            )
            if built.returncode != 0:
                raise ValueError(f"{solution.name} 컴파일 에러: " + (built.stderr or built.stdout).strip()[-300:])

        for seed in seeds:
            generated = subprocess.run(
                [sys.executable, str(script), *seed.split()],
                cwd=str(package),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            if generated.returncode != 0:
                raise ValueError(f"시드 {seed}로 입력을 만들지 못했습니다: " + (generated.stderr or generated.stdout).strip()[-300:])
            answered = subprocess.run(
                run_cmd,
                input=generated.stdout,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            if answered.returncode != 0:
                raise ValueError(f"시드 {seed}의 정답을 만들지 못했습니다: " + (answered.stderr or answered.stdout).strip()[-300:])
            pending.append((seed, generated.stdout, answered.stdout))

        for seed, input_text, answer_text in pending:
            name = str(number)
            write_text(package / "data" / group / f"{name}.in", input_text)
            write_text(package / "data" / group / f"{name}.ans", answer_text)
            made.append(f"{group}/{name} (시드 {seed})")
            records.append({"seed": seed, "name": name, "input": input_text, "answer": answer_text})
            number += 1
    log = seed_log_path(package)
    previous = log.read_text(encoding="utf-8") if log.is_file() else ""
    write_text(log, previous + "\n".join(made) + "\n")
    save_generated_case_records(package, records)
    return f"테스트케이스 {len(made)}개를 만들었습니다."


def run_legacy_generator(package: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(legacy_generator_path(package))],
        cwd=str(package),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    if result.returncode != 0:
        raise ValueError("생성기 실행에 실패했습니다: " + (result.stderr or result.stdout).strip()[-400:])
    return "기존 생성기로 테스트케이스를 다시 만들었습니다."


# ---- 코드 검증: 올라간 코드를 모든 데이터에 돌려 본다 ----

# (대회, 라벨) -> 마지막 검증 결과. 리다이렉트 뒤에도 화면에 남기려고 들고 있는다.
LAST_VERIFY = {}


def run_and_build(path: Path, workdir: Path):
    """(실행 명령, 컴파일 명령). 이 컨테이너에서 못 돌리는 언어면 (None, None)."""
    suffix = path.suffix.lower()
    if suffix == ".py":
        return [sys.executable, str(path)], None
    if suffix in (".cpp", ".cc"):
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            return None, None
        binary = workdir / "program"
        return [str(binary)], [compiler, "-O2", "-std=c++17", "-o", str(binary), str(path)]
    if suffix == ".c":
        compiler = shutil.which("cc") or shutil.which("gcc")
        if not compiler:
            return None, None
        binary = workdir / "program"
        return [str(binary)], [compiler, "-O2", "-o", str(binary), str(path)]
    if suffix == ".java":
        javac, java = shutil.which("javac"), shutil.which("java")
        if not javac or not java:
            return None, None
        shutil.copy(path, workdir / path.name)
        return [java, "-cp", str(workdir), path.stem], [javac, "-d", str(workdir), str(workdir / path.name)]
    return None, None


def same_output(produced: str, expected: str) -> bool:
    """줄 끝 공백과 마지막 빈 줄은 무시한다."""
    left = [line.rstrip() for line in produced.replace("\r\n", "\n").rstrip("\n").split("\n")]
    right = [line.rstrip() for line in expected.replace("\r\n", "\n").rstrip("\n").split("\n")]
    return left == right


def all_tests(package: Path):
    tests = []
    for group in ("sample", "secret"):
        folder = package / "data" / group
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.in")):
            answer = path.with_suffix(".ans")
            if answer.is_file():
                tests.append((group, path.stem, path, answer))
    return tests


def verify_one(path: Path, tests, time_limit: float):
    """코드 하나를 모든 데이터에 돌린다. 실제 판정과 가장 느린 시간을 돌려준다."""
    with tempfile.TemporaryDirectory() as directory:
        workdir = Path(directory)
        run_cmd, build_cmd = run_and_build(path, workdir)
        if run_cmd is None:
            return {"verdict": "건너뜀", "detail": "이 서버에 실행 환경이 없습니다", "slowest": 0.0}
        if build_cmd:
            built = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
            if built.returncode != 0:
                message = (built.stderr or built.stdout).strip()
                last = message.splitlines()[-1][:120] if message else "컴파일 에러"
                return {"verdict": "CE", "detail": last, "slowest": 0.0}

        hard_limit = max(time_limit * 6, 10)
        slowest = 0.0
        for group, name, input_path, answer_path in tests:
            started = time.monotonic()
            try:
                result = subprocess.run(
                    run_cmd,
                    input=input_path.read_text(encoding="utf-8"),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=hard_limit,
                    cwd=str(workdir),
                )
            except subprocess.TimeoutExpired:
                return {"verdict": "TLE", "detail": f"{group}/{name}에서 끝나지 않음", "slowest": hard_limit}
            elapsed = time.monotonic() - started
            slowest = max(slowest, elapsed)
            if result.returncode != 0:
                return {"verdict": "RE", "detail": f"{group}/{name}에서 런타임 에러", "slowest": slowest}
            if elapsed > time_limit:
                return {"verdict": "TLE", "detail": f"{group}/{name}에서 {elapsed:.2f}초", "slowest": slowest}
            if not same_output(result.stdout, answer_path.read_text(encoding="utf-8")):
                return {"verdict": "WA", "detail": f"{group}/{name}에서 출력이 다름", "slowest": slowest}
        return {"verdict": "AC", "detail": "모든 테스트케이스 통과", "slowest": slowest}


def verify_package(package: Path):
    tests = all_tests(package)
    if not tests:
        raise ValueError("테스트케이스가 없습니다. 테스트케이스를 먼저 만드세요.")
    time_limit = problem_meta(package)["time_limit"]
    rows = []
    for folder, expected, verdict_text in SUBMISSION_LABELS:
        directory = package / "submissions" / folder
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.name == ".gitkeep":
                continue
            outcome = verify_one(path, tests, time_limit)
            rows.append(
                {
                    "order": len(rows) + 1,
                    "file": path.name,
                    "expected": expected,
                    "expected_text": verdict_text,
                    "actual": outcome["verdict"],
                    "detail": outcome["detail"],
                    "slowest": outcome["slowest"],
                    "ok": outcome["verdict"] == expected,
                    "skipped": outcome["verdict"] == "건너뜀",
                }
            )
    if not rows:
        raise ValueError("올라간 코드가 없습니다.")
    return {"tests": len(tests), "time_limit": pretty_seconds(time_limit), "rows": rows, "at": time.strftime("%H:%M:%S")}


# ---- 지문: 본문만 편집하고 HTML은 여기서 만든다 ----
#
# 입력은 짧은 표기법만 쓴다. 나머지 문자는 전부 이스케이프하므로 태그를 넣어도 지문이 깨지지 않는다.
#   `N`              -> <code>N</code>       코드, 변수, 값
#   $N$              -> <var>N</var>         수식 기호
#   **굵게**          -> <strong>굵게</strong>
#   *기울임*          -> <em>기울임</em>
#   ![설명](그림.png)  -> <img>                problem_statement/images/ 에 올린 그림


def inline_image(package: Path, name: str, alt: str) -> str:
    """그림은 지문 안에 그대로 박아 넣는다. 채점 시스템은 HTML 한 장만 가져가기 때문이다."""
    source = image_dir(package) / name
    if not source.is_file():
        return f'<span class="missing-image">그림 없음: {html.escape(name)}</span>'
    kind = mimetypes.guess_type(name)[0] or "image/png"
    encoded = base64.b64encode(source.read_bytes()).decode("ascii")
    return (
        f'<img src="data:{kind};base64,{encoded}" alt="{html.escape(alt, quote=True)}"'
        f' data-name="{html.escape(name, quote=True)}">'
    )


def markup_to_html(text: str, package: Path = None) -> str:
    escaped = html.escape(text, quote=False)
    if package is not None:
        escaped = IMAGE_MARKUP.sub(lambda m: inline_image(package, m.group(2), m.group(1)), escaped)
    escaped = re.sub(r"`([^`\n]+)`", lambda m: "<code>" + m.group(1) + "</code>", escaped)
    escaped = re.sub(r"\$([^$\n]+)\$", lambda m: "<var>" + m.group(1) + "</var>", escaped)
    escaped = re.sub(r"\*\*([^*\n]+)\*\*", lambda m: "<strong>" + m.group(1) + "</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", lambda m: "<em>" + m.group(1) + "</em>", escaped)
    return escaped


def html_to_markup(fragment: str) -> str:
    text = fragment
    text = re.sub(
        r'<img[^>]*?alt="([^"]*)"[^>]*?data-name="([^"]+)"[^>]*?>',
        lambda m: f"![{m.group(1)}]({m.group(2)})",
        text,
    )
    text = re.sub(r"<code>(.*?)</code>", lambda m: "`" + m.group(1) + "`", text, flags=re.S)
    text = re.sub(r"<var>(.*?)</var>", lambda m: "$" + m.group(1) + "$", text, flags=re.S)
    text = re.sub(r"<strong>(.*?)</strong>", lambda m: "**" + m.group(1) + "**", text, flags=re.S)
    text = re.sub(r"<b>(.*?)</b>", lambda m: "**" + m.group(1) + "**", text, flags=re.S)
    text = re.sub(r"<em>(.*?)</em>", lambda m: "*" + m.group(1) + "*", text, flags=re.S)
    text = re.sub(r"<i>(.*?)</i>", lambda m: "*" + m.group(1) + "*", text, flags=re.S)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    return html.unescape(text)


def section_body(statement: str, key: str) -> str:
    pattern = re.compile(
        '<section aria-labelledby="' + key + '-heading">\\s*<h2[^>]*>.*?</h2>(.*?)</section>',
        re.S,
    )
    found = pattern.search(statement)
    return found.group(1).strip() if found else ""


def paragraphs_to_text(fragment: str) -> str:
    parts = re.findall(r"<p>(.*?)</p>", fragment, re.S)
    if not parts:
        parts = [fragment]
    return "\n\n".join(html_to_markup(part).strip() for part in parts if part.strip())


def text_to_paragraphs(text: str, package: Path) -> str:
    blocks = [block.strip() for block in PARAGRAPH_SPLIT.split(text.strip()) if block.strip()]
    if not blocks:
        blocks = ["내용을 작성한다."]
    return "\n".join(
        "    <p>" + markup_to_html(block.replace("\n", " "), package) + "</p>" for block in blocks
    )


def limits_text(statement: str) -> str:
    items = re.findall(r"<li>(.*?)</li>", section_body(statement, "limits"), re.S)
    return "\n".join(html_to_markup(item).strip() for item in items)


def limits_to_html(text: str, package: Path) -> str:
    items = [line.strip() for line in text.splitlines() if line.strip()]
    if not items:
        items = ["제한을 작성한다."]
    return "\n".join("      <li>" + markup_to_html(item, package) + "</li>" for item in items)


def sample_section(package: Path) -> str:
    """예제는 data/sample 파일에서 만든다. 지문과 데이터가 어긋날 수 없다."""
    folder = package / "data" / "sample"
    blocks = []
    if folder.is_dir():
        for index, path in enumerate(sorted(folder.glob("*.in")), start=1):
            answer = path.with_suffix(".ans")
            if not answer.is_file():
                continue
            blocks.append(
                '    <div class="sample-card">\n'
                '      <div class="sample-pane">\n'
                '        <div class="sample-label">예제 입력 ' + str(index) + "</div>\n"
                "        <pre data-sample-input>"
                + html.escape(path.read_text(encoding="utf-8").rstrip("\n"))
                + "</pre>\n"
                "      </div>\n"
                '      <div class="sample-pane">\n'
                '        <div class="sample-label">예제 출력 ' + str(index) + "</div>\n"
                "        <pre data-sample-output>"
                + html.escape(answer.read_text(encoding="utf-8").rstrip("\n"))
                + "</pre>\n"
                "      </div>\n"
                "    </div>"
            )
    if not blocks:
        return ""
    return (
        '\n  <section aria-labelledby="sample-heading">\n'
        '    <h2 id="sample-heading">예제</h2>\n' + "\n".join(blocks) + "\n  </section>\n"
    )


def build_statement(package: Path, label: str, fields) -> str:
    contest_name = new_problem.contest_name_of(package.parent)
    meta = problem_meta(package)
    return (
        '<article class="problem-statement" aria-labelledby="problem-title">\n'
        '  <header class="problem-header">\n'
        '    <p class="problem-eyebrow">' + html.escape(contest_name) + " · " + html.escape(label) + "</p>\n"
        '    <h1 id="problem-title">' + html.escape(meta["name"]) + "</h1>\n"
        '    <dl class="problem-limits" aria-label="문제 제한">\n'
        "      <div><dt>시간 제한</dt><dd>" + f"{pretty_seconds(meta['time_limit'])}초" + "</dd></div>\n"
        "      <div><dt>메모리 제한</dt><dd>" + f"{meta['memory']} MB" + "</dd></div>\n"
        "    </dl>\n"
        "  </header>\n\n"
        '  <section aria-labelledby="description-heading">\n'
        '    <h2 id="description-heading">문제</h2>\n' + text_to_paragraphs(fields["description"], package) + "\n"
        "  </section>\n\n"
        '  <section aria-labelledby="input-heading">\n'
        '    <h2 id="input-heading">입력</h2>\n' + text_to_paragraphs(fields["input"], package) + "\n"
        "  </section>\n\n"
        '  <section aria-labelledby="output-heading">\n'
        '    <h2 id="output-heading">출력</h2>\n' + text_to_paragraphs(fields["output"], package) + "\n"
        "  </section>\n\n"
        '  <section aria-labelledby="limits-heading">\n'
        '    <h2 id="limits-heading">제한</h2>\n'
        '    <ul class="constraint-list">\n' + limits_to_html(fields["limits"], package) + "\n    </ul>\n"
        "  </section>\n" + sample_section(package) + "</article>\n"
    )


def statement_fields(package: Path):
    statement = statement_path(package).read_text(encoding="utf-8")
    return {
        "description": paragraphs_to_text(section_body(statement, "description")),
        "input": paragraphs_to_text(section_body(statement, "input")),
        "output": paragraphs_to_text(section_body(statement, "output")),
        "limits": limits_text(statement),
    }


def rebuild_statement(package: Path) -> None:
    """데이터나 제한이 바뀌면 지문도 다시 만든다."""
    if statement_path(package).is_file():
        write_text(statement_path(package), build_statement(package, package.name, statement_fields(package)))


PREVIEW_STYLE = """
 body { font-family: system-ui, -apple-system, "Malgun Gothic", sans-serif; color: #1b1f24; margin: 0; padding: 1.4rem 1.6rem 2rem; line-height: 1.7; }
 .problem-eyebrow { color: #1b4dbb; font-size: .74rem; font-weight: 800; letter-spacing: .09em; margin: 0 0 .4rem; }
 h1 { font-size: 1.45rem; font-weight: 800; letter-spacing: -.035em; margin: 0 0 1rem; }
 h2 { font-size: 1rem; font-weight: 750; border-bottom: 2px solid #1b4dbb; padding-bottom: .3rem; margin: 1.6rem 0 .6rem; }
 p { margin: .5rem 0; }
 .problem-limits { display: grid; grid-template-columns: repeat(2, minmax(0, 150px)); border-top: 1px solid #e2e7ee; border-bottom: 1px solid #e2e7ee; margin: 0; }
 .problem-limits div { padding: .45rem .7rem; border-right: 1px solid #e2e7ee; }
 .problem-limits div:last-child { border-right: 0; }
 .problem-limits dt { color: #6b7480; font-size: .7rem; font-weight: 700; }
 .problem-limits dd { margin: .1rem 0 0; font-weight: 700; font-size: .88rem; }
 code, var { background: #eef1f5; border-radius: 4px; padding: .05rem .3rem; font-size: .9em; font-style: normal; }
 ul { padding-left: 1.2rem; }
 img { max-width: 100%; display: block; margin: .8rem auto; }
 .missing-image { color: #b3261e; font-weight: 700; }
 .sample-card { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; margin-bottom: .8rem; }
 .sample-label { font-weight: 700; font-size: .8rem; margin-bottom: .3rem; color: #4b5563; }
 pre { background: #f6f8fa; border: 1px solid #e2e7ee; border-radius: 6px; padding: .7rem; margin: 0; font-size: .82rem; overflow: auto; }
"""


def preview_document(package: Path) -> str:
    """로그인된 편집 화면 안에서 그대로 보여 줄 독립 미리보기 문서."""
    return (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        "<style>" + PREVIEW_STYLE + "</style></head><body>"
        + statement_path(package).read_text(encoding="utf-8")
        + "</body></html>"
    )

PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="icon" href="data:,">
<style>
 :root {{
   --ink:#171a1f; --muted:#6b7480; --line:#e4e8ee; --bg:#f6f7f9; --panel:#fff;
   --accent:#1b4dbb; --accent-dark:#143a90; --soft:#eaf0fd; --ok:#0f7a43; --warn:#b3261e;
 }}
 * {{ box-sizing:border-box; }}
 body {{ margin:0; background:var(--bg); color:var(--ink); line-height:1.65;
   font-family:system-ui,-apple-system,"Malgun Gothic",sans-serif; }}
 a {{ color:var(--accent); }}
 .bar {{ background:var(--panel); border-bottom:1px solid var(--line); position:sticky; top:0; z-index:20; }}
 .bar-in {{ max-width:1240px; margin:0 auto; padding:.75rem 1.25rem; display:flex; align-items:center; gap:1.25rem; }}
 .bar-in .brand {{ font-weight:800; letter-spacing:-.02em; font-size:1rem; text-decoration:none; color:var(--ink); }}
 .bar-in nav a {{ font-size:.88rem; font-weight:600; color:var(--muted); text-decoration:none; margin-right:1rem; }}
 .bar-in nav a:hover {{ color:var(--accent); }}
 .bar-in .right {{ margin-left:auto; display:flex; gap:.6rem; align-items:center; }}
 .wrap {{ max-width:1240px; margin:0 auto; padding:1.75rem 1.25rem 4rem; }}
 h1 {{ font-size:1.6rem; font-weight:800; letter-spacing:-.035em; margin:0 0 .3rem; }}
 h2 {{ font-size:1.02rem; font-weight:750; letter-spacing:-.02em; margin:0; }}
 .sub {{ color:var(--muted); font-size:.9rem; margin:0 0 1.5rem; }}
 .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:1.3rem 1.45rem; margin-bottom:1.15rem; }}
 .panel > header {{ display:flex; align-items:baseline; gap:.7rem; margin-bottom:1rem; }}
 .panel > header .hint {{ color:var(--muted); font-size:.84rem; }}
 .hint {{ color:var(--muted); font-size:.84rem; }}
 table {{ border-collapse:collapse; width:100%; font-size:.92rem; }}
 th {{ text-align:left; font-size:.76rem; font-weight:700; color:var(--muted); padding:.45rem .7rem; border-bottom:2px solid var(--line); }}
 td {{ padding:.6rem .7rem; border-bottom:1px solid var(--line); vertical-align:top; }}
 tr:last-child td {{ border-bottom:0; }}
 .empty {{ color:var(--muted); font-size:.89rem; padding:1rem .7rem; }}
 label {{ display:block; font-size:.8rem; font-weight:700; color:#39414c; margin-bottom:.3rem; }}
 input, select, textarea {{ width:100%; padding:.5rem .6rem; border:1px solid var(--line); border-radius:8px;
   font-family:inherit; font-size:.92rem; background:#fff; color:inherit; }}
 textarea {{ font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:.85rem; line-height:1.55; resize:vertical; }}
 input:focus, select:focus, textarea:focus {{ outline:0; border-color:var(--accent); box-shadow:0 0 0 3px rgba(27,77,187,.12); }}
 .field {{ margin-bottom:.85rem; }}
 .fields {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.85rem; align-items:end; }}
 .two {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }}
 .editor-grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:1.15rem; align-items:start; }}
 .sticky {{ position:sticky; top:4.2rem; }}
 .btn {{ display:inline-block; background:var(--accent); color:#fff; border:0; border-radius:8px;
   padding:.55rem 1.15rem; font:inherit; font-weight:700; font-size:.89rem; cursor:pointer; width:auto;
   text-decoration:none; }}
 .btn:hover {{ background:var(--accent-dark); color:#fff; }}
 .btn-ghost {{ background:#fff; color:var(--muted); border:1px solid var(--line); }}
 .btn-ghost:hover {{ background:#fff; color:var(--accent); border-color:var(--accent); }}
 .btn-danger:hover {{ color:var(--warn); border-color:#e6bcb7; }}
 .btn-row {{ display:flex; gap:.6rem; align-items:center; margin-top:.9rem; flex-wrap:wrap; }}
 .tag {{ display:inline-block; font-size:.73rem; font-weight:700; padding:.12rem .55rem; border-radius:999px; background:var(--soft); color:var(--accent); white-space:nowrap; }}
 .tag-grey {{ background:#f0f2f5; color:var(--muted); }}
 .tag-main {{ background:#173a7a; color:#fff; }}
 .tag-warn {{ background:#fdeceb; color:var(--warn); }}
 .tag-ok {{ background:#e8f6ee; color:var(--ok); }}
 .flash {{ border-radius:10px; padding:.7rem 1rem; margin-bottom:1.2rem; font-size:.91rem; font-weight:600; }}
 .flash-ok {{ background:#e8f6ee; color:var(--ok); }}
 .flash-err {{ background:#fdeceb; color:var(--warn); }}
 .checklist {{ display:flex; flex-wrap:wrap; gap:.5rem; margin:.6rem 0 1.3rem; padding:0; list-style:none; }}
 .checklist li {{ font-size:.82rem; font-weight:600; padding:.25rem .7rem; border-radius:999px; border:1px solid var(--line); color:var(--muted); background:#fff; }}
 .checklist li.done {{ color:var(--ok); border-color:#bfe3cd; background:#f2fbf6; }}
 .checklist li.todo {{ color:var(--warn); border-color:#f0cbc7; background:#fdf5f4; }}
 iframe {{ width:100%; height:660px; border:1px solid var(--line); border-radius:10px; background:#fff; display:block; }}
 pre.peek {{ background:#f6f8fa; border:1px solid var(--line); border-radius:6px; padding:.45rem .6rem;
   font-size:.75rem; max-height:6.5rem; overflow:auto; margin:.35rem 0 0; white-space:pre-wrap; word-break:break-all; }}
 label.sample-toggle {{ display:flex; gap:.35rem; align-items:center; margin:0; font-weight:600; font-size:.85rem; cursor:pointer; white-space:nowrap; }}
 label.sample-toggle input {{ width:auto; margin:0; }}
 form.data-add {{ margin:0 0 1.4rem; padding:0 0 1.4rem; border-bottom:1px solid var(--line); }}
 code {{ background:#eef1f5; border-radius:4px; padding:.05rem .3rem; font-size:.88em; }}
 @media (max-width:900px) {{ .editor-grid {{ grid-template-columns:1fr; }} .sticky {{ position:static; }}
   .two {{ grid-template-columns:1fr; }} }}
</style></head><body>
<div class="bar"><div class="bar-in">
  <a class="brand" href="{home}">문제 만들기</a>
  <nav><a href="{home}">문제 목록</a><a href="/jury">채점 시스템</a></nav>
  <div class="right">{barright}</div>
</div></div>
<div class="wrap">{body}</div>
<script>
(function () {{
  var names = {languages};
  document.querySelectorAll("[data-language-for]").forEach(function (select) {{
    var target = document.getElementById(select.getAttribute("data-language-for"));
    if (!target) return;
    select.addEventListener("change", function () {{
      if (names[select.value]) target.value = names[select.value];
    }});
  }});
}})();
</script>
</body></html>"""

LANGUAGE_FILENAMES = json.dumps(DEFAULT_FILENAME)


# ---- 참가자 이름: 처음 로그인한 참가자가 스코어보드에 보일 이름을 정한다 ----
#
# 로그인 아이디(user_001)와 화면에 보이는 이름(팀 display_name)은 따로 저장된다.
# DOMjudge 9.0에는 팀 이름을 고치는 API가 없어서, provisioner와 같은 팀 가져오기로 덮어쓴다.
# 어느 팀인지는 요청 본문이 아니라 DOMjudge 로그인 세션으로만 정한다.

NICKNAME_PATH = "/participant/nickname"
NICKNAME_MAX_LENGTH = 20
NICKNAME_PENDING_GROUP = "pending"
NICKNAME_VISIBLE_GROUP = "participants"
# 이름을 정하면 숨긴 분류에서 순위표에 보이는 분류로 옮긴다. 대회 참가자와 공개 대회 게스트가 따로 있다.
GUEST_PENDING_GROUP = "guest-pending"
GUEST_VISIBLE_GROUP = "guests"
NICKNAME_PROMOTIONS = {NICKNAME_PENDING_GROUP: NICKNAME_VISIBLE_GROUP, GUEST_PENDING_GROUP: GUEST_VISIBLE_GROUP}
DOMJUDGE_URL = os.environ.get("DOMJUDGE_URL", "http://domserver").rstrip("/")
DOMJUDGE_ADMIN_PASSWORD_FILE = Path(
    os.environ.get("DOMJUDGE_ADMIN_PASSWORD_FILE", "/domjudge-etc/initial_admin_password.secret")
)
_nickname_lock = __import__("threading").Lock()


class NicknameError(ValueError):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def domjudge_request(method: str, path: str, cookie: str | None = None, upload=None):
    """DOMjudge API를 부른다. cookie가 있으면 그 참가자로, 없으면 관리자로 부른다."""
    import urllib.error
    import urllib.request

    headers = {"Accept": "application/json"}
    data = None
    if cookie is not None:
        headers["Cookie"] = cookie
    else:
        password = DOMJUDGE_ADMIN_PASSWORD_FILE.read_text(encoding="utf-8").strip()
        headers["Authorization"] = "Basic " + base64.b64encode(f"admin:{password}".encode()).decode()
    if upload is not None:
        boundary = "nickname" + "".join(random.choice("0123456789abcdef") for _ in range(24))
        payload = json.dumps(upload, ensure_ascii=False).encode("utf-8")
        data = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"json\"; filename=\"teams.json\"\r\n"
            "Content-Type: application/json\r\n\r\n"
        ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    request = urllib.request.Request(DOMJUDGE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, body = error.code, error.read()
    try:
        return status, json.loads(body.decode("utf-8") or "null")
    except ValueError:
        return status, body.decode("utf-8", "replace")


def nickname_team(cookie: str) -> dict | None:
    """로그인한 계정의 팀을 돌려준다. 팀이 없는 계정(운영자)은 None."""
    if not cookie:
        raise NicknameError(401, "로그인이 필요합니다.")
    status, user = domjudge_request("GET", "/api/v4/user", cookie=cookie)
    if status != 200 or not isinstance(user, dict):
        raise NicknameError(401, "로그인이 필요합니다.")
    team_id = user.get("team_id")
    if "team" not in (user.get("roles") or []) or not team_id:
        return None
    status, team = domjudge_request("GET", f"/api/v4/teams/{quote(str(team_id), safe='')}")
    if status != 200 or not isinstance(team, dict):
        raise NicknameError(502, "팀 정보를 불러오지 못했습니다. 운영진에게 알려 주세요.")
    return team


def nickname_state(cookie: str) -> dict:
    team = nickname_team(cookie)
    name = ((team or {}).get("display_name") or "").strip()
    guest = GUEST_VISIBLE_GROUP in ((team or {}).get("group_ids") or [])
    return {"needs_nickname": team is not None and not name, "display_name": name, "guest": guest}


def clean_nickname(raw) -> str:
    name = " ".join(str(raw or "").split(" ")).strip()
    if not name:
        raise NicknameError(400, "이름을 입력하세요.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise NicknameError(400, "이름에는 줄바꿈이나 탭을 넣을 수 없습니다.")
    if len(name) > NICKNAME_MAX_LENGTH:
        raise NicknameError(400, f"이름은 {NICKNAME_MAX_LENGTH}자 이하로 정하세요.")
    return name


def set_nickname(cookie: str, raw) -> str:
    name = clean_nickname(raw)
    with _nickname_lock:
        team = nickname_team(cookie)
        if team is None:
            raise NicknameError(403, "참가자 계정만 이름을 정할 수 있습니다.")
        if (team.get("display_name") or "").strip():
            raise NicknameError(409, "이미 이름을 정했습니다. 바꾸려면 운영진에게 말해 주세요.")
        status, teams = domjudge_request("GET", "/api/v4/teams")
        if status != 200 or not isinstance(teams, list):
            raise NicknameError(502, "팀 목록을 불러오지 못했습니다. 잠시 후 다시 시도하세요.")
        wanted = name.casefold()
        for other in teams:
            if other.get("id") == team["id"]:
                continue
            taken = {(other.get(key) or "").strip().casefold() for key in ("display_name", "name")}
            if wanted in taken:
                raise NicknameError(409, "다른 참가자가 쓰는 이름입니다. 다른 이름을 정하세요.")
        updated = {
            "id": team["id"],
            "name": team["name"],
            "display_name": name,
            # 이름을 정하기 전에는 순위표에서 숨긴 분류에 있다. 이름을 정하면 보이는 분류로 옮긴다.
            "group_ids": [NICKNAME_PROMOTIONS.get(group, group) for group in team.get("group_ids") or []],
        }
        status, _ = domjudge_request("POST", "/api/v4/users/teams", upload=[updated])
        if status != 200:
            raise NicknameError(502, "이름을 저장하지 못했습니다. 잠시 후 다시 시도하세요.")
    return name


# ---- 공개 대회 게스트 ----
# 공개 대회에는 로그인 화면이 없다. nginx가 로그인 화면(GET /login) 요청을 여기로 보낸다.
# 처음 온 브라우저에는 게스트 계정을 하나 만들고, 서버가 그 계정으로 DOMjudge에 대신 로그인해
# 세션 쿠키를 넘겨준 뒤 바로 대회 화면으로 보낸다. 계정은 브라우저 쿠키에 남아 다음에도 같은 계정으로 들어간다.
# 사람마다 계정이 따로라 다른 사람의 제출이나 코드는 보이지 않는다.
# 운영진과 KAUPC 계정은 /login?account=1 의 원래 로그인 화면을 쓴다.
GUEST_ENTER_PATH = "/participant/enter"
GUEST_COOKIE = "kaupc_guest"
GUEST_COOKIE_MAX_AGE = 30 * 24 * 3600
GUEST_TRIES_COOKIE = "kaupc_enter"
ACCOUNT_LOGIN_PATH = "/login?account=1"
GUEST_CREDENTIAL = re.compile(r"^(guest_[a-z0-9]{6,32}):([A-Za-z0-9]{16,64})$")
GUEST_ENABLED = os.environ.get("GUEST_SIGNUP", "1").strip().lower() not in ("0", "false", "no", "off", "")
GUEST_PER_CLIENT_PER_HOUR = int(os.environ.get("GUEST_PER_CLIENT_PER_HOUR", "30"))
GUEST_TOTAL_PER_HOUR = int(os.environ.get("GUEST_TOTAL_PER_HOUR", "300"))
_guest_lock = __import__("threading").Lock()
_guest_history: list[tuple[float, str]] = []


def _random_token(length: int, alphabet: str) -> str:
    chooser = random.SystemRandom()
    return "".join(chooser.choice(alphabet) for _ in range(length))


def guest_allowed(client: str, now: float | None = None) -> bool:
    """한 사람이 계정을 마구 만들지 못하게 한 시간 안의 생성 수를 센다. 허용하면 기록까지 남긴다."""
    now = time.time() if now is None else now
    with _guest_lock:
        _guest_history[:] = [(at, who) for at, who in _guest_history if now - at < 3600]
        if len(_guest_history) >= GUEST_TOTAL_PER_HOUR:
            return False
        if sum(1 for _, who in _guest_history if who == client) >= GUEST_PER_CLIENT_PER_HOUR:
            return False
        _guest_history.append((now, client))
        return True


def create_guest(client: str) -> dict:
    if not GUEST_ENABLED:
        raise NicknameError(403, "게스트 참가가 꺼져 있습니다.")
    if not guest_allowed(client):
        raise NicknameError(429, "게스트 계정을 너무 많이 만들었습니다. 잠시 후 다시 시도하세요.")
    username = "guest_" + _random_token(10, "abcdefghijkmnpqrstuvwxyz23456789")
    password = _random_token(24, "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789")
    # 이름을 묻지 않는다. 순위표와 채점 현황에는 "게스트 xxxxxx"로 보인다.
    team = {"id": username, "name": username, "display_name": "게스트 " + username[len("guest_"):][:6],
            "group_ids": [GUEST_VISIBLE_GROUP]}
    status, _ = domjudge_request("POST", "/api/v4/users/teams", upload=[team])
    if status != 200:
        raise NicknameError(502, "게스트 계정을 만들지 못했습니다. 잠시 후 다시 시도하세요.")
    account = {"id": username, "username": username, "password": password, "type": "team",
               "team_id": username, "name": username}
    status, _ = domjudge_request("POST", "/api/v4/users/accounts", upload=[account])
    if status != 200:
        raise NicknameError(502, "게스트 계정을 만들지 못했습니다. 잠시 후 다시 시도하세요.")
    return {"username": username, "password": password}


def domjudge_login(username: str, password: str):
    """DOMjudge 로그인 폼을 서버에서 대신 제출한다. 성공하면 브라우저에 넘길 Set-Cookie 값들을, 실패하면 None을 돌려준다."""
    from urllib.parse import urlencode

    target = urlparse(DOMJUDGE_URL)
    connection_class = http.client.HTTPSConnection if target.scheme == "https" else http.client.HTTPConnection

    def call(method: str, body: str | None = None, cookie: str = ""):
        connection = connection_class(target.netloc, timeout=10)
        headers = {"Cookie": cookie} if cookie else {}
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            # nginx는 ?account=1이 없는 GET /login을 다시 여기로 보낸다. 원래 로그인 화면을 받으려고 붙인다.
            connection.request(method, ACCOUNT_LOGIN_PATH, body=body, headers=headers)
            response = connection.getresponse()
            page = response.read().decode("utf-8", "replace")
            return response.status, response.getheader("Location", ""), page, response.headers.get_all("Set-Cookie") or []
        finally:
            connection.close()

    status, _, page, first_cookies = call("GET")
    field = re.search(r"<input[^>]*name=\"_csrf_token\"[^>]*>", page)
    token = re.search(r"value=\"([^\"]*)\"", field.group(0)) if field else None
    if status != 200 or not token:
        raise NicknameError(502, "채점 서버에 연결하지 못했습니다. 잠시 후 다시 시도하세요.")
    session = "; ".join(cookie.split(";", 1)[0] for cookie in first_cookies)
    form = urlencode({"_username": username, "_password": password, "_csrf_token": html.unescape(token.group(1))})
    status, location, _, cookies = call("POST", form, session)
    if status not in (301, 302, 303) or urlparse(location).path == "/login":
        return None
    return [re.sub(r";\s*domain=[^;]*", "", cookie, flags=re.I) for cookie in (cookies or first_cookies)]


def enter_as_guest(remembered: str, client: str):
    """(브라우저에 넘길 Set-Cookie 값들, 기억할 게스트 계정)을 돌려준다."""
    match = GUEST_CREDENTIAL.match(remembered or "")
    if match:
        cookies = domjudge_login(match.group(1), match.group(2))
        if cookies is not None:
            return cookies, remembered
    # 처음 왔거나 기억한 계정이 지워졌다. 새로 만든다.
    guest = create_guest(client)
    cookies = domjudge_login(guest["username"], guest["password"])
    if cookies is None:
        raise NicknameError(502, "게스트 계정으로 들어가지 못했습니다. 잠시 후 다시 시도하세요.")
    return cookies, f"{guest['username']}:{guest['password']}"


# ---- 채점 현황(모든 제출 공개) ----
# 운영자 화면의 제출 목록을 참가자에게도 보여 준다. 공개 대회의 제출만, 순위표에 보이는 팀의 것만 보인다.
# 제출을 열면 코드, 컴파일 결과, 실행한 테스트의 입력·정답·프로그램 출력이 보인다. 관리자 API에 없는 값은 DB에서 읽는다.
PUBLIC_SUBMISSIONS_PATH = "/participant/submissions"
PUBLIC_SUBMISSIONS_CONTEST = os.environ.get("PUBLIC_SUBMISSIONS_CONTEST", "kaupcopen")
PUBLIC_SUBMISSIONS_LIMIT = 500
PUBLIC_SUBMISSIONS_CACHE_SECONDS = 5
_status_lock = __import__("threading").Lock()
_status_cache: dict = {"at": 0.0, "value": None}
_submission_details: dict = {}
SUBMISSION_DETAILS_KEPT = 200
# 화면에는 앞부분만 보이고, 전체는 내려받는다. 입력이 9MB인 테스트도 있다.
RUN_TEXT_LIMIT = 64 * 1024
RUN_COLUMNS = {"input": "tc.input", "answer": "tc.output", "output": "o.output_run", "diff": "o.output_diff", "error": "o.output_error"}
RUN_FILES = ("input", "answer", "output")
RUN_FROM = (
    " FROM judging j JOIN judging_run jr ON jr.judgingid = j.judgingid"
    " JOIN testcase t ON t.testcaseid = jr.testcaseid"
    " JOIN testcase_content tc ON tc.testcaseid = t.testcaseid"
    " LEFT JOIN judging_run_output o ON o.runid = jr.runid"
    " WHERE j.submitid = %s AND j.valid = 1 AND t.ranknumber = %s AND jr.runresult IS NOT NULL"
    " ORDER BY j.judgingid DESC LIMIT 1"
)


def _api_list(path: str) -> list:
    status, value = domjudge_request("GET", path)
    if status != 200 or not isinstance(value, list):
        raise NicknameError(502, "채점 현황을 불러오지 못했습니다. 잠시 후 다시 시도하세요.")
    return value


def public_submissions() -> dict:
    contest = quote(PUBLIC_SUBMISSIONS_CONTEST, safe="")
    base = f"/api/v4/contests/{contest}"
    hidden_groups = {group["id"] for group in _api_list(f"{base}/groups") if group.get("hidden")}
    teams = {
        team["id"]: (team.get("display_name") or team.get("name") or team["id"])
        for team in _api_list(f"{base}/teams")
        if not hidden_groups.intersection(team.get("group_ids") or []) and not team.get("hidden")
    }
    problems = {problem["id"]: problem for problem in _api_list(f"{base}/problems")}
    languages = {language["id"]: language.get("name") or language["id"] for language in _api_list(f"{base}/languages")}
    verdicts = {}
    for judgement in _api_list(f"{base}/judgements"):
        if judgement.get("valid") is False:
            continue
        current = verdicts.get(judgement["submission_id"])
        if current is None or str(judgement.get("start_time") or "") >= str(current.get("start_time") or ""):
            verdicts[judgement["submission_id"]] = judgement
    # 운영자 제출 목록처럼 목록에서 테스트별 결과를 바로 보인다.
    cases: dict = {}
    for run in sorted(_api_list(f"{base}/runs"), key=lambda run: run.get("ordinal") or 0):
        cases.setdefault(run.get("judgement_id"), []).append(run.get("judgement_type_id"))
    rows = []
    for submission in _api_list(f"{base}/submissions"):
        if submission.get("team_id") not in teams:
            continue
        problem = problems.get(submission.get("problem_id")) or {}
        judgement = verdicts.get(submission["id"]) or {}
        rows.append({
            "id": submission["id"],
            "time": submission.get("time"),
            "team": teams[submission["team_id"]],
            "problem": problem.get("label") or submission.get("problem_id"),
            "problem_name": problem.get("name") or "",
            "language": languages.get(submission.get("language_id"), submission.get("language_id")),
            "verdict": judgement.get("judgement_type_id"),
            "runtime": judgement.get("max_run_time"),
            "tests": problem.get("test_data_count"),
            "cases": cases.get(judgement.get("id"), []),
        })
    rows.sort(key=lambda row: str(row["time"] or ""), reverse=True)
    return {"contest": PUBLIC_SUBMISSIONS_CONTEST, "submissions": rows[:PUBLIC_SUBMISSIONS_LIMIT]}


def cached_public_submissions(now: float | None = None) -> dict:
    # 참가자 화면이 몇 초마다 다시 부른다. 여러 명이 열어도 DOMjudge에는 몇 초에 한 번만 묻는다.
    now = time.time() if now is None else now
    with _status_lock:
        if _status_cache["value"] is None or now - _status_cache["at"] >= PUBLIC_SUBMISSIONS_CACHE_SECONDS:
            _status_cache["value"] = public_submissions()
            _status_cache["at"] = now
        return _status_cache["value"]


def _db_one(query: str, args: tuple):
    import pymysql

    connection = pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "mariadb"), user=os.environ.get("MYSQL_USER", "domjudge"),
        password=os.environ.get("MYSQL_PASSWORD", ""), database=os.environ.get("MYSQL_DATABASE", "domjudge"),
        connect_timeout=5, read_timeout=30, cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, args)
            return cursor.fetchone()
    finally:
        connection.close()


def _public_row(submission_id: str) -> dict:
    # 목록에 보이는 제출만 열 수 있다. KAUPC 제출이나 숨긴 팀의 제출은 여기서 걸러진다.
    row = next((row for row in cached_public_submissions()["submissions"] if row["id"] == submission_id), None)
    if row is None:
        raise NicknameError(404, "제출을 찾을 수 없습니다.")
    return row


def _text(value) -> str:
    return (value or b"").decode("utf-8", "replace")


def public_run_data(submission_id: str, rank: int) -> dict:
    _public_row(submission_id)
    columns = ", ".join(
        f"SUBSTRING({column}, 1, {RUN_TEXT_LIMIT}) AS {kind}, LENGTH({column}) AS {kind}_size"
        for kind, column in RUN_COLUMNS.items()
    )
    row = _db_one(f"SELECT {columns}{RUN_FROM}", (submission_id, rank))
    if row is None:
        raise NicknameError(404, "실행 결과를 찾을 수 없습니다.")
    data = {}
    for kind in RUN_COLUMNS:
        size = row.get(f"{kind}_size") or 0
        data[kind] = {"text": _text(row.get(kind)), "size": size, "truncated": size > RUN_TEXT_LIMIT}
    return data


def public_run_file(submission_id: str, rank: int, kind: str) -> bytes:
    if kind not in RUN_FILES:
        raise NicknameError(404, "파일을 찾을 수 없습니다.")
    _public_row(submission_id)
    row = _db_one(f"SELECT {RUN_COLUMNS[kind]} AS content{RUN_FROM}", (submission_id, rank))
    if row is None:
        raise NicknameError(404, "실행 결과를 찾을 수 없습니다.")
    return row.get("content") or b""


def public_submission_detail(submission_id: str) -> dict:
    row = _public_row(submission_id)
    with _status_lock:
        kept = _submission_details.get(submission_id)
    if kept is not None:
        return kept
    base = f"/api/v4/contests/{quote(PUBLIC_SUBMISSIONS_CONTEST, safe='')}"
    judgements = [
        judgement for judgement in _api_list(f"{base}/judgements?submission_id={quote(submission_id, safe='')}")
        if judgement.get("valid") is not False
    ]
    judgement = max(judgements, key=lambda item: str(item.get("start_time") or ""), default=None)
    runs = []
    if judgement:
        runs = sorted(
            ({"ordinal": run.get("ordinal"), "verdict": run.get("judgement_type_id"), "runtime": run.get("run_time")}
             for run in _api_list(f"{base}/runs?judging_id={quote(str(judgement['id']), safe='')}")
             if run.get("judgement_id") == judgement["id"]),
            key=lambda run: run["ordinal"] or 0,
        )
    sources = [
        {"filename": source.get("filename"), "source": base64.b64decode(source.get("source") or "").decode("utf-8", "replace")}
        for source in _api_list(f"{base}/submissions/{quote(submission_id, safe='')}/source-code")
    ]
    # DB를 못 읽어도 코드와 테스트 결과는 보인다.
    compile_read = True
    try:
        compiled = _db_one(
            f"SELECT SUBSTRING(output_compile, 1, {RUN_TEXT_LIMIT}) AS compile FROM judging"
            " WHERE submitid = %s AND valid = 1 ORDER BY judgingid DESC LIMIT 1",
            (submission_id,),
        ) or {}
    except Exception:  # noqa: BLE001
        traceback.print_exc(file=sys.stderr)
        compiled = {}
        compile_read = False
    detail = {**row, "runs": runs, "sources": sources, "compile_output": _text(compiled.get("compile"))}
    # 채점이 끝난 제출은 다시 바뀌지 않는다. 채점 중인 제출은 다음에 다시 묻는다.
    if compile_read and judgement and judgement.get("judgement_type_id"):
        with _status_lock:
            if len(_submission_details) >= SUBMISSION_DETAILS_KEPT:
                _submission_details.clear()
            _submission_details[submission_id] = detail
    return detail


ENTER_ERROR_PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>KAUPC 2026</title>
<style>body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:system-ui,sans-serif;
background:linear-gradient(160deg,#0a1f42,#0f2c5c);color:#fff;text-align:center;padding:1rem}}a{{color:#fff}}</style></head>
<body><main><h1>KAUPC 2026</h1><p>{message}</p><p><a href="/login">다시 시도</a></p></main></body></html>"""


class Editor(http.server.BaseHTTPRequestHandler):
    server_version = "ProblemEditor/3.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # ---- 응답 ----

    def send_page(self, body: str, status: int = 200, title: str = "문제 만들기"):
        payload = PAGE.format(
            body=body,
            title=html.escape(title),
            home=link("/"),
            barright="",
            languages=LANGUAGE_FILENAMES,
        ).encode("utf-8")
        self.send_bytes(payload, "text/html; charset=utf-8", status)

    def send_bytes(self, payload: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        # 저장하면 화면이 바뀐다. 미리보기가 옛 내용으로 남으면 안 된다.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def redirect(self, location: str):
        # Location 헤더는 latin-1만 담을 수 있어 비ASCII는 퍼센트 인코딩한다.
        self.send_response(303)
        self.send_header("Location", quote(location, safe="/?&=%#"))
        self.end_headers()

    def back(self, form, message: str = "", error: str = "", section: str = ""):
        """누른 칸으로 돌려보낸다. 결과도 오류도 그 칸 안에 띄운다."""
        contest = (form.get("contest") or "").strip()
        label = (form.get("label") or "").strip()
        key = "msg" if message else "err"
        value = message or error
        known = (
            contest
            and label
            and SAFE_NAME.match(contest)
            and SAFE_NAME.match(label)
            and (CONTESTS / contest / label / "problem.yaml").is_file()
        )
        if known:
            where = f"&s={section}#{section}" if section in SECTIONS else ""
            self.redirect(link(f"/edit?c={contest}&l={label}&{key}={value}{where}"))
        else:
            self.redirect(link(f"/?{key}={value}"))

    # ---- 라우팅 ----

    def send_json(self, value, status: int = 200):
        self.send_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def handle_nickname(self, method: str):
        cookie = self.headers.get("Cookie", "")
        try:
            if method == "GET":
                self.send_json(nickname_state(cookie))
                return
            # 다른 사이트의 폼은 JSON 본문을 보낼 수 없다. 세션 쿠키를 빌린 요청을 여기서 막는다.
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                raise NicknameError(415, "잘못된 요청입니다.")
            length = int(self.headers.get("Content-Length", "0") or 0)
            body = json.loads(self.rfile.read(min(length, 4096)).decode("utf-8") or "{}")
            self.send_json({"display_name": set_nickname(cookie, body.get("nickname"))})
        except NicknameError as error:
            self.send_json({"error": str(error)}, error.status)
        except (ValueError, AttributeError):
            self.send_json({"error": "잘못된 요청입니다."}, 400)
        except Exception:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            self.send_json({"error": "이름을 저장하지 못했습니다. 운영진에게 알려 주세요."}, 500)

    def client_id(self) -> str:
        # Caddy와 domserver nginx가 앞에서 X-Forwarded-For에 접속한 주소를 적어 준다. 맨 앞이 실제 접속자다.
        forwarded = self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        return forwarded or self.client_address[0]

    def handle_enter(self):
        from http.cookies import CookieError, SimpleCookie

        jar = SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except CookieError:
            pass
        tries_cookie = jar.get(GUEST_TRIES_COOKIE)
        tries = int(tries_cookie.value) if tries_cookie and tries_cookie.value.isdigit() else 0
        remembered = jar.get(GUEST_COOKIE)
        try:
            # 들어가자마자 다시 로그인 화면으로 돌아오기를 되풀이하면 멈춘다.
            if tries >= 3:
                raise NicknameError(503, "대회 화면에 들어가지 못했습니다. 잠시 후 다시 시도하세요.")
            cookies, credential = enter_as_guest(remembered.value if remembered else "", self.client_id())
        except NicknameError as error:
            self.send_enter_error(str(error), error.status)
            return
        except Exception:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            self.send_enter_error("대회 화면에 들어가지 못했습니다. 운영진에게 알려 주세요.", 500)
            return
        self.send_response(302)
        # 첫 화면은 공개 대회가 보이는 대회 목록이다.
        self.send_header("Location", "/team")
        self.send_header("Cache-Control", "no-store")
        for cookie in cookies:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Set-Cookie", f"{GUEST_COOKIE}={credential}; Max-Age={GUEST_COOKIE_MAX_AGE}; Path=/; HttpOnly; SameSite=Lax")
        self.send_header("Set-Cookie", f"{GUEST_TRIES_COOKIE}={tries + 1}; Max-Age=20; Path=/; HttpOnly; SameSite=Lax")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_enter_error(self, message: str, status: int):
        page = ENTER_ERROR_PAGE.format(message=html.escape(message))
        self.send_bytes(page.encode("utf-8"), "text/html; charset=utf-8", status)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == GUEST_ENTER_PATH:
            self.handle_enter()
            return
        if parsed.path == PUBLIC_SUBMISSIONS_PATH:
            try:
                self.send_json(cached_public_submissions())
            except NicknameError as error:
                self.send_json({"error": str(error)}, error.status)
            except Exception:  # noqa: BLE001
                traceback.print_exc(file=sys.stderr)
                self.send_json({"error": "채점 현황을 불러오지 못했습니다."}, 500)
            return
        if parsed.path.startswith(PUBLIC_SUBMISSIONS_PATH + "/"):
            try:
                rest = parsed.path[len(PUBLIC_SUBMISSIONS_PATH) + 1:]
                run = re.fullmatch(r"([0-9]{1,12})/runs/([0-9]{1,6})(?:/([a-z]+))?", rest)
                if run and run.group(3):
                    payload = public_run_file(run.group(1), int(run.group(2)), run.group(3))
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("Content-Disposition", f'attachment; filename="{run.group(1)}-{run.group(2)}-{run.group(3)}.txt"')
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(payload)
                elif run:
                    self.send_json(public_run_data(run.group(1), int(run.group(2))))
                else:
                    self.send_json(public_submission_detail(rest))
            except NicknameError as error:
                self.send_json({"error": str(error)}, error.status)
            except Exception:  # noqa: BLE001
                traceback.print_exc(file=sys.stderr)
                self.send_json({"error": "제출을 불러오지 못했습니다."}, 500)
            return
        if parsed.path == NICKNAME_PATH:
            self.handle_nickname("GET")
            return
        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        try:
            if parsed.path == "/":
                self.send_page(self.index_page(query.get("msg", ""), query.get("err", "")))
            elif parsed.path == "/edit":
                package = package_dir(query["c"], query["l"])
                self.send_page(
                    self.edit_page(
                        query["c"],
                        query["l"],
                        query.get("msg", ""),
                        query.get("err", ""),
                        query.get("s", ""),
                    ),
                    title=problem_name_of(package),
                )
            elif parsed.path == "/preview":
                package = package_dir(query["c"], query["l"])
                body = preview_document(package)
                self.send_bytes(body.encode("utf-8"), "text/html; charset=utf-8")
            elif parsed.path == "/api/problems":
                payload = json.dumps(list_packages(), ensure_ascii=False).encode("utf-8")
                self.send_bytes(payload, "application/json; charset=utf-8")
            else:
                self.send_page("<h1>없는 페이지입니다</h1><p><a href='" + link("/") + "'>문제 목록으로</a></p>", 404)
        except (Exception, SystemExit) as error:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            self.send_page(
                f"<div class='flash flash-err'>{html.escape(str(error))}</div>"
                "<p><a href='" + link("/") + "'>문제 목록으로</a></p>",
                400,
            )

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == NICKNAME_PATH:
            self.handle_nickname("POST")
            return
        form = read_form(self)
        try:
            handler = {
                "/create": self.post_create,
                "/statement": self.post_statement,
                "/image": self.post_image,
                "/testcase": self.post_testcase,
                "/testcase-delete": self.post_testcase_delete,
                "/testcase-sample": self.post_testcase_sample,
                "/generator": self.post_generator,
                "/generate": self.post_generate,
                "/generate-legacy": self.post_generate_legacy,
                "/submission": self.post_submission,
                "/submission-delete": self.post_submission_delete,
                "/verify": self.post_verify,
                "/publish": self.post_publish,
                "/sync": self.post_sync,
            }.get(parsed.path)
            if handler is None:
                self.send_page("<h1>없는 페이지입니다</h1>", 404)
                return
            handler(form)
        except (Exception, SystemExit) as error:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            message = str(error) or error.__class__.__name__
            if parsed.path == "/create":
                # 만들기는 목록에서 누른다. 실패하면 목록으로 돌아가야 한다.
                self.redirect(link(f"/?err={message}"))
            else:
                self.back(form, error=message, section=SECTION_OF_ROUTE.get(parsed.path, ""))

    # ---- 동작 ----

    def post_create(self, form):
        contest = safe_part(form.get("contest", ""))
        label = safe_part(form.get("label", ""))
        problem_id = safe_part(form.get("problem_id", ""), SAFE_PROBLEM_ID)
        name = (form.get("name", "") or "").strip()
        if not name:
            raise ValueError("제목을 입력하세요.")
        package = new_problem.create(contest, label, problem_id, name, "", "")
        # 템플릿 지문에 박혀 있는 제한 값을 problem.yaml 값으로 맞춘다.
        rebuild_statement(package)
        note = git_save([package, package.parent / "problems.yaml"], f"문제 추가: {contest}/{label} {name}")
        self.redirect(link(f"/edit?c={contest}&l={label}&msg=문제를 만들었습니다. {note}"))

    def post_statement(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        try:
            time_limit = float((form.get("time_limit") or "1").strip())
            memory = int((form.get("memory_limit") or "512").strip())
        except ValueError:
            raise ValueError("시간 제한과 메모리 제한은 숫자로 입력하세요.")
        name = clean_problem_name(form.get("name", ""))
        write_problem_meta(package, time_limit, memory)
        renamed = rename_problem(package, name)
        fields = {
            "description": form.get("description", ""),
            "input": form.get("input", ""),
            "output": form.get("output", ""),
            "limits": form.get("limits", ""),
        }
        write_text(statement_path(package), build_statement(package, package.name, fields))
        note = git_save([package, *renamed], f"지문 수정: {package.parent.name}/{package.name}")
        self.back(form, f"지문을 저장했습니다. {note}", section="statement")

    def post_image(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        filename = (form.get("image__filename") or "").strip().replace("\\", "/").split("/")[-1]
        payload = form.get("image__bytes") or b""
        if not filename or not payload:
            raise ValueError("올릴 그림을 먼저 고르세요.")
        if Path(filename).suffix.lower() not in IMAGE_SUFFIXES:
            raise ValueError("그림 파일만 올릴 수 있습니다. (png, jpg, gif, svg, webp)")
        if len(payload) > MAX_IMAGE_BYTES:
            raise ValueError(f"그림이 너무 큽니다. {MAX_IMAGE_BYTES // 1024}KB 이하로 줄여 주세요.")
        folder = image_dir(package)
        folder.mkdir(parents=True, exist_ok=True)
        saved = safe_image_name(filename, folder)
        (folder / saved).write_bytes(payload)
        rebuild_statement(package)
        note = git_save([package], f"그림 추가: {package.parent.name}/{package.name} {saved}")
        self.back(form, f"지문에 ![설명]({saved})라고 쓰면 그림이 들어갑니다. {note}", section="statement")

    def post_testcase(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        name = safe_part(form.get("name", ""))
        group = "sample" if form.get("is_sample") else "secret"
        data_in = form.get("input_file") or form.get("input_text", "")
        data_ans = form.get("answer_file") or form.get("answer_text", "")
        if not data_in.strip() or not data_ans.strip():
            raise ValueError("입력과 출력을 모두 입력하세요.")
        write_text(package / "data" / group / f"{name}.in", data_in)
        write_text(package / "data" / group / f"{name}.ans", data_ans)
        rebuild_statement(package)
        kind = "예제" if group == "sample" else "테스트케이스"
        note = git_save([package], f"테스트케이스 추가: {package.parent.name}/{package.name} {group}/{name}")
        self.back(form, f"{kind} {name}을(를) 저장했습니다. {note}", section="data")

    def post_testcase_delete(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        name = safe_part(form.get("name", ""))
        group = "sample" if form.get("group") == "sample" else "secret"
        for suffix in (".in", ".ans"):
            target = package / "data" / group / f"{name}{suffix}"
            if target.is_file():
                target.unlink()
        rebuild_statement(package)
        note = git_save([package], f"테스트케이스 삭제: {package.parent.name}/{package.name} {group}/{name}")
        section = form.get("section") if form.get("section") in SECTIONS else "data"
        self.back(form, f"{name}을(를) 삭제했습니다. {note}", section=section)

    def post_testcase_sample(self, form):
        """예제 체크박스. data/sample과 data/secret 사이로 파일을 옮긴다."""
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        name = safe_part(form.get("name", ""))
        source = "sample" if form.get("group") == "sample" else "secret"
        target = "sample" if form.get("is_sample") else "secret"
        if source == target:
            self.back(form, section="data")
            return
        if not (package / "data" / source / f"{name}.in").is_file():
            raise ValueError(f"테스트케이스 {name}을(를) 찾을 수 없습니다.")
        target_label = "예제" if target == "sample" else "채점용 테스트케이스"
        if (package / "data" / target / f"{name}.in").is_file():
            raise ValueError(f"{target_label}에 같은 이름 {name}이(가) 이미 있습니다. 이름을 바꾼 뒤 다시 시도하세요.")
        (package / "data" / target).mkdir(parents=True, exist_ok=True)
        for suffix in (".in", ".ans"):
            moved = package / "data" / source / f"{name}{suffix}"
            if moved.is_file():
                moved.rename(package / "data" / target / f"{name}{suffix}")
        rebuild_statement(package)
        note = git_save([package], f"테스트케이스 이동: {package.parent.name}/{package.name} {source}/{name} -> {target}/{name}")
        self.back(form, f"{name}을(를) {target_label}(으)로 옮겼습니다. {note}", section="data")

    def post_generator(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        code = form.get("code_text", "")
        if not code.strip():
            raise ValueError("생성기 코드가 비어 있습니다.")
        write_generator(package, code)
        note = git_save([package], f"생성기 수정: {package.parent.name}/{package.name}")
        self.back(form, "저장되었습니다.", section="generator")

    def post_generate(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        seeds = [line.strip() for line in form.get("seeds", "").splitlines() if line.strip()]
        summary = sync_seeds(package, seeds)
        rebuild_statement(package)
        note = git_save([package], f"시드 저장: {package.parent.name}/{package.name} {summary}")
        self.back(form, f"{summary} {note}", section="generator")

    def post_generate_legacy(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        summary = run_legacy_generator(package)
        rebuild_statement(package)
        note = git_save([package], f"테스트케이스 재생성: {package.parent.name}/{package.name}")
        self.back(form, f"{summary}. {note}", section="generator")

    def post_submission(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        folder = form.get("folder", "accepted")
        if folder not in SUBMISSION_FOLDERS:
            raise ValueError(f"허용하지 않는 종류입니다: {folder}")
        filename = (form.get("code__filename") or form.get("filename", "")).strip()
        filename = filename.replace("\\", "/").split("/")[-1]
        if not filename:
            filename = DEFAULT_FILENAME.get(form.get("language", "py"), "solution.py")
        if not SAFE_FILE.match(filename):
            raise ValueError(f"파일 이름을 확인하세요: {filename!r}")
        if Path(filename).suffix.lstrip(".").lower() not in EXTENSION_LANGUAGE:
            raise ValueError("확장자로 언어를 정합니다. py, c, cpp, java 중 하나를 쓰세요.")
        code = form.get("code") or form.get("code_text", "")
        if not code.strip():
            raise ValueError("코드가 비어 있습니다.")
        write_text(package / "submissions" / folder / filename, code)
        if form.get("make_main") and folder == "accepted":
            write_text(package / "generators" / "main.txt", filename)
        note = git_save([package], f"코드 추가: {package.parent.name}/{package.name} {folder}/{filename}")
        self.back(form, f"{filename}을(를) 저장했습니다. {note}", section="code")

    def post_submission_delete(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        folder = form.get("folder", "")
        filename = form.get("filename", "")
        delete_submission(package, folder, filename)
        note = git_save([package], f"코드 삭제: {package.parent.name}/{package.name} {folder}/{filename}")
        self.back(form, f"{filename}을(를) 삭제했습니다. {note}", section="code")

    def post_verify(self, form):
        package = package_dir(form.get("contest", ""), form.get("label", ""))
        LAST_VERIFY[(package.parent.name, package.name)] = verify_package(package)
        self.back(form, "코드 검증을 마쳤습니다.", section="verify")

    def post_publish(self, form):
        package_dir(form.get("contest", ""), form.get("label", ""))
        self.back(form, run_provisioner(), section="publish")

    def post_sync(self, form):
        self.back(form, git_pull())

    # ---- 화면 ----

    def flash_at(self, section: str, current: str, message: str, error: str) -> str:
        """결과는 누른 칸 안에만 띄운다."""
        if section != current:
            return ""
        return self.flash(message, error)

    def flash(self, message: str, error: str) -> str:
        out = ""
        if message:
            out += f"<div class='flash flash-ok'>{html.escape(message)}</div>"
        if error:
            out += f"<div class='flash flash-err'>{html.escape(error)}</div>"
        return out

    def index_page(self, message: str, error: str) -> str:
        rows = []
        for row in list_packages():
            if row["editable"]:
                data_cell = (
                    f"예제 {row['samples']} · 채점 {row['secrets']}"
                    if (row["samples"] or row["secrets"])
                    else "<span class='tag tag-warn'>없음</span>"
                )
                code_cell = (
                    f"<span class='tag'>{row['accepted']}개</span>"
                    if row["accepted"]
                    else "<span class='tag tag-warn'>없음</span>"
                )
                target = link("/edit") + f"?c={row['contest']}&l={row['label']}"
                action = f"<a class='btn' href='{target}'>편집</a>"
                name = html.escape(row["name"])
            else:
                data_cell = code_cell = ""
                action = ""
                name = f"<span class='tag tag-grey'>{html.escape(row['source'])} 재사용</span>"
            rows.append(
                f"<tr><td>{html.escape(row['contest'])}</td><td><b>{html.escape(row['label'])}</b></td>"
                f"<td>{name}</td><td>{data_cell}</td><td>{code_cell}</td>"
                f"<td style='text-align:right'>{action}</td></tr>"
            )
        table_body = "".join(rows) if rows else "<tr><td colspan='6' class='empty'>아직 문제가 없습니다.</td></tr>"
        contests = sorted(p.name for p in CONTESTS.iterdir() if p.is_dir()) if CONTESTS.is_dir() else []
        options = "".join(f"<option>{html.escape(name)}</option>" for name in contests)
        return f"""
<h1>문제 목록</h1>
{self.flash(message, error)}
<section class='panel'>
  <header><h2>새 문제</h2></header>
  <form method='post' action='{link("/create")}' autocomplete='off'>
    <div class='fields'>
      <div><label for='f-contest'>대회</label><select id='f-contest' name='contest'>{options}</select></div>
      <div><label for='f-label'>문제 번호</label><input id='f-label' name='label' placeholder='C' required></div>
      <div><label for='f-id'>영문 ID</label><input id='f-id' name='problem_id' placeholder='helloworld' required></div>
      <div><label for='f-name'>제목</label><input id='f-name' name='name' placeholder='Hello World 출력하기' required></div>
      <div><button class='btn' type='submit'>만들기</button></div>
    </div>
    <p class='hint'>영문 ID는 영어 소문자와 숫자만 쓸 수 있습니다. 채점 시스템이 문제를 구분하는 값이라 나중에 바꾸기 어렵습니다.</p>
  </form>
</section>
<section class='panel'>
  <table>
    <tr><th>대회</th><th>번호</th><th>이름</th><th>테스트케이스</th><th>정답 코드</th><th></th></tr>
    {table_body}
  </table>
</section>
"""

    def snippet(self, path: Path) -> str:
        """데이터 내용 앞부분. 접지 않고 칸 안에서 바로 보여 준다."""
        if not path.is_file():
            return ""
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > 600:
            text = text[:600] + f"\n… 이하 {len(text) - 600}자 생략"
        return f"<pre class='peek'>{html.escape(text)}</pre>"

    def testcase_row(self, package: Path, path: Path, group: str, hidden: str, section: str, seed=None) -> str:
        """테스트케이스 한 줄. 직접 넣은 것과 생성기로 만든 것이 같은 모양을 쓴다."""
        answer = path.with_suffix(".ans")
        answer_cell = f"{answer.stat().st_size} B" if answer.is_file() else "<span class='tag tag-warn'>없음</span>"
        name = html.escape(path.stem)
        checked = " checked" if group == "sample" else ""
        seed_note = f"<div class='hint'>시드 {html.escape(str(seed))}</div>" if seed is not None else ""
        return (
            "<tr>"
            f"<td><form method='post' action='{link('/testcase-sample')}'>{hidden}"
            f"<input type='hidden' name='group' value='{group}'>"
            f"<input type='hidden' name='name' value='{name}'>"
            "<label class='sample-toggle'>"
            f"<input type='checkbox' name='is_sample' value='1'{checked} onchange='this.form.submit()'> 예제</label>"
            "</form></td>"
            f"<td><b>{name}</b>{seed_note}</td>"
            f"<td>{path.stat().st_size} B{self.snippet(path)}</td>"
            f"<td>{answer_cell}{self.snippet(answer)}</td>"
            "<td style='text-align:right'>"
            f"<form method='post' action='{link('/testcase-delete')}'"
            f" onsubmit=\"return confirm('{name}을(를) 삭제할까요?')\">{hidden}"
            f"<input type='hidden' name='group' value='{group}'>"
            f"<input type='hidden' name='name' value='{name}'>"
            f"<input type='hidden' name='section' value='{section}'>"
            "<button class='btn btn-ghost btn-danger' type='submit'>삭제</button></form></td></tr>"
        )

    def data_panel(self, package: Path, hidden: str, flash: str = ""):
        """(예제 수, 채점용 테스트케이스 수, 화면 조각). 생성기로 만든 것은 랜덤 데이터 칸에 따로 보인다."""
        rows = []
        counts = {"sample": 0, "secret": 0}
        generated = {str(record.get("name")) for record in generated_cases(package)}
        natural = lambda path: [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.stem)]
        for group in ("sample", "secret"):
            folder = package / "data" / group
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.in"), key=natural):
                counts[group] += 1
                if group == "secret" and path.stem in generated:
                    continue
                rows.append(self.testcase_row(package, path, group, hidden, "data"))
        body = (
            "".join(rows)
            if rows
            else "<tr><td colspan='5' class='empty'>직접 넣은 테스트케이스가 없습니다. 위에서 예제부터 추가하세요.</td></tr>"
        )
        panel = f"""
<section class='panel' id='data'>
  <header><h2>테스트케이스</h2><span class='hint'>예제로 체크한 테스트케이스는 지문에 그대로 실립니다</span></header>
  {flash}
  <form class='data-add' method='post' action='{link("/testcase")}' enctype='multipart/form-data' autocomplete='off'>
      {hidden}
      <div class='fields' style='margin-bottom:.9rem'>
        <div><label for='t-name'>이름</label><input id='t-name' name='name' placeholder='corner' required></div>
        <label style='display:flex;gap:.4rem;align-items:center;margin:1.8rem 0 0;font-weight:600'>
          <input id='t-sample' type='checkbox' name='is_sample' value='1' style='width:auto'> 예제</label>
      </div>
      <div class='two'>
        <div><label for='t-in'>입력</label><textarea id='t-in' name='input_text' rows='6'></textarea></div>
        <div><label for='t-out'>출력</label><textarea id='t-out' name='answer_text' rows='6'></textarea></div>
      </div>
      <div class='two' style='margin-top:.6rem'>
        <div><label>또는 입력 파일</label><input type='file' name='input_file'></div>
        <div><label>또는 출력 파일</label><input type='file' name='answer_file'></div>
      </div>
      <div class='btn-row'><button class='btn' type='submit'>추가</button></div>
  </form>
  <table>
    <tr><th>예제</th><th>이름</th><th>입력</th><th>출력</th><th></th></tr>
    {body}
  </table>
</section>
"""
        return counts["sample"], counts["secret"], panel

    def verify_panel(self, package: Path) -> str:
        result = LAST_VERIFY.get((package.parent.name, package.name))
        if not result:
            return ""
        rows = []
        for row in result["rows"]:
            if row["skipped"]:
                mark = "<span class='tag tag-grey'>확인 못 함</span>"
            elif row["ok"]:
                mark = "<span class='tag tag-ok'>일치</span>"
            else:
                mark = "<span class='tag tag-warn'>불일치</span>"
            rows.append(
                f"<tr><td>{row['order']}</td><td><b>{html.escape(row['file'])}</b></td>"
                f"<td><span class='tag'>{row['expected']}</span></td>"
                f"<td><span class='tag tag-grey'>{html.escape(row['actual'])}</span></td>"
                f"<td>{mark}</td>"
                f"<td class='hint'>{html.escape(row['detail'])}</td>"
                f"<td>{row['slowest']:.2f}초</td></tr>"
            )
        return (
            "<table style='margin-top:1.2rem'>"
            "<tr><th>순서</th><th>파일</th><th>기대 결과</th><th>실제 결과</th><th>일치 여부</th><th>내용</th><th>가장 느린 테스트케이스</th></tr>"
            + "".join(rows)
            + "</table>"
            + f"<p class='hint'>테스트케이스 {result['tests']}개 · 시간 제한 {result['time_limit']}초 · {result['at']} 기준 · 위 순서대로 하나씩 실행</p>"
        )

    def edit_page(self, contest: str, label: str, message: str, error: str, section: str = "") -> str:
        package = package_dir(contest, label)
        meta = problem_meta(package)
        fields = statement_fields(package)
        hidden = (
            f"<input type='hidden' name='contest' value='{html.escape(contest)}'>"
            f"<input type='hidden' name='label' value='{html.escape(label)}'>"
        )

        sample_count, secret_count, data_panel = self.data_panel(
            package, hidden, self.flash_at("data", section, message, error)
        )

        code_rows = []
        accepted_count = 0
        main_name = main_solution_name(package)
        for folder, tag, verdict in SUBMISSION_LABELS:
            directory = package / "submissions" / folder
            if not directory.is_dir():
                continue
            for path in sorted(directory.iterdir()):
                if path.name == ".gitkeep" or not path.is_file():
                    continue
                if folder == "accepted":
                    accepted_count += 1
                is_main = folder == "accepted" and path.name == main_name
                badge = "<span class='tag tag-main'>MAIN</span> " if is_main else ""
                language = EXTENSION_LANGUAGE.get(path.suffix.lstrip(".").lower(), path.suffix)
                name = html.escape(path.name)
                warning = " MAIN이라 다른 정답 코드가 MAIN이 됩니다." if is_main else ""
                code_rows.append(
                    f"<tr><td>{badge}<span class='tag'>{tag}</span></td>"
                    f"<td><b>{name}</b></td>"
                    f"<td>{html.escape(language)}</td>"
                    f"<td class='hint'>{verdict}</td><td>{path.stat().st_size} B</td>"
                    "<td style='text-align:right'>"
                    f"<form method='post' action='{link('/submission-delete')}'"
                    f" onsubmit=\"return confirm('{folder}/{name}을(를) 삭제할까요?{warning}')\">{hidden}"
                    f"<input type='hidden' name='folder' value='{folder}'>"
                    f"<input type='hidden' name='filename' value='{name}'>"
                    "<button class='btn btn-ghost btn-danger' type='submit'>삭제</button></form></td></tr>"
                )
        code_body = (
            "".join(code_rows)
            if code_rows
            else "<tr><td colspan='6' class='empty'>코드가 없습니다. 정답 코드부터 추가하세요.</td></tr>"
        )
        folder_options = "".join(
            f"<option value='{key}'>{tag} · {verdict}</option>" for key, tag, verdict in SUBMISSION_LABELS
        )
        language_options = "".join(
            f"<option value='{key}'>{html.escape(name)}</option>" for key, name, _ in LANGUAGES
        )

        written = fields["description"].strip()
        checks = [
            ("지문", bool(written) and written not in PLACEHOLDER_TEXT),
            (f"예제 {sample_count}개", sample_count > 0),
            (f"채점용 테스트케이스 {secret_count}개", secret_count > 0),
            (f"정답 코드 {accepted_count}개", accepted_count > 0),
        ]
        checklist = "".join(
            f"<li class='{'done' if ok else 'todo'}'>{'완료' if ok else '필요'} · {html.escape(text)}</li>"
            for text, ok in checks
        )

        generator_code = html.escape(generator_body(package))
        generated = generated_cases(package)
        saved_seeds = html.escape("\n".join(dict.fromkeys(str(record.get("seed")) for record in generated)))
        generated_rows = "".join(
            self.testcase_row(package, package / "data" / "secret" / f"{record.get('name')}.in", "secret", hidden, "generator", record.get("seed"))
            for record in generated
        ) or "<tr><td colspan='5' class='empty'>아직 생성한 테스트케이스가 없습니다. 시드를 적고 저장하세요.</td></tr>"
        legacy_block = (
            "<form method='post' action='" + link("/generate-legacy") + "' style='margin-top:1.2rem'>" + hidden
            + "<div class='btn-row'><button class='btn btn-ghost' type='submit'>기존 생성기 다시 돌리기</button>"
            + "<span class='hint'>이 문제는 <code>generate_tests.py</code>로 테스트케이스를 만듭니다</span></div></form>"
            if legacy_generator_path(package).is_file()
            else ""
        )
        images = sorted(p.name for p in image_dir(package).glob("*")) if image_dir(package).is_dir() else []
        image_list = (
            " ".join(f"<code>![설명]({html.escape(name)})</code>" for name in images)
            if images
            else "<span class='hint'>올린 그림이 없습니다.</span>"
        )
        preview_srcdoc = html.escape(preview_document(package), quote=True)
        top_flash = self.flash(message, error) if section not in SECTIONS else ""
        return f"""
<h1>{html.escape(meta["name"])}</h1>
<p class='sub'>{html.escape(contest)} {html.escape(label)}번 · <code>problems/contests/{html.escape(contest)}/{html.escape(label)}</code></p>
<ul class='checklist'>{checklist}</ul>
{top_flash}

<div class='editor-grid'>
  <section class='panel' id='statement'>
    <header><h2>지문</h2><span class='hint'>빈 줄로 문단을 나눕니다</span></header>
    {self.flash_at("statement", section, message, error)}
    <form method='post' action='{link("/statement")}'>
      {hidden}
      <div class='field'><label for='s-name'>제목</label>
        <input id='s-name' name='name' type='text' required maxlength='{PROBLEM_NAME_MAX_LENGTH}' value='{html.escape(meta["name"], quote=True)}'></div>
      <div class='fields' style='margin-bottom:1rem'>
        <div><label for='s-time'>시간 제한 (초)</label>
          <input id='s-time' name='time_limit' type='number' step='0.5' min='0.5' max='60' value='{pretty_seconds(meta["time_limit"])}'></div>
        <div><label for='s-mem'>메모리 제한 (MB)</label>
          <input id='s-mem' name='memory_limit' type='number' step='16' min='16' max='4096' value='{meta["memory"]}'></div>
      </div>
      <div class='field'><label for='s-desc'>문제</label>
        <textarea id='s-desc' name='description' rows='9' placeholder='문제 상황과 구해야 하는 값을 설명하세요.'>{html.escape(fields["description"])}</textarea></div>
      <div class='field'><label for='s-in'>입력</label>
        <textarea id='s-in' name='input' rows='4' placeholder='첫째 줄에 ...'>{html.escape(fields["input"])}</textarea></div>
      <div class='field'><label for='s-out'>출력</label>
        <textarea id='s-out' name='output' rows='4' placeholder='첫째 줄에 ...'>{html.escape(fields["output"])}</textarea></div>
      <div class='field'><label for='s-lim'>제한 · 한 줄에 하나</label>
        <textarea id='s-lim' name='limits' rows='4' placeholder='1 ≤ N ≤ 100'>{html.escape(fields["limits"])}</textarea></div>
      <div class='btn-row'><button class='btn' type='submit'>저장</button>
        <span class='hint'>제목과 시간·메모리 제한은 채점 서버에도 그대로 적용됩니다</span></div>
      <p class='hint'>표기법 · <code>`N`</code> 코드, <code>$N$</code> 수식 기호, <code>**굵게**</code>, <code>*기울임*</code>, <code>![설명](그림.png)</code></p>
    </form>
    <form method='post' action='{link("/image")}' enctype='multipart/form-data' style='margin-top:1rem'>
        {hidden}
        <div class='fields'>
          <div><input type='file' name='image' accept='image/*'></div>
          <div><button class='btn btn-ghost' type='submit'>올리기</button></div>
        </div>
      </form>
      <p class='hint' style='margin-top:.6rem'>올린 그림: {image_list}</p>
  </section>

  <section class='panel sticky'>
    <header><h2>미리보기</h2><span class='hint'>참가자가 보는 화면</span></header>
    <iframe srcdoc='{preview_srcdoc}' title='지문 미리보기'></iframe>
  </section>
</div>

{data_panel}

<section class='panel' id='generator'>
  <header><h2>랜덤 데이터</h2><span class='hint'>시드를 저장하면 생성기와 MAIN 정답 코드로 테스트케이스를 바로 만듭니다</span></header>
  {self.flash_at("generator", section, message, error)}
  <form method='post' action='{link("/generate")}' autocomplete='off'>
    {hidden}
    <div class='field'><label for='g-seeds'>시드 · 한 줄에 하나</label>
      <textarea id='g-seeds' name='seeds' rows='5' placeholder='11&#10;29&#10;47'>{saved_seeds}</textarea></div>
    <div class='btn-row'><button class='btn' type='submit'>시드 저장</button>
      <span class='hint'>새 시드는 테스트케이스를 만들고, 목록에서 지운 시드의 테스트케이스는 지웁니다.</span></div>
  </form>
  <table style='margin-top:1.2rem'>
    <tr><th>예제</th><th>이름</th><th>입력</th><th>출력</th><th></th></tr>
    {generated_rows}
  </table>
  <form method='post' action='{link("/generator")}' style='margin-top:1.4rem'>
    {hidden}
    <div class='field'><label for='g-code'>생성기 코드</label>
      <textarea id='g-code' name='code_text' rows='12'>{generator_code}</textarea></div>
    <div class='btn-row'><button class='btn btn-ghost' type='submit'>생성기 저장</button>
      <span class='hint'><code>random</code>은 시드가 고정된 상태로 주어집니다. 입력 하나를 출력하면 됩니다</span></div>
  </form>
  {legacy_block}
</section>

<section class='panel' id='code'>
  <header><h2>정답 코드</h2><span class='hint'>MAIN은 테스트케이스의 정답 파일을 만드는 코드입니다</span></header>
  {self.flash_at("code", section, message, error)}
  <table>
    <tr><th>태그</th><th>파일</th><th>언어</th><th>기대 판정</th><th>크기</th><th></th></tr>
    {code_body}
  </table>
  <form method='post' action='{link("/submission")}' enctype='multipart/form-data' style='margin-top:1.4rem' autocomplete='off'>
    {hidden}
    <div class='fields' style='margin-bottom:.9rem'>
      <div><label for='c-folder'>기대 판정</label><select id='c-folder' name='folder'>{folder_options}</select></div>
      <div><label for='c-lang'>언어</label>
        <select id='c-lang' name='language' data-language-for='c-file'>{language_options}</select></div>
      <div><label for='c-file'>파일 이름</label><input id='c-file' name='filename' value='solution.py'></div>
    </div>
    <div class='field'><label for='c-code'>코드</label><textarea id='c-code' name='code_text' rows='12'></textarea></div>
    <div class='field'><label>또는 코드 파일</label><input type='file' name='code'></div>
    <div class='btn-row'><button class='btn' type='submit'>추가</button>
      <label style='display:flex;gap:.4rem;align-items:center;margin:0;font-weight:600'>
        <input type='checkbox' name='make_main' value='1' style='width:auto'> 이 코드를 MAIN 정답 코드로 사용</label>
    <p class='hint'>MAIN 코드는 생성한 입력의 정답 출력을 만들 때 사용합니다.</p></div>
  </form>
</section>

<section class='panel' id='verify'>
  <header><h2>코드 검증</h2><span class='hint'>올라간 코드를 모든 데이터로 실행해 기대 결과와 맞는지 확인합니다</span></header>
  {self.flash_at("verify", section, message, error)}
  <form method='post' action='{link("/verify")}'>
    {hidden}
    <div class='btn-row'><button class='btn' type='submit'>검증 실행</button></div>
  </form>
  {self.verify_panel(package)}
</section>

<section class='panel' id='publish'>
  <header><h2>채점 시스템 반영</h2><span class='hint'>저장한 문제 패키지를 실제 DOMjudge 문제로 등록합니다</span></header>
  {self.flash_at("publish", section, message, error)}
  <form method='post' action='{link("/publish")}'>
    {hidden}
    <div class='btn-row'><button class='btn' type='submit'>채점 시스템에 반영</button>
      <a class='btn btn-ghost' href='/jury/problems' target='_blank' rel='noopener'>등록된 문제 보기</a></div>
  </form>
</section>
"""

def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", port), Editor) as server:
        server.daemon_threads = True
        sys.stderr.write(f"problem editor on port {port} (repo: {REPO_ROOT}, base: {BASE_PATH or '/'})\n")
        server.serve_forever()


if __name__ == "__main__":
    main()
