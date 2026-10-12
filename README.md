# OSS Project

# 오픈 소스 소프트웨어 프로젝트 
오픈 소스 소프트웨어 개발에 필요한 도구와 협업 방식을 직접 실습하며, Git/github 활용 능력과 소프트웨어 개발 기초 역량을 기르는 것을 목표

## 🎯 핵심 기능

- 주요 기능 1 // 오픈 소스 소프트웨어 학습
- 주요 기능 2 // 공개 리포지토리화를 통한 외부 검사 
- 주요 기능 3 // 깃허브 기능 실습

### Prerequisites

- Python
- Json, xml
- git/github/github desktop/vscode
- 

## DORA Metrics Automation

`.github/workflows/throughput.yml` runs every Sunday at 00:00 UTC and can also
be started manually with **Run workflow**. It collects deployment data from the
GitHub Deployments API, calculates the four DORA metrics for the previous seven
days, and publishes a Markdown report in the Actions job summary. It also keeps
the weekly closed-issue count.

The workflow uploads `dora-metrics.json`, `weekly-report.md`, and
`dora-dashboard.html` as the `weekly-dora-report` artifact. Download the artifact
from the workflow run to inspect the raw data, report, or standalone dashboard.
The built-in `github.token` is granted read-only access to deployments, issues,
and repository contents; no personal access token secret is required.

### Metric definitions

- **Deployment frequency:** successful deployments created during the reporting week.
- **Lead time for changes:** time from the deployed commit's committer timestamp to its successful deployment status. This uses the deployment's SHA as a consistent commit-level proxy.
- **Change failure rate:** deployments whose latest status is `failure` or `error`, divided by completed (`success`, `failure`, or `error`) deployments created during the reporting week.
- **MTTR:** average time from a `failure` or `error` status to the next `success` status in the same environment. The workflow checks up to 30 days of deployment history for recovery context.

If a repository has no GitHub deployment records, deployment-based metrics are
reported as `N/A` or zero rather than inferred from issue closures. Configure
deployments in the repository's CI/CD workflow for meaningful DORA results.


