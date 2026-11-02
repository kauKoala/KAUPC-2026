import unittest
from tests.test_registration import SYNC

class DeliverySharingTests(unittest.TestCase):
    def test_kaupc_uses_the_completed_test_problems(self):
        state = SYNC.repository_state()
        self.assertEqual(state[('kaupc', 'C')], state[('test', 'J')])
        self.assertEqual(state[('kaupc', 'H')], state[('test', 'K')])

    def test_existing_hard_problem_keeps_its_slot(self):
        self.assertEqual(SYNC.repository_state()[('kaupc', 'K')], 'dessert2')

    def test_test_aliases_keep_bridges_and_bot_as_distinct_problems(self):
        state = SYNC.repository_state()
        self.assertEqual(state[('test', 'A')], 'addingbridges')
        self.assertEqual(state[('test', 'C')], 'botmaintenance')


class DifficultyOrderTests(unittest.TestCase):
    # 쉬운 문제부터 A, B, C ... 순서다. 라벨 폴더, problems.yaml 순서, 색이 서로 어긋나면 안 된다.
    EXPECTED = [
        ('A', 'wavingbanner'), ('B', 'kaupc001'), ('C', 'testdelivery1'), ('D', 'kaupc002'),
        ('E', 'kaupcfairopponent'), ('F', 'dessert1'), ('G', 'botmaintenance'), ('H', 'delivery2'),
        ('I', 'addingbridges'), ('J', 'taxidriver'), ('K', 'dessert2'),
    ]

    def test_label_folders_follow_difficulty_order(self):
        state = SYNC.repository_state()
        self.assertEqual(sorted((label, pid) for (cid, label), pid in state.items() if cid == 'kaupc'), self.EXPECTED)

    def test_problems_yaml_lists_labels_in_order_with_distinct_colors(self):
        text = (SYNC.REPO_ROOT / 'problems' / 'contests' / 'KAUPC' / 'problems.yaml').read_text(encoding='utf-8')
        ids = [line.split(':', 1)[1].strip() for line in text.splitlines() if line.startswith('- id:')]
        labels = [line.split(':', 1)[1].strip() for line in text.splitlines() if line.startswith('  label:')]
        rgbs = [line.split(':', 1)[1].strip() for line in text.splitlines() if line.startswith('  rgb:')]
        self.assertEqual(list(zip(labels, ids)), self.EXPECTED)
        self.assertEqual(len(set(rgbs)), len(rgbs))
