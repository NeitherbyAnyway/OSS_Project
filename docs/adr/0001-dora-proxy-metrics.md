# ADR 0001: Use GitHub releases as DORA proxy data

- Status: Accepted
- Decision makers: @NeitherbyAnyway, @kygi123
- Related context: `.github/scripts/collect_dora_metrics.py`

## Context

The repository does not currently have production deployment events to measure. The project still needs a repeatable way to exercise DORA reporting while making the limitations of the available data clear.

## Decision

Use GitHub Releases as a proxy for deployments and `dora-failure`-labeled issues as a proxy for failed changes and recovery time. Reports must identify the proxy source and must not present the values as production deployment measurements.

## Consequences

- The existing workflow can generate metrics without a deployment platform.
- Release timing and issue labels may differ from actual deployment and incident data, so proxy results are not directly comparable to operational DORA metrics.
- When deployment records become available, add an ADR and migrate the source deliberately rather than silently changing the meaning of historical reports.

## Follow-up

- [ ] Propose a source of real deployment events through a repository RFC.
