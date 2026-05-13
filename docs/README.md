<!-- code2docs:start --># qualbench

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-94-green)
> **94** functions | **21** classes | **24** files | CC̄ = 4.0

> Auto-generated project documentation from source code analysis.

**Author:** Softreck  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/qualbench](https://github.com/semcod/qualbench)

## Installation

Install QualBench from PyPI or from source.

### From PyPI

```bash
pip install qualbench
```

### From Source

```bash
git clone https://github.com/semcod/qualbench
cd qualbench
pip install -e .
```

### Optional Extras

```bash
pip install qualbench[test]    # testing tools
pip install qualbench[all]    # all optional features
```

## Quick Start

Get started with QualBench in under 60 seconds.

### CLI Usage

Use the `qualbench` command to generate documentation, check health, and sync changes.

```bash
# Generate full documentation for your project
qualbench ./my-project

# Only regenerate README
qualbench ./my-project --readme-only

# Preview what would be generated (no file writes)
qualbench ./my-project --dry-run

# Check documentation health
qualbench check ./my-project

# Sync — regenerate only changed modules
qualbench sync ./my-project
```

### Python API

```python
from qualbench import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `qualbench`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `qualbench.yaml` in your project root (or run `qualbench init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

qualbench can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- qualbench:start -->
# Project Title
... auto-generated content ...
<!-- qualbench:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
qualbench/
├── project├── qualbench/    ├── cli├── server    ├── supervisor        ├── repos    ├── utils/    ├── dataset    ├── runners/├── scripts/    ├── evaluation/    ├── evaluate    ├── generate_dataset_v1    ├── entrypoint    ├── score    ├── cline_runner    ├── template    ├── copilot_runner├── runners/    ├── prollama_runner    ├── aider_runner    ├── openhands_runner    ├── benchmark/    ├── api```

## API Overview

Key classes and functions exposed by the `qualbench` package.

### Classes

- **`Handler`** — —
- **`RoutingDecision`** — Decision made by supervisor for an issue.
- **`ParallelResult`** — Result from parallel execution.
- **`SupervisorAI`** — Intelligent supervisor for AI code generation.
- **`QualityGates`** — Quality gates for v0 and v1 datasets.
- **`Issue`** — —
- **`Dataset`** — —
- **`RunResult`** — —
- **`BaseRunner`** — Base class for QualBench tool runners.
- **`CorrectnessResult`** — —
- **`SecurityResult`** — —
- **`QualityResult`** — —
- **`EvaluationResult`** — —
- **`Runner`** — —
- **`Runner`** — —
- **`Runner`** — —
- **`QualBenchResult`** — Portable result schema — used in CLI, API, GitHub Action, leaderboard.
- **`QualBenchRunner`** — Run QualBench on current repository diff.
- **`ResultSubmission`** — Result in portable schema format.
- **`LeaderboardEntry`** — —
- **`LeaderboardResponse`** — —

### Functions

- `cli()` — QualBench — CI for AI-generated code.
- `run(tool, mode, issue, use_json)` — Score the current diff against quality gates.
- `quickstart(tool)` — Run one issue, show your first score in 60 seconds.
- `compare(tool, issue)` — Compare your tool against the leaderboard.
- `info(dataset)` — Show dataset summary.
- `doctor()` — Check if required tools are available.
- `submit(tool, mode, issue, api_url)` — Submit benchmark result to leaderboard.
- `leaderboard(api_url, issue, tool)` — View current leaderboard rankings.
- `main()` — —
- `main()` — CLI for supervisor AI.
- `clone_repo(repo, target, commit)` — Clone a repository and optionally checkout a specific commit.
- `collect_baseline(repo_path)` — Collect baseline metrics (CC, bandit count) for a repository.
- `setup_repos(dataset, output_dir)` — Clone all repos needed for the dataset.
- `evaluate_correctness(patch, repo_path)` — Apply patch and run tests.
- `evaluate_security(repo_path, baseline_count)` — Run bandit and compute delta.
- `evaluate_quality(repo_path, baseline_cc, patch_lines)` — Measure CC delta and dead code.
- `evaluate_patch(issue_id, patch, repo_path, baseline_cc)` — Full evaluation of a single patch.
- `run_cmd(cmd, cwd, timeout)` — Run a command and return (returncode, stdout, stderr).
- `evaluate_correctness(patch_path, repo_path, issue)` — Check if patch makes tests pass without regressions.
- `evaluate_security(repo_path, baseline_bandit)` — Run bandit and compare with baseline.
- `evaluate_quality(repo_path, baseline_cc, patch_lines)` — Measure cyclomatic complexity delta and code efficiency.
- `evaluate_tool(tool_dir, dataset)` — Evaluate all patches from a single tool.
- `main()` — —
- `generate_dataset_v1()` — Generate the full dataset v1 JSON file.
- `score_iterations(iterations, resolved)` — Score iteration efficiency. Lower = better for resolved tasks.
- `score_cost(cost_usd, resolved)` — Score cost efficiency. Cheaper = better for resolved tasks.
- `compute_mergeability(scores)` — —
- `load_human_reviews(reviews_dir)` — —
- `score_tool(tool_name, evaluations, human_reviews)` — —
- `generate_leaderboard(scores)` — —
- `main()` — —
- `run_cline(repo_path, problem_statement, timeout)` — Run Cline-style prompting on a repository.
- `main()` — —
- `run(issue, repo_path, timeout)` — Run your AI coding tool on a single issue.
- `main()` — —
- `run_aider(repo_path, problem_statement, timeout)` — Run Aider on a repository with the given problem statement.
- `main()` — —
- `submit_result(submission, authorization)` — Submit a benchmark result. Requires tool-owner token.
- `get_leaderboard(issue, tool)` — Get current leaderboard rankings.
- `get_result(tool, issue_id)` — Get specific result by tool and issue.
- `health_check()` — —


## Project Structure

📄 `action.entrypoint`
📄 `project`
📦 `qualbench`
📄 `qualbench.api` (6 functions, 3 classes)
📦 `qualbench.benchmark` (16 functions, 2 classes)
📄 `qualbench.cli` (10 functions)
📄 `qualbench.dataset` (6 functions, 3 classes)
📦 `qualbench.evaluation` (6 functions, 4 classes)
📦 `qualbench.runners` (7 functions, 2 classes)
📄 `qualbench.supervisor` (11 functions, 3 classes)
📦 `qualbench.utils`
📄 `qualbench.utils.repos` (3 functions)
📦 `runners`
📄 `runners.aider_runner` (3 functions)
📄 `runners.cline_runner` (2 functions)
📄 `runners.copilot_runner` (2 functions, 1 classes)
📄 `runners.openhands_runner` (2 functions, 1 classes)
📄 `runners.prollama_runner` (2 functions, 1 classes)
📄 `runners.template` (2 functions)
📦 `scripts`
📄 `scripts.evaluate` (6 functions)
📄 `scripts.generate_dataset_v1` (1 functions)
📄 `scripts.score` (7 functions)
📄 `server` (2 functions, 1 classes)

## Requirements

- Python >= >=3.10
- click >=8.1- radon >=6.0- bandit >=1.7- ruff >=0.4- GitPython >=3.1- fastapi >=0.100- requests >=2.31- uvicorn >=0.23- pydantic >=2.0

## Contributing

**Contributors:**
- Tom Sapletta

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

Set up a local development environment for contributing.

```bash
# Clone the repository
git clone https://github.com/semcod/qualbench
cd qualbench

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

Run the full test suite to verify your setup is working.

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/qualbench/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/qualbench/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/qualbench/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/qualbench/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](https://github.com/wronai/qualbench/tree/main/examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](https://github.com/wronai/qualbench/blob/main/docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](https://github.com/wronai/qualbench/blob/main/docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](https://github.com/wronai/qualbench/blob/main/docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](https://github.com/wronai/qualbench/blob/main/docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](https://github.com/wronai/qualbench/blob/main/docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](https://github.com/wronai/qualbench/blob/main/docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](https://github.com/wronai/qualbench/blob/main/docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](https://github.com/wronai/qualbench/tree/main/examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->