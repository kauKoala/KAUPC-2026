import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]


class ContestPortalAssetsTests(unittest.TestCase):
    def test_portal_intercepts_statement_links_and_builds_a_contest_lobby(self) -> None:
        script = (ROOT / "custom" / "js" / "contest-portal.js").read_text(encoding="utf-8")
        self.assertIn("buildContestLobby", script)
        self.assertIn("displayContestName", script)
        self.assertIn("enterContest", script)
        self.assertIn("buildContestDashboard", script)
        self.assertIn("injectContestTabs", script)
        self.assertIn('href="/contest/problems"', script)
        self.assertIn('href="/contest/scoreboard"', script)
        self.assertIn("buildProblemTable", script)
        self.assertIn("statement", script)

    def test_styles_define_problem_component_and_lobby(self) -> None:
        stylesheet = (ROOT / "custom" / "css" / "contest-portal.css").read_text(encoding="utf-8")
        self.assertIn(".contest-lobby", stylesheet)
        self.assertIn(".contest-statement", stylesheet)
        self.assertIn(".problem-statement", stylesheet)


if __name__ == "__main__":
    unittest.main()
