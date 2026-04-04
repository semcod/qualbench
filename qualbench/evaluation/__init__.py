"""Automated evaluation: correctness, security, quality."""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CorrectnessResult:
    score: float
    patch_applies: bool
    tests_pass: bool
    error: Optional[str] = None


@dataclass
class SecurityResult:
    score: float
    baseline_issues: int
    current_issues: int
    new_issues: int


@dataclass
class QualityResult:
    score: float
    baseline_cc: float
    current_cc: float
    cc_delta: float
    dead_code_issues: int
    patch_lines: int


@dataclass
class EvaluationResult:
    issue_id: str
    correctness: CorrectnessResult
    security: SecurityResult
    quality: QualityResult
    cost_usd: float = 0.0
    time_seconds: float = 0.0
    iterations: int = 0

    def to_dict(self) -> dict:
        return {
            "issue_id": self.issue_id,
            "correctness": {
                "score": self.correctness.score,
                "patch_applies": self.correctness.patch_applies,
                "tests_pass": self.correctness.tests_pass,
                "error": self.correctness.error,
            },
            "security": {
                "score": self.security.score,
                "baseline_issues": self.security.baseline_issues,
                "current_issues": self.security.current_issues,
                "new_issues": self.security.new_issues,
            },
            "quality": {
                "score": self.quality.score,
                "baseline_cc": self.quality.baseline_cc,
                "current_cc": self.quality.current_cc,
                "cc_delta": self.quality.cc_delta,
                "dead_code_issues": self.quality.dead_code_issues,
                "patch_lines": self.quality.patch_lines,
            },
            "cost_usd": self.cost_usd,
            "time_seconds": self.time_seconds,
            "iterations": self.iterations,
        }


def _run(cmd: list[str], cwd: str = None, timeout: int = 120) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def evaluate_correctness(patch: str, repo_path: str) -> CorrectnessResult:
    """Apply patch and run tests."""
    _run(["git", "checkout", "."], cwd=repo_path)
    _run(["git", "clean", "-fd"], cwd=repo_path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
        f.write(patch)
        patch_file = f.name

    rc, _, stderr = _run(["git", "apply", patch_file], cwd=repo_path)
    if rc != 0:
        return CorrectnessResult(score=0, patch_applies=False, tests_pass=False, error=stderr[:500])

    rc, stdout, stderr = _run(["python", "-m", "pytest", "--tb=short", "-q"], cwd=repo_path, timeout=300)
    return CorrectnessResult(
        score=100 if rc == 0 else 0,
        patch_applies=True,
        tests_pass=rc == 0,
        error=stderr[:500] if rc != 0 else None,
    )


def evaluate_security(repo_path: str, baseline_count: int = 0) -> SecurityResult:
    """Run bandit and compute delta."""
    rc, stdout, _ = _run(["python", "-m", "bandit", "-r", ".", "-f", "json", "-q"], cwd=repo_path)
    try:
        findings = json.loads(stdout) if stdout else {"results": []}
    except json.JSONDecodeError:
        findings = {"results": []}

    current = len(findings.get("results", []))
    new = max(0, current - baseline_count)

    if new == 0:
        score = 100
    elif new == 1:
        sevs = [r.get("issue_severity", "LOW") for r in findings["results"][baseline_count:]]
        score = 40 if "HIGH" in sevs else (70 if "MEDIUM" in sevs else 90)
    else:
        highs = sum(1 for r in findings["results"][baseline_count:] if r.get("issue_severity") == "HIGH")
        score = 0 if highs >= 2 else 30

    return SecurityResult(score=score, baseline_issues=baseline_count, current_issues=current, new_issues=new)


def evaluate_quality(repo_path: str, baseline_cc: float = 5.0, patch_lines: int = 0) -> QualityResult:
    """Measure CC delta and dead code."""
    _, stdout, _ = _run(["python", "-m", "radon", "cc", ".", "-a", "-s", "-j"], cwd=repo_path)
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {}

    all_cc = []
    for funcs in data.values():
        if isinstance(funcs, list):
            all_cc.extend(f["complexity"] for f in funcs if isinstance(f, dict) and "complexity" in f)

    current_cc = sum(all_cc) / len(all_cc) if all_cc else 0
    cc_delta = current_cc - baseline_cc
    cc_score = max(0, 100 - int(max(0, cc_delta) * 15))

    _, ruff_out, _ = _run(["python", "-m", "ruff", "check", ".", "--select", "F841,F811"], cwd=repo_path)
    dead_code = ruff_out.strip().count("\n") + (1 if ruff_out.strip() else 0) if ruff_out else 0

    score = max(0, cc_score - dead_code * 10)
    return QualityResult(
        score=score,
        baseline_cc=round(baseline_cc, 2),
        current_cc=round(current_cc, 2),
        cc_delta=round(cc_delta, 2),
        dead_code_issues=dead_code,
        patch_lines=patch_lines,
    )


def evaluate_patch(issue_id: str, patch: str, repo_path: str,
                   baseline_cc: float = 5.0, baseline_bandit: int = 0,
                   cost_usd: float = 0, time_seconds: float = 0,
                   iterations: int = 1) -> EvaluationResult:
    """Full evaluation of a single patch."""
    correctness = evaluate_correctness(patch, repo_path)
    security = evaluate_security(repo_path, baseline_bandit)
    patch_lines = len(patch.split("\n"))
    quality = evaluate_quality(repo_path, baseline_cc, patch_lines)

    return EvaluationResult(
        issue_id=issue_id,
        correctness=correctness,
        security=security,
        quality=quality,
        cost_usd=cost_usd,
        time_seconds=time_seconds,
        iterations=iterations,
    )
