import unittest
from datetime import datetime, timezone

from collect_dora_metrics import calculate_metrics, make_dashboard, make_report


class CalculateMetricsTests(unittest.TestCase):
    def test_empty_data_is_reported_without_failing(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 8, tzinfo=timezone.utc)

        metrics = calculate_metrics([], start, end)
        report = make_report("owner/repo", start, end, metrics)
        dashboard = make_dashboard("owner/repo", start, end, metrics)

        self.assertEqual(metrics["deployment_frequency"]["value"], 0)
        self.assertIsNone(metrics["lead_time_for_changes"]["value_minutes"])
        self.assertIsNone(metrics["change_failure_rate"]["value_percent"])
        self.assertIsNone(metrics["mttr"]["value_minutes"])
        self.assertIn("N/A", report)
        self.assertIn("N/A", dashboard)

    def test_calculates_all_four_metrics(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 8, tzinfo=timezone.utc)
        records = [
            {
                "deployment": {"id": 1, "environment": "production", "created_at": "2026-01-02T00:00:00Z"},
                "statuses": [{"state": "success", "created_at": "2026-01-02T01:00:00Z"}],
                "commit_date": "2026-01-01T13:00:00Z",
            },
            {
                "deployment": {"id": 2, "environment": "production", "created_at": "2026-01-03T00:00:00Z"},
                "statuses": [{"state": "failure", "created_at": "2026-01-03T01:00:00Z"}],
                "commit_date": None,
            },
            {
                "deployment": {"id": 3, "environment": "production", "created_at": "2026-01-03T02:00:00Z"},
                "statuses": [{"state": "success", "created_at": "2026-01-03T03:00:00Z"}],
                "commit_date": "2026-01-02T15:00:00Z",
            },
        ]

        metrics = calculate_metrics(records, start, end)

        self.assertEqual(metrics["deployment_frequency"]["value"], 2)
        self.assertEqual(metrics["lead_time_for_changes"]["value_minutes"], 720)
        self.assertEqual(metrics["change_failure_rate"]["value_percent"], 33.33)
        self.assertEqual(metrics["mttr"]["value_minutes"], 120)
        self.assertEqual(metrics["mttr"]["recovered_incidents"], 1)


if __name__ == "__main__":
    unittest.main()