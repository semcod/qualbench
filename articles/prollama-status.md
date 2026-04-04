---
title: "prollama — Security Layer for AI on Proprietary Code"
slug: prollama-security-layer-ai-coding
date: 2026-04-04
status: publish
category: products
tags: [prollama, anonymization, ast, llm, privacy, compliance, ai-coding]
excerpt: "The only AI coding execution layer with AST-based code anonymization. Your code never reaches an LLM in readable form. EU AI Act ready."
author: Softreck
featured_image: prollama-hero.png
---

# prollama — Security Layer for AI on Proprietary Code

**Project status: Python package production-ready, SaaS monetization in progress**

## What prollama does

prollama is a security layer that lets companies use AI coding tools on proprietary code without risking data leaks or compliance violations. It sits between your development environment and any LLM provider — anonymizing code before it leaves, routing requests to the cheapest capable model, and rehydrating results with your original identifiers.

The core capability that no competitor offers: AST-based code anonymization using tree-sitter. While every other tool handles privacy through data retention policies or deployment architecture, prollama transforms the code itself. Variable names, function names, class names, and proprietary identifiers are replaced with generic equivalents while preserving syntactic structure. After the LLM responds, original names are restored automatically.

## Current state of the package

The Python package is production-ready at approximately 5,400 lines of code across 56 files. It ships with 124 passing tests at 86% coverage and zero lint errors. Average cyclomatic complexity is 3.8.

The three-layer anonymization pipeline is fully implemented. Layer 1 uses 70+ regex patterns to catch secrets, API keys, tokens, connection strings, emails, and IPs in under 1ms. Layer 2 applies Microsoft Presidio with spaCy NLP to detect person names and PII in comments at 5–10ms. Layer 3 parses code into abstract syntax trees via tree-sitter and renames proprietary identifiers at 10–50ms. All three layers support reversible rehydration — after the LLM responds, original names are restored.

The 4-tier model router classifies tasks by complexity and starts with the cheapest available model. Simple tasks (lint fixes, typos) go to local Qwen or DeepSeek at effectively $0. Medium tasks use mid-tier cloud models. Only genuinely hard tasks escalate to premium models like Claude Sonnet. Approximately 75% of tasks are solved by the cheapest tier.

The autonomous task executor accepts GitHub Issues, GitLab Issues, or CLI descriptions. It builds context from the repository's AST dependency graph, anonymizes, selects a model, generates a fix, runs tests, iterates if needed, and opens a PR. The entire pipeline runs without human intervention.

Additional capabilities include a Click-based CLI with 18 commands, an interactive REPL shell, an OpenAI-compatible proxy stub (change one environment variable to route all requests through prollama), and a full documentation suite.

## Known technical debt

The primary refactoring target is `cli.py` — a 518-line god module with cyclomatic complexity of 19 and one circular dependency. The refactoring plan splits it into four submodules (auth, solve, config, tickets) and breaks five high-CC functions. Estimated effort is 11 hours.

The www SaaS project is functionally improved after a prior refactor but is missing all monetization infrastructure: plan enforcement middleware, usage metering, upsell triggers, and the partner panel.

## Market position

In a $7.4 billion AI coding tools market, no established product performs AST-based code anonymization before LLM requests. The closest tools — Stacklok's CodeGate (archived June 2025), LLM Guard, CloakPipe — operate at the text/pattern level with regex and NER. None parses code structure.

The timing is favorable. GitHub began collecting Copilot interaction data for model training on April 24, 2026 — generating significant developer backlash. The EU AI Act's high-risk obligations become fully enforceable on August 2, 2026 with fines up to €35 million. GitGuardian's 2026 report found 29 million secrets leaked on GitHub in 2025, with AI service credential leaks surging 81%.

The target buyer is not the individual developer. It's the CTO, CISO, or Head of Engineering at a mid-size company (50–500 developers) in fintech, healthtech, or enterprise SaaS who needs their team to use AI but is blocked by security, compliance, or legal concerns.

## Pricing

Three tiers. Free/BYO Key gives CLI access with regex anonymization and solve capabilities at zero subscription cost — the user pays only their own API costs. Professional at $39/month adds AST anonymization, Supervisor AI review, parallel tasks, proxy, and audit logging. Team at $29/developer/month adds shared context and team dashboard. Enterprise pricing starts at $15K–$60K annually for on-premises deployment, SSO, RBAC, compliance exports, and custom anonymization rules.

## What's next

Immediate priorities are completing the monetization infrastructure for the SaaS (plan enforcement, usage metering, upsell triggers), refactoring the cli.py god module, and executing the QualBench benchmark to validate quality-gated iteration against competitors.

The EU AI Act compliance deadline in August 2026 creates a natural market timing trigger for enterprise outreach.

## Technical details

Built with Python, FastAPI, tree-sitter, Microsoft Presidio, LiteLLM, Click, prompt-toolkit, Pydantic, and hatchling. Supports Ollama, vLLM, and llama.cpp for local inference, plus OpenAI, Anthropic, and OpenRouter for cloud.

**Repository:** github.com/softreck/prollama
**License:** Apache 2.0 (core), Proprietary (cloud/dashboard)

---

*prollama is built by Softreck in Gdańsk, Poland. Part of the pyqual developer tooling ecosystem.*
