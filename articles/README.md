# Softreck Articles

WordPress-ready articles about the status of each project in the Softreck developer tooling ecosystem.

## Articles

| # | Article | Project | Status |
|---|---------|---------|--------|
| 1 | [QualBench — The Missing Benchmark for AI Code Quality](qualbench-status.md) | QualBench | v0 released |
| 2 | [prollama — Security Layer for AI on Proprietary Code](prollama-status.md) | prollama | Production-ready package |
| 3 | [pyqual — Declarative Quality Gates for AI-Assisted Development](pyqual-status.md) | pyqual | Beta (v0.1.29 on PyPI) |
| 4 | [The Softreck Ecosystem — Six Tools That Work Better Together](softreck-ecosystem-overview.md) | Ecosystem | Overview |
| 5 | [Taskinity — Quality-Gated AI Ticket Solving at $0.50 per PR](taskinity-concept.md) | Taskinity | Concept / pending QualBench |
| 6 | [AI Coding Tools in Q2 2026 — Where prollama Fits](competitive-landscape-q2-2026.md) | Market analysis | April 2026 |

## Format

Each article is a standalone Markdown file with YAML front matter compatible with WordPress import plugins (WP All Import, Jeykll-to-WP, etc.):

```yaml
---
title: "Article Title"
slug: article-slug
date: 2026-04-04
status: publish
category: products
tags: [tag1, tag2, tag3]
excerpt: "Short description for RSS and social."
author: Softreck
featured_image: image-name.png
---
```

## Publishing

Import directly into WordPress via WP-CLI:

```bash
# With WP-CLI markdown importer
for f in *.md; do
  wp post create "$f" --post_status=publish --post_type=post
done
```

Or use any Markdown-to-WordPress plugin that reads YAML front matter.

## License

Content: CC BY 4.0
Code examples within articles: Apache 2.0
