import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen


TERMINAL_STATES = {"success", "failure", "error"}
RECOVERY_CONTEXT = timedelta(days=30)


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def average(values):
    return round(sum(values) / len(values), 2) if values else None


def calculate_metrics(records, period_start, period_end):
    completed = []
    successful = []
    failed = []
    leads_minutes = []
    events_by_environment = {}

    for record in records:
        deployment = record["deployment"]
        statuses = record["statuses"]
        environment = deployment.get("environment") or "default"
        created_at = parse_time(deployment["created_at"])
        ordered_statuses = sorted(statuses, key=lambda item: parse_time(item["created_at"]))

        for status in ordered_statuses:
            if status.get("state") in TERMINAL_STATES:
                events_by_environment.setdefault(environment, []).append(
                    (parse_time(status["created_at"]), status["state"])
                )

        latest_terminal = next(
            (status for status in reversed(ordered_statuses) if status.get("state") in TERMINAL_STATES),
            None,
        )
        if not (period_start <= created_at < period_end) or latest_terminal is None:
            continue

        completed.append(record)
        if latest_terminal["state"] == "success":
            successful.append(record)
            successful_statuses = [status for status in ordered_statuses if status.get("state") == "success"]
            if record.get("commit_date") and successful_statuses:
                lead_minutes = (
                    parse_time(successful_statuses[-1]["created_at"]) - parse_time(record["commit_date"])
                ).total_seconds() / 60
                if lead_minutes >= 0:
                    leads_minutes.append(lead_minutes)
        elif latest_terminal["state"] in {"failure", "error"}:
            failed.append(record)

    recovery_minutes = []
    open_incidents = 0
    for events in events_by_environment.values():
        pending_failure = None
        for event_time, state in sorted(events, key=lambda event: (event[0], event[1] == "success")):
            if state in {"failure", "error"}:
                if pending_failure is None:
                    pending_failure = event_time
            elif state == "success" and pending_failure is not None:
                if period_start <= pending_failure < period_end:
                    recovery_minutes.append((event_time - pending_failure).total_seconds() / 60)
                pending_failure = None

        if pending_failure is not None and period_start <= pending_failure < period_end:
            open_incidents += 1

    failure_rate = round(100 * len(failed) / len(completed), 2) if completed else None
    return {
        "deployment_frequency": {
            "value": len(successful),
            "unit": "successful deployments/week",
        },
        "lead_time_for_changes": {
            "value_minutes": average(leads_minutes),
            "unit": "minutes",
            "measured_deployments": len(leads_minutes),
        },
        "change_failure_rate": {
            "value_percent": failure_rate,
            "unit": "percent",
            "failed_deployments": len(failed),
            "completed_deployments": len(completed),
        },
        "mttr": {
            "value_minutes": average(recovery_minutes),
            "unit": "minutes",
            "recovered_incidents": len(recovery_minutes),
            "open_incidents": open_incidents,
        },
    }


def calculate_release_proxy_metrics(releases, incidents, period_start, period_end):
    period_releases = [
        release
        for release in releases
        if period_start <= parse_time(release["published_at"]) < period_end
    ]
    release_tags = {release["tag_name"] for release in period_releases}
    leads_minutes = []
    for release in period_releases:
        if release.get("commit_date"):
            lead_minutes = (
                parse_time(release["published_at"]) - parse_time(release["commit_date"])
            ).total_seconds() / 60
            if lead_minutes >= 0:
                leads_minutes.append(lead_minutes)

    failed_release_tags = set()
    unlinked_failures = 0
    recovery_minutes = []
    open_incidents = 0
    for incident in incidents:
        labels = {label["name"] for label in incident.get("labels", [])}
        if "dora-failure" not in labels:
            continue

        linked_tags = {
            label.removeprefix("release:")
            for label in labels
            if label.startswith("release:")
        }
        if not linked_tags:
            unlinked_failures += 1
        failed_release_tags.update(linked_tags & release_tags)

        created_at = parse_time(incident["created_at"])
        closed_at = parse_time(incident["closed_at"]) if incident.get("closed_at") else None
        if closed_at and period_start <= closed_at < period_end:
            recovery_minutes.append((closed_at - created_at).total_seconds() / 60)
        elif not closed_at and period_start <= created_at < period_end:
            open_incidents += 1

    failure_rate = (
        round(100 * len(failed_release_tags) / len(period_releases), 2)
        if period_releases
        else None
    )
    return {
        "deployment_frequency": {
            "value": len(period_releases),
            "unit": "published releases/week (deployment proxy)",
        },
        "lead_time_for_changes": {
            "value_minutes": average(leads_minutes),
            "unit": "minutes",
            "measured_deployments": len(leads_minutes),
        },
        "change_failure_rate": {
            "value_percent": failure_rate,
            "unit": "percent",
            "failed_deployments": len(failed_release_tags),
            "completed_deployments": len(period_releases),
            "unlinked_failure_issues": unlinked_failures,
        },
        "mttr": {
            "value_minutes": average(recovery_minutes),
            "unit": "minutes",
            "recovered_incidents": len(recovery_minutes),
            "open_incidents": open_incidents,
        },
    }


def api_request(url, token):
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response), response.headers.get("Link", "")
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"GitHub API request failed: {error}") from error


def iter_api_items(api_url, repository, endpoint, token):
    next_url = f"{api_url}/repos/{repository}/{endpoint}"
    separator = "&" if "?" in next_url else "?"
    next_url = f"{next_url}{separator}per_page=100"
    while next_url:
        payload, link_header = api_request(next_url, token)
        yield from payload
        next_link = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
        next_url = urljoin(next_url, next_link.group(1)) if next_link else None


def get_commit_date(api_url, repository, sha, token):
    payload, _ = api_request(f"{api_url}/repos/{repository}/commits/{sha}", token)
    commit = payload.get("commit", {})
    committer = commit.get("committer") or commit.get("author") or {}
    return committer.get("date")


def collect_records(api_url, repository, token, cutoff):
    records = []
    commit_dates = {}
    for deployment in iter_api_items(api_url, repository, "deployments", token):
        if parse_time(deployment["created_at"]) < cutoff:
            break
        statuses = list(
            iter_api_items(
                api_url,
                repository,
                f"deployments/{deployment['id']}/statuses",
                token,
            )
        )
        sha = deployment.get("sha")
        commit_date = None
        if sha:
            if sha not in commit_dates:
                commit_dates[sha] = get_commit_date(api_url, repository, sha, token)
            commit_date = commit_dates[sha]
        records.append({"deployment": deployment, "statuses": statuses, "commit_date": commit_date})
    return records


def collect_release_proxy_data(api_url, repository, token, period_start, period_end):
    releases = []
    for release in iter_api_items(api_url, repository, "releases", token):
        published_at = release.get("published_at")
        if release.get("draft") or not published_at:
            continue
        if not period_start <= parse_time(published_at) < period_end:
            continue
        try:
            commit_date = get_commit_date(api_url, repository, release.get("target_commitish") or release["tag_name"], token)
        except Exception:
            commit_date = None
        releases.append(
            {
                "tag_name": release["tag_name"],
                "published_at": published_at,
                "commit_date": commit_date,
            }
        )

    incidents = []
    for issue in iter_api_items(api_url, repository, "issues?state=all", token):
        if "pull_request" not in issue:
            incidents.append(issue)
    return releases, incidents


def count_closed_issues(api_url, repository, token, period_start, period_end):
    closed_issues = 0
    for issue in iter_api_items(api_url, repository, "issues?state=closed", token):
        if "pull_request" in issue:
            continue
        closed_at = issue.get("closed_at")
        if not closed_at:
            continue
        if period_start <= parse_time(closed_at) < period_end:
            closed_issues += 1
    return closed_issues


def display(value, suffix=""):
    return "N/A" if value is None else f"{value:g}{suffix}"


def format_metric_value(label, value):
    if value is None:
        return "N/A"
    if label == "Change failure rate":
        return f"{value:g}%"
    if label == "Lead time for changes" or label == "MTTR":
        return f"{value:g} min"
    return str(value)


def make_report(repository, period_start, period_end, metrics, source="github_releases_proxy", closed_issues=0):
    lead = metrics["lead_time_for_changes"]
    failure = metrics["change_failure_rate"]
    mttr = metrics["mttr"]
    return "\n".join(
        [
            "# Weekly DORA Metrics",
            "",
            f"- Repository: `{repository}`",
            f"- Period: **{period_start:%Y-%m-%d} to {period_end:%Y-%m-%d} UTC**",
            "",
            "| Metric | Result | Sample size |",
            "| --- | ---: | ---: |",
            f"| Deployment frequency | {metrics['deployment_frequency']['value']} successful deployments/week | - |",
            f"| Lead time for changes | {display(lead['value_minutes'], ' min')} | {lead['measured_deployments']} deployments |",
            f"| Change failure rate | {display(failure['value_percent'], '%')} | {failure['failed_deployments']}/{failure['completed_deployments']} deployments |",
            f"| MTTR | {display(mttr['value_minutes'], ' min')} | {mttr['recovered_incidents']} recovered; {mttr['open_incidents']} open |",
            "",
            "## Calculation rules",
            "",
            "- Metric source: GitHub Deployments API." if source == "github_deployments" else "- Metric source: GitHub Releases and labeled Issues (explicit deployment proxy).",
            "- Deployment frequency counts deployments created in the period whose latest status is `success`." if source == "github_deployments" else "- Deployment frequency counts published releases in the period as deployment proxies.",
            "- Lead time is the deployed commit's committer timestamp to its successful deployment status." if source == "github_deployments" else "- Lead time is the release tag commit's committer timestamp to its publication time.",
            "- Change failure rate is failed or errored deployments divided by completed deployments in the period." if source == "github_deployments" else "- Change failure rate is unique releases linked to `dora-failure` Issues divided by published releases. Label each incident `release:<tag>`.",
            "- MTTR is the average time from a `failure`/`error` status to the next `success` status in the same environment. Recovery context is limited to 30 days." if source == "github_deployments" else "- MTTR is the average time from a `dora-failure` Issue's creation to closure; open incidents created in the period are counted separately.",
            "- Metrics without eligible deployment data are reported as `N/A`; these are deployment-based measures, not issue-based proxies.",
            "",
            "## Weekly Throughput",
            "",
            f"- Period: **{period_start:%Y-%m-%d} to {period_end:%Y-%m-%d} UTC**",
            f"- Closed issues: **{closed_issues}**",
            "",
        ]
    )


def make_dashboard(repository, period_start, period_end, metrics, source="github_releases_proxy", closed_issues=0):
    lead = metrics["lead_time_for_changes"]
    failure = metrics["change_failure_rate"]
    mttr = metrics["mttr"]
    chart_labels = [
        "Deployment frequency",
        "Lead time for changes",
        "Change failure rate",
        "MTTR",
    ]
    chart_values = [
        metrics["deployment_frequency"]["value"],
        lead["value_minutes"],
        failure["value_percent"],
        mttr["value_minutes"],
    ]
    labels = [
        "Deployment frequency",
        "Lead time for changes",
        "Change failure rate",
        "MTTR",
    ]
    series = [
        str(metrics["deployment_frequency"]["value"]),
        display(lead["value_minutes"], " min"),
        display(failure["value_percent"], "%"),
        display(mttr["value_minutes"], " min"),
    ]
    card_html = "\n".join(
        f'<article><h2>{html.escape(title)}</h2><strong>{html.escape(value)}</strong><p>{html.escape(detail)}</p></article>'
        for title, value, detail in [
            ("Deployment frequency", str(metrics["deployment_frequency"]["value"]), "successful deployments / week"),
            ("Lead time for changes", display(lead["value_minutes"], " min"), f"{lead['measured_deployments']} measured deployments"),
            ("Change failure rate", display(failure["value_percent"], "%"), f"{failure['failed_deployments']} failed / {failure['completed_deployments']} completed"),
            ("MTTR", display(mttr["value_minutes"], " min"), f"{mttr['recovered_incidents']} recovered / {mttr['open_incidents']} open"),
        ]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Weekly DORA Metrics</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{ color-scheme: light; font-family: Georgia, 'Times New Roman', serif; background: #0f1720; color: #edf5f3; }}
    body {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px; background: #0f1720; }}
    header {{ border-bottom: 2px solid #c9d9d4; padding-bottom: 20px; margin-bottom: 20px; }}
    h1 {{ font-size: 2.4rem; margin: 0 0 8px; }}
    header p {{ color: #b9c7c2; margin: 0; }}
    main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; padding-bottom: 24px; }}
    article {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.12); border-top: 5px solid #df6b45; padding: 20px; min-height: 150px; }}
    article:nth-child(even) {{ border-top-color: #328378; }}
    h2 {{ font: 600 0.95rem 'Segoe UI', sans-serif; margin: 0 0 24px; color: #f2f7f5; }}
    strong {{ display: block; font-size: 2rem; overflow-wrap: anywhere; }}
    article p, footer {{ font: 0.85rem 'Segoe UI', sans-serif; color: #d3ddd9; }}
    .chart-card {{ margin-top: 12px; background: rgba(255,255,255,0.03); padding: 18px; border: 1px solid rgba(255,255,255,0.12); }}
    canvas {{ max-height: 350px; }}
  </style>
</head>
<body>
  <header><h1>Weekly DORA Metrics</h1><p>{html.escape(repository)} · {period_start:%Y-%m-%d} to {period_end:%Y-%m-%d} UTC</p></header>
  <main>{card_html}</main>
  <div class="chart-card">
    <canvas id="doraChart"></canvas>
  </div>
  <footer>{'GitHub Deployments API measurements.' if source == 'github_deployments' else 'Release-based deployment proxy. Record incidents as Issues labeled dora-failure and release:&lt;tag&gt;.'} Weekly throughput is shown alongside the DORA metrics. No eligible data is shown as N/A.</footer>
  <script>
    const labels = {json.dumps(chart_labels)};
    const values = {json.dumps(chart_values)};
    new Chart(document.getElementById('doraChart'), {{
      type: 'bar',
      data: {{
        labels: labels,
        datasets: [{{
          label: 'Metric value',
          data: values,
          backgroundColor: ['#4ecdc4', '#f7b267', '#ff6b6b', '#7bdff2'],
          borderRadius: 6
        }}]
      }},
      options: {{
        responsive: true,
        scales: {{
          y: {{
            beginAtZero: false,
            ticks: {{
              callback: function(value) {{
                return value + (labels[2] === 'Change failure rate' ? '%' : '');
              }}
            }}
          }}
        }},
        plugins: {{
          legend: {{ display: false }}
        }}
      }}
    }});
  </script>
</body>
</html>
"""


def main():
    token = os.environ.get("GH_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    if not token or not repository:
        raise RuntimeError("GH_TOKEN and GITHUB_REPOSITORY must be set")

    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=7)
    records = collect_records(api_url, repository, token, period_start - RECOVERY_CONTEXT)
    if records:
        source = "github_deployments"
        metrics = calculate_metrics(records, period_start, period_end)
    else:
        source = "github_releases_proxy"
        releases, incidents = collect_release_proxy_data(
            api_url, repository, token, period_start, period_end
        )
        metrics = calculate_release_proxy_metrics(releases, incidents, period_start, period_end)
    closed_issues = count_closed_issues(api_url, repository, token, period_start, period_end)
    output = Path("reports")
    output.mkdir(parents=True, exist_ok=True)

    data = {
        "schema_version": 1,
        "repository": repository,
        "data_source": source,
        "generated_at": period_end.isoformat(),
        "period": {"start": period_start.isoformat(), "end": period_end.isoformat()},
        "weekly_throughput": {"closed_issues": closed_issues},
        "metrics": metrics,
    }
    (output / "dora-metrics.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    report = make_report(repository, period_start, period_end, metrics, source, closed_issues)
    (output / "weekly-report.md").write_text(report, encoding="utf-8")
    dashboard = make_dashboard(repository, period_start, period_end, metrics, source, closed_issues)
    (output / "dora-dashboard.html").write_text(dashboard, encoding="utf-8")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(report)
    print(f"Wrote DORA metrics, report, and dashboard for {repository}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)