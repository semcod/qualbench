# QualBench Methodology

## Why QualBench Exists

Existing benchmarks (SWE-bench, SWE-bench Pro, HumanEval) measure one thing: **correctness**. Does the patch make the failing tests pass without breaking existing ones?

This matters, but it's not what engineering teams care about most. In production, the question is: **would a senior developer approve this PR?**

A patch can be correct but unmergeable — it might add unnecessary complexity, introduce dead code, skip edge cases, or use patterns the team avoids. QualBench measures the full spectrum from "does it work" to "would you ship it."

## Dataset Construction

QualBench v0 contains 10 issues selected for diversity across:

**Difficulty tiers:**
- 3 simple (single-function fixes, clear root cause)
- 3 medium (cross-module bugs, requires context)
- 2 hard (refactoring, architectural changes)
- 2 security (vulnerability patches)

**Repositories:**
- pallets/flask (web framework, ~15k stars)
- psf/requests (HTTP library, ~52k stars)
- tiangolo/fastapi (modern web framework, ~80k stars)
- django/django (full-stack framework, ~80k stars)
- encode/httpx (async HTTP client, ~13k stars)
- pydantic/pydantic (data validation, ~22k stars)
- encode/starlette (ASGI framework, ~10k stars)

All repositories have comprehensive test suites, making automated correctness evaluation reliable.

**Issue selection criteria:**
1. Issue has a known solution (closed PR with tests)
2. Issue is self-contained (no external dependencies needed)
3. Issue has clear acceptance criteria in the description
4. Repository has >80% test coverage in affected area
5. Fix requires non-trivial reasoning (not just a typo)

## Evaluation Protocol

### Environment
- Each tool runs in an isolated Docker container
- Repository cloned at a specific base_commit (before the fix)
- Python version matches repository requirements
- All dependencies installed per repository's setup instructions
- No network access during evaluation (prevents data leakage)
- 15-minute timeout per issue

### Automated Metrics

**Correctness (weight: 30%)**
Binary pass/fail using the repository's test suite:
- FAIL_TO_PASS tests must now pass (issue resolved)
- PASS_TO_PASS tests must still pass (no regressions)
- Score: 100 if all pass, 0 otherwise

**Security (weight: 20%)**
Delta of bandit static analysis findings:
- Baseline: bandit run on repo before patch
- Post-patch: bandit run on repo after patch
- Score based on new findings severity (see README)

**Quality (weight: 20%)**
Composite of three sub-metrics:
- Cyclomatic complexity delta (radon): CC should not increase
- Patch efficiency: lines changed vs gold patch size
- Dead code: ruff F841/F811 check for unused variables/imports

### Human Review (weight: 30%)

Two independent reviewers evaluate each patch on a 1-5 scale:

| Score | Label | Meaning |
|-------|-------|---------|
| 1 | Reject | Fundamentally wrong approach, would not accept |
| 2 | Major rework | Correct idea but poor implementation, 3+ comments |
| 3 | Minor fixes | Acceptable approach, 2-3 comments needed |
| 4 | Approve with nits | Good code, 0-1 minor style comments |
| 5 | Ship it | Merge immediately, no changes needed |

**Review process:**
- Reviewers see only the patch diff (not the tool name)
- Reviewers do not see each other's scores until both are submitted
- If scores differ by more than 2 points, a third reviewer is added
- Final score = average of all reviews, normalized to 0-100

## Scoring

Quality Score = Σ (dimension_score × dimension_weight)

All dimension scores are normalized to 0-100 before weighting.

## Reproducibility

Every benchmark run must be fully reproducible:

```bash
git clone https://github.com/softreck/qualbench.git
cd qualbench
make setup
make benchmark
make evaluate
```

All random seeds, API parameters, and environment details are logged in `results/{tool}/metadata.json`.

## Limitations

1. **Small dataset (v0):** 10 issues is insufficient for statistical significance. Results should be treated as directional, not definitive. v1 will expand to 50+ issues.

2. **Python only (v0):** All repositories are Python. v1 will add TypeScript.

3. **Human review subjectivity:** Mergeability scores depend on reviewer experience and standards. We mitigate this with multiple reviewers and blind evaluation.

4. **Tool configuration:** Each tool is run with default settings. Custom configurations might improve results. We document exact settings used.

5. **Issue representativeness:** 10 curated issues cannot represent the full spectrum of real-world development tasks.

## Versioning

- **v0** (current): 10 issues, 4 metrics, proof of concept
- **v1** (planned): 50 issues, 6 metrics (+ coverage, review rounds), TypeScript support
- **v2** (planned): 100+ issues, multi-language, automated leaderboard updates
