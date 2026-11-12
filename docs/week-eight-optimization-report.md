# Week 8 CI/CD Optimization Report

## Changes measured

The workflow matrix grew from four combinations (Python 3.11/3.12 on Ubuntu and Windows) to six (Python 3.11/3.12/3.13 on Ubuntu and Windows). The test matrix was extracted into a reusable workflow, Python setup and pip caching into a composite action, and Pages deployment is limited to eligible changes on `main`.

Build and test are independent, so they now run concurrently. Deployment still waits for the build, all six test combinations, and the changed-file check to succeed.

## GitHub Actions measurements

| Run | Configuration | Matrix | Pip cache | Dependency install | Workflow duration |
| --- | --- | ---: | --- | ---: | ---: |
| [Week 7 baseline](https://github.com/NeitherbyAnyway/OSS_Project/actions/runs/43274696072) | Original sequential pipeline | 4 combinations | Not measured | Not measured | 29 seconds |
| [Week 8 cold-cache run](https://github.com/NeitherbyAnyway/OSS_Project/actions/runs/43277929121) | Expanded matrix, build before tests | 6 combinations | Miss | 1,220 ms | 33 seconds |
| [Week 8 warm-cache and parallel run](https://github.com/NeitherbyAnyway/OSS_Project/actions/runs/43278599671) | Expanded matrix, build and tests in parallel | 6 combinations | Hit | 1,177 ms | 21 seconds |

All three runs succeeded; deployment was skipped for pull requests as intended.

## Results and limitations

- The observed pull request workflow duration fell from 29 to 21 seconds, about a 27.6% reduction, while coverage increased from four to six matrix combinations.
- The cached dependency-install step took 43 ms less (about 3.5%) in the warm run. This is a small difference and should not be treated as a meaningful standalone speedup.
- The overall timing comparison is based on one run per configuration. Runner startup, scheduling, and network variability affect these short workflows, so the results are indicative rather than a controlled benchmark.
- The clearest optimization is running independent build and test jobs concurrently; deployment remains gated on both.
