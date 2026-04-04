---
title: "QualBench v1 Results: Cost Per Mergeable PR — The Metric That Matters"
date: 2026-04-04
author: Softreck Team
tags: [qualbench, benchmark, ai-tools, cost-analysis]
---

# Cost Per Mergeable PR — The Metric That Matters

Every AI coding tool claims to "resolve 70–80% of issues." But resolution is not the same as mergeability. A patch that passes tests but introduces security regressions or complexity explosions still requires human rework.

QualBench v1 introduces a new metric: **cost per mergeable PR** — the total AI cost divided by the number of PRs that meet all quality gates and are ready to merge without human fixes.

## The numbers

| Tool | Issues Resolved | Mergeable | Cost/Issue | Cost/Mergeable |
|------|----------------|-----------|------------|----------------|
| prollama (quality) | 42/50 (84%) | 31/50 (62%) | $0.32 | $0.52 |
| Aider + Claude | 38/50 (76%) | 28/50 (56%) | $0.45 | $0.80 |
| Copilot Workspace | 35/50 (70%) | 22/50 (44%) | $0.28 | $0.64 |
| Cline + Claude | 41/50 (82%) | 26/50 (52%) | $0.38 | $0.73 |
| OpenHands | 29/50 (58%) | 14/50 (28%) | $0.15 | $0.54 |

*Based on QualBench v1 dataset: 50 real-world issues across Python and TypeScript.*

## What the data shows

**Higher resolution rates don't guarantee lower costs.** Copilot resolves 70% of issues at the lowest per-issue cost ($0.28), but its mergeable rate is only 44%. The rework required brings its true cost per mergeable PR to $0.64 — higher than prollama's $0.52.

**Quality gates catch what resolution rates miss.**
- Copilot's security gate failures: 18 issues with new Bandit findings
- Cline's complexity regressions: 14 issues with >20% CC increase
- Aider's test coverage drops: 11 issues with >5% coverage loss

## The methodology

QualBench v1 evaluates on six dimensions:
1. **Correctness** (25%): Tests pass, no regressions
2. **Mergeability** (25%): Senior dev would approve without changes
3. **Security** (15%): No new vulnerabilities (Bandit/Semgrep)
4. **Code quality** (15%): No complexity increase >10%
5. **Coverage delta** (new): No >5% coverage drops
6. **Type checking** (new): No new mypy/pyright errors

A PR is "mergeable" only if quality score ≥ 85 (all gates pass).

## What this means for engineering teams

If you're evaluating AI coding tools:

1. **Ask for cost per mergeable PR, not resolution rate.**
2. **Test on your own codebase.** Generic benchmarks overestimate performance.
3. **Include security scanning in your evaluation.** 35% of "resolved" issues in our test had security regressions.
4. **Measure coverage and type safety.** These predict long-term maintenance costs.

## Try it yourself

```bash
pip install qualbench
qualbench run --tool <your-tool> --dataset dataset/qualbench-v1.json
qualbench submit --api-key YOUR_KEY
```

Submit your results to [qualbench.com/leaderboard](https://qualbench.com/leaderboard).

---

*QualBench is an open-source benchmark by Softreck. Dataset v1 includes 50 real-world issues from popular Python and TypeScript repositories.*
