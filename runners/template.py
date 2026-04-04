"""
QualBench Runner Template
=========================

Copy this file and implement the `run()` function to benchmark your AI coding tool.

Usage:
    python runners/my_tool.py --dataset dataset/qualbench-v0.json --output results/my_tool/
"""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path


def run(issue: dict, repo_path: str, timeout: int = 900) -> dict:
    """
    Run your AI coding tool on a single issue.

    Args:
        issue: Dataset entry with fields:
            - id: str (e.g., "QB-001")
            - repo: str (e.g., "pallets/flask")
            - problem_statement: str (the issue description)
            - title: str (short issue title)
            - difficulty: str (simple/medium/hard/security)
        repo_path: Absolute path to cloned repo at base_commit
        timeout: Maximum seconds for the tool to produce a patch

    Returns:
        dict with:
            - patch: str — git diff of the changes (empty string if failed)
            - resolved: bool — whether the tool believes it solved the issue
            - cost_usd: float — estimated cost in USD
            - time_seconds: float — wall clock time
            - model_used: str — primary model name
            - iterations: int — number of fix attempts
            - error: str | None — error message if failed
    """
    start = time.time()

    # =========================================================
    # YOUR IMPLEMENTATION HERE
    #
    # Example pseudocode:
    #
    # 1. Initialize your tool
    # tool = MyAITool(api_key=os.environ["MY_API_KEY"])
    #
    # 2. Pass the issue to the tool
    # result = tool.solve(
    #     issue_text=issue["problem_statement"],
    #     repo_path=repo_path,
    #     timeout=timeout,
    # )
    #
    # 3. Capture the git diff
    # patch = subprocess.run(
    #     ["git", "diff"], cwd=repo_path, capture_output=True, text=True
    # ).stdout
    #
    # 4. Return structured result
    # =========================================================

    elapsed = time.time() - start

    return {
        "patch": "",
        "resolved": False,
        "cost_usd": 0.0,
        "time_seconds": elapsed,
        "model_used": "unknown",
        "iterations": 0,
        "error": "Not implemented — replace this with your tool's logic",
    }


def main():
    parser = argparse.ArgumentParser(description="Run QualBench with your tool")
    parser.add_argument("--dataset", required=True, help="Path to qualbench-v0.json")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--timeout", type=int, default=900, help="Timeout per issue (seconds)")
    parser.add_argument("--issues", nargs="*", help="Specific issue IDs to run (e.g., QB-001 QB-005)")
    args = parser.parse_args()

    with open(args.dataset) as f:
        dataset = json.load(f)

    os.makedirs(args.output, exist_ok=True)

    issues = dataset["issues"]
    if args.issues:
        issues = [i for i in issues if i["id"] in args.issues]

    results = []
    for issue in issues:
        print(f"\n{'='*60}")
        print(f"Running: {issue['id']} — {issue['title']}")
        print(f"Repo: {issue['repo']} | Difficulty: {issue['difficulty']}")
        print(f"{'='*60}\n")

        repo_path = os.path.join("repos", issue["repo"].replace("/", "__"))

        if not os.path.isdir(repo_path):
            print(f"  SKIP: repo not found at {repo_path}")
            print(f"  Run `make setup-repos` first.")
            continue

        # Reset repo to clean state
        subprocess.run(["git", "checkout", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "clean", "-fd"], cwd=repo_path, capture_output=True)

        try:
            result = run(issue, repo_path, timeout=args.timeout)
        except Exception as e:
            result = {
                "patch": "",
                "resolved": False,
                "cost_usd": 0.0,
                "time_seconds": 0.0,
                "model_used": "error",
                "iterations": 0,
                "error": str(e),
            }

        result["issue_id"] = issue["id"]
        results.append(result)

        # Save individual result
        result_path = os.path.join(args.output, f"{issue['id']}.json")
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)

        status = "RESOLVED" if result["resolved"] else "FAILED"
        print(f"\n  Result: {status} | Cost: ${result['cost_usd']:.4f} | Time: {result['time_seconds']:.1f}s")

    # Save summary
    summary_path = os.path.join(args.output, "summary.json")
    with open(summary_path, "w") as f:
        json.dump({
            "tool": Path(__file__).stem,
            "dataset": "qualbench-v0",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "results": results,
        }, f, indent=2)

    print(f"\nResults saved to {args.output}")
    resolved = sum(1 for r in results if r["resolved"])
    print(f"Resolved: {resolved}/{len(results)}")


if __name__ == "__main__":
    main()
