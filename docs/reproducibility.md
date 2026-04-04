# Reproducibility Guide

QualBench results must be fully reproducible. This document describes how to verify and reproduce any published result.

## Environment Requirements

- Python 3.11+
- Docker (for isolated repo environments)
- 8GB RAM minimum
- 20GB disk space (for cloned repositories)

## Reproduce Published Results

```bash
# 1. Clone at the exact version tag
git clone https://github.com/softreck/qualbench.git
cd qualbench
git checkout v0.1.0  # match the published version

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup repositories at exact commits
make setup-repos

# 4. Re-run evaluation on published patches
make evaluate-auto

# 5. Compare scores
python scripts/compare_scores.py \
    --published results/published/scores.json \
    --reproduced results/evaluation.json
```

## What Gets Logged

Every benchmark run creates:

```
results/{tool}/
├── metadata.json     # tool version, API params, timestamps
├── QB-001.json       # per-issue result with patch
├── QB-002.json
├── ...
└── summary.json      # aggregate results
```

`metadata.json` includes:
- Tool name and version
- Model(s) used with exact version strings
- API parameters (temperature, max_tokens, etc.)
- Timestamp (start and end)
- Python version
- OS and architecture

## Verification Checklist

Before submitting results to the leaderboard:

- [ ] All 10 issues attempted (even if some fail)
- [ ] Each result has a non-empty `patch` field or explicit `error`
- [ ] `metadata.json` includes all required fields
- [ ] `make evaluate-auto` passes without errors
- [ ] Results directory committed with exact file structure
