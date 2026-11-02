import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = ROOT / "submissions" / "accepted"
SAMPLES = sorted((ROOT / "data" / "sample").glob("*.in"))


def command(source: Path, workdir: Path):
    """정답 코드를 실행할 명령. 컴파일러가 없으면 None."""
    if source.suffix == ".py":
        return [sys.executable, str(source)]
    if source.suffix == ".cpp":
        compiler = shutil.which("g++")
        if not compiler:
            return None
        binary = workdir / source.stem
        subprocess.run([compiler, "-O2", "-std=gnu++17", "-o", str(binary), str(source)], check=True)
        return [str(binary)]
    return None


class ReferenceSolutionTest(unittest.TestCase):
    def test_samples_exist(self):
        self.assertTrue(SAMPLES, "data/sample에 예제가 없다")
        for sample in SAMPLES:
            self.assertTrue(sample.with_suffix(".ans").is_file(), sample.name)

    def test_accepted_solutions_pass_every_sample(self):
        sources = [path for path in sorted(ACCEPTED.iterdir()) if path.suffix in (".py", ".cpp")]
        self.assertTrue(sources, "submissions/accepted에 정답 코드가 없다")
        with tempfile.TemporaryDirectory() as directory:
            for source in sources:
                cmd = command(source, Path(directory))
                if cmd is None:
                    continue
                for sample in SAMPLES:
                    with self.subTest(solution=source.name, sample=sample.name):
                        result = subprocess.run(
                            cmd, input=sample.read_text(encoding="utf-8"), text=True, capture_output=True, check=True
                        )
                        self.assertEqual(result.stdout.split(), sample.with_suffix(".ans").read_text(encoding="utf-8").split())


if __name__ == "__main__":
    unittest.main()
