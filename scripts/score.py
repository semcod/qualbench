"""
QualBench Scoring v1
=====================

6 dimensions: correctness, security, quality, mergeability, iterations, cost.
"""

import argparse
import json
import os
from datetime import datetime


WEIGHTS = {
    "correctness": 0.25,
    "security": 0.15,
    "quality": 0.15,
    "mergeability": 0.25,
    "iterations": 0.10,
    "cost": 0.10,
}


def score_iterations(iterations: int, resolved: bool) -> float:
    """Score iteration efficiency. Lower = better for resolved tasks."""
    if not resolved:
        return 0
    if iterations <= 1:
        return 100
    if iterations == 2:
        return 85
    if iterations == 3:
        return 70
    if iterations <= 5:
        return 50
    return max(0, 100 - iterations * 12)


def score_cost(cost_usd: float, resolved: bool) -> float:
    """Score cost efficiency. Cheaper = better for resolved tasks."""
    if not resolved:
        return 0
    if cost_usd <= 0.05:
        return 100
    if cost_usd <= 0.20:
        return 90
    if cost_usd <= 0.50:
        return 75
    if cost_usd <= 1.00:
        return 60
    if cost_usd <= 2.00:
        return 40
    if cost_usd <= 5.00:
        return 20
    return 5


def compute_mergeability(scores: list[int]) -> float:
    if not scores:
        return 50.0
    avg = sum(scores) / len(scores)
    return (avg - 1) / 4 * 100


def load_human_reviews(reviews_dir: str) -> dict:
    reviews = {}
    if not os.path.isdir(reviews_dir):
        return reviews
    for filename in os.listdir(reviews_dir):
        if filename.endswith(".json"):
            with open(os.path.join(reviews_dir, filename)) as f:
                data = json.load(f)
                for review in data.get("reviews", []):
                    key = f"{review['tool']}/{review['issue_id']}"
                    reviews.setdefault(key, []).append(review["score"])
    return reviews


def score_tool(tool_name: str, evaluations: list[dict], human_reviews: dict) -> dict:
    issue_scores = []

    for ev in evaluations:
        issue_id = ev["issue_id"]

        if ev.get("skipped") or ev.get("no_patch"):
            issue_scores.append({
                "issue_id": issue_id,
                "correctness": 0, "security": 0, "quality": 0,
                "mergeability": 0, "iterations": 0, "cost": 0,
                "quality_score": 0, "resolved": False,
                "cost_usd": 0, "time_seconds": 0, "iteration_count": 0,
            })
            continue

        resolved = ev["correctness"]["score"] == 100
        correctness = ev["correctness"]["score"]
        security = ev["security"]["score"]
        quality = ev["quality"]["score"]

        review_key = f"{tool_name}/{issue_id}"
        human_scores = human_reviews.get(review_key, [])
        mergeability = compute_mergeability(human_scores)

        iteration_count = ev.get("iterations", 1)
        iterations_score = score_iterations(iteration_count, resolved)

        cost_usd = ev.get("cost_usd", 0)
        cost_score = score_cost(cost_usd, resolved)

        quality_score = (
            correctness * WEIGHTS["correctness"]
            + security * WEIGHTS["security"]
            + quality * WEIGHTS["quality"]
            + mergeability * WEIGHTS["mergeability"]
            + iterations_score * WEIGHTS["iterations"]
            + cost_score * WEIGHTS["cost"]
        )

        issue_scores.append({
            "issue_id": issue_id,
            "correctness": round(correctness, 1),
            "security": round(security, 1),
            "quality": round(quality, 1),
            "mergeability": round(mergeability, 1),
            "iterations": round(iterations_score, 1),
            "cost": round(cost_score, 1),
            "quality_score": round(quality_score, 1),
            "resolved": resolved,
            "cost_usd": cost_usd,
            "time_seconds": ev.get("time_seconds", 0),
            "iteration_count": iteration_count,
        })

    total = len(issue_scores)
    resolved_count = sum(1 for s in issue_scores if s["resolved"])
    mergeable_count = sum(1 for s in issue_scores if s["mergeability"] >= 75)
    avg_score = sum(s["quality_score"] for s in issue_scores) / total if total else 0
    avg_cost = sum(s["cost_usd"] for s in issue_scores) / total if total else 0
    avg_iterations = sum(s["iteration_count"] for s in issue_scores) / total if total else 0

    # Cost per mergeable PR
    mergeable_issues = [s for s in issue_scores if s["mergeability"] >= 75]
    total_cost = sum(s["cost_usd"] for s in issue_scores)
    cost_per_mergeable = total_cost / len(mergeable_issues) if mergeable_issues else float("inf")

    return {
        "tool": tool_name,
        "resolved": f"{resolved_count}/{total}",
        "mergeable": f"{mergeable_count}/{total}",
        "avg_quality_score": round(avg_score, 1),
        "avg_cost_per_task": round(avg_cost, 4),
        "cost_per_mergeable_pr": round(cost_per_mergeable, 4) if cost_per_mergeable != float("inf") else "N/A",
        "avg_iterations": round(avg_iterations, 1),
        "issues": issue_scores,
    }


def generate_leaderboard(scores: dict) -> str:
    lines = [
        "# QualBench leaderboard",
        "",
        f"*Updated: {datetime.now().strftime('%Y-%m-%d')}*",
        f"*Dataset: QualBench v0 (10 issues) | [Methodology](docs/methodology.md)*",
        "",
        "## Rankings by Quality Score",
        "",
        "| Rank | Tool | Quality Score | Resolved | Mergeable | Avg Iterations | Cost/Mergeable PR |",
        "|------|------|:------------:|:--------:|:---------:|:--------------:|:-----------------:|",
    ]

    sorted_tools = sorted(scores["tools"], key=lambda t: t["avg_quality_score"], reverse=True)

    for i, tool in enumerate(sorted_tools, 1):
        cpm = tool["cost_per_mergeable_pr"]
        cpm_str = f"${cpm:.2f}" if isinstance(cpm, (int, float)) else cpm
        lines.append(
            f"| {i} | **{tool['tool']}** | {tool['avg_quality_score']} "
            f"| {tool['resolved']} | {tool['mergeable']} "
            f"| {tool['avg_iterations']} | {cpm_str} |"
        )

    lines.extend([
        "",
        "## Rankings by cost per mergeable PR",
        "",
        "| Rank | Tool | Cost/Mergeable PR | Quality Score | Mergeable |",
        "|------|------|:-----------------:|:------------:|:---------:|",
    ])

    cost_sorted = sorted(
        [t for t in sorted_tools if isinstance(t["cost_per_mergeable_pr"], (int, float))],
        key=lambda t: t["cost_per_mergeable_pr"],
    )
    for i, tool in enumerate(cost_sorted, 1):
        lines.append(
            f"| {i} | **{tool['tool']}** | ${tool['cost_per_mergeable_pr']:.2f} "
            f"| {tool['avg_quality_score']} | {tool['mergeable']} |"
        )

    lines.extend([
        "",
        "## Per-issue breakdown",
        "",
    ])

    for tool in sorted_tools:
        lines.append(f"### {tool['tool']}")
        lines.append("")
        lines.append("| Issue | Correct | Security | Quality | Merge | Iters | Cost | **Score** |")
        lines.append("|-------|:-------:|:--------:|:-------:|:-----:|:-----:|:----:|:---------:|")
        for issue in tool["issues"]:
            c = "pass" if issue["resolved"] else "fail"
            lines.append(
                f"| {issue['issue_id']} | {c} | {issue['security']:.0f} "
                f"| {issue['quality']:.0f} | {issue['mergeability']:.0f} "
                f"| {issue['iteration_count']} | ${issue['cost_usd']:.2f} "
                f"| **{issue['quality_score']:.0f}** |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "[Submit your tool](https://github.com/softreck/qualbench#adding-your-tool) to the leaderboard.",
        "",
        "Built by [Softreck](https://softreck.com). Powered by [pyqual](https://github.com/semcod/pyqual).",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", default="results/evaluation.json")
    parser.add_argument("--reviews", default="reviews/")
    parser.add_argument("--output", default="results/scores.json")
    parser.add_argument("--leaderboard", default="LEADERBOARD.md")
    args = parser.parse_args()

    with open(args.evaluation) as f:
        evaluation = json.load(f)

    human_reviews = load_human_reviews(args.reviews)

    scores = {"version": "0.1.0", "weights": WEIGHTS, "tools": []}
    for tool_name, tool_evals in evaluation.items():
        scores["tools"].append(score_tool(tool_name, tool_evals, human_reviews))

    with open(args.output, "w") as f:
        json.dump(scores, f, indent=2)

    with open(args.leaderboard, "w") as f:
        f.write(generate_leaderboard(scores))

    print(f"Scores: {args.output}")
    print(f"Leaderboard: {args.leaderboard}")


if __name__ == "__main__":
    main()
