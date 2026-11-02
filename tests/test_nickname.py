"""참가자가 처음 로그인할 때 스코어보드에 보일 이름을 정하는 기능."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EDITOR_PATH = ROOT / "tools" / "problem-editor" / "app.py"
NGINX = (ROOT / "custom" / "nginx" / "domjudge-site.conf").read_text(encoding="utf-8")
PROVISION = (ROOT / "bootstrap" / "provision.sh").read_text(encoding="utf-8")
COMPOSE = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
PORTAL = (ROOT / "custom" / "js" / "contest-portal.js").read_text(encoding="utf-8")


def load_editor_module():
    spec = importlib.util.spec_from_file_location("problem_editor_nickname_under_test", EDITOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDITOR = load_editor_module()


class FakeDomjudge:
    """DOMjudge API 중 이름 설정이 쓰는 부분만 흉내 낸다."""

    def __init__(self):
        self.sessions = {"team-cookie": {"roles": ["team"], "team_id": "user_001"},
                         "admin-cookie": {"roles": ["admin"], "team_id": None}}
        self.teams = {
            "user_001": {"id": "user_001", "name": "user_001", "display_name": None, "group_ids": ["pending"]},
            "user_002": {"id": "user_002", "name": "user_002", "display_name": "코알라", "group_ids": ["participants"]},
        }
        self.imports = []

    def __call__(self, method, path, cookie=None, upload=None):
        if path == "/api/v4/user":
            session = self.sessions.get(cookie)
            return (200, session) if session else (401, {"message": "unauthorized"})
        if method == "GET" and path == "/api/v4/teams":
            return 200, list(self.teams.values())
        if method == "GET" and path.startswith("/api/v4/teams/"):
            team = self.teams.get(path.rsplit("/", 1)[1])
            return (200, team) if team else (404, {"message": "not found"})
        if method == "POST" and path == "/api/v4/users/teams":
            self.imports.append(upload)
            for team in upload:
                self.teams[team["id"]] = dict(team)
            return 200, f"{len(upload)} new team(s) successfully added."
        raise AssertionError(f"unexpected call {method} {path}")


class NicknameTests(unittest.TestCase):
    def setUp(self):
        self.domjudge = FakeDomjudge()
        self.original = EDITOR.domjudge_request
        EDITOR.domjudge_request = self.domjudge

    def tearDown(self):
        EDITOR.domjudge_request = self.original

    def assertNicknameError(self, status, call, *args):
        with self.assertRaises(EDITOR.NicknameError) as caught:
            call(*args)
        self.assertEqual(caught.exception.status, status)
        return str(caught.exception)

    def test_team_without_a_name_is_asked_for_one(self):
        self.assertEqual(EDITOR.nickname_state("team-cookie"), {"needs_nickname": True, "display_name": "", "guest": False})

    def test_team_with_a_name_is_not_asked_again(self):
        self.domjudge.sessions["team-cookie"]["team_id"] = "user_002"
        self.assertEqual(EDITOR.nickname_state("team-cookie"), {"needs_nickname": False, "display_name": "코알라", "guest": False})

    def test_logged_out_visitor_is_rejected(self):
        self.assertNicknameError(401, EDITOR.nickname_state, "")

    def test_account_without_a_team_is_not_asked(self):
        self.assertEqual(EDITOR.nickname_state("admin-cookie"), {"needs_nickname": False, "display_name": "", "guest": False})
        self.assertNicknameError(403, EDITOR.set_nickname, "admin-cookie", "운영진")

    def test_saving_a_name_moves_the_team_onto_the_scoreboard(self):
        saved = EDITOR.set_nickname("team-cookie", "  알고리즘 고수  ")

        self.assertEqual(saved, "알고리즘 고수")
        self.assertEqual(self.domjudge.imports, [[
            {"id": "user_001", "name": "user_001", "display_name": "알고리즘 고수", "group_ids": ["participants"]}
        ]])

    def test_teams_in_other_groups_keep_their_group(self):
        self.domjudge.teams["user_001"]["group_ids"] = ["staff"]
        EDITOR.set_nickname("team-cookie", "운영 테스트")
        self.assertEqual(self.domjudge.teams["user_001"]["group_ids"], ["staff"])

    def test_the_team_is_taken_from_the_session_not_the_request(self):
        EDITOR.set_nickname("team-cookie", "새이름")
        self.assertEqual(self.domjudge.teams["user_002"]["display_name"], "코알라")

    def test_a_name_can_only_be_set_once(self):
        EDITOR.set_nickname("team-cookie", "첫이름")
        message = self.assertNicknameError(409, EDITOR.set_nickname, "team-cookie", "둘째이름")
        self.assertIn("이미", message)
        self.assertEqual(self.domjudge.teams["user_001"]["display_name"], "첫이름")

    def test_a_name_used_by_another_team_is_rejected(self):
        self.assertNicknameError(409, EDITOR.set_nickname, "team-cookie", "코알라")
        self.assertNicknameError(409, EDITOR.set_nickname, "team-cookie", " USER_002 ")
        self.assertEqual(self.domjudge.imports, [])

    def test_blank_long_or_control_character_names_are_rejected(self):
        for name in ("", "   ", "가" * (EDITOR.NICKNAME_MAX_LENGTH + 1), "줄\n바꿈", "탭\t이름"):
            with self.subTest(name=name):
                self.assertNicknameError(400, EDITOR.set_nickname, "team-cookie", name)
        self.assertEqual(self.domjudge.imports, [])

    def test_name_at_the_length_limit_is_accepted(self):
        name = "가" * EDITOR.NICKNAME_MAX_LENGTH
        self.assertEqual(EDITOR.set_nickname("team-cookie", name), name)


class NicknameWiringTests(unittest.TestCase):
    def test_editor_routes_answer_the_participant_nickname_path(self):
        source = EDITOR_PATH.read_text(encoding="utf-8")
        self.assertIn('NICKNAME_PATH = "/participant/nickname"', source)

    def test_nginx_exposes_only_the_nickname_path_to_participants(self):
        self.assertIn("location = /participant/nickname {", NGINX)
        self.assertIn("proxy_pass http://problem-editor:8088/participant/nickname;", NGINX)

    def test_authoring_requires_an_operator_not_just_any_login(self):
        # /api/v4/user는 참가자 계정에도 200을 준다. 운영자만 통과하는 목록 API로 확인한다.
        self.assertNotIn("proxy_pass http://127.0.0.1/api/v4/user;", NGINX)
        self.assertIn("proxy_pass http://127.0.0.1/api/v4/users?ids%5B%5D=admin;", NGINX)

    def test_editor_can_read_the_domjudge_admin_password(self):
        self.assertIn("dj_domserver_etc:/domjudge-etc:ro", COMPOSE)

    def test_provisioner_does_not_overwrite_names_participants_chose(self):
        self.assertNotIn("import_once users/teams -m POST -f json=/bootstrap/teams.json", PROVISION)
        self.assertIn("import_new_teams /bootstrap/teams.json", PROVISION)

    def test_portal_asks_for_a_name_on_first_login(self):
        self.assertIn("function askForNickname()", PORTAL)
        self.assertIn('"/participant/nickname"', PORTAL)
        self.assertIn("askForNickname();", PORTAL)


if __name__ == "__main__":
    unittest.main()
