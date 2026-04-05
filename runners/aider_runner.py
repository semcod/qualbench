"""Aider runner for QualBench — Claude Sonnet integration.

This runner uses Aider (https://aider.chat/) with Claude Sonnet
to solve QualBench issues.

Prerequisites:
    pip install aider-chat
    export ANTHROPIC_API_KEY=...

Usage:
    python runners/aider_runner.py --dataset dataset/qualbench-v1.json --output results/aider/
"""

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path


# Constants
DEFAULT_TIMEOUT = 900
COST_TIME_THRESHOLD_LOW = 300  # 5 min
COST_TIME_THRESHOLD_HIGH = 600  # 10 min
BASE_COST_LOW = 0.30
BASE_COST_MEDIUM = 0.50
BASE_COST_HIGH = 0.80


def run_aider(
    repo_path: str,
    problem_statement: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Run Aider on a repository with the given problem statement.
    
    Aider uses Claude Sonnet by default for complex tasks.
    """
    start_time = time.time()
    
    # Create instructions file for Aider
    instructions = f"""
# Task

{problem_statement}

# Requirements
1. Read the existing code to understand the context
2. Make minimal, focused changes to fix the issue
3. Ensure all existing tests still pass
4. Add or update tests as needed
5. Do not change any other functionality

# Output
After making changes, run the test suite and report:
- What files were modified
- What tests pass/fail
- Any issues encountered
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(instructions)
        instructions_path = f.name
    
    try:
        # Run Aider with Claude Sonnet
        # Aider will auto-detect the repository structure
        cmd = [
            'aider',
            '--model', 'claude-3-5-sonnet-20241022',
            '--yes',  # Auto-accept changes
            '--no-git',  # Don't create git commits
            '--message-file', instructions_path,
            '.',  # Current directory (repo_path)
        ]
        
        env = os.environ.copy()
        env['ANTHROPIC_API_KEY'] = env.get('ANTHROPIC_API_KEY', '')
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        
        elapsed = time.time() - start_time
        
        # Parse Aider output
        # Aider outputs changes made and test results
        output = result.stdout + result.stderr
        
        # Extract changed files
        changed_files = []
        for line in output.split('\n'):
            if 'Added ' in line or 'Modified ' in line:
                file = line.split()[-1]
                changed_files.append(file)
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': output[:5000],
            'stderr': result.stderr[:2000],
            'time_seconds': elapsed,
            'changed_files': changed_files,
            'model': 'claude-3-5-sonnet-20241022',
            'cost_usd': _estimate_cost(output, elapsed),
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': 'Timeout',
            'time_seconds': timeout,
            'changed_files': [],
            'model': 'claude-3-5-sonnet-20241022',
            'cost_usd': _estimate_cost('', timeout),
        }
    finally:
        os.unlink(instructions_path)


def _estimate_cost(output: str, elapsed: float) -> float:
    """Estimate cost based on Aider output and time.
    
    Claude Sonnet: ~$3/million input tokens, $15/million output tokens
    Typical Aider session: ~50k input, ~20k output = $0.45
    """
    # Rough heuristic: $0.30-0.60 per task
    base_cost = BASE_COST_LOW
    if elapsed > COST_TIME_THRESHOLD_LOW:  # >5 min tasks cost more
        base_cost = BASE_COST_MEDIUM
    if elapsed > COST_TIME_THRESHOLD_HIGH:  # >10 min
        base_cost = BASE_COST_HIGH
    return base_cost


def main() -> None:
    parser = argparse.ArgumentParser(description='Run Aider on QualBench dataset')
    parser.add_argument('--dataset', required=True, help='Path to dataset JSON')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--timeout', type=int, default=900, help='Timeout per issue')
    parser.add_argument('--issues', nargs='+', help='Specific issue IDs to run')
    parser.add_argument('--repo-dir', help='Directory with cloned repos')
    
    args = parser.parse_args()
    
    # Load dataset
    with open(args.dataset) as f:
        dataset = json.load(f)
    
    issues = dataset['issues']
    if args.issues:
        issues = [i for i in issues if i['id'] in args.issues]
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run Aider on each issue
    results = []
    for issue in issues:
        print(f"\n🔧 Running Aider on {issue['id']}: {issue['title']}")
        
        repo_path = args.repo_dir or f"repos/{issue['repo'].split('/')[-1]}"
        
        if not Path(repo_path).exists():
            print(f"  ⚠️ Repo not found: {repo_path}")
            continue
        
        result = run_aider(
            repo_path=repo_path,
            problem_statement=issue['problem_statement'],
            timeout=args.timeout,
        )
        
        results.append({
            'issue_id': issue['id'],
            'tool': 'aider',
            'model': result['model'],
            **result,
        })
        
        print(f"  {'✅' if result['success'] else '❌'} {result['time_seconds']:.0f}s ${result['cost_usd']:.2f}")
    
    # Save results
    results_file = output_dir / 'aider_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to {results_file}")
    print(f"  Total: {len(results)} issues")
    print(f"  Success: {sum(1 for r in results if r['success'])}")
    print(f"  Total cost: ${sum(r['cost_usd'] for r in results):.2f}")


if __name__ == '__main__':
    main()
