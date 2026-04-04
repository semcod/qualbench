"""QualBench runner for OpenHands (formerly OpenDevin)."""

import os
import subprocess
import time

from qualbench.dataset import Issue
from qualbench.runners import BaseRunner, RunResult


class Runner(BaseRunner):
    name = "openhands"

    def setup(self):
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("Set ANTHROPIC_API_KEY or OPENAI_API_KEY for OpenHands")

    def run(self, issue: Issue, repo_path: str, timeout: int = 900) -> RunResult:
        start = time.time()

        # OpenHands runs in Docker
        # Adapt this to your OpenHands installation
        result = subprocess.run(
            [
                "python", "-m", "openhands.core.main",
                "-t", issue.problem_statement,
                "-d", repo_path,
            ],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ},
        )

        elapsed = time.time() - start
        patch = self.get_diff(repo_path)

        return RunResult(
            issue_id=issue.id,
            patch=patch,
            resolved=bool(patch),
            cost_usd=0.0,  # Parse from OpenHands logs
            time_seconds=elapsed,
            model_used=os.environ.get("OPENHANDS_MODEL", "claude-sonnet-4-20250514"),
            iterations=1,
        )
