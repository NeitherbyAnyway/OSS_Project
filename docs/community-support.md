# Issue response and SLA

The `Community Support` workflow acknowledges newly opened issues and publishes a weekly first-response report. It is separate from `Weekly Throughput`, so the existing DORA and issue-throughput schedule and output remain unchanged.

## Response target

- Target: a first human maintainer response within **48 calendar hours** of issue creation.
- Maintainers are read from individual GitHub usernames in `.github/CODEOWNERS`.
- The automatic acknowledgment is not a human response and is excluded from SLA calculations.
- A response is considered within target when the earliest maintainer comment is posted no more than 48 hours after issue creation.
- Unanswered issues are `pending` before the deadline and `overdue` after it. Responses after the deadline are `late`.

## Automation

- On each new issue, the workflow posts an acknowledgment once. A marker prevents duplicate acknowledgments on workflow retries.
- Every Sunday at 00:00 UTC, or on manual dispatch, it reviews issues created during the preceding seven days.
- The Actions summary and `community-support-sla-report` artifact include counts and per-issue response status.
- The workflow uses `issues: write` only for acknowledgments; the reporting job has `issues: read`. The existing throughput workflow is not modified.

## Local checks

Run the focused tests with:

```powershell
python .github/scripts/test_community_support.py
```

Never put tokens in source files or logs. GitHub Actions supplies its short-lived `github.token` through `GH_TOKEN`.
