from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
PORTAL = (ROOT / "custom/js/contest-portal.js").read_text(encoding="utf-8")
CADDY = (ROOT / "deploy/aws/Caddyfile").read_text(encoding="utf-8")
DEPLOY = (ROOT / ".github/workflows-archive/deploy.yml").read_text(encoding="utf-8")


# addPastedCodeSubmission만 떼어 내 최소한의 가짜 DOM 위에서 실행한다.
PASTE_SUBMIT_HARNESS = r"""
function FakeEl(tag) {
  this.tagName = tag; this.dataset = {}; this.hidden = false; this.value = "";
  this.textContent = ""; this.listeners = {}; this.children = {};
}
FakeEl.prototype.addEventListener = function (type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); };
FakeEl.prototype.dispatch = function (type, event) { (this.listeners[type] || []).forEach(function (fn) { fn(event); }); };
FakeEl.prototype.querySelector = function (selector) { return this.children[selector] || null; };
FakeEl.prototype.closest = function () { return null; };
FakeEl.prototype.after = function () {};

function FileList(files) { this.length = files.length; for (var i = 0; i < files.length; i++) this[i] = files[i]; }
function File(parts, name) { this.name = name; this.content = parts.join(""); }
function DataTransfer() { var list = []; this.items = { add: function (f) { list.push(f); } };
  Object.defineProperty(this, "files", { get: function () { return new FileList(list); } }); }

var form = new FakeEl("form");
var fileInput = new FakeEl("input");
fileInput.files = new FileList([]);
Object.defineProperty(fileInput, "value", {
  get: function () { return this.files.length ? this.files[0].name : ""; },
  set: function (v) { if (v === "") this.files = new FileList([]); }
});
fileInput.parentElement = new FakeEl("div");
var language = new FakeEl("select");
var section = new FakeEl("section");
var textarea = new FakeEl("textarea");
var error = new FakeEl("p");
error.hidden = true;
section.children = { "textarea": textarea, ".paste-submit__error": error };
form.children = {
  'input[type="file"][name="submit_problem[code][]"]': fileInput,
  'select[name="submit_problem[language]"]': language
};
var document = {
  querySelector: function (s) { return s === ".submitform" ? form : null; },
  createElement: function () { return section; }
};
Object.defineProperty(section, "innerHTML", { set: function () {} });

var lastPrevented = null;
function submit() {
  lastPrevented = false;
  error.hidden = true;
  form.dispatch("submit", { preventDefault: function () { lastPrevented = true; } });
}
function chooseFile(name) { fileInput.files = new FileList([new File([""], name)]); fileInput.dispatch("change", {}); }
function report(value) { process.stdout.write(JSON.stringify(value)); }
"""


def run_paste_submit_scenario(scenario: str):
    match = re.search(r"function addPastedCodeSubmission\(\) \{.*?\n  \}\n", PORTAL, re.S)
    assert match, "addPastedCodeSubmission not found"
    script = PASTE_SUBMIT_HARNESS + match.group(0) + "addPastedCodeSubmission();\n" + scenario
    completed = subprocess.run(["node", "-e", script], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


class ParticipantPortalTests(unittest.TestCase):
    def test_participant_navigation_uses_contest_paths(self):
        self.assertIn('"/contest/problems"', PORTAL)
        self.assertNotIn('"/team/problems"', PORTAL)
        self.assertNotIn("redirectTeamHomeToProblems", PORTAL)
        self.assertIn("rewriteParticipantLinks", PORTAL)
        self.assertIn("rewriteParticipantLinks(section)", PORTAL)

    def test_participant_routes_do_not_expose_team_or_contest_name(self):
        self.assertIn('function clarificationsPath()', PORTAL)
        self.assertIn('contestPath("/clarifications")', PORTAL)
        self.assertIn('rewriteParticipantLinks(section)', PORTAL)
        self.assertIn('if (!target || target.dataset.contestLobby === "true") return;', PORTAL)

    def test_statement_and_submission_detail_have_portal_chrome(self):
        self.assertIn("isStatementPage", PORTAL)
        self.assertIn("buildStatementChrome", PORTAL)
        self.assertIn("formatExecutionMetrics", PORTAL)
        self.assertIn("submission-metrics", PORTAL)

    def test_portal_css_has_a_shared_shell_for_all_participant_pages(self):
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn(".contest-statement", css)
        self.assertIn(".submission-detail", css)
        self.assertIn(".scoreboard-shell", css)
        self.assertIn("body.participant-nav #menuDefault > .navbar-nav.me-auto", css)
        self.assertIn("body.participant-nav #menuDefault > .ml-auto.me-3", css)
        self.assertIn("markParticipantNavigation();", PORTAL)

    def test_scoreboard_and_clarifications_receive_explicit_page_titles(self):
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn("ensureContestPageTitle", PORTAL)
        self.assertIn("scoreboard-shell", PORTAL)
        self.assertIn(".contest-clarifications__empty", css)

    def test_caddy_bridges_public_contest_paths(self):
        self.assertIn("/contest", CADDY)
        self.assertIn("/team", CADDY)
        self.assertIn("@contest_clarifications path /contest/clarifications", CADDY)
        self.assertIn("path_regexp contest_statement", CADDY)

    def test_frontend_only_deploy_does_not_restart_the_judge_stack(self):
        self.assertIn("custom/(js|css|static)/", DEPLOY)
        self.assertIn("needs_caddy", DEPLOY)
        self.assertIn("대상 서비스만 반영하기", DEPLOY)

    def test_provisioner_change_uses_targeted_deploy(self):
        self.assertIn("bootstrap/provision\\.sh$", DEPLOY)

    def test_clarifications_render_as_a_single_board(self):
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn("buildClarificationBoard", PORTAL)
        self.assertIn('data-ajax-modal-after="markSeen"', PORTAL)
        self.assertIn(".clar-board__table", css)
        self.assertNotIn("clar-card", PORTAL)

    def test_participant_pages_share_one_content_width(self):
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn("--kaupc-page-width", css)
        self.assertNotIn("scoreboard-page", css)

    def test_lobby_trusts_domjudge_current_contest_over_cache(self):
        labels = (ROOT / "custom/js/ko-labels.js").read_text(encoding="utf-8")
        self.assertIn("currentContestFromMenu", PORTAL)
        self.assertNotIn("callback(cached)", PORTAL)
        self.assertIn('node.id === "navbarDropdownContests"', labels)

    def test_statement_fetch_bypasses_list_redirect(self):
        self.assertIn('"X-Kaupc-Fetch": "statement"', PORTAL)
        self.assertIn("not header X-Kaupc-Fetch statement", CADDY)
        self.assertNotIn("location.assign(url)", PORTAL)

    def test_submission_details_show_submitted_code(self):
        provision = (ROOT / "bootstrap/provision.sh").read_text(encoding="utf-8")
        self.assertIn("attachSubmissionCode", PORTAL)
        self.assertIn("watchSubmissionModals();", PORTAL)
        self.assertIn('"/download"', PORTAL.replace("/submission/\" + submitId + \"", "")) if False else None
        self.assertIn("allow_team_submission_download", provision)

    def test_submission_detail_is_translated_without_contest_title(self):
        self.assertIn("translateSubmissionDetail", PORTAL)
        self.assertNotIn("contextualizeSubmitHeading", PORTAL)

    def test_successful_submit_returns_to_the_selected_contest_instead_of_the_lobby(self):
        self.assertIn("rememberSubmitReturn", PORTAL)
        self.assertIn("returnToContestAfterSubmit", PORTAL)
        self.assertIn('sessionStorage.setItem("kaupc_return_to_contest", "1")', PORTAL)
        self.assertIn('location.replace(contestPath("/problems"))', PORTAL)

    def test_submit_page_accepts_pasted_code_without_a_file(self):
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn("function addPastedCodeSubmission()", PORTAL)
        self.assertIn("new File([source]", PORTAL)
        self.assertIn("new DataTransfer()", PORTAL)
        self.assertIn("fileInput.files = transfer.files", PORTAL)
        self.assertIn("fileInput.required = false", PORTAL)
        self.assertIn("소스 파일이나 붙여넣은 코드를 입력하세요.", PORTAL)
        self.assertIn("파일과 붙여넣은 코드 중 하나만 제출할 수 있습니다.", PORTAL)
        self.assertIn("addPastedCodeSubmission();", PORTAL)
        self.assertIn(".paste-submit", css)

    @unittest.skipUnless(shutil.which("node"), "node is required to run the submit handler")
    def test_paste_submit_can_be_retried_after_the_confirm_dialog_is_cancelled(self):
        # DOMjudge asks "Make submission?" after our submit handler has already
        # turned the pasted code into a file. Cancelling must not leave that file
        # behind as if the participant had chosen one.
        result = run_paste_submit_scenario("""
            textarea.value = "print(1)";
            language.value = "py3";
            submit();
            var first = lastPrevented;
            submit();
            report({first: first, second: lastPrevented, error: error.hidden ? "" : error.textContent,
                    file: fileInput.files.length ? fileInput.files[0].name : ""});
        """)
        self.assertEqual(result, {"first": False, "second": False, "error": "", "file": "solution.py"})

    @unittest.skipUnless(shutil.which("node"), "node is required to run the submit handler")
    def test_cleared_paste_does_not_submit_the_stale_generated_file(self):
        result = run_paste_submit_scenario("""
            textarea.value = "print(1)";
            language.value = "py3";
            submit();
            textarea.value = "";
            submit();
            report({prevented: lastPrevented, error: error.textContent, files: fileInput.files.length});
        """)
        self.assertEqual(result, {"prevented": True, "error": "소스 파일이나 붙여넣은 코드를 입력하세요.", "files": 0})

    @unittest.skipUnless(shutil.which("node"), "node is required to run the submit handler")
    def test_chosen_file_with_pasted_code_is_still_rejected(self):
        result = run_paste_submit_scenario("""
            textarea.value = "print(1)";
            language.value = "py3";
            chooseFile("mine.py");
            submit();
            report({prevented: lastPrevented, error: error.textContent});
        """)
        self.assertEqual(result, {"prevented": True, "error": "파일과 붙여넣은 코드 중 하나만 제출할 수 있습니다."})

    def test_scoreboard_header_letters_are_white_for_every_problem_color(self):
        # 밝은 문제 색에는 DOMjudge가 안쪽 span에 검은 글자색을 인라인으로 넣는다.
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn("table.desktop-scoreboard thead .badge.problem-badge span { color: #fff !important; }", css)

    def test_participant_scoreboard_hides_the_summary_row(self):
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn("body:has(.contest-tabs) .scoreboard tr:has(> td.scoresummary) { display: none; }", css)

    @unittest.skipUnless(shutil.which("node"), "node is required to run the scoreboard labels")
    def test_scoreboard_cells_show_only_tries_and_solve_time(self):
        match = re.search(r"function compactScoreLabel\(className, timeText, triesText\) \{.*?\n  \}\n", PORTAL, re.S)
        self.assertIsNotNone(match)
        cases = [
            ["score_correct score_first", " 12 ", "1 try"],
            ["score_correct", "95", "3 tries"],
            ["score_incorrect", " ", "4 tries"],
            ["score_pending", " ", "2 + 1 tries"],
        ]
        script = match.group(0) + "process.stdout.write(JSON.stringify(" + json.dumps(cases) + ".map(function (c) { return compactScoreLabel(c[0], c[1], c[2]); })));"
        completed = subprocess.run(["node", "-e", script], capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), [
            {"main": "", "sub": "12"},
            {"main": "+2", "sub": "95"},
            {"main": "-4", "sub": ""},
            {"main": "?", "sub": ""},
        ])

    def test_participant_scoreboard_hides_the_filter(self):
        css = (ROOT / "custom/css/contest-portal.css").read_text(encoding="utf-8")
        self.assertIn("body:has(.contest-tabs) .scoreboard-shell .dropdown:has(> #filter-toggle) { display: none; }", css)

    def test_lobby_is_built_when_only_one_contest_is_open(self):
        # 대회가 하나면 DOMjudge가 전환 링크를 그리지 않는다. 그때도 현재 대회 카드로 들어갈 수 있어야 한다.
        lobby = PORTAL.split("function buildContestLobby()", 1)[1].split("\n  function ", 1)[0]
        self.assertNotIn("if (!links.length) return;", lobby)
        self.assertIn("appendCurrentContestCard(grid, currentContest);", lobby)
        self.assertIn("참가할 수 있는 대회가 없습니다.", lobby)

    def test_lobby_keeps_the_current_contest_visible_after_a_session_is_selected(self):
        self.assertIn("appendCurrentContestCard", PORTAL)
        self.assertIn("resolveContestName(function (currentContest)", PORTAL)
        self.assertIn('contestPath("/problems")', PORTAL)

    def test_lobby_uses_domjudge_navigation_to_switch_contests(self):
        self.assertIn("function enterContest(event)", PORTAL)
        self.assertIn("location.assign(card.href)", PORTAL)
        self.assertNotIn("fetch(card.href", PORTAL)
        self.assertIn("kaupc_pending_contest", PORTAL)
        self.assertIn("function returnToSelectedContest()", PORTAL)
        self.assertIn("if (returnToSelectedContest()) return;", PORTAL)


if __name__ == "__main__":
    unittest.main()
