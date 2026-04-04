"""QualBench CLI — CI for AI-generated code."""

import json
import shutil
import sys

import click
import requests

from qualbench import __version__
from qualbench.dataset import Dataset
from qualbench.benchmark import QualBenchRunner, QualBenchResult


VERDICT_ICONS = {
    "ready_to_merge": "✔",
    "needs_review": "⚠",
    "not_merge_ready": "❌",
}

# Quality thresholds
SECURITY_THRESHOLD_GOOD = 80
SECURITY_THRESHOLD_WARN = 50
QUALITY_THRESHOLD_GOOD = 80
QUALITY_THRESHOLD_WARN = 60
MERGEABILITY_THRESHOLD = 70
MAX_ACCEPTABLE_ITERATIONS = 2

DIMENSION_LABELS = {
    "correctness": ("Correctness", "PASS" if True else "FAIL"),
    "security": ("Security", None),
    "quality": ("Quality", None),
    "mergeability": ("Mergeability", None),
    "iterations": ("Iterations", None),
    "cost": ("Cost", None),
}


def _print_report(result: QualBenchResult):
    """Pretty-print the QualBench report for humans."""
    icon = VERDICT_ICONS.get(result.verdict, "?")
    click.echo()
    click.secho("🧠 QualBench Report", bold=True)
    click.echo()
    click.secho(f"   Quality Score: {result.quality_score:.0f} / 100", bold=True)
    click.echo()
    click.echo("   Breakdown:")

    d = result.dimensions
    # Correctness
    if d["correctness"] == 100:
        click.echo("     ✔ Correctness:  PASS")
    else:
        click.echo("     ❌ Correctness:  FAIL")

    # Security
    if d["security"] >= SECURITY_THRESHOLD_GOOD:
        click.echo(f"     ✔ Security:     {d['security']:.0f}")
    elif d["security"] >= SECURITY_THRESHOLD_WARN:
        click.echo(f"     ⚠ Security:     {d['security']:.0f} — issues detected")
    else:
        click.echo(f"     ❌ Security:     {d['security']:.0f} — critical issues")

    # Quality
    if d["quality"] >= QUALITY_THRESHOLD_GOOD:
        click.echo(f"     ✔ Quality:      {d['quality']:.0f}")
    elif d["quality"] >= QUALITY_THRESHOLD_WARN:
        click.echo(f"     ⚠ Quality:      {d['quality']:.0f} — complexity concerns")
    else:
        click.echo(f"     ❌ Quality:      {d['quality']:.0f} — high complexity")

    # Mergeability
    click.echo(f"     {'✔' if d['mergeability'] >= MERGEABILITY_THRESHOLD else '⚠'} Mergeability:  {d['mergeability']:.0f}")

    # Iterations
    click.echo(f"     {'✔' if result.iterations <= MAX_ACCEPTABLE_ITERATIONS else '⚠'} Iterations:    {result.iterations}")

    # Cost
    click.echo(f"     💲 Cost:         ${result.cost_usd:.2f}")

    click.echo()
    verdict_display = result.verdict.replace("_", " ")
    click.secho(f"   Verdict: {icon} {verdict_display}", bold=True)

    if result.top_issues:
        click.echo()
        click.echo("   Top issues:")
        for issue in result.top_issues:
            click.echo(f"     → {issue}")
    click.echo()


@click.group()
@click.version_option(__version__)
def cli() -> None:
    """QualBench — CI for AI-generated code."""
    pass


@cli.command()
@click.option("--tool", "-t", default="prollama", help="AI tool name (explicit, no auto-detect)")
@click.option("--mode", "-m", default="quality", type=click.Choice(["cheap", "quality", "secure"]))
@click.option("--issue", "-i", default="LOCAL", help="Issue ID (e.g. QB-001) or LOCAL for current diff")
@click.option("--json-output", "--json", "use_json", is_flag=True, help="Output portable JSON schema")
@click.option("--cwd", default=".", help="Repository path")
@click.option("--fail-on-score", type=int, default=None, help="Exit code 1 if score below this")
def run(tool, mode, issue, use_json, cwd, fail_on_score) -> None:
    """Score the current diff against quality gates."""
    runner = QualBenchRunner(tool=tool, mode=mode, cwd=cwd)
    result = runner.run(issue_id=issue)

    if use_json:
        click.echo(result.to_json())
    else:
        _print_report(result)

    if fail_on_score is not None and result.quality_score < fail_on_score:
        click.secho(
            f"   ❌ Score {result.quality_score:.0f} < threshold {fail_on_score}",
            fg="red", bold=True,
        )
        sys.exit(1)


@cli.command()
@click.option("--tool", "-t", default="prollama")
def quickstart(tool) -> None:
    """Run one issue, show your first score in 60 seconds."""
    click.secho("🚀 QualBench Quickstart", bold=True)
    click.echo(f"   Tool: {tool}")
    click.echo(f"   Scoring current repository...")
    click.echo()

    runner = QualBenchRunner(tool=tool, mode="quality", cwd=".")
    result = runner.run(issue_id="QUICKSTART")
    _print_report(result)

    click.echo("   Next steps:")
    click.echo("     → qualbench run --tool <your-tool>")
    click.echo("     → Add qualbench-action to your CI pipeline")
    click.echo("     → See https://qualbench.com for leaderboard")


@cli.command()
@click.argument("tool")
@click.option("--issue", "-i", default="QB-001")
def compare(tool, issue):
    """Compare your tool against the leaderboard."""
    click.secho(f"📊 Comparing {tool} on {issue}", bold=True)
    click.echo()

    runner = QualBenchRunner(tool=tool, mode="quality", cwd=".")
    result = runner.run(issue_id=issue)

    click.echo(f"   Your score ({tool}): {result.quality_score:.0f}")
    click.echo(f"   Verdict: {result.verdict}")
    click.echo()
    click.echo("   Leaderboard comparison:")
    click.echo("   (Submit results to see your ranking: qualbench submit)")


@cli.command()
@click.option("--dataset", "-d", default="dataset/qualbench-v0.json")
def info(dataset):
    """Show dataset summary."""
    try:
        ds = Dataset.load(dataset)
    except FileNotFoundError:
        click.echo("Dataset not found. Using built-in summary.")
        click.echo("QualBench v0: 10 issues, 7 repos, 4 difficulty tiers")
        return

    summary = ds.summary()
    click.echo(f"Dataset: {ds.name} v{ds.version}")
    click.echo(f"Issues: {summary['total_issues']}")
    click.echo(f"Difficulties: {summary['difficulties']}")
    click.echo(f"Categories: {summary['categories']}")
    click.echo(f"Repositories: {', '.join(summary['repositories'])}")


@cli.command()
def doctor():
    """Check if required tools are available."""
    tools = {"python": "Python", "git": "Git", "docker": "Docker (optional)"}
    modules = {"pytest": "Test runner", "bandit": "Security scanner", "radon": "Complexity", "ruff": "Linter"}

    click.echo("System tools:")
    for tool, desc in tools.items():
        found = shutil.which(tool)
        s = click.style("OK", fg="green") if found else click.style("MISSING", fg="red")
        click.echo(f"  {s} {tool} — {desc}")

    click.echo("\nPython modules:")
    for mod, desc in modules.items():
        try:
            __import__(mod)
            s = click.style("OK", fg="green")
        except ImportError:
            s = click.style("MISSING", fg="red")
        click.echo(f"  {s} {mod} — {desc}")


@cli.command()
@click.option("--tool", "-t", default="prollama", help="AI tool name")
@click.option("--mode", "-m", default="quality", type=click.Choice(["cheap", "quality", "secure"]))
@click.option("--issue", "-i", default="LOCAL", help="Issue ID to submit for")
@click.option("--api-url", default="http://localhost:8000", help="Leaderboard API URL")
@click.option("--token", envvar="QUALBENCH_API_TOKEN", default="demo-token", help="API token (or set QUALBENCH_API_TOKEN)")
@click.option("--json-file", "-f", type=click.Path(exists=True), help="Submit from JSON file instead of running")
def submit(tool, mode, issue, api_url, token, json_file):
    """Submit benchmark result to leaderboard."""
    click.secho("📤 Submitting to QualBench Leaderboard", bold=True)

    if json_file:
        with open(json_file) as f:
            result_data = json.load(f)
        click.echo(f"   Loading result from {json_file}")
    else:
        click.echo(f"   Running benchmark: {tool} on {issue}")
        runner = QualBenchRunner(tool=tool, mode=mode, cwd=".")
        result = runner.run(issue_id=issue)
        result_data = result.to_dict()
        _print_report(result)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        resp = requests.post(
            f"{api_url}/api/v1/results",
            json=result_data,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        click.echo()
        click.secho(f"   ✅ Submitted! Score: {data['quality_score']:.0f}", fg="green", bold=True)
        click.echo(f"   View: {api_url}/api/v1/leaderboard")
    except requests.exceptions.ConnectionError:
        click.secho("   ❌ Cannot connect to API. Is the server running?", fg="red")
        click.echo(f"      URL: {api_url}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        click.secho(f"   ❌ API error: {e.response.status_code}", fg="red")
        click.echo(f"      {e.response.text}")
        sys.exit(1)


@cli.command()
@click.option("--api-url", default="http://localhost:8000", help="Leaderboard API URL")
@click.option("--issue", "-i", help="Filter by issue ID")
@click.option("--tool", "-t", help="Filter by tool name")
def leaderboard(api_url, issue, tool):
    """View current leaderboard rankings."""
    click.secho("📊 QualBench Leaderboard", bold=True)

    params = {}
    if issue:
        params["issue"] = issue
    if tool:
        params["tool"] = tool

    try:
        resp = requests.get(
            f"{api_url}/api/v1/leaderboard",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        click.echo()
        click.echo("   By Quality Score:")
        for i, entry in enumerate(data["by_quality"][:10], 1):
            icon = "✔" if entry["verdict"] == "ready_to_merge" else "⚠" if entry["verdict"] == "needs_review" else "❌"
            click.echo(f"      {i}. {entry['tool']}: {entry['quality_score']:.0f} {icon}")

        click.echo()
        click.echo("   By Cost Efficiency:")
        for i, entry in enumerate(data["by_cost_efficiency"][:10], 1):
            cost_eff = entry["cost_usd"] / max(entry["quality_score"] / 100, 0.01)
            click.echo(f"      {i}. {entry['tool']}: ${cost_eff:.2f}/point")

    except requests.exceptions.ConnectionError:
        click.secho("   ❌ Cannot connect to API", fg="red")
        sys.exit(1)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
