# Development Guide

This guide describes the lightweight workflow for contributing to OSS_Project.

## Create a change

1. Start from the latest `main` branch and create a focused feature branch, for example `feature/improve-report`.
2. Keep the change limited to one coherent task.
3. Use a [Conventional Commit](https://www.conventionalcommits.org/) message such as `feat: add response SLA report` or `docs: explain DORA proxy data`.
4. Open a pull request with the purpose, implementation notes, and test results. Ask a teammate for review before merging.

## Run checks

The project uses Python's standard library and does not require installing packages. Run the tests relevant to the change:

```powershell
python .github/scripts/test_collect_dora_metrics.py
python .github/scripts/test_community_support.py
```

For documentation-only changes, check links and run `git diff --check`.

## Project conventions

- Keep Actions workflows on `windows-latest` and use PowerShell where the existing workflow does.
- Keep each workflow's permissions to the minimum needed. Never print or commit a token.
- The existing `Weekly Throughput` workflow runs weekly and on manual dispatch; preserve its seven-day issue window and Actions summary when changing DORA behavior.
- Current DORA values use GitHub Releases and labeled issues as proxies. See [ADR 0001](https://github.com/NeitherbyAnyway/OSS_Project/tree/main/docs/adr/0001-dora-proxy-metrics.md).
- Record broader technical choices in an [Architecture Decision Record](https://github.com/NeitherbyAnyway/OSS_Project/tree/main/docs/adr).

## Use GitHub Discussions

- **Announcements**: maintainer-only project updates.
- **General**: conversations that do not fit another category.
- **Ideas**: feature suggestions.
- **Q&A**: questions that benefit from an accepted answer.
- **Polls** and **Show and tell**: community votes and demos.
- **RFCs**: proposed technical or process changes; keep this category open-ended.

An RFC should state its context, proposal, alternatives, trade-offs, open questions, and feedback deadline. Discuss before implementation, then record an accepted architectural decision in an ADR.

## Where to go next

- [Getting Started](https://github.com/NeitherbyAnyway/OSS_Project/wiki/Getting-Started)
- [Troubleshooting](https://github.com/NeitherbyAnyway/OSS_Project/wiki/Troubleshooting)
- [RFC discussions](https://github.com/NeitherbyAnyway/OSS_Project/discussions/categories/rfcs)
