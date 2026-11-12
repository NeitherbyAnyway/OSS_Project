import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from community_support import classify_issue, make_report, parse_codeowners


class ClassifyIssueTests(unittest.TestCase):
    def setUp(self):
        self.issue = {
            "number": 7,
            "title": "Example issue",
            "created_at": "2026-03-01T00:00:00Z",
            "html_url": "https://github.com/owner/repo/issues/7",
        }
        self.now = datetime(2026, 3, 3, tzinfo=timezone.utc)

    def test_bot_acknowledgment_does_not_count_as_human_response(self):
        comments = [
            {
                "created_at": "2026-03-01T00:01:00Z",
                "user": {"login": "NeitherbyAnyway[bot]", "type": "Bot"},
            },
            {
                "created_at": "2026-03-01T00:02:00Z",
                "user": {"login": "community-helper"},
            },
        ]

        result = classify_issue(self.issue, comments, {"NeitherbyAnyway", "kygi123"}, 48, self.now)

        self.assertEqual(result["status"], "overdue")
        self.assertIsNone(result["first_response_at"])

    def test_earliest_codeowner_response_is_measured_in_calendar_hours(self):
        comments = [
            {
                "created_at": "2026-03-02T00:00:00Z",
                "user": {"login": "kygi123"},
            },
            {
                "created_at": "2026-03-01T12:00:00Z",
                "user": {"login": "NeitherbyAnyway"},
            },
        ]

        result = classify_issue(self.issue, comments, {"NeitherbyAnyway", "kygi123"}, 48, self.now)

        self.assertEqual(result["status"], "met")
        self.assertEqual(result["response_hours"], 12)

    def test_response_at_deadline_meets_the_target(self):
        comment = {
            "created_at": "2026-03-03T00:00:00Z",
            "user": {"login": "NeitherbyAnyway"},
        }

        result = classify_issue(self.issue, [comment], {"NeitherbyAnyway"}, 48, self.now)

        self.assertEqual(result["status"], "met")
        self.assertEqual(result["response_hours"], 48)

    def test_unanswered_issue_is_pending_before_deadline(self):
        now = datetime(2026, 3, 2, 23, 59, tzinfo=timezone.utc)

        result = classify_issue(self.issue, [], {"NeitherbyAnyway"}, 48, now)

        self.assertEqual(result["status"], "pending")


class ReportingTests(unittest.TestCase):
    def test_codeowners_are_parsed_as_case_insensitive_user_logins(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CODEOWNERS"
            path.write_text("* @NeitherbyAnyway @kygi123\ndocs/ @organization/reviewers\n", encoding="utf-8")

            self.assertEqual(parse_codeowners(path), {"neitherbyanyway", "kygi123"})

    def test_report_summarizes_sla_status_and_empty_period(self):
        start = datetime(2026, 3, 1, tzinfo=timezone.utc)
        end = datetime(2026, 3, 8, tzinfo=timezone.utc)

        report = make_report("owner/repo", start, end, [], 48)

        self.assertIn("0 met, 0 late, 0 pending, 0 overdue", report)
        self.assertIn("No issues opened in this period", report)


if __name__ == "__main__":
    unittest.main()
