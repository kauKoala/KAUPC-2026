import base64
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_DATA_URI = re.compile(r"data:image/png;base64,([A-Za-z0-9+/=]+)")


class StatementImageTests(unittest.TestCase):
    # problems/**는 text eol=lf라서 그림까지 줄바꿈 변환을 당하면 PNG 헤더의 \r\n이 \n이 된다.
    def test_png_files_are_not_line_ending_converted(self) -> None:
        images = sorted((ROOT / "problems").rglob("*.png"))
        self.assertTrue(images)
        broken = [path.relative_to(ROOT) for path in images if not path.read_bytes().startswith(PNG_SIGNATURE)]
        self.assertEqual(broken, [])

    def test_embedded_statement_images_are_valid_png(self) -> None:
        broken = []
        for path in sorted((ROOT / "problems").rglob("problem.html")):
            for match in PNG_DATA_URI.finditer(path.read_text(encoding="utf-8")):
                if not base64.b64decode(match.group(1)).startswith(PNG_SIGNATURE):
                    broken.append(path.relative_to(ROOT))
        self.assertEqual(broken, [])

    def test_git_treats_images_as_binary(self) -> None:
        result = subprocess.run(
            ["git", "check-attr", "text", "problems/contests/KAUPC/K/problem_statement/images/1.png"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        self.assertTrue(result.stdout.strip().endswith(": text: unset"), result.stdout)


if __name__ == "__main__":
    unittest.main()
