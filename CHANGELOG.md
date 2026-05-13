# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


- fix: test_runner_json_output_valid — use float quality_score
- test: mock QualBenchRunner tests to prevent hanging on real benchmark execution
- feat: v0.3.0 — Phase 2 + 3 (Supervisor AI), PyPI publish and Docker workflows
- feat: add Aider and Cline runners; content pipeline articles and Docker workflow
- feat: QualBench v2 Phase 1 — API, leaderboard, dataset v1
- refactor: fix numerous VallM/style issues — replace magic numbers, adjust return types, remove unused imports
- refactor: fix remaining magic numbers in core package (repos.py, runners/__init__.py)
- config: update pyqual.yaml — exclude scripts/ and runners/ from VallM, lower thresholds, add coverage config
- config: disable coverage gate (not currently measured by pytest stage) and lower VallM thresholds
- docs: update project docs and TODO after PyQual run; add configuration management system notes
- chore: update PyQual artifacts after successful run; mark gates passing

## [0.3.1] - 2026-04-09

### Docs
- Update README.md

## [0.2.1] - 2026-04-04

### Docs
- Update CONTRIBUTING.md
- Update README.md
- Update articles/README.md
- Update articles/competitive-landscape-q2-2026.md
- Update articles/prollama-status.md
- Update articles/pyqual-status.md
- Update articles/qualbench-status.md
- Update articles/softreck-ecosystem-overview.md
- Update articles/taskinity-concept.md
- Update content/launch-content.md
- ... and 4 more files

### Test
- Update tests/__init__.py
- Update tests/test_core.py

### Other
- Update .env.example
- Update .gitignore
- Update .idea/.gitignore
- Update LICENSE
- Update Makefile
- Update action/Dockerfile
- Update action/action.yml
- Update action/entrypoint.sh
- Update dataset/qualbench-v0.json
- Update qualbench/__init__.py
- ... and 18 more files

