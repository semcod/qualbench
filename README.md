# QualBench — CI for AI-Generated Code

## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.15-brightgreen) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fqwen%2Fqwen3-coder-next-lightgrey)

This project uses AI-generated code. Total cost: **$0.1500** with **1** AI commits.

Generated on 2026-04-04 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/models/openrouter/qwen/qwen3-coder-next)

---



> **Correct code is not the same as mergeable code.**
> eslint + code review, but for AI. Add to your pipeline in 2 minutes.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Dataset: v0](https://img.shields.io/badge/dataset-v0_(10_issues)-green.svg)](dataset/)
[![CI](https://img.shields.io/badge/CI-qualbench--action-orange.svg)](action/)

---

## 60 seconds to your first score

```bash
pip install qualbench
qualbench quickstart
```

No config, no API keys. QualBench evaluates your current diff and prints a Quality Score.

## Add to CI in 2 minutes

```yaml
# .github/workflows/qualbench.yml
name: QualBench
on: [pull_request]
jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: semcod/qualbench-action@v1
        with:
          tool: prollama
          fail_on_score: 70
```

Every AI-generated PR gets a quality review comment. Set `fail_on_score` and the pipeline fails if quality is below your threshold.

```
🧠 QualBench Review

Quality Score: 78/100

  ❌ Complexity increased (+12%)
  ⚠ Security: 1 new medium-severity finding
  ✔ Tests pass, no regressions

Verdict: needs_review
```

## CI/CD Examples

### GitHub Action (recommended)

```yaml
# .github/workflows/qualbench.yml
name: QualBench
on: [pull_request]
jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: semcod/qualbench-action@v1
        with:
          tool: prollama
          fail_on_score: 70
```

### GitLab CI

```yaml
# .gitlab-ci.yml
qualbench:
  stage: test
  image: python:3.12-slim
  before_script:
    - pip install qualbench
  script:
    - qualbench run --tool prollama --json --fail-on-score 70
  only:
    - merge_requests
```

### Azure DevOps

```yaml
# azure-pipelines.yml
steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.12'
  - script: |
      pip install qualbench
      qualbench run --tool prollama --json --fail-on-score 70
    displayName: 'QualBench Quality Check'
```

### Jenkins

```groovy
// Jenkinsfile
stage('Quality Check') {
    steps {
        sh '''
            pip install qualbench
            qualbench run --tool prollama --fail-on-score 70
        '''
    }
}
```

### CircleCI

```yaml
# .circleci/config.yml
version: 2.1
jobs:
  quality:
    docker:
      - image: python:3.12-slim
    steps:
      - checkout
      - run: pip install qualbench
      - run: qualbench run --tool prollama --fail-on-score 70
workflows:
  quality-check:
    jobs:
      - quality
```

## The problem

AI coding tools resolve 70–80% of benchmark tasks. But most AI-generated PRs are not mergeable without human fixes. Every existing benchmark asks "do tests pass?" — nobody asks "would a senior developer approve this PR?"

## Six dimensions of production readiness

| Dimension | What it measures | Weight |
|-----------|-----------------|--------|
| **Correctness** | All tests pass, no regressions | 25% |
| **Mergeability** | Would a senior dev merge this? (1–5) | 25% |
| **Security** | New vulnerabilities introduced | 15% |
| **Code quality** | Complexity delta, dead code | 15% |
| **Iterations** | Attempts to reach acceptable output | 10% |
| **Cost efficiency** | USD per successful patch | 10% |

**Verdicts:** `ready_to_merge` (≥85), `needs_review` (65–84), `not_merge_ready` (<65).

## CLI

```bash
qualbench run --tool prollama          # score current diff
qualbench run --tool prollama --json   # portable JSON output
qualbench run --mode cheap             # lowest-cost models
qualbench quickstart                   # first score in 60 seconds
qualbench compare my_tool              # vs leaderboard
qualbench info                         # dataset summary
qualbench doctor                       # check dependencies
```

## One portable format everywhere

CLI, API, GitHub Action — same JSON schema. See [docs/schema.md](docs/schema.md).

## Adding your tool

```bash
cp runners/template.py runners/my_tool.py
# Implement run() → return portable schema
qualbench run --tool my_tool
# Submit PR with results
```

## License

Licensed under Apache-2.0.
