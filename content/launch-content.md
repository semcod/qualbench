# QualBench Launch Content

## 1. Hacker News — Show HN post

**Title:**
Show HN: QualBench – benchmark that measures if you'd merge AI-generated PRs, not just if tests pass

**Body:**

Hey HN,

We've been frustrated that every AI coding benchmark measures one thing: does the patch make tests pass?

That's necessary but not sufficient. In our experience, the majority of AI-generated PRs that "pass tests" still need significant human rework before anyone would actually merge them. They introduce complexity, skip edge cases, add dead code, or create subtle security issues.

So we built QualBench — an open-source benchmark that scores AI coding tools on production readiness, not just correctness.

6 dimensions: correctness (tests pass), security (bandit delta), code quality (CC, dead code), mergeability (blind human review 1-5), iterations (attempts to converge), and cost efficiency ($/successful patch).

Key design decisions:
- Human review is 25% of the score. Two independent reviewers evaluate each patch blind (no tool names). This is the metric that matters most to engineering teams and nobody measures it.
- Iterations are a first-class metric. Single-shot tools that dump a first draft get penalized vs agents that iterate against quality gates.
- Cost per mergeable PR. Not cost per attempt — cost per result you'd actually ship.
- Fully reproducible: `make benchmark` runs everything. Apache 2.0.

v0 has 10 issues from Flask, Django, FastAPI, Requests, httpx, Pydantic, and Starlette. Mix of bug fixes, refactors, and security patches. We're running Copilot Coding Agent, OpenHands + Claude, and our own tool (prollama + pyqual quality gates) against it now.

We expect the results to show that correctness and mergeability are very different things — tools that score 70%+ on SWE-bench may score 30-40% on mergeability.

Anyone can add their tool: copy the runner template, implement run(), submit a PR.

GitHub: https://github.com/semcod/qualbench


---

## 2. Twitter/X thread

**Tweet 1 (hook):**
AI coding tools can fix 70% of benchmark bugs.

But most AI-generated PRs are not mergeable without human fixes.

We built QualBench — the first benchmark that measures production readiness, not just correctness.

Thread:

**Tweet 2 (problem):**
SWE-bench asks: "do tests pass?"

That's like grading a hire by checking if their code compiles.

Engineering teams care about:
→ Would a senior dev approve this PR?
→ How many review rounds?
→ Did it introduce vulnerabilities?
→ What did it actually cost?

**Tweet 3 (solution):**
QualBench scores AI tools on 6 dimensions:

• Correctness (25%)
• Security (15%)
• Code quality (15%)
• Mergeability — blind human review (25%)
• Iterations to converge (10%)
• Cost per mergeable PR (10%)

"Does it work?" → "Would you ship it?"

**Tweet 4 (insight):**
The killer metric nobody tracks:

Cost per MERGEABLE PR.

Not cost per attempt.
Not cost per "tests pass."
Cost per PR a senior dev would approve without changes.

We expect this varies 10-100x across tools.

**Tweet 5 (iteration):**
Most AI tools are single-shot:
generate → return → pray

QualBench rewards tools that iterate:
generate → evaluate → fix → repeat until quality gates pass

Just like real engineering.

**Tweet 6 (CTA):**
QualBench v0: 10 issues, 3 tools, open source.

Results coming next week.

Add your tool: copy the runner template, implement run(), submit a PR.

github.com/semcod/qualbench


---

## 3. LinkedIn post

**AI coding tools pass tests. But would you merge the PR?**

We've been researching AI coding agents for the past 6 months. The benchmarks show impressive numbers — 70-80% resolution rates on SWE-bench.

But when we talked to engineering leads, we heard the same thing over and over:

"The AI generates code that works. But I still need to rewrite half of it before I'd merge it."

The gap isn't correctness. It's production readiness.

So we built QualBench — an open-source benchmark that measures whether AI-generated code is actually mergeable, not just functional.

We score on 6 dimensions: correctness, security, code quality, mergeability (blind human review), iteration efficiency, and cost per usable result.

The metric that matters most: "Would a senior developer approve this PR without changes?"

Nobody has been measuring this. We think it changes how the industry evaluates AI coding tools.

v0 is live on GitHub with 10 issues from Flask, Django, FastAPI, and 4 other well-tested repositories. Apache 2.0 licensed. Anyone can add their tool.

First results coming next week.

Link in comments.


---

## 4. Dev.to / Blog post outline

**Title:** "We benchmarked AI coding tools on code quality, not just correctness. Here's what the industry is missing."

**Structure:**

1. **Hook:** "70% resolution rate sounds great — until you review the PRs."

2. **The correctness trap:** SWE-bench is excellent for what it measures. But it creates a blind spot. A patch that passes all tests can still have CC 25, no tests added, 3 new bandit findings, and require 4 rounds of code review. SWE-bench gives that patch 100%.

3. **What we built:** QualBench, 6 dimensions, methodology overview. Link to docs/methodology.md.

4. **The 10 issues:** Why we chose these specific bugs/refactors/security issues. What each category tests.

5. **Expected findings** (publish before results):
   - Correctness ≠ mergeability
   - Iteration beats single-shot
   - Security regressions are common
   - Cost per usable PR varies dramatically

6. **Results** (publish after benchmark):
   - Tables with all 6 dimensions per tool
   - Cost per mergeable PR ranking
   - Specific examples: "Here's what Tool A generated vs Tool B for QB-007 (refactoring task)"
   - Diff screenshots

7. **What this means for teams:**
   - Don't evaluate AI tools on SWE-bench scores alone
   - Track cost per mergeable PR, not cost per request
   - Quality gates change the equation

8. **CTA:** Add your tool to QualBench. Methodology is open. Results are open.


---

## 5. Reddit r/programming post

**Title:** "We built an open-source benchmark that measures if you'd actually merge AI-generated PRs (not just if tests pass)"

**Body:** Same as HN but shorter, link to repo. Key callout: "We're running Copilot, OpenHands, and our own tool. Results next week. Add yours."


---

## Distribution timeline

| Day | Channel | Content |
|-----|---------|---------|
| D-Day | GitHub | Push repo, README visible |
| D-Day | HN | Show HN post (morning US Pacific) |
| D-Day | Twitter | Thread (timed 1hr after HN) |
| D-Day | LinkedIn | Post (afternoon EU) |
| D+1 | Reddit | r/programming, r/MachineLearning |
| D+3 | Dev.to | Full blog post (before results) |
| D+7 | All channels | Results announcement + updated leaderboard |
| D+8 | Dev.to | Deep-dive blog with result analysis |
| D+14 | Twitter | "Cost per mergeable PR" analysis thread |

Tag in all channels: @GitHubCopilot, @OpenHands, @AnthropicAI (tastefully, with results not demands).
