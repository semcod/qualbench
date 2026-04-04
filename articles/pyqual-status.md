---
title: "pyqual — Declarative Quality Gates for AI-Assisted Development"
slug: pyqual-declarative-quality-gates-status
date: 2026-04-04
status: publish
category: products
tags: [pyqual, quality-gates, ci-cd, yaml, llm, testing, code-review]
excerpt: "One YAML file. One command. pyqual iterates analyze → validate → fix → test until your code meets quality thresholds. The missing layer between AI-generated code and production."
author: Softreck
featured_image: pyqual-hero.png
---

# pyqual — Declarative Quality Gates for AI-Assisted Development

**Project status: active development / beta (v0.1.29 on PyPI)**

## The gap pyqual closes

Copilot, Claude, and GPT generate code fast. But nobody automatically checks whether that code meets engineering standards before it reaches code review. And nobody automatically iterates if it doesn't.

pyqual closes that gap. You define quality metrics in YAML, and pyqual runs a loop: analyze, validate, fix, test. It iterates until your code meets the thresholds or the iteration limit is reached. The key principle is deterministic orchestration of non-deterministic tools — LLMs are probabilistic, but your quality standards are not.

## How it works

Three commands cover the entire workflow. `pyqual init` creates a configuration file with sensible defaults. `pyqual run` executes the pipeline loop. `pyqual gates` checks current metrics without running stages.

The pipeline is defined declaratively in `pyqual.yaml`. You specify metrics thresholds — cyclomatic complexity no higher than 15, test coverage at least 80%, validation pass rate at least 90% — and a sequence of stages: analyze with code2llm, validate with vallm, fix with prollama when metrics fail, and test with pytest. The loop runs up to a configurable number of iterations. Each iteration runs the full pipeline. If all gates pass, it stops. If any fail, it triggers the fix stage and iterates again.

## Current state

pyqual v0.1.29 is published on PyPI with 129 functions, 27 classes, and 17 source files. Average cyclomatic complexity is 4.7. The core pipeline, CLI, Python API, and plugin system are all implemented and tested.

The tool integrates with 13+ analysis and testing tools out of the box: pylint, ruff, flake8, and bandit for code quality and security; code2llm and radon for complexity metrics; pytest with coverage for testing; interrogate for documentation coverage; pip-audit for vulnerability scanning; and vallm for LLM-based code validation.

The plugin system allows custom metric collectors with approximately 20 lines of Python. Subclass `MetricCollector`, implement `collect()`, and register with the plugin registry. Built-in plugin collectors cover LLM benchmarks, hallucination detection, SBOM compliance, internationalization, accessibility, repository health, and security scanning.

## Design philosophy

pyqual is intentionally small — approximately 800 lines of Python core code. It orchestrates, it doesn't implement. It reads metrics from tools you already use and makes pass/fail decisions based on your thresholds.

The fix provider is pluggable. prollama is the native fix provider, but any CLI tool that accepts code and produces patches can be integrated. The `when: metrics_fail` directive triggers fixing only when gates fail, preventing unnecessary LLM usage.

The YAML manifest is the source of truth. The LLM is just a tool that transforms failing code into passing code, validated by deterministic quality gates. This framing — treating LLMs as compilers, not decision-makers — is central to the architecture.

## Integration with prollama

When pyqual detects quality gate failures, it writes a fix request describing which metrics failed and by how much. prollama reads this request, anonymizes the code, selects the cheapest capable model, generates a fix, runs tests, and returns results. pyqual re-checks all gates. The entire loop runs autonomously in CI/CD.

Configuration is minimal — one line in the fix stage: `provider: prollama` with an optional strategy (auto, cheap, quality, or local-only) and budget cap.

## Role in the ecosystem

pyqual is the orchestration layer that connects all other tools in the Softreck ecosystem. code2llm provides analysis metrics. vallm provides LLM-based validation. prollama provides intelligent fixing with anonymization. planfile manages tickets and synchronizes TODO.md with GitHub Issues.

In the context of QualBench, pyqual's iterate-until-pass approach is the core differentiator being tested. The hypothesis is that iterative quality-gated execution produces significantly more mergeable PRs than single-shot AI code generation.

## Technical details

Requires Python 3.9 or later. Core dependencies are pyyaml, typer, rich, litellm, python-dotenv, mcp, prefact, and planfile. Optional extras include analysis features, cost tracking, and MCP integration.

GitHub Actions and GitLab CI templates are available. MkDocs-based documentation covers quickstart, configuration, integrations, and API reference.

**Repository:** github.com/semcod/pyqual
**License:** Apache 2.0
**Website:** pyqual.dev

---

*pyqual is the brain of the Softreck developer tooling ecosystem, built in Gdańsk, Poland.*
