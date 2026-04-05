"""Clone and prepare repositories for benchmarking."""

import subprocess
from pathlib import Path

from qualbench.dataset import Dataset


# Constants
CLONE_DEPTH = 50
ERROR_SNIPPET_LENGTH = 200


REPO_URLS = {
    "pallets/flask": "https://github.com/pallets/flask.git",
    "psf/requests": "https://github.com/psf/requests.git",
    "tiangolo/fastapi": "https://github.com/tiangolo/fastapi.git",
    "django/django": "https://github.com/django/django.git",
    "encode/httpx": "https://github.com/encode/httpx.git",
    "pydantic/pydantic": "https://github.com/pydantic/pydantic.git",
    "encode/starlette": "https://github.com/encode/starlette.git",
}


def clone_repo(repo: str, target: Path, commit: str = None) -> bool:
    """Clone a repository and optionally checkout a specific commit."""
    url = REPO_URLS.get(repo)
    if not url:
        print(f"  WARNING: Unknown repo {repo}, skipping")
        return False

    if target.exists():
        print(f"  EXISTS: {target}")
        return True

    print(f"  Cloning {url}...")
    result = subprocess.run(
        ["git", "clone", "--depth", str(CLONE_DEPTH), url, str(target)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:ERROR_SNIPPET_LENGTH]}")
        return False

    if commit:
        subprocess.run(["git", "checkout", commit], cwd=str(target), capture_output=True)

    return True


def collect_baseline(repo_path: Path) -> dict:
    """Collect baseline metrics (CC, bandit count) for a repository."""
    baseline = {"cc": 0.0, "bandit_count": 0}

    # Cyclomatic complexity
    result = subprocess.run(
        ["python", "-m", "radon", "cc", ".", "-a", "-s", "-n", "C"],
        cwd=str(repo_path), capture_output=True, text=True,
    )
    for line in result.stdout.strip().split("\n"):
        if line.startswith("Average complexity:"):
            try:
                baseline["cc"] = float(line.split("(")[0].split(":")[-1].strip())
            except (ValueError, IndexError):
                pass

    # Bandit findings
    result = subprocess.run(
        ["python", "-m", "bandit", "-r", ".", "-f", "json", "-q"],
        cwd=str(repo_path), capture_output=True, text=True,
    )
    try:
        import json
        data = json.loads(result.stdout) if result.stdout else {"results": []}
        baseline["bandit_count"] = len(data.get("results", []))
    except Exception:
        pass

    return baseline


def setup_repos(dataset: Dataset, output_dir: str = "repos/") -> dict:
    """Clone all repos needed for the dataset."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    repos_needed = set()
    for issue in dataset.issues:
        repos_needed.add(issue.repo)

    results = {}
    for repo in sorted(repos_needed):
        dir_name = repo.replace("/", "__")
        target = output / dir_name
        print(f"\nSetting up {repo}:")
        success = clone_repo(repo, target, commit=None)
        results[repo] = {
            "path": str(target),
            "cloned": success,
        }
        if success:
            print(f"  Collecting baseline metrics...")
            results[repo]["baseline"] = collect_baseline(target)

    return results
