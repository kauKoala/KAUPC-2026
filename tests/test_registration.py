import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded

CREATE = module('create_problem_test', 'scripts/new-problem.py')
SYNC = module('sync_test', 'scripts/check-sync.py')

class RegistrationTests(unittest.TestCase):
    def test_new_problem_quotes_ini_title_with_parentheses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'problems/contests/TEST').mkdir(parents=True)
            with patch.object(CREATE, 'REPO_ROOT', root):
                package = CREATE.create('TEST', 'X', 'testtitle', 'Triple (easy)', '', '')
            self.assertIn('name = "Triple (easy)"', (package / 'domjudge-problem.ini').read_text(encoding='utf-8'))

    def test_independent_packages_do_not_share_external_ids(self):
        seen = {}
        for ini in sorted((ROOT / 'problems/contests').glob('*/*/domjudge-problem.ini')):
            problem_id = SYNC.problem_id_of(ini.parent)
            self.assertNotIn(problem_id, seen, f'{ini} overwrites {seen.get(problem_id)}')
            seen[problem_id] = ini

    def test_sync_fails_when_repository_problem_is_not_registered(self):
        with patch.object(SYNC, 'repository_state', return_value={('kaupc', 'D'): 'dessert1'}), \
             patch.object(SYNC, 'database_state', return_value={}), \
             patch('sys.argv', ['check-sync']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(SYNC.main(), 1)
