---
title: "The Softreck Ecosystem — Six Tools That Work Better Together"
slug: softreck-ecosystem-tools-overview
date: 2026-04-04
status: publish
category: ecosystem
tags: [softreck, pyqual, prollama, code2llm, vallm, planfile, algitex, developer-tools]
excerpt: "Six open-source tools forming a complete pipeline from code analysis through AI-powered fixing to quality-gated delivery. Each useful alone, more powerful together."
author: Softreck
featured_image: ecosystem-hero.png
---

# The Softreck Ecosystem — Six Tools That Work Better Together

**Ecosystem status: 4 tools active, 2 in development**

## Architecture

The Softreck ecosystem is built around one principle: each tool does one thing well and communicates through standard file formats. pyqual orchestrates. prollama executes. Everything else feeds data in or takes action on results.

The data flow is straightforward. A developer labels an issue or pushes code. pyqual runs the pipeline: code2llm analyzes metrics, vallm validates via LLM, prollama fixes what fails (with anonymization), pytest verifies, and planfile tracks the work. The loop iterates until quality gates pass or the iteration limit is reached.

## code2llm — The Analyzer

**Status: active**

code2llm scans source code and generates structured metrics consumed by pyqual's quality gates. It produces cyclomatic complexity per function, critical issue counts, and function-level breakdowns. Output goes to `analysis_toon.yaml` in a format pyqual reads directly.

The tool also generates "evolution" format output showing how metrics change over time — useful for tracking whether code quality is improving or degrading across commits. This feeds into pyqual's ability to detect quality trends and trigger proactive fixes.

In the pipeline: `code2llm ./ -f toon,evolution` runs as the first stage, establishing the baseline metrics that pyqual checks against its gates.

## vallm — The Validator

**Status: active**

vallm uses LLMs to validate code quality beyond what static analysis catches. Where pylint finds syntax issues and ruff catches style violations, vallm assesses whether code logic makes sense, whether error handling is adequate, whether naming is meaningful, and whether the overall approach is sound.

Output goes to `validation_toon.yaml` or `.pyqual/errors.json`. The `vallm_pass` metric — the percentage of files passing validation — is one of pyqual's core gates. A typical threshold is 90%: if more than 10% of files fail LLM validation, the gate fails and triggers a fix iteration.

vallm operates in batch mode for efficiency, scanning entire directories recursively. It uses LiteLLM for model access, supporting any provider from local Ollama to cloud APIs.

## planfile — The Ticket Manager

**Status: active**

planfile bridges the gap between informal TODO lists and formal issue trackers. It has two backends: a markdown backend that parses TODO.md checklists, and a GitHub backend that syncs with GitHub Issues via the API.

In the pyqual ecosystem, planfile serves two roles. First, it tracks work items that feed into the pipeline — issues labeled for automated fixing trigger the full pyqual loop. Second, it creates tickets when quality gates fail persistently: if pyqual exhausts its iteration limit without passing all gates, it can create a ticket describing what failed and by how much, routing the problem to a human developer.

CLI access is through pyqual: `pyqual tickets todo` syncs TODO.md, `pyqual tickets github` syncs GitHub Issues, `pyqual tickets all` syncs both.

## algitex — The Extender

**Status: planned**

algitex imports pyqual as a dependency and provides extended integrations for specific workflows. It's designed for enterprise environments that need to wrap pyqual's pipeline into larger CI/CD systems or custom toolchains.

Where pyqual is deliberately minimal, algitex is intentionally expansive — supporting complex multi-repo pipelines, custom reporting formats, and integration with enterprise tools like Jira, Linear, and Azure DevOps.

## How the tools connect

The integration is file-based and loosely coupled. code2llm writes `analysis_toon.yaml`. vallm writes `validation_toon.yaml` or `.pyqual/errors.json`. prollama reads these files to understand what needs fixing. pytest writes coverage reports. pyqual reads all of them to check gates.

This design means each tool is independently useful. You can use code2llm without pyqual for standalone code analysis. You can use vallm without prollama for LLM-based code review. You can use prollama without pyqual as a standalone AI coding assistant with anonymization. Together they form a pipeline; apart they're useful standalone tools.

## Design principles

Never block the user mid-task. If a fix is hard, it takes longer — but it always finishes. No paywalls, no unexpected limits, no abandoned tasks.

Pay for outcomes, not tokens. prollama absorbs the cost risk of failed LLM attempts. The user pays for completed, quality-gated results.

Privacy by architecture. Code is anonymized before leaving the developer's machine. The LLM never sees your proprietary identifiers.

Cheapest model first. Approximately 75% of tasks are solved by the cheapest available model. Escalation happens only on failure.

Declarative over imperative. Quality standards are defined in YAML, not enforced by manual review. The machine checks what humans defined.

## Licensing

All ecosystem tools use Apache 2.0 for open-source components. prollama's cloud orchestrator, Supervisor AI, and dashboard are proprietary.

---

*The Softreck ecosystem is built in Gdańsk, Poland. Learn more at softreck.com.*
