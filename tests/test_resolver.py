from pathlib import Path
import subprocess
import unittest

class ResolverTest(unittest.TestCase):
    def test_engine(self):
        path=Path(__file__).with_name('resolver_engine.cjs')
        r=subprocess.run(['node','--test',str(path)],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
