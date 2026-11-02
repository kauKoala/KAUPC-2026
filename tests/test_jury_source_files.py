from pathlib import Path
import subprocess
import unittest


class JurySourceFilesTest(unittest.TestCase):
    def test_duplicate_download_links_preserve_distinct_files(self):
        source = (Path(__file__).resolve().parents[1] / "custom/js/contest-portal.js").read_text(encoding="utf-8")
        begin = source.index("var downloads = Array.from(doc.querySelectorAll(")
        end = source.index("if (!downloads.length)", begin)
        selection = source[begin:end]
        harness = """
const assert = require('node:assert/strict');
const urls = ['/jury/submissions/309/source?fetch=0',
              '/jury/submissions/309/source?fetch=0',
              '/jury/submissions/309/source?fetch=1',
              '/jury/submissions/309/source?fetch=1'];
const links = urls.map(href => ({getAttribute: () => href}));
const doc = {querySelectorAll: () => links};
""" + selection + """
assert.deepEqual(downloads.map(link => link.getAttribute('href')), [urls[0], urls[2]]);
"""
        result = subprocess.run(["node", "-e", harness], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
