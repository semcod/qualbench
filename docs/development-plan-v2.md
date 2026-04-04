---
title: "Softreck — Master Development Plan v2"
slug: softreck-master-development-plan-v2
date: 2026-04-04
status: active
category: engineering
tags: [roadmap, planning, qualbench, prollama, pyqual, taskinity]
---

# Softreck — Master Development Plan v2

Last updated: 2026-04-04

This is the updated plan incorporating distribution-first thinking, CI-as-product positioning, and ruthless prioritization. The previous plan (v1) had the right phases but treated QualBench as a benchmark. This plan treats it as what it actually needs to be: CI for AI-generated code.


## The positioning shift that changes everything

v1 positioning: "benchmark AI coding tools"
v2 positioning: **"CI for AI-generated code — eslint + code review, but for AI"**

This is not a branding change. It changes what gets built first, how distribution works, and where revenue comes from. A benchmark gets stars and citations. A CI tool gets installed in every repo and becomes part of the workflow. The second one wins.

The core growth loop:

```
Developer uses AI tool (Copilot / prollama / aider)
    → PR is created
    → QualBench evaluates PR (GitHub Action / CLI)
    → Score + verdict + suggestions posted as PR comment
    → Developer wants to improve score
    → Uses prollama / pyqual / taskinity to iterate
    → Badge + leaderboard → viral growth
```

Everything in this plan serves this loop. If a task doesn't feed the loop, it gets cut.


## Three access levels (designing for real adoption)

90% of people will never clone the repo. They want to see results. 9% want to try one command on their own code. 1% want the full benchmark. The plan must serve all three simultaneously.

**Passive (90%):** leaderboard on qualbench.com, shareable comparison tables, PR badges. Zero installation required. This is where viral distribution happens.

**Curious (9%):** `pip install qualbench && qualbench run --tool prollama` gives a score in 60 seconds. One command, instant value. This is the "aha moment" that converts users.

**Power user (1%):** full dataset, runner API, reproducible benchmarks, custom tool submissions. This is where credibility comes from.

The 60-second rule is non-negotiable: if a user needs more than 60 seconds to see their first quality score, distribution fails.


## The one portable format (used everywhere)

One JSON schema for CLI output, API responses, GitHub Action comments, and leaderboard entries. No format translation, no conversion bugs, no "it looks different in CI vs locally."

```json
{
  "tool": "prollama",
  "issue_id": "QB-001",
  "quality_score": 74.0,
  "dimensions": {
    "correctness": 100.0,
    "security": 80.0,
    "quality": 65.0,
    "mergeability": 75.0,
    "iterations": 70.0,
    "cost": 90.0
  },
  "verdict": "needs_review",
  "top_issues": ["complexity_increase", "missing_edge_case"],
  "patch": "...",
  "resolved": true,
  "cost_usd": 0.32,
  "time_seconds": 45.0,
  "iterations": 3,
  "model_used": "qwen2.5-coder:32b"
}
```

Verdicts: `ready_to_merge` (score ≥85), `needs_review` (65–84), `not_merge_ready` (<65).

This schema is the standard. Every runner must produce it. Every consumer must read it.


## Critical path (updated)

```
Phase 0: Prove it (weeks 1–3)
    QualBench v0 results → validates strategy
        │
Phase 1: Core loop (weeks 4–8)     ← NEW: this is the real MVP
    prollama benchmark run + GitHub Action + live leaderboard
        │
Phase 2: Fix the engine (weeks 9–12)
    prollama refactoring + monetization features
        │
Phase 3: Scale distribution (weeks 13–16)
    QualBench v1 + API + pip package + Docker
        │
Phase 4: Taskinity + enterprise (weeks 17–24)
    Per-task billing + SSO + RBAC + on-prem
```

The biggest change from v1: Phase 1 (core loop) is moved before engine refactoring. Distribution matters more than clean code. A working GitHub Action with a messy cli.py gets more users than a perfectly refactored CLI that nobody has installed.


## Phase 0: Prove it (weeks 1–3, 50h)

Unchanged from v1. Run the benchmark, get results, publish.

### 0.1 Dataset verification (week 1, 12h)

Verify each of the 10 issues against real closed PRs. Record base_commit, extract test_patch, collect baseline metrics (CC, bandit, coverage). Without verified issues the benchmark is not reproducible and everything downstream is built on sand.

### 0.2 Runner implementations (weeks 1–2, 16h)

Three runners producing real patches. prollama runner (4h): invoke `prollama solve --mode quality`, capture diff, parse cost and iterations from JSON output. OpenHands runner (4h): Docker-based, Claude Sonnet, single-shot. Copilot runner (8h): GitHub API orchestration — create issues, assign to Copilot, poll for PR, download diff. If Copilot API proves too fragile, fall back to manual execution.

### 0.3 Evaluation and human review (weeks 2–3, 14h)

Run automated evaluation (pytest, bandit, radon, ruff) on all 30 patches. Two blind human reviewers rate each patch 1–5. Compute Quality Scores with the 6-dimension weighting.

### 0.4 Publication (week 3, 8h)

Push repo, deploy qualbench.com landing, publish HN/Twitter/LinkedIn/Reddit simultaneously. Blog post on dev.to.

**Go/no-go gate:** quality gates produce ≥20% more mergeable PRs than single-shot. If <10%, revisit approach.


## Phase 1: Core loop — CI for AI code (weeks 4–8, 65h)

This is the new phase that v1 didn't have. The goal is not "more benchmark features." The goal is: developers install QualBench in their CI pipeline because it catches problems in AI-generated PRs.

### 1.1 `prollama benchmark run` — the runner (week 4, 16h)

Build `prollama/benchmark/runner.py` as the execution core. The QualBenchRunner class runs locally on the current repo, measuring the current git diff against quality gates.

```python
class QualBenchRunner:
    def run(self, issue_id="LOCAL") -> QualBenchResult:
        patch = self._get_git_diff()
        correctness = self._run_tests()      # pytest
        security = self._run_bandit()         # bandit delta
        quality = self._run_radon()           # CC + ruff
        mergeability = self._estimate_mergeability(correctness, quality)
        # ... compute dimensions, verdict, top_issues
        return QualBenchResult(...)
```

The mergeability dimension starts as a heuristic proxy (correctness=100 + quality>80 → high mergeability) until human review data accumulates. This is acceptable for v1 — the heuristic is transparent and documented.

Register as CLI subcommand in prollama:

```bash
prollama benchmark run                    # score current diff
prollama benchmark run --tool prollama    # explicit tool name
prollama benchmark run --json             # machine-readable output
prollama benchmark run --mode cheap       # taskinity mode
prollama benchmark quickstart             # run QB-001, show first score
```

Explicit tool selection, never magic detection. `--tool prollama` is the default but must be stated. This avoids flaky auto-detection that becomes a support nightmare.

CLI output for humans (the "aha moment"):

```
🧠 QualBench Report

Quality Score: 74 / 100

Breakdown:
  ✔ Correctness:  PASS
  ⚠ Security:     +1 medium issue (bandit)
  ❌ Quality:      +18% complexity (radon)
  ✔ Mergeability:  estimated 4.0 / 5
  ⚠ Iterations:   3 (expected: 1–2)
  💲 Cost:         $0.32

Verdict: needs_review

Top issues:
  → complexity_increase
  → missing_edge_case
```

Same data, `--json` flag produces the portable schema. No format translation.

### 1.2 GitHub Action — distribution king (weeks 5–6, 20h)

This is the single highest-priority distribution channel. Zero installation. Runs where decisions are made (PR review). Creates viral loop through badges and PR comments.

**action.yml:**

```yaml
name: QualBench
description: "CI for AI-generated code"
inputs:
  tool:
    description: "AI tool name"
    required: true
    default: "prollama"
  fail_on_score:
    description: "Fail if quality score below this"
    required: false
runs:
  using: "docker"
  image: "docker://softreck/qualbench-action:latest"
```

**PR comment output** (posted automatically via GitHub API):

```
🧠 QualBench Review

Quality Score: 78/100

  ❌ Complexity increased (+12%)
  ⚠ Security: 1 new medium-severity finding
  ✔ Tests pass, no regressions

Suggestions:
  → Extract function validate_user_input()
  → Add test for empty payload edge case

Verdict: needs_review
```

**The killer feature:** `fail_on_score_below: 70` makes the pipeline fail. QualBench becomes a gatekeeper, not just an informational comment. This is the moment it transitions from "nice benchmark" to "part of the workflow."

```yaml
# .github/workflows/qualbench.yml
name: QualBench
on: [pull_request]
jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: softreck/qualbench-action@v1
        with:
          tool: prollama
          fail_on_score: 70
```

Dockerfile is minimal: Python 3.12-slim, pip install prollama, entrypoint runs `prollama benchmark run --json`, parses score, posts PR comment, exits with code 1 if below threshold.

### 1.3 Live leaderboard (weeks 7–8, 12h)

Not a static LEADERBOARD.md. A page on qualbench.com that updates when results are submitted.

Minimum viable: a simple FastAPI endpoint that accepts POST /api/v1/results (with tool-owner token authentication) and serves GET /api/v1/leaderboard as JSON. The HTML page on qualbench.com fetches the JSON and renders it client-side. No database on day one — JSON file on disk, committed to repo.

Two rankings displayed: by Quality Score and by cost per mergeable PR.

Any tool owner can submit by running the benchmark and POSTing results. This creates the "submit your tool" growth mechanic.

### 1.4 `qualbench quickstart` (week 8, 4h)

The 60-second path for curious users:

```bash
pip install qualbench
qualbench quickstart
```

This auto-clones one benchmark repo (Flask), runs QB-001, and shows the score. No config, no API keys for BYO-key mode with a local model. The user sees their first quality score in under a minute.

### 1.5 Compare command (week 8, 4h)

```bash
qualbench compare my_tool --issue QB-001
```

Shows the user's score alongside the leaderboard entries for the same issue. The gap analysis ("Biggest gap: mergeability") naturally leads to "how do I improve?" which leads to pyqual/prollama.

Phase 1 milestone (week 8): 10–15 open-source projects have `qualbench-action` in their CI. 500+ `prollama benchmark run` executions logged. QualBench = "the quality check for AI PRs."


## Phase 2: Fix the engine (weeks 9–12, 45h)

Now that distribution is live, fix the internals. Users are running the tool — technical debt matters because it affects reliability.

### 2.1 prollama cli.py refactor (week 9, 11h)

Split the 518-line god module into four submodules: cli/auth.py, cli/solve.py, cli/config.py, cli/tickets.py. Break five high-CC functions (anonymize CC=19, login_device_flow CC=19, Config.load CC=21, ModelRouter.select CC=18, ProllamaShell._cmd_solve CC=15). Resolve the circular dependency.

Add `benchmark` as a new CLI group registered alongside existing commands. This integrates `prollama benchmark run` natively rather than as a separate package.

Target: CC̄ from 3.8 to ≤3.0, max-CC from 21 to ≤10, zero god modules, zero cycles.

### 2.2 Monetization features (weeks 10–11, 22h)

Supervisor AI (8h): second LLM pass reviewing output before delivery. Professional-only. The single feature that most visibly differentiates $39/month from free.

Parallel task execution (6h): asyncio.TaskGroup with concurrency semaphore. Professional gets 5 parallel, Free gets sequential. Creates natural time-based upsell.

Feature gates in CLI (4h): PlanTier enum checking subscription status at startup. Free = solve + regex + shell. Professional = AST anonymization + Supervisor + proxy + parallel + audit.

Audit logging (4h): every LLM call logged with model, tokens, cost, anonymization level, files touched. Stored in .prollama/audit.json. Professional-only — compliance value for enterprise.

### 2.3 SaaS plan enforcement (week 12, 12h)

Plan enforcement middleware (4h), rate limiter per plan (3h), feature gates in proxy (3h), landing page pricing updates (2h).

After this phase: prollama Professional at $39/month is chargeable. The CLI enforces plan limits. The SaaS dashboard reflects actual pricing.


## Phase 3: Scale distribution (weeks 13–16, 64h)

QualBench is in CI pipelines. prollama is monetizable. Now scale both.

### 3.1 QualBench v1 dataset (weeks 13–14, 30h)

Expand from 10 to 50 issues. Add TypeScript (Express, Next.js). Add two evaluation dimensions: test coverage delta and mypy type checking. Benchmark 5 tools instead of 3: add Aider + Claude Sonnet and Cline + Claude Sonnet. Publish updated leaderboard.

### 3.2 pip install qualbench — data platform (week 14, 8h)

```python
from qualbench import load_dataset, evaluate

dataset = load_dataset("v1")
result = evaluate(patch, repo_path)
print(result.quality_score)
```

This turns QualBench from "a repo you clone" into "a library you import." Researchers, tool builders, and CI systems can consume QualBench programmatically. Publish to PyPI.

### 3.3 Minimal API (week 15, 8h)

Two endpoints. No more until demand proves otherwise.

`GET /api/v1/results?tool=prollama&issue=QB-001` — returns results in the portable schema.
`GET /api/v1/leaderboard` — returns current rankings.

Overengineering the API at this stage is a waste. If people want CSV or GraphQL or webhooks, they'll ask. Ship the minimum that makes data consumable.

### 3.4 Docker runner (week 15, 6h)

```bash
docker run softreck/qualbench:latest run --tool prollama
```

For users who don't want Python dependencies. Maps to the same `prollama benchmark run` internally.

### 3.5 Content pipeline (weeks 13–16, 12h)

Each tool from QualBench v1 gets a dedicated deep-dive article. One article on cost per mergeable PR. One on security regressions. Tag tool creators. Publish on dev.to, Hashnode, WordPress blog simultaneously.

Phase 3 milestone (week 16): 100+ repos with qualbench-action in CI. 1000+ pip installs. 50+ inbound leads from qualbench.com to prollama/taskinity.


## Phase 4: Taskinity launch (weeks 17–19, 44h)

Conditional on Phase 0 results validating iterate-until-gates-pass.

### 4.1 Cheap mode in CLI (week 17, 8h)

`prollama solve --mode cheap --quality-gates` — the taskinity mode. Privacy level basic (regex only), model selection cost-optimized (including providers where data may be used for training), pyqual gates as primary quality mechanism. Not a new binary, not a new package — a flag on the existing command.

### 4.2 Branding and landing (week 18, 12h)

taskinity.com with the hook: "AI that doesn't stop until your PR passes quality checks. $0.50 per result." Link to QualBench results as proof. Clear differentiation from prollama.com: taskinity = cost + quality, prollama = security + compliance.

### 4.3 Per-task billing (week 18–19, 16h)

Stripe metered billing. Each successful quality-gated PR creates a billing event. Failed tasks are not billed. Alternative $9/month flat plan.

### 4.4 Validation benchmark (week 19, 8h)

Re-run QualBench with taskinity mode vs prollama quality mode. Publish cost per mergeable PR comparison. Expected: taskinity produces comparable quality at 3–5x lower cost.


## Phase 5: Enterprise + ecosystem (weeks 20–28, 125h)

### 5.1 Usage metering + upsell engine (weeks 20–21, 22h)

UsageEvent model tracking every proxy request, task solve, and anonymization event. Stats service with monthly summaries. Dashboard with charts.

Seven automated upsell triggers: QueueTrigger, TimeTrigger, QualityTrigger, PrivacyTrigger, TeamTrigger, ROITrigger, IterationTrigger. Each produces a notification header and optional dashboard banner.

### 5.2 Partner panel (weeks 22–23, 26h)

Partner and PartnerUsage models. Admin interface. Routing logic for free partner offers. Revenue share tracking. This drives free-tier acquisition.

### 5.3 Architecture cleanup (week 24, 13h)

Extract business logic into services layer. Reduce fan-out in dashboard context builder and stripe webhook handler.

### 5.4 Enterprise features (weeks 25–28, 64h)

On-premises proxy deployment via Docker. SSO (SAML/OIDC). RBAC with Organization → Team → User → Role. API token scoping. Custom anonymization rules UI. Compliance export (SOC 2, ISO 27001, GDPR, AI Act).

QualBench Enterprise Mode: `prollama benchmark --mode enterprise` with on-prem proxy integration, audit trail for every QualBench event, and compliance-ready reporting.

Phase 5 milestone (week 28): 5–10 enterprise demos/PoCs. First $15K+ annual contracts in pipeline.


## Phase 6: API ecosystem + community (Q1 2027, weeks 29–36)

### 6.1 SDK for Python and TypeScript (weeks 29–30)

```python
from prollama.client import ProllamaClient
client = ProllamaClient()
result = client.run_task(issue)
score = client.score(result)
```

TypeScript/JS SDK for Node.js consumers.

### 6.2 IDE integrations (weeks 31–33)

VS Code extension: status bar showing Quality Score, command palette "QualBench: Run on PR", inline suggestions from top_issues. JetBrains plugin: on-commit quality score display.

GitHub App (qualbench-bot): richer than the Action, with persistent dashboards per repo, trend tracking across PRs, and team-level analytics.

### 6.3 Community tools (weeks 34–36)

"Submit your tool" marketplace on qualbench.com. Public compare pages generated automatically when results are submitted. Open dataset on Hugging Face for ML researchers.

Phase 6 milestone: QualBench is what developers add to CI "because that's what you do." 500+ repos with the Action. Category owned.


## Language and IDE expansion (backlog)

Full TypeScript/JavaScript AST anonymization (8h). Java, Go, Rust tree-sitter grammars (12h). JetBrains plugin (20h). Streaming SSE in proxy (6h). Custom model fine-tuning hooks (8h). Encrypted mapping storage (4h). "Paste your diff" playground on qualbench.com (20h, only after brand established). CSV export (4h, only on enterprise request).


## What got cut from v1 (and why)

**Auto-detection of tools:** replaced with explicit `--tool` flag. Magic detection is flaky, hard to debug, and creates support overhead. Explicit is always better than magic.

**10-endpoint API:** replaced with 2 endpoints. Overengineering APIs before demand exists wastes time.

**"Paste your diff" landing page feature:** moved to backlog. Requires backend sandbox, security isolation, and has low adoption early. Only build after brand trust exists.

**CSV export:** moved to backlog. Nice for PMOs and enterprise but doesn't drive early adoption.

**Compare tool on landing page:** moved to Phase 3. Requires data that doesn't exist until QualBench v1 runs.

**Docker as day-one distribution:** moved to Phase 3. The GitHub Action is Docker-based already — a standalone Docker image is redundant until there's demand from non-Python users.


## Risk register (updated)

### Risk 1: QualBench results are marginal
Probability: 30%. Impact: high. Mitigation: pivot framing to cost per mergeable PR. Even if quality scores are similar, the cost story may be 10x different.

### Risk 2: GitHub Action adoption is slow
Probability: 40%. Impact: high. Mitigation: seed adoption by adding qualbench-action to Softreck's own repos and 5–10 friendly OSS projects. Write case studies. The first 20 installs are manual outreach, not organic.

### Risk 3: "CI for AI code" positioning doesn't land
Probability: 25%. Impact: medium. Mitigation: keep "benchmark" as secondary positioning. Some audiences respond to "benchmark" (researchers, HN), others to "CI tool" (engineering leads). Use both, lead with CI.

### Risk 4: prollama cli.py refactoring breaks users mid-distribution
Probability: 20%. Impact: medium. Mitigation: refactoring happens in Phase 2 (after distribution is live), not Phase 1. 124 existing tests provide safety net. Run full suite after each step.

### Risk 5: Scope creep from uploaded feedback
Probability: 60%. Impact: high. Mitigation: this plan explicitly lists what got cut. The uploaded documents contain at least 15 good ideas (playground, live dashboard, SDK, compare marketplace, paste-diff tool). All are Phase 3+ or backlog. The core loop (run → score → compare → improve) ships in Phase 1. Everything else waits.


## Metrics that matter

### Distribution (leading indicators)
- GitHub Action installs (target: 100 by week 16)
- `prollama benchmark run` executions per week
- PyPI downloads for qualbench
- GitHub stars on softreck/qualbench

### Revenue (lagging indicators)
- MRR from Professional subscriptions
- Taskinity tasks per month and cost per mergeable PR
- Enterprise pipeline value
- Conversion rate: QualBench user → prollama/taskinity customer

### Product health
- Time to first score (target: <60 seconds via quickstart)
- CI pipeline pass rate (qualbench-action must not be flaky)
- Runner reliability (patches must apply cleanly, tests must run)


## Timeline summary

| Weeks | Phase | Key deliverable | Effort | Revenue impact |
|-------|-------|----------------|--------|----------------|
| 1–3 | Prove it | QualBench v0 results published | 50h | Validates strategy |
| 4–8 | Core loop | `prollama benchmark run` + GitHub Action + leaderboard | 65h | Distribution engine live |
| 9–12 | Fix engine | cli.py refactored + billing enforceable | 45h | $39/mo chargeable |
| 13–16 | Scale | QualBench v1 + API + pip + Docker + content | 64h | Inbound pipeline |
| 17–19 | Taskinity | Cheap mode + branding + per-task billing | 44h | Mass-market entry |
| 20–28 | Enterprise | Metering + partners + SSO + RBAC + on-prem | 125h | $15K+ deals |
| 29–36 | Ecosystem | SDK + IDE + community + marketplace | 60h | Category ownership |

Total: ~453h (~57 working days) across 36 weeks.

First distribution: week 4 (prollama benchmark run).
First revenue: week 12 (Professional plan enforcement).
First mass-market revenue: week 19 (taskinity per-task billing).
First enterprise pipeline: week 28 (on-prem + SSO + compliance).
