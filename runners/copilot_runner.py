"""QualBench runner for GitHub Copilot Coding Agent.

NOTE: Copilot Coding Agent runs asynchronously via GitHub Issues.
This runner creates issues and polls for PRs. Requires:
- GitHub Copilot Pro/Pro+ subscription
- Repository with Copilot agent enabled
"""

import os
import time

from qualbench.dataset import Issue
from qualbench.runners import BaseRunner, RunResult


# Constants
DEFAULT_TIMEOUT = 900


class Runner(BaseRunner):
    name = "copilot"

    def setup(self) -> None:
        if not os.environ.get("GITHUB_TOKEN"):
            raise RuntimeError("Set GITHUB_TOKEN for Copilot Coding Agent")

    def run(self, issue: Issue, repo_path: str, timeout: int = DEFAULT_TIMEOUT) -> RunResult:
        """
        Copilot workflow:
        1. Create GitHub Issue in benchmark fork
        2. Assign to Copilot
        3. Poll for PR creation
        4. Extract patch from PR
        """
        start = time.time()

        # TODO: Implement GitHub API integration
        # - Create issue via API
        # - Assign to Copilot
        # - Wait for PR
        # - Download diff

        return RunResult(
            issue_id=issue.id,
            error="Copilot runner requires manual setup. See docs/runners/copilot.md",
            time_seconds=time.time() - start,
        )
