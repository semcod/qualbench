"""
QualBench Automated Evaluation
===============================

Evaluates patches from all tools on:
1. Correctness — do tests pass?
2. Security — bandit findings delta
3. Quality — cyclomatic complexity delta, dead code

Usage:
    python scripts/evaluate.py --results-dir results/ --dataset dataset/qualbench-v0.json
"""

import argparse
import json
import os
import subprocess
from pathlib import Path


# Constants
DEFAULT_CMD_TIMEOUT = 120
TEST_TIMEOUT = 300
OUTPUT_SNIPPET_LENGTH = 500
BASELINE_CC_DEFAULT = 5.0
SCORE_100 = 100
SCORE_90 = 90
SCORE_70 = 70
SCORE_40 = 40
SCORE_30 = 30
SCORE_0 = 0
CC_PENALTY_PER_POINT = 15
DEAD_CODE_PENALTY = 10
HIGH_SEVERITY_THRESHOLD = 2

REPO_PATH_PREFIX = "repos"


def run_cmd(cmd: list[str], cwd: str = None, timeout: int = DEFAULT_CMD_TIMEOUT) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def evaluate_correctness(patch_path: str, repo_path: str, issue: dict) -> dict:
    """Check if patch makes tests pass without regressions."""
    # Reset repo
    run_cmd(["git", "checkout", "."], cwd=repo_path)
    run_cmd(["git", "clean", "-fd"], cwd=repo_path)

    # Apply patch
    rc, stdout, stderr = run_cmd(["git", "apply", patch_path], cwd=repo_path)
    if rc != 0:
        return {"score": 0, "patch_applies": False, "tests_pass": False, "error": stderr}

    # Run tests
    rc, stdout, stderr = run_cmd(
        ["python", "-m", "pytest", "--tb=short", "-q"],
        cwd=repo_path,
        timeout=TEST_TIMEOUT,
    )

    tests_pass = rc == 0
    return {
        "score": 100 if tests_pass else 0,
        "patch_applies": True,
        "tests_pass": tests_pass,
        "test_output": stdout[-OUTPUT_SNIPPET_LENGTH:] if stdout else "",
        "error": stderr[-OUTPUT_SNIPPET_LENGTH:] if not tests_pass else None,
    }


def evaluate_security(repo_path: str, baseline_bandit: dict) -> dict:
    """Run bandit and compare with baseline."""
    rc, stdout, stderr = run_cmd(
        ["python", "-m", "bandit", "-r", ".", "-f", "json", "-q"],
        cwd=repo_path,
    )

    try:
        findings = json.loads(stdout) if stdout else {"results": []}
    except json.JSONDecodeError:
        findings = {"results": []}

    current_count = len(findings.get("results", []))
    baseline_count = baseline_bandit.get("count", 0)
    new_issues = max(0, current_count - baseline_count)

    # Score: 0 new = 100%, 1 low = 90%, 1 med = 70%, 1 high = 40%, 2+ high = 0%
    if new_issues == 0:
        score = SCORE_100
    elif new_issues == 1:
        severities = [r["issue_severity"] for r in findings["results"]]
        new_severities = severities[baseline_count:]
        if "HIGH" in new_severities:
            score = SCORE_40
        elif "MEDIUM" in new_severities:
            score = SCORE_70
        else:
            score = SCORE_90
    else:
        high_count = sum(
            1 for r in findings["results"][baseline_count:]
            if r.get("issue_severity") == "HIGH"
        )
        score = SCORE_0 if high_count >= HIGH_SEVERITY_THRESHOLD else SCORE_30

    return {
        "score": score,
        "baseline_issues": baseline_count,
        "current_issues": current_count,
        "new_issues": new_issues,
    }


def evaluate_quality(repo_path: str, baseline_cc: float, patch_lines: int) -> dict:
    """Measure cyclomatic complexity delta and code efficiency."""
    # Measure CC with radon
    rc, stdout, stderr = run_cmd(
        ["python", "-m", "radon", "cc", ".", "-a", "-s", "-j"],
        cwd=repo_path,
    )

    try:
        radon_data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        radon_data = {}

    # Calculate average CC
    all_cc = []
    for filepath, functions in radon_data.items():
        if isinstance(functions, list):
            for func in functions:
                if isinstance(func, dict) and "complexity" in func:
                    all_cc.append(func["complexity"])

    current_cc = sum(all_cc) / len(all_cc) if all_cc else 0

    # CC score: lower or equal = 100%, each point increase = -15%
    cc_delta = current_cc - baseline_cc
    if cc_delta <= 0:
        cc_score = SCORE_100
    else:
        cc_score = max(SCORE_0, SCORE_100 - int(cc_delta * CC_PENALTY_PER_POINT))

    # Check for dead code with ruff
    rc_ruff, stdout_ruff, _ = run_cmd(
        ["python", "-m", "ruff", "check", ".", "--select", "F841,F811"],
        cwd=repo_path,
    )
    dead_code_issues = stdout_ruff.count("\n") if stdout_ruff else 0

    quality_score = max(SCORE_0, cc_score - dead_code_issues * DEAD_CODE_PENALTY)

    return {
        "score": quality_score,
        "baseline_cc": round(baseline_cc, 2),
        "current_cc": round(current_cc, 2),
        "cc_delta": round(cc_delta, 2),
        "dead_code_issues": dead_code_issues,
        "patch_lines": patch_lines,
    }


def evaluate_tool(tool_dir: str, dataset: dict) -> list[dict]:
    """Evaluate all patches from a single tool."""
    results = []

    for issue in dataset["issues"]:
        issue_id = issue["id"]
        result_file = os.path.join(tool_dir, f"{issue_id}.json")

        if not os.path.exists(result_file):
            results.append({
                "issue_id": issue_id,
                "skipped": True,
                "correctness": {"score": 0},
                "security": {"score": 0},
                "quality": {"score": 0},
            })
            continue

        with open(result_file) as f:
            tool_result = json.load(f)

        if not tool_result.get("patch"):
            results.append({
                "issue_id": issue_id,
                "no_patch": True,
                "correctness": {"score": 0},
                "security": {"score": 0},
                "quality": {"score": 0},
            })
            continue

        repo_path = os.path.join(REPO_PATH_PREFIX, issue["repo"].replace("/", "__"))

        # Save patch to temp file
        patch_path = os.path.join(tool_dir, f"{issue_id}.patch")
        with open(patch_path, "w") as f:
            f.write(tool_result["patch"])

        # Evaluate dimensions
        correctness = evaluate_correctness(patch_path, repo_path, issue)
        security = evaluate_security(repo_path, issue.get("baseline_bandit", {}))
        quality = evaluate_quality(
            repo_path,
            issue.get("baseline_cc", BASELINE_CC_DEFAULT),
            len(tool_result["patch"].split("\n")),
        )

        results.append({
            "issue_id": issue_id,
            "correctness": correctness,
            "security": security,
            "quality": quality,
            "cost_usd": tool_result.get("cost_usd", 0),
            "time_seconds": tool_result.get("time_seconds", 0),
            "iterations": tool_result.get("iterations", 0),
        })

    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", default="results/evaluation.json")
    args = parser.parse_args()

    with open(args.dataset) as f:
        dataset = json.load(f)

    evaluation = {}
    tools_dir = Path(args.results_dir)

    for tool_dir in sorted(tools_dir.iterdir()):
        if tool_dir.is_dir() and not tool_dir.name.startswith("."):
            tool_name = tool_dir.name
            print(f"\nEvaluating: {tool_name}")
            evaluation[tool_name] = evaluate_tool(str(tool_dir), dataset)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(evaluation, f, indent=2)

    print(f"\nEvaluation saved to {args.output}")


if __name__ == "__main__":
    main()
