# Troubleshooting

## The Actions run failed

1. Open the failed run in the repository's Actions tab and inspect the failing step.
2. Confirm that the workflow has the permissions it needs. `Weekly Throughput` reads issues, contents, and deployments; `Community Support` reads issue comments and writes only the acknowledgment comment.
3. Check that the run used the expected repository and that the GitHub API is available. Do not copy tokens into logs or issue comments.

## The DORA report shows zero deployments

This repository currently has no production deployment records. The DORA script uses GitHub Releases and `dora-failure`-labeled issues as proxy data. Check the report's source label and compare the underlying Releases/issues before treating a value as meaningful.

## The report has no issue rows

The weekly reports cover issues created in the preceding seven days. An empty table means no matching issues were opened in that period. It does not mean that no older issues remain open.

## A new issue has only an automated acknowledgment

The bot acknowledgment confirms receipt but does not count toward the first-human-response SLA. The target is a maintainer response within 48 calendar hours. Check the `Community Support` workflow run if the acknowledgment was not posted, and contact a maintainer if the response is overdue.

## Python tests fail locally

Confirm Python 3.x is available with `python --version`, then run the test command from the repository root:

```powershell
python .github/scripts/test_collect_dora_metrics.py
python .github/scripts/test_community_support.py
```

For the development workflow and other project links, see the [Development Guide](https://github.com/NeitherbyAnyway/OSS_Project/wiki/Development-Guide) and [Getting Started](https://github.com/NeitherbyAnyway/OSS_Project/wiki/Getting-Started).
