"""KAUPC가 끝난 뒤 결과를 그대로 두고, 같은 문제로 로그인 없이 참여하는 공개 대회를 연다."""

import importlib.util
import base64
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTESTS = ROOT / "problems" / "contests"
EDITOR_PATH = ROOT / "tools" / "problem-editor" / "app.py"
NGINX = (ROOT / "custom" / "nginx" / "domjudge-site.conf").read_text(encoding="utf-8")
PROVISION = (ROOT / "bootstrap" / "provision.sh").read_text(encoding="utf-8")
PORTAL = (ROOT / "custom" / "js" / "contest-portal.js").read_text(encoding="utf-8")
GROUPS = json.loads((ROOT / "bootstrap" / "groups.json").read_text(encoding="utf-8"))


def load_editor_module():
    spec = importlib.util.spec_from_file_location("problem_editor_guest_under_test", EDITOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EDITOR = load_editor_module()


class FakeDomjudge:
    def __init__(self, fail=None):
        self.teams = {}
        self.accounts = {}
        self.fail = fail

    def __call__(self, method, path, cookie=None, upload=None):
        if path == self.fail:
            return 500, {"message": "boom"}
        if method == "POST" and path == "/api/v4/users/teams":
            for team in upload:
                self.teams[team["id"]] = dict(team)
            return 200, "ok"
        if method == "POST" and path == "/api/v4/users/accounts":
            for account in upload:
                self.accounts[account["username"]] = dict(account)
            return 200, "ok"
        if path == "/api/v4/user":
            return 200, {"roles": ["team"], "team_id": cookie}
        if method == "GET" and path == "/api/v4/teams":
            return 200, list(self.teams.values())
        if method == "GET" and path.startswith("/api/v4/teams/"):
            return 200, self.teams[path.rsplit("/", 1)[1]]
        raise AssertionError(f"unexpected call {method} {path}")


class OpenContestPackageTests(unittest.TestCase):
    def test_open_contest_reuses_every_kaupc_problem_without_copying(self):
        kaupc = sorted(p.name for p in (CONTESTS / "KAUPC").iterdir() if p.is_dir())
        opened = sorted(p.name for p in (CONTESTS / "OPEN").iterdir() if p.is_dir())
        self.assertEqual(opened, kaupc)
        for label in opened:
            with self.subTest(label=label):
                folder = CONTESTS / "OPEN" / label
                self.assertEqual([p.name for p in folder.iterdir()], ["source.txt"])
                # provisioner는 source.txt를 한 번만 따라간다. KAUPC가 다시 빌려 쓰는 문제는 실제 패키지를 가리켜야 한다.
                source = (CONTESTS / "OPEN" / folder.joinpath("source.txt").read_text(encoding="utf-8").strip()).resolve()
                self.assertTrue((source / "problem.yaml").is_file(), source)
                original = CONTESTS / "KAUPC" / label
                if (original / "source.txt").is_file():
                    original = (CONTESTS / "KAUPC" / (original / "source.txt").read_text(encoding="utf-8").strip()).resolve()
                self.assertEqual(source, original.resolve())

    def test_open_contest_has_its_own_id_and_no_freeze(self):
        contest = (CONTESTS / "OPEN" / "contest.yaml").read_text(encoding="utf-8")
        self.assertIn("id: kaupcopen\n", contest)
        self.assertIn("duration: 336:00:00\n", contest)
        self.assertIn("scoreboard_freeze_duration: 0:00:00\n", contest)

    def test_kaupc_contest_definition_is_untouched(self):
        contest = (CONTESTS / "KAUPC" / "contest.yaml").read_text(encoding="utf-8")
        self.assertIn("id: kaupc\n", contest)
        self.assertIn("start_time: 2026-10-31T14:00:00+09:00\n", contest)
        self.assertIn("duration: 4:00:00\n", contest)


class ProvisionTests(unittest.TestCase):
    def test_finished_kaupc_is_closed_to_teams_created_later(self):
        self.assertIn("INSERT IGNORE INTO contestteam", PROVISION)
        self.assertIn("UPDATE contest SET public = 0, open_to_all_teams = 0 WHERE cid = $cid;", PROVISION)
        # 한 번만 묶는다. 나중에 이름을 정한 계정이 끝난 대회에 다시 들어가지 않는다.
        self.assertIn('run_once "lock-$1-teams"', PROVISION)

    def test_locking_runs_after_contests_are_created(self):
        self.assertGreater(PROVISION.index("lock_finished_contest \"$finished\""), PROVISION.index("for pass in own reused"))

    def test_finished_kaupc_is_private_but_stays_reachable_by_the_admin_api(self):
        self.assertIn('FINISHED_CONTESTS="kaupc"', PROVISION)
        self.assertIn("UPDATE contest SET public = 0, open_to_all_teams = 0 WHERE cid = $cid;", PROVISION)
        # 비활성 시각을 쓰거나 끄면 관리자 API가 대회를 못 찾아 다음 배포가 실패한다.
        self.assertNotIn("SET deactivatetime", PROVISION)
        self.assertNotIn("SET enabled = 0 WHERE externalid = 'kaupc'", PROVISION)

    def test_empty_kaupc_open_contest_has_no_teams(self):
        self.assertIn("for staff_only in test kaupc-open; do", PROVISION)

    def test_open_contest_is_public_and_only_guests_take_part(self):
        self.assertIn('OPEN_CONTESTS="kaupcopen"', PROVISION)
        self.assertIn("SET enabled = 1, public = 1, open_to_all_teams = 0 WHERE externalid = '$open_contest'", PROVISION)
        self.assertIn("INSERT IGNORE INTO contestteamcategory", PROVISION)
        self.assertIn("tc.externalid = 'guests'", PROVISION)

    def test_jury_pages_ask_for_an_account_instead_of_entering_as_guest(self):
        caddy = (ROOT / "deploy" / "aws" / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn("@jury path /jury /jury/*", caddy)
        self.assertIn('header_down Location "^(https?://[^/]+)?/login$" "/login?account=1"', caddy)
        self.assertIn("@denied status 403", caddy)
        self.assertIn("redir * /login?account=1 temporary", caddy)

    def test_failed_account_login_stays_on_the_login_page_with_its_error(self):
        caddy = (ROOT / "deploy" / "aws" / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn('header_down Location "^(https?://[^/]+)?/login$" "/login?account=1&failed=1"', caddy)
        # 오류 문구는 세션에 있다. 이때는 세션 쿠키를 지우지 않는다.
        self.assertIn("not query failed=1", caddy)

    def test_guests_have_no_scoreboard_but_accounts_keep_it(self):
        self.assertIn("if (state && state.guest) hideScoreboardFromGuest();", PORTAL)
        self.assertIn('location.replace("/contest/status")', PORTAL)
        # KAUPC 계정은 이 탭으로 자기 대회 결과를 본다. 탭 자체는 그대로 만든다.
        self.assertIn('<a href="/contest/scoreboard">순위표</a>', PORTAL)

    def test_guest_header_offers_login_in_place_of_logout(self):
        self.assertIn("function offerGuestLogin()", PORTAL)
        self.assertIn('a[href="/logout"]', PORTAL)
        self.assertIn('"/login?account=1"', PORTAL)
        self.assertIn("if (state && state.guest) offerGuestLogin();", PORTAL)

    def test_account_login_page_opens_even_with_a_guest_session(self):
        caddy = (ROOT / "deploy" / "aws" / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn("query account=1", caddy)
        self.assertIn("request_header @account_login -Cookie", caddy)

    def test_open_contest_scoreboard_never_freezes(self):
        # DOMjudge는 duration이 큰 대회의 프리즈 0시간을 대회 중간 시각으로 계산한다. 프리즈를 아예 지운다.
        self.assertIn("SET freezetime = NULL, freezetime_string = NULL WHERE externalid = '$open_contest'", PROVISION)

    def test_guest_groups_exist(self):
        hidden = {group["id"]: group["hidden"] for group in GROUPS}
        self.assertFalse(hidden["guests"])
        self.assertTrue(hidden["guest-pending"])


class GuestAccountTests(unittest.TestCase):
    def setUp(self):
        self.domjudge = FakeDomjudge()
        self.original = EDITOR.domjudge_request
        EDITOR.domjudge_request = self.domjudge
        EDITOR._guest_history.clear()

    def tearDown(self):
        EDITOR.domjudge_request = self.original
        EDITOR._guest_history.clear()

    def test_guest_gets_a_fresh_team_and_account(self):
        guest = EDITOR.create_guest("1.2.3.4")
        self.assertRegex(guest["username"], r"^guest_[a-z0-9]{10}$")
        self.assertGreaterEqual(len(guest["password"]), 24)
        team = self.domjudge.teams[guest["username"]]
        self.assertEqual(team["group_ids"], ["guests"])
        self.assertEqual(team["display_name"], "게스트 " + guest["username"][6:12])
        account = self.domjudge.accounts[guest["username"]]
        self.assertEqual(account["type"], "team")
        self.assertEqual(account["team_id"], guest["username"])
        self.assertEqual(account["password"], guest["password"])

    def test_every_guest_is_separate(self):
        names = {EDITOR.create_guest(f"10.0.0.{n}")["username"] for n in range(5)}
        self.assertEqual(len(names), 5)

    def test_one_client_cannot_create_many_accounts(self):
        for _ in range(EDITOR.GUEST_PER_CLIENT_PER_HOUR):
            EDITOR.create_guest("1.2.3.4")
        with self.assertRaises(EDITOR.NicknameError) as caught:
            EDITOR.create_guest("1.2.3.4")
        self.assertEqual(caught.exception.status, 429)
        EDITOR.create_guest("5.6.7.8")

    def test_limit_resets_after_an_hour(self):
        for _ in range(EDITOR.GUEST_PER_CLIENT_PER_HOUR):
            self.assertTrue(EDITOR.guest_allowed("c", now=0))
        self.assertFalse(EDITOR.guest_allowed("c", now=10))
        self.assertTrue(EDITOR.guest_allowed("c", now=3601))

    def test_failed_import_is_reported(self):
        EDITOR.domjudge_request = FakeDomjudge(fail="/api/v4/users/accounts")
        with self.assertRaises(EDITOR.NicknameError) as caught:
            EDITOR.create_guest("1.2.3.4")
        self.assertEqual(caught.exception.status, 502)

    def test_guest_is_never_asked_for_a_name(self):
        guest = EDITOR.create_guest("1.2.3.4")
        self.assertFalse(EDITOR.nickname_state(guest["username"])["needs_nickname"])
        self.assertTrue(EDITOR.nickname_state(guest["username"])["guest"])


class GuestEntryTests(unittest.TestCase):
    """로그인 화면 대신 서버가 게스트로 로그인시킨다."""

    def setUp(self):
        self.domjudge = FakeDomjudge()
        self.original = (EDITOR.domjudge_request, EDITOR.domjudge_login)
        EDITOR.domjudge_request = self.domjudge
        self.logins = []

        def fake_login(username, password):
            self.logins.append(username)
            ok = self.domjudge.accounts.get(username, {}).get("password") == password
            return [f"PHPSESSID=s-{username}; path=/; httponly"] if ok else None

        EDITOR.domjudge_login = fake_login
        EDITOR._guest_history.clear()

    def tearDown(self):
        EDITOR.domjudge_request, EDITOR.domjudge_login = self.original
        EDITOR._guest_history.clear()

    def test_first_visit_creates_a_guest_and_logs_in(self):
        cookies, credential = EDITOR.enter_as_guest("", "1.2.3.4")
        username, password = credential.split(":")
        self.assertEqual(self.domjudge.accounts[username]["password"], password)
        self.assertEqual(cookies, [f"PHPSESSID=s-{username}; path=/; httponly"])

    def test_returning_visitor_keeps_the_same_account(self):
        _, credential = EDITOR.enter_as_guest("", "1.2.3.4")
        _, again = EDITOR.enter_as_guest(credential, "1.2.3.4")
        self.assertEqual(again, credential)
        self.assertEqual(len(self.domjudge.accounts), 1)

    def test_deleted_account_is_replaced(self):
        _, credential = EDITOR.enter_as_guest("guest_gone000:" + "x" * 24, "1.2.3.4")
        self.assertNotEqual(credential.split(":")[0], "guest_gone000")
        self.assertEqual(self.logins[0], "guest_gone000")

    def test_cookie_cannot_name_a_non_guest_account(self):
        EDITOR.enter_as_guest("koala:not-a-guest", "1.2.3.4")
        self.assertNotIn("koala", self.logins)

    def test_rate_limit_shows_an_error_instead_of_a_login_page(self):
        for n in range(EDITOR.GUEST_PER_CLIENT_PER_HOUR):
            EDITOR.enter_as_guest("", "1.2.3.4")
        with self.assertRaises(EDITOR.NicknameError) as caught:
            EDITOR.enter_as_guest("", "1.2.3.4")
        self.assertEqual(caught.exception.status, 429)


class PublicSubmissionsTests(unittest.TestCase):
    def setUp(self):
        self.original = EDITOR.domjudge_request
        self.calls = []
        base = "/api/v4/contests/kaupcopen"
        data = {
            f"{base}/groups": [{"id": "guests", "hidden": False}, {"id": "staff", "hidden": True}],
            f"{base}/teams": [
                {"id": "guest_a", "name": "guest_a", "display_name": "게스트 a", "group_ids": ["guests"]},
                {"id": "tester", "name": "tester", "display_name": "tester", "group_ids": ["staff"]},
            ],
            f"{base}/problems": [{"id": "wavingbanner", "label": "A", "name": "현수막 출력하기", "test_data_count": 42}],
            f"{base}/languages": [{"id": "cpp", "name": "C++"}],
            f"{base}/judgements": [
                {"submission_id": "1", "judgement_type_id": "WA", "valid": False, "start_time": "2026-11-01T10:00:00"},
                {"id": "j2", "submission_id": "1", "judgement_type_id": "AC", "valid": True, "start_time": "2026-11-01T10:05:00", "max_run_time": 0.012},
            ],
            f"{base}/runs": [
                {"id": "r2", "judgement_id": "j2", "ordinal": 2, "judgement_type_id": "WA", "run_time": 0.5},
                {"id": "r1", "judgement_id": "j2", "ordinal": 1, "judgement_type_id": "AC", "run_time": 0.012},
                {"id": "r0", "judgement_id": "j1", "ordinal": 1, "judgement_type_id": "WA", "run_time": 0.1},
            ],
            f"{base}/submissions": [
                {"id": "1", "team_id": "guest_a", "problem_id": "wavingbanner", "language_id": "cpp", "time": "2026-11-01T10:00:00+09:00"},
                {"id": "2", "team_id": "guest_a", "problem_id": "wavingbanner", "language_id": "cpp", "time": "2026-11-01T11:00:00+09:00"},
                {"id": "3", "team_id": "tester", "problem_id": "wavingbanner", "language_id": "cpp", "time": "2026-11-01T12:00:00+09:00"},
            ],
            f"{base}/judgements?submission_id=1": [
                {"id": "j1", "submission_id": "1", "judgement_type_id": "WA", "valid": False, "start_time": "2026-11-01T10:00:00"},
                {"id": "j2", "submission_id": "1", "judgement_type_id": "AC", "valid": True, "start_time": "2026-11-01T10:05:00"},
            ],
            # DOMjudge는 모르는 조건을 무시하고 대회의 모든 실행을 돌려준다. 다른 채점의 결과가 섞이면 안 된다.
            f"{base}/runs?judging_id=j2": [
                {"id": "r2", "judgement_id": "j2", "ordinal": 2, "judgement_type_id": "WA", "run_time": 0.5},
                {"id": "r1", "judgement_id": "j2", "ordinal": 1, "judgement_type_id": "AC", "run_time": 0.012},
                {"id": "r0", "judgement_id": "j1", "ordinal": 1, "judgement_type_id": "WA", "run_time": 0.1},
            ],
            f"{base}/submissions/1/source-code": [
                {"id": "1", "filename": "main.cpp", "source": base64.b64encode("// 한글\n".encode("utf-8")).decode("ascii")},
            ],
            f"{base}/judgements?submission_id=2": [],
            f"{base}/submissions/2/source-code": [
                {"id": "2", "filename": "main.cpp", "source": base64.b64encode(b"int main;").decode("ascii")},
            ],
        }

        def fake(method, path, cookie=None, upload=None):
            self.calls.append(path)
            return 200, data[path]

        self.db_calls = []
        self.db_row = {"compile": b"warning: unused\n"}

        def fake_db(query, args):
            self.db_calls.append((query, args))
            return self.db_row

        self.original_db = EDITOR._db_one
        EDITOR._db_one = fake_db
        EDITOR.domjudge_request = fake
        EDITOR._status_cache.update({"at": 0.0, "value": None})
        EDITOR._submission_details.clear()

    def tearDown(self):
        EDITOR.domjudge_request = self.original
        EDITOR._db_one = self.original_db
        EDITOR._status_cache.update({"at": 0.0, "value": None})
        EDITOR._submission_details.clear()

    def test_lists_open_contest_submissions_newest_first_without_hidden_teams(self):
        rows = EDITOR.public_submissions()["submissions"]
        self.assertEqual([row["id"] for row in rows], ["2", "1"])
        self.assertEqual(rows[1], {
            "id": "1", "time": "2026-11-01T10:00:00+09:00", "team": "게스트 a", "problem": "A",
            "problem_name": "현수막 출력하기", "language": "C++", "verdict": "AC", "runtime": 0.012, "tests": 42, "cases": ["AC", "WA"],
        })
        self.assertIsNone(rows[0]["verdict"])
        self.assertEqual(rows[0]["cases"], [])

    def test_detail_opens_code_and_every_test_result(self):
        detail = EDITOR.public_submission_detail("1")
        self.assertEqual(detail["team"], "게스트 a")
        self.assertEqual(detail["tests"], 42)
        self.assertEqual(detail["sources"], [{"filename": "main.cpp", "source": "// 한글\n"}])
        self.assertEqual(detail["runs"], [
            {"ordinal": 1, "verdict": "AC", "runtime": 0.012},
            {"ordinal": 2, "verdict": "WA", "runtime": 0.5},
        ])

    def test_detail_of_a_submission_still_being_judged_has_no_runs(self):
        detail = EDITOR.public_submission_detail("2")
        self.assertEqual(detail["runs"], [])
        self.assertEqual(detail["sources"], [{"filename": "main.cpp", "source": "int main;"}])

    def test_detail_is_limited_to_the_public_list(self):
        for submission in ("3", "999", "1/source-code", "../kaupc", ""):
            with self.subTest(submission=submission):
                with self.assertRaises(EDITOR.NicknameError) as caught:
                    EDITOR.public_submission_detail(submission)
                self.assertEqual(caught.exception.status, 404)
        self.assertFalse(any("submissions/3" in path for path in self.calls))

    def test_detail_includes_compile_output(self):
        self.assertEqual(EDITOR.public_submission_detail("1")["compile_output"], "warning: unused\n")

    def test_detail_still_opens_when_the_database_fails(self):
        def broken(query, args):
            raise OSError("down")
        EDITOR._db_one = broken
        detail = EDITOR.public_submission_detail("1")
        self.assertEqual(detail["compile_output"], "")
        self.assertEqual(detail["sources"], [{"filename": "main.cpp", "source": "// 한글\n"}])
        self.assertEqual(EDITOR._submission_details, {})

    def test_run_data_opens_input_answer_output_and_checker_message(self):
        self.db_row = {
            "input": b"1 2\n", "input_size": 4,
            "answer": b"3\n", "answer_size": 2,
            "output": b"4\n", "output_size": 2,
            "diff": b"Wrong answer\n", "diff_size": 13,
            "error": None, "error_size": None,
        }
        data = EDITOR.public_run_data("1", 2)
        self.assertEqual(self.db_calls[0][1], ("1", 2))
        self.assertIn("j.valid = 1", self.db_calls[0][0])
        self.assertIn("jr.runresult IS NOT NULL", self.db_calls[0][0])
        self.assertEqual(data["input"], {"text": "1 2\n", "size": 4, "truncated": False})
        self.assertEqual(data["answer"]["text"], "3\n")
        self.assertEqual(data["output"]["text"], "4\n")
        self.assertEqual(data["diff"]["text"], "Wrong answer\n")
        self.assertEqual(data["error"], {"text": "", "size": 0, "truncated": False})

    def test_large_run_data_is_marked_as_cut(self):
        limit = EDITOR.RUN_TEXT_LIMIT
        self.db_row = {key: None for key in ("answer", "answer_size", "output", "output_size", "diff", "diff_size", "error", "error_size")}
        self.db_row.update({"input": b"x" * limit, "input_size": limit + 1})
        self.assertTrue(EDITOR.public_run_data("1", 1)["input"]["truncated"])

    def test_run_that_did_not_finish_is_not_found(self):
        self.db_row = None
        for call in (lambda: EDITOR.public_run_data("1", 9), lambda: EDITOR.public_run_file("1", 9, "input")):
            with self.assertRaises(EDITOR.NicknameError) as caught:
                call()
            self.assertEqual(caught.exception.status, 404)

    def test_run_data_is_limited_to_the_public_list(self):
        for call in (lambda: EDITOR.public_run_data("3", 1), lambda: EDITOR.public_run_file("48", 1, "input")):
            with self.assertRaises(EDITOR.NicknameError) as caught:
                call()
            self.assertEqual(caught.exception.status, 404)
        self.assertEqual(self.db_calls, [])

    def test_run_file_returns_the_whole_data_for_known_kinds_only(self):
        self.db_row = {"content": b"full"}
        self.assertEqual(EDITOR.public_run_file("1", 1, "answer"), b"full")
        self.assertIn("tc.output AS content", self.db_calls[0][0])
        with self.assertRaises(EDITOR.NicknameError):
            EDITOR.public_run_file("1", 1, "password")

    def test_only_finished_details_are_kept(self):
        EDITOR.public_submission_detail("1")
        count = len(self.calls)
        EDITOR.public_submission_detail("1")
        self.assertEqual(len(self.calls), count)
        EDITOR.public_submission_detail("2")
        count = len(self.calls)
        EDITOR.public_submission_detail("2")
        self.assertGreater(len(self.calls), count)

    def test_list_itself_carries_no_source_code(self):
        EDITOR.public_submissions()
        self.assertFalse(any("source" in path or "files" in path for path in self.calls))

    def test_results_are_cached_briefly(self):
        EDITOR.cached_public_submissions(now=100)
        count = len(self.calls)
        EDITOR.cached_public_submissions(now=102)
        self.assertEqual(len(self.calls), count)
        EDITOR.cached_public_submissions(now=100 + EDITOR.PUBLIC_SUBMISSIONS_CACHE_SECONDS)
        self.assertGreater(len(self.calls), count)


class GuestWiringTests(unittest.TestCase):
    def test_root_and_public_go_straight_to_problems(self):
        # 첫 화면은 DOMjudge가 권한에 따라 나눈다. 운영자는 로그인 뒤 운영자 화면으로 간다.
        self.assertNotIn('if ($uri = "/") {', NGINX)
        self.assertIn('if ($uri = "/public") {\n\t\treturn 302 /team;', NGINX)

    def test_first_screen_shows_the_open_contest_list(self):
        editor = EDITOR_PATH.read_text(encoding="utf-8")
        self.assertIn('self.send_header("Location", "/team")', editor)
        self.assertNotIn('self.send_header("Location", "/team/problems")', editor)

    def test_status_tab_is_wired(self):
        caddy = (ROOT / "deploy" / "aws" / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn("@contest_status path /contest/status", caddy)
        self.assertLess(caddy.index("@contest_status path"), caddy.index("@contest_path path /contest/*"))
        self.assertIn("location = /participant/submissions {", NGINX)
        self.assertIn('<a href="/contest/status">채점 현황</a>', PORTAL)
        self.assertIn("function buildStatusPage()", PORTAL)
        self.assertIn('fetch("/participant/submissions"', PORTAL)

    def test_submission_page_follows_the_jury_submission_page(self):
        caddy = (ROOT / "deploy" / "aws" / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn("@contest_status_detail path_regexp ^/contest/status/[0-9]+$", caddy)
        self.assertLess(caddy.index("@contest_status_detail"), caddy.index("@contest_path path /contest/*"))
        self.assertIn("rewrite * /team", caddy)
        self.assertIn("location ^~ /participant/submissions/ {", NGINX)
        self.assertIn('fetch("/participant/submissions/" + encodeURIComponent(id)', PORTAL)
        self.assertIn("function buildSubmissionPage(", PORTAL)
        self.assertIn('"제출 코드 · #"', PORTAL)
        self.assertIn('"결과 새로고침"', PORTAL)
        self.assertIn('"테스트 결과 · "', PORTAL)
        self.assertIn('"/contest/status/" + encodeURIComponent(row.id)', PORTAL)
        # 코드는 HTML로 넣지 않는다. 다른 사람의 코드가 화면에서 실행되면 안 된다.
        self.assertIn("pre.textContent = source.source", PORTAL)
        self.assertNotIn("contest-status__detail-row", PORTAL)

    def test_submission_page_opens_test_data_and_compile_output(self):
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        editor = compose[compose.index("  problem-editor:"):]
        self.assertIn("MYSQL_HOST: mariadb", editor)
        self.assertIn("MYSQL_PASSWORD: ${MYSQL_PASSWORD:-domjudge_pw}", editor)
        self.assertIn("pymysql", (ROOT / "tools" / "problem-editor" / "Dockerfile").read_text(encoding="utf-8"))
        self.assertIn("function renderRunPanel(", PORTAL)
        self.assertIn('"/runs/"', PORTAL)
        for label in ("입력", "정답", "프로그램 출력", "채점기 메시지", "컴파일 결과"):
            self.assertIn(label, PORTAL)
        self.assertIn("X-Content-Type-Options", EDITOR_PATH.read_text(encoding="utf-8"))

    def test_nginx_sends_the_login_page_to_guest_entry(self):
        self.assertIn('"GET:/login:" 1;', NGINX)
        self.assertIn("map \"$request_method:$uri:$arg_account\" $kaupc_guest_entry {", NGINX)
        self.assertIn("rewrite ^ /participant/enter last;", NGINX)

    def test_guest_entry_is_reachable_only_through_the_login_rewrite(self):
        block = NGINX[NGINX.index("location = /participant/enter {"):]
        block = block[:block.index("}")]
        self.assertIn("internal;", block)
        self.assertIn("proxy_pass http://problem-editor:8088/participant/enter;", block)
        self.assertIn("X-Forwarded-For $proxy_add_x_forwarded_for", block)

    def test_server_side_login_uses_the_original_login_page(self):
        # ?account=1이 없으면 nginx가 다시 게스트 입장으로 보내 무한히 돈다.
        source = EDITOR_PATH.read_text(encoding="utf-8")
        self.assertIn('ACCOUNT_LOGIN_PATH = "/login?account=1"', source)

    def test_editor_routes_guest_entry(self):
        source = EDITOR_PATH.read_text(encoding="utf-8")
        self.assertIn('GUEST_ENTER_PATH = "/participant/enter"', source)
        self.assertIn("self.handle_enter()", source)

    def test_portal_has_no_guest_login_screen(self):
        self.assertNotIn("guest-entry", PORTAL)
        self.assertNotIn('"/participant/guest"', PORTAL)

    def test_portal_names_the_open_contest(self):
        self.assertIn('return "KAUPC2026 Open";', PORTAL)


if __name__ == "__main__":
    unittest.main()
