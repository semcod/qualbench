"""
QualBench Runner — the execution core.

Runs locally on the current repo, measures the current git diff
against quality gates, produces the portable QualBench result schema.
"""

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Optional

# Constants
DEFAULT_TIMEOUT = 120
TEST_TIMEOUT = 300
VERDICT_READY_THRESHOLD = 85
VERDICT_REVIEW_THRESHOLD = 65


@dataclass
class QualBenchResult:
    """Portable result schema — used in CLI, API, GitHub Action, leaderboard."""

    tool: str
    issue_id: str
    quality_score: float
    dimensions: dict[str, float]
    verdict: str
    top_issues: list[str]
    patch: str = ""
    resolved: bool = False
    cost_usd: float = 0.0
    time_seconds: float = 0.0
    iterations: int = 1
    model_used: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["quality_score"] = round(d["quality_score"], 1)
        d["dimensions"] = {k: round(v, 1) for k, v in d["dimensions"].items()}
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "QualBenchResult":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


WEIGHTS = {
    "correctness": 0.25,
    "security": 0.15,
    "quality": 0.15,
    "mergeability": 0.25,
    "iterations": 0.10,
    "cost": 0.10,
}


def _run(cmd: list[str], cwd: str = None, timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


class QualBenchRunner:
    """Run QualBench on current repository diff."""

    def __init__(self, tool: str = "prollama", mode: str = "quality", cwd: str = "."):
        self.tool = tool
        self.mode = mode
        self.cwd = cwd

    def run(self, issue_id: str = "LOCAL") -> QualBenchResult:
        start = time.time()

        patch = self._get_git_diff()
        correctness = self._run_tests()
        security = self._run_bandit()
        quality = self._run_quality()
        mergeability = self._estimate_mergeability(correctness, quality)
        iterations = 1
        cost_usd = self._estimate_cost()

        dimensions = {
            "correctness": correctness,
            "security": security,
            "quality": quality,
            "mergeability": mergeability,
            "iterations": _score_iterations(iterations, correctness == 100),
            "cost": _score_cost(cost_usd, correctness == 100),
        }

        quality_score = sum(dimensions[k] * WEIGHTS[k] for k in WEIGHTS)
        verdict = _compute_verdict(quality_score)
        top_issues = self._extract_issues(correctness, security, quality)

        return QualBenchResult(
            tool=self.tool,
            issue_id=issue_id,
            quality_score=quality_score,
            dimensions=dimensions,
            verdict=verdict,
            top_issues=top_issues,
            patch=patch[:5000],
            resolved=correctness == 100,
            cost_usd=cost_usd,
            time_seconds=round(time.time() - start, 2),
            iterations=iterations,
            model_used=self.mode,
        )

    def _get_git_diff(self) -> str:
        rc, stdout, _ = _run(["git", "diff"], cwd=self.cwd)
        if rc != 0:
            rc, stdout, _ = _run(["git", "diff", "HEAD"], cwd=self.cwd)
        return stdout

    def _run_tests(self) -> float:
        rc, stdout, stderr = _run(
            ["python", "-m", "pytest", "-q", "--tb=no"], cwd=self.cwd, timeout=TEST_TIMEOUT
        )
        return 100.0 if rc == 0 else 0.0

    def _run_bandit(self) -> float:
        rc, stdout, _ = _run(
            ["python", "-m", "bandit", "-r", ".", "-f", "json", "-q", "--exit-zero"],
            cwd=self.cwd,
        )
        try:
            data = json.loads(stdout) if stdout else {"results": []}
            issues = data.get("results", [])
            count = len(issues)
        except (json.JSONDecodeError, TypeError):
            return 50.0

        if count == 0:
            return 100.0
        highs = sum(1 for i in issues if i.get("issue_severity") == "HIGH")
        meds = sum(1 for i in issues if i.get("issue_severity") == "MEDIUM")
        if highs >= 2:
            return 0.0
        if highs == 1:
            return 40.0
        if meds >= 2:
            return 50.0
        if count <= 2:
            return 80.0
        return max(20.0, 100.0 - count * 10)

    def _run_quality(self) -> float:
        rc, stdout, _ = _run(
            ["python", "-m", "radon", "cc", ".", "-a", "-s", "-j"], cwd=self.cwd
        )
        try:
            data = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            data = {}

        complexities = []
        for funcs in data.values():
            if isinstance(funcs, list):
                complexities.extend(
                    f["complexity"] for f in funcs if isinstance(f, dict) and "complexity" in f
                )

        if not complexities:
            return 80.0

        avg = sum(complexities) / len(complexities)
        if avg <= 5:
            return 100.0
        if avg <= 10:
            return 80.0
        if avg <= 15:
            return 60.0
        return max(20.0, 100.0 - avg * 3)

    def _estimate_mergeability(self, correctness: float, quality: float) -> float:
        """Heuristic proxy until human review data accumulates."""
        if correctness < 100:
            return 20.0
        if quality >= 80:
            return 90.0
        if quality >= 60:
            return 70.0
        return 50.0

    def _estimate_cost(self) -> float:
        cost_map = {"cheap": 0.05, "quality": 0.30, "secure": 0.50}
        return cost_map.get(self.mode, 0.25)

    def _extract_issues(self, correctness: float, security: float, quality: float) -> list[str]:
        issues = []
        if correctness < 100:
            issues.append("tests_failed")
        if security < 80:
            issues.append("security_issues")
        if quality < 70:
            issues.append("high_complexity")
        return issues


def _score_iterations(iterations: int, resolved: bool) -> float:
    if not resolved:
        return 0.0
    return {1: 100, 2: 85, 3: 70}.get(iterations, 50.0 if iterations <= 5 else max(0, 100 - iterations * 12))


def _score_cost(cost: float, resolved: bool) -> float:
    if not resolved:
        return 0.0
    for threshold, score in [(0.05, 100), (0.20, 90), (0.50, 75), (1.0, 60), (2.0, 40), (5.0, 20)]:
        if cost <= threshold:
            return score
    return 5.0


def _compute_verdict(score: float) -> str:
    if score >= VERDICT_READY_THRESHOLD:
        return "ready_to_merge"
    if score >= VERDICT_REVIEW_THRESHOLD:
        return "needs_review"
    return "not_merge_ready"
