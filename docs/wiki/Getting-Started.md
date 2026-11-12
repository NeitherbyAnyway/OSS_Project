# Getting Started

Welcome to OSS_Project. This project practices GitHub collaboration and Actions automation while calculating DORA indicators from GitHub data.

## Before you start

- Git
- Python 3.x
- A GitHub account

## Set up locally

```powershell
git clone https://github.com/NeitherbyAnyway/OSS_Project.git
Set-Location OSS_Project
python --version
```

The project scripts use the Python standard library. Run the existing DORA tests with:

```powershell
python .github/scripts/test_collect_dora_metrics.py
```

## Where to go next

- [Development Guide](https://github.com/NeitherbyAnyway/OSS_Project/wiki/Development-Guide) explains branches, commits, tests, and pull requests.
- [Troubleshooting](https://github.com/NeitherbyAnyway/OSS_Project/wiki/Troubleshooting) covers common Actions and metric issues.
- [Architecture Decision Records](https://github.com/NeitherbyAnyway/OSS_Project/tree/main/docs/adr) explains how project decisions are recorded.

The `Weekly Throughput` workflow runs every Sunday at 00:00 UTC and can also be started manually from the Actions tab. Open its run summary or download the `weekly-dora-report` artifact to inspect results. GitHub Releases and failure-labeled issues are currently proxy data, not production deployment measurements.
