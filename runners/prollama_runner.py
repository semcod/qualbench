"""QualBench runner for prollama + pyqual (quality-gated iteration)."""

import os
import subprocess
import time

from qualbench.dataset import Issue
from qualbench.runners import BaseRunner, RunResult


class Runner(BaseRunner):
    name = "prollama"

    def setup(self):
        # Verify prollama is installed
        result = subprocess.run(["prollama", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("prollama not found. Install: pip install prollama")

    def run(self, issue: Issue, repo_path: str, timeout: int = 900) -> RunResult:
        start = time.time()

        # Run prollama solve with pyqual quality gates
        result = subprocess.run(
            [
                "prollama", "solve",
                "--mode", "quality",
                "--description", issue.problem_statement,
                "--repo", repo_path,
                "--timeout", str(timeout),
                "--output-format", "json",
            ],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PROLLAMA_STRATEGY": "cost-optimized"},
        )

        elapsed = time.time() - start

        if result.returncode != 0:
            return RunResult(
                issue_id=issue.id,
                error=result.stderr[:500],
                time_seconds=elapsed,
            )

        # Get the diff
        patch = self.get_diff(repo_path)

        # Parse prollama output for cost/iterations
        import json
        try:
            output = json.loads(result.stdout)
            cost = output.get("total_cost", 0.0)
            iterations = output.get("iterations", 1)
            model = output.get("model_used", "unknown")
        except (json.JSONDecodeError, TypeError):
            cost, iterations, model = 0.0, 1, "unknown"

        return RunResult(
            issue_id=issue.id,
            patch=patch,
            resolved=bool(patch),
            cost_usd=cost,
            time_seconds=elapsed,
            model_used=model,
            iterations=iterations,
        )
