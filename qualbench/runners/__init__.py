"""Base runner interface for QualBench tools."""

import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from qualbench.dataset import Issue


# Constants
DEFAULT_TIMEOUT = 900


@dataclass
class RunResult:
    issue_id: str
    patch: str = ""
    resolved: bool = False
    cost_usd: float = 0.0
    time_seconds: float = 0.0
    model_used: str = "unknown"
    iterations: int = 0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "issue_id": self.issue_id,
            "patch": self.patch,
            "resolved": self.resolved,
            "cost_usd": self.cost_usd,
            "time_seconds": self.time_seconds,
            "model_used": self.model_used,
            "iterations": self.iterations,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseRunner(ABC):
    """Base class for QualBench tool runners."""

    name: str = "unnamed"

    @abstractmethod
    def run(self, issue: Issue, repo_path: str, timeout: int = DEFAULT_TIMEOUT) -> RunResult:
        """Run the tool on a single issue and return results."""
        ...

    def setup(self) -> None:
        """Optional setup before running (install deps, check API keys, etc.)."""
        pass

    def teardown(self) -> None:
        """Optional cleanup after all runs."""
        pass

    def reset_repo(self, repo_path: str) -> None:
        """Reset repository to clean state."""
        subprocess.run(["git", "checkout", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "clean", "-fd"], cwd=repo_path, capture_output=True)

    def get_diff(self, repo_path: str) -> str:
        """Get git diff of current changes."""
        result = subprocess.run(
            ["git", "diff"], cwd=repo_path, capture_output=True, text=True
        )
        return result.stdout

    def run_timed(self, issue: Issue, repo_path: str, timeout: int = DEFAULT_TIMEOUT) -> RunResult:
        """Run with timing wrapper."""
        self.reset_repo(repo_path)
        start = time.time()
        try:
            result = self.run(issue, repo_path, timeout)
        except Exception as e:
            result = RunResult(
                issue_id=issue.id,
                error=str(e),
                time_seconds=time.time() - start,
            )
        result.time_seconds = round(time.time() - start, 2)
        return result
