"""QualBench CLI — CI for AI-generated code."""

import json
import shutil
import sys
from pathlib import Path

import click

from qualbench import __version__
from qualbench.dataset import Dataset
from qualbench.benchmark import QualBenchRunner, QualBenchResult


VERDICT_ICONS = {
    "ready_to_merge": "✔",
    "needs_review": "⚠",
    "not_merge_ready": "❌",
}

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
    if d["security"] >= 80:
        click.echo(f"     ✔ Security:     {d['security']:.0f}")
    elif d["security"] >= 50:
        click.echo(f"     ⚠ Security:     {d['security']:.0f} — issues detected")
    else:
        click.echo(f"     ❌ Security:     {d['security']:.0f} — critical issues")

    # Quality
    if d["quality"] >= 80:
        click.echo(f"     ✔ Quality:      {d['quality']:.0f}")
    elif d["quality"] >= 60:
        click.echo(f"     ⚠ Quality:      {d['quality']:.0f} — complexity concerns")
    else:
        click.echo(f"     ❌ Quality:      {d['quality']:.0f} — high complexity")

    # Mergeability
    click.echo(f"     {'✔' if d['mergeability'] >= 70 else '⚠'} Mergeability:  {d['mergeability']:.0f}")

    # Iterations
    click.echo(f"     {'✔' if result.iterations <= 2 else '⚠'} Iterations:    {result.iterations}")

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
def cli():
    """QualBench — CI for AI-generated code."""
    pass


@cli.command()
@click.option("--tool", "-t", default="prollama", help="AI tool name (explicit, no auto-detect)")
@click.option("--mode", "-m", default="quality", type=click.Choice(["cheap", "quality", "secure"]))
@click.option("--issue", "-i", default="LOCAL", help="Issue ID (e.g. QB-001) or LOCAL for current diff")
@click.option("--json-output", "--json", "use_json", is_flag=True, help="Output portable JSON schema")
@click.option("--cwd", default=".", help="Repository path")
@click.option("--fail-on-score", type=int, default=None, help="Exit code 1 if score below this")
def run(tool, mode, issue, use_json, cwd, fail_on_score):
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
def quickstart(tool):
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


def main():
    cli()


if __name__ == "__main__":
    main()
