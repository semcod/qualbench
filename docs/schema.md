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
