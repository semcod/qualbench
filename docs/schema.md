# QualBench Result Schema v1

One format. Used everywhere: CLI output, API responses, GitHub Action comments, leaderboard entries.

## Schema

```json
{
  "tool": "string",
  "issue_id": "string",
  "quality_score": 0.0,
  "dimensions": {
    "correctness": 0.0,
    "security": 0.0,
    "quality": 0.0,
    "mergeability": 0.0,
    "iterations": 0.0,
    "cost": 0.0
  },
  "verdict": "string",
  "top_issues": ["string"],
  "patch": "string",
  "resolved": false,
  "cost_usd": 0.0,
  "time_seconds": 0.0,
  "iterations": 0,
  "model_used": "string"
}
```

## Fields

**tool** — name of the AI tool that generated the patch. Always explicit, never auto-detected.

**issue_id** — QualBench issue identifier (e.g., "QB-001") or "LOCAL" for current diff scoring.

**quality_score** — composite score 0–100, computed from weighted dimensions.

**dimensions** — each dimension scored 0–100 independently. Weights: correctness 25%, mergeability 25%, security 15%, quality 15%, iterations 10%, cost 10%.

**verdict** — one of three values: `ready_to_merge` (score ≥85), `needs_review` (65–84), `not_merge_ready` (<65).

**top_issues** — list of identified problems: `tests_failed`, `security_issues`, `high_complexity`, `missing_edge_case`, `complexity_increase`.

**patch** — git diff of the changes (truncated to 5000 chars in JSON output).

**resolved** — boolean, true if all tests pass.

**cost_usd** — estimated or actual cost in USD.

**time_seconds** — wall clock execution time.

**iterations** — number of fix attempts.

**model_used** — primary LLM model identifier.

## Usage

```bash
# CLI
qualbench run --tool prollama --json

# Python
from qualbench.benchmark import QualBenchRunner
result = QualBenchRunner(tool="prollama").run()
print(result.to_json())

# GitHub Action
# Result available as step output: ${{ steps.qualbench.outputs.result_json }}
```

## Verdicts

| Verdict | Score range | Meaning |
|---------|-----------|---------|
| `ready_to_merge` | ≥85 | Ship it — merge without changes |
| `needs_review` | 65–84 | Acceptable with minor fixes |
| `not_merge_ready` | <65 | Requires significant rework |

## Examples

### Ready to merge (high quality)
```json
{
  "tool": "prollama",
  "issue_id": "QB-003",
  "quality_score": 91.5,
  "dimensions": {
    "correctness": 100.0,
    "security": 100.0,
    "quality": 85.0,
    "mergeability": 90.0,
    "iterations": 100.0,
    "cost": 75.0
  },
  "verdict": "ready_to_merge",
  "top_issues": [],
  "patch": "diff --git a/src/utils.py b/src/utils.py...",
  "resolved": true,
  "cost_usd": 0.25,
  "time_seconds": 32.4,
  "iterations": 1,
  "model_used": "qwen2.5-coder:32b"
}
```

### Needs review (moderate issues)
```json
{
  "tool": "copilot",
  "issue_id": "QB-007",
  "quality_score": 72.0,
  "dimensions": {
    "correctness": 100.0,
    "security": 60.0,
    "quality": 65.0,
    "mergeability": 70.0,
    "iterations": 85.0,
    "cost": 80.0
  },
  "verdict": "needs_review",
  "top_issues": ["security_issues", "high_complexity"],
  "patch": "diff --git a/src/auth.py b/src/auth.py...",
  "resolved": true,
  "cost_usd": 0.18,
  "time_seconds": 28.1,
  "iterations": 2,
  "model_used": "gpt-4o"
}
```

### Not merge ready (critical failures)
```json
{
  "tool": "openhands",
  "issue_id": "QB-002",
  "quality_score": 45.0,
  "dimensions": {
    "correctness": 0.0,
    "security": 70.0,
    "quality": 60.0,
    "mergeability": 20.0,
    "iterations": 0.0,
    "cost": 0.0
  },
  "verdict": "not_merge_ready",
  "top_issues": ["tests_failed", "missing_edge_case"],
  "patch": "diff --git a/src/parser.py b/src/parser.py...",
  "resolved": false,
  "cost_usd": 0.12,
  "time_seconds": 45.0,
  "iterations": 3,
  "model_used": "claude-3-5-sonnet"
}
```

## Edge Cases

### Unresolved (tests failing)
When tests fail (`correctness: 0`), the score formula automatically zeros out iterations and cost dimensions:
- `iterations` = 0 (no points for iterations if unresolved)
- `cost` = 0 (no points for cheap cost if unresolved)
- `mergeability` ≤ 20 (cannot be mergeable if tests fail)

### Security critical issues
Multiple HIGH severity bandit findings will zero the security dimension:
- 2+ HIGH severity issues → security = 0
- 1 HIGH severity issue → security = 40
- 2+ MEDIUM severity issues → security = 50

### Complexity thresholds
Quality dimension based on cyclomatic complexity (radon):
- avg CC ≤ 5 → quality = 100
- avg CC ≤ 10 → quality = 80
- avg CC ≤ 15 → quality = 60
- avg CC > 15 → quality degrades linearly

### Cost scoring
Cost dimension (only counted when resolved):
- ≤ $0.05 → 100 points
- ≤ $0.20 → 90 points
- ≤ $0.50 → 75 points
- ≤ $1.00 → 60 points
- ≤ $2.00 → 40 points
- ≤ $5.00 → 20 points
- > $5.00 → 5 points
