---
title: "QualBench — The Missing Benchmark for AI Code Quality"
slug: qualbench-ai-code-quality-benchmark
date: 2026-04-04
status: publish
category: products
tags: [qualbench, benchmark, ai, code-quality, swe-bench, open-source]
excerpt: "SWE-bench measures if AI solves the problem. QualBench measures if you'd ship the PR. An open-source benchmark for production readiness of AI-generated code."
author: Softreck
featured_image: qualbench-hero.png
---

# QualBench — The Missing Benchmark for AI Code Quality

**Project status: v0 released, benchmark execution in progress**

## The problem we're solving

AI coding tools resolve 70–80% of curated benchmark tasks. The numbers sound impressive — until you look at what actually happens in engineering teams. Most AI-generated pull requests are not mergeable without human fixes. They pass tests but increase complexity, introduce subtle security issues, skip edge cases, and require multiple review rounds.

Every existing benchmark — SWE-bench, SWE-bench Pro, HumanEval — asks one question: does the patch make tests pass? Nobody asks the question that engineering teams actually care about: would a senior developer approve this PR?

## What QualBench is

QualBench is an open-source benchmark that measures production readiness of AI-generated code. Not just correctness — the full spectrum from "does it work" to "would you merge it."

Every AI-generated patch is evaluated across six dimensions: correctness (25% weight, verified via pytest), mergeability (25%, blind human review on a 1–5 scale), security (15%, bandit delta), code quality (15%, cyclomatic complexity and dead code), iteration efficiency (10%, attempts to converge), and cost efficiency (10%, USD per successful patch).

The composite Quality Score runs 0–100. We also track cost per mergeable PR separately — the metric CFOs actually care about.

## Current state

The v0 dataset contains 10 real-world issues from 7 well-tested Python repositories: Flask, Django, FastAPI, Requests, httpx, Pydantic, and Starlette. Issues span four difficulty tiers — 3 simple bug fixes, 3 medium cross-module bugs, 2 hard refactoring tasks, and 2 security vulnerability patches.

The Python package is published and installable via pip. The CLI provides commands for setup, running tools, evaluation, and leaderboard generation. 26 unit tests cover dataset loading, all scoring functions, and dimension weight validation. GitHub Actions CI runs lint and tests on Python 3.10–3.12.

Three tools are being benchmarked in v0: GitHub Copilot Coding Agent, OpenHands with Claude Sonnet, and prollama with pyqual quality gates.

## Key design decisions

Human review is 25% of the score — the single largest weight. Two independent reviewers evaluate each patch blind, without knowing which tool generated it. This is expensive, subjective, and doesn't scale. It's also the only metric that actually correlates with what engineering teams care about. We mitigate subjectivity with multiple reviewers and a third-reviewer tiebreaker for large disagreements.

Iterations are a first-class metric. Most AI coding tools are single-shot: generate once, return PR. QualBench rewards tools that iterate against quality gates and converge to better output, reflecting how real engineering works.

Cost efficiency measures USD per successful patch including retries. Two tools can produce identical correctness scores, but if one costs $0.20 and the other $20, that matters.

## What we expect to find

We're testing five hypotheses. First, that correctness and mergeability are very different things — tools scoring 70% on SWE-bench may score 30–40% on mergeability. Second, that iterative agents outperform single-shot approaches on quality. Third, that cheap models combined with iteration can beat expensive models running once. Fourth, that security regressions are common in AI-generated patches. Fifth, that cost per usable PR varies 10–100x across tools.

## What's next

Results from v0 will be published as soon as benchmark execution and human review are complete. The leaderboard, methodology, and all raw data will be open on GitHub.

v1 will expand to 50 issues, add TypeScript, and include test coverage delta and mypy type checking as additional quality metrics.

The benchmark is designed as an open platform — anyone can add their tool by implementing a single Python function and submitting a PR.

## Technical details

The package is built with hatchling, uses Click for CLI, and integrates radon (complexity), bandit (security), ruff (linting), and pytest (correctness) for automated evaluation. The runner interface is a simple abstract base class with one required method.

**Repository:** github.com/semcod/qualbench
**License:** Apache 2.0
**Website:** qualbench.com

---

*QualBench is built by Softreck in Gdańsk, Poland. Powered by pyqual quality gate orchestration.*
