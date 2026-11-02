from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT / "generators"), str(ROOT / "submissions" / "accepted")])
from gen import all_heights
from solution import render


secret = ROOT / "data" / "secret"
secret.mkdir(parents=True, exist_ok=True)
# 문제 에디터로 예제로 옮긴 케이스(sample/40)는 secret에 다시 만들지 않는다.
samples = {path.read_text(encoding="utf-8") for path in (ROOT / "data" / "sample").glob("*.in")}
for index, heights in enumerate(all_heights(), start=1):
    stem = f"{index:02d}"
    if " ".join(map(str, heights)) + "\n" in samples:
        continue
    (secret / f"{stem}.in").write_text(" ".join(map(str, heights)) + "\n", encoding="utf-8", newline="\n")
    (secret / f"{stem}.ans").write_text(render(list(heights)), encoding="utf-8", newline="\n")

# 예제로 옮겨진 입력도 같은 출력 규칙으로 갱신한다.
for input_path in (ROOT / "data").rglob("*.in"):
    heights = list(map(int, input_path.read_text(encoding="utf-8").split()))
    input_path.with_suffix(".ans").write_text(render(heights), encoding="utf-8", newline="\n")
