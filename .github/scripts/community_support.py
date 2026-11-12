import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ACK_MARKER = "<!-- community-support-ack -->"
DEFAULT_SLA_HOURS = 48
DEFAULT_ACKNOWLEDGMENT = """Thanks for opening this issue. A maintainer will aim to provide a first human response within {hours} hours (calendar time). This automated acknowledgment does not count as that response.

Please include any details that help clarify the issue, and never post passwords, access tokens, or other secrets.

<!-- community-support-ack -->"""


def parse_datetime(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def classify_issue(issue, comments, maintainers, sla_hours, now):
    if sla_hours <= 0:
        raise ValueError("SLA hours must be greater than zero")
    created_at = parse_datetime(issue["created_at"])
    deadline = created_at + timedelta(hours=sla_hours)
    maintainer_logins = {login.casefold() for login in maintainers}
    human_responses = [
        comment
        for comment in comments
        if _is_human_maintainer_comment(comment, maintainer_logins)
        and parse_datetime(comment["created_at"]) >= created_at
    ]
    first_response = min(
        human_responses,
        key=lambda comment: parse_datetime(comment["created_at"]),
        default=None,
    )

    if first_response:
        response_at = parse_datetime(first_response["created_at"])
        response_hours = (response_at - created_at).total_seconds() / 3600
        status = "met" if response_hours <= sla_hours else "late"
    else:
        response_at = None
        response_hours = None
        status = "pending" if now.astimezone(timezone.utc) < deadline else "overdue"

    return {
        "number": issue["number"],
        "title": issue["title"],
        "created_at": created_at,
        "deadline": deadline,
        "first_response_at": response_at,
        "response_hours": response_hours,
        "status": status,
        "url": issue["html_url"],
    }


def _is_human_maintainer_comment(comment, maintainer_logins):
    user = comment.get("user") or {}
    login = user.get("login")
    return (
        isinstance(login, str)
        and login.casefold() in maintainer_logins
        and user.get("type") != "Bot"
    )


def parse_codeowners(path):
    maintainers = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        tokens = line.partition("#")[0].split()
        for owner in tokens[1:]:
            if owner.startswith("@") and "/" not in owner:
                maintainers.add(owner[1:].casefold())
    if not maintainers:
        raise RuntimeError(f"No individual maintainers found in {path}")
    return maintainers


def api_request(url, token, method="GET", payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            response_body = response.read()
            return (json.loads(response_body) if response_body else {}), response.headers.get("Link", "")
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"GitHub API request failed: {error}") from error


def iter_api_items(url, token):
    next_url = url
    while next_url:
        payload, link_header = api_request(next_url, token)
        if not isinstance(payload, list):
            raise RuntimeError(f"Expected a list response from GitHub API: {next_url}")
        yield from payload
        next_link = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
        next_url = next_link.group(1) if next_link else None


def find_recent_issues(api_url, repository, token, start, end):
    query = f"repo:{repository} is:issue created:>={start.date().isoformat()}"
    search_url = f"{api_url}/search/issues?{urlencode({'q': query, 'per_page': 100, 'page': 1})}"
    first_page, _ = api_request(search_url, token)
    total_count = first_page.get("total_count", 0)
    if total_count > 1000:
        raise RuntimeError("GitHub issue search returned more than 1,000 results; narrow the reporting period")

    issues = list(first_page.get("items", []))
    for page in range(2, (total_count + 99) // 100 + 1):
        page_url = f"{api_url}/search/issues?{urlencode({'q': query, 'per_page': 100, 'page': page})}"
        payload, _ = api_request(page_url, token)
        issues.extend(payload.get("items", []))

    return [
        issue
        for issue in issues
        if start <= parse_datetime(issue["created_at"]) <= end
    ]


def fetch_issue_comments(issue, token):
    comments_url = issue.get("comments_url")
    if not comments_url:
        raise RuntimeError(f"Issue #{issue.get('number')} is missing its comments URL")
    separator = "&" if "?" in comments_url else "?"
    return list(iter_api_items(f"{comments_url}{separator}per_page=100", token))


def make_report(repository, start, end, rows, sla_hours):
    statuses = ("met", "late", "pending", "overdue")
    counts = {status: sum(row["status"] == status for row in rows) for status in statuses}
    lines = [
        "# Weekly Issue Response SLA",
        "",
        f"- Repository: `{repository}`",
        f"- Period: {start.isoformat()} to {end.isoformat()} (UTC)",
        f"- Target: first human maintainer response within {sla_hours} calendar hours",
        "- Automated acknowledgments are excluded.",
        f"- Results: {counts['met']} met, {counts['late']} late, {counts['pending']} pending, {counts['overdue']} overdue.",
        "",
        "| Issue | Status | First human response | Elapsed hours |",
        "| --- | --- | --- | ---: |",
    ]
    for row in rows:
        title = row["title"].replace("|", "\\|").replace("\n", " ")
        issue_link = f"[#{row['number']} {title}]({row['url']})"
        response = row["first_response_at"].isoformat() if row["first_response_at"] else "—"
        elapsed = f"{row['response_hours']:.1f}" if row["response_hours"] is not None else "—"
        lines.append(f"| {issue_link} | {row['status']} | {response} | {elapsed} |")
    if not rows:
        lines.append("| No issues opened in this period | — | — | — |")
    return "\n".join(lines) + "\n"


def require_environment():
    token = os.environ.get("GH_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        raise RuntimeError("GH_TOKEN and GITHUB_REPOSITORY must be set")
    return token, repository, os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")


def acknowledge_issue(issue_number, token, repository, api_url, sla_hours):
    if sla_hours <= 0:
        raise ValueError("SLA hours must be greater than zero")
    issue_url = f"{api_url}/repos/{repository}/issues/{issue_number}"
    issue, _ = api_request(issue_url, token)
    comments = fetch_issue_comments(issue, token)
    if any(ACK_MARKER in comment.get("body", "") for comment in comments):
        return
    api_request(
        f"{issue_url}/comments",
        token,
        method="POST",
        payload={"body": DEFAULT_ACKNOWLEDGMENT.format(hours=sla_hours)},
    )


def write_weekly_report(output_path, sla_hours):
    token, repository, api_url = require_environment()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    maintainers = parse_codeowners(".github/CODEOWNERS")
    issues = find_recent_issues(api_url, repository, token, start, now)
    rows = [
        classify_issue(issue, fetch_issue_comments(issue, token), maintainers, sla_hours, now)
        for issue in issues
    ]
    report = make_report(repository, start, now, rows, sla_hours)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(report)


def main():
    parser = argparse.ArgumentParser(description="Acknowledge issues and report first human response times.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    acknowledge = subparsers.add_parser("acknowledge")
    acknowledge.add_argument("--issue", type=int, required=True)
    weekly = subparsers.add_parser("weekly-report")
    weekly.add_argument("--hours", type=int, default=int(os.environ.get("SLA_HOURS", DEFAULT_SLA_HOURS)))
    weekly.add_argument("--output", default="reports/community-sla-weekly.md")
    args = parser.parse_args()

    if args.command == "acknowledge":
        token, repository, api_url = require_environment()
        hours = int(os.environ.get("SLA_HOURS", DEFAULT_SLA_HOURS))
        acknowledge_issue(args.issue, token, repository, api_url, hours)
    else:
        if args.hours <= 0:
            parser.error("--hours must be greater than zero")
        write_weekly_report(args.output, args.hours)


if __name__ == "__main__":
    main()
