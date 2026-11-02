"""순위표에는 이름을 정한 참가자만 보이고, 운영진 테스트 계정과 TEST 대회는 숨긴다."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GROUPS = json.loads((ROOT / "bootstrap" / "groups.json").read_text(encoding="utf-8"))
TEAMS = json.loads((ROOT / "bootstrap" / "teams.json").read_text(encoding="utf-8"))
PROVISION = (ROOT / "bootstrap" / "provision.sh").read_text(encoding="utf-8")
STAFF_TEAMS = {"a", "b", "c", "d", "tester"}


class ScoreboardVisibilityTests(unittest.TestCase):
    def test_groups_hide_unnamed_participants_and_staff(self):
        hidden = {group["id"]: group["hidden"] for group in GROUPS}
        self.assertEqual(hidden, {"participants": False, "pending": True, "staff": True, "guests": False, "guest-pending": True})

    def test_new_participant_accounts_start_hidden_until_named(self):
        participants = [team for team in TEAMS if team["id"].startswith("user_")]
        self.assertEqual(len(participants), 27)
        for team in participants:
            self.assertEqual(team["group_ids"], ["pending"], team["id"])
            self.assertNotIn("display_name", team, team["id"])

    def test_staff_test_accounts_are_hidden(self):
        staff = {team["id"]: team["group_ids"] for team in TEAMS if not team["id"].startswith("user_")}
        self.assertEqual(staff, {team: ["staff"] for team in STAFF_TEAMS})

    def test_provisioner_moves_existing_teams_to_the_right_group(self):
        # 팀은 처음 한 번만 가져오므로 이미 있는 팀의 분류는 provisioner가 DB에서 맞춘다.
        self.assertIn("sync_team_visibility", PROVISION)
        self.assertIn("sync_team_visibility\n", PROVISION.split("import_new_accounts /bootstrap/accounts.yaml", 1)[1])
        self.assertIn("STAFF_TEAMS=\"'a','b','c','d','tester'\"", PROVISION)

    def test_test_contest_is_closed_to_participants_but_stays_enabled(self):
        # 끄면 API가 대회를 못 찾아 다음 배포에서 다시 만들려다 실패한다.
        self.assertIn("for retired in fivemin; do", PROVISION)
        self.assertIn("for staff_only in test kaupc-open; do", PROVISION)
        self.assertIn("SET public = 0, open_to_all_teams = 0", PROVISION)


if __name__ == "__main__":
    unittest.main()
