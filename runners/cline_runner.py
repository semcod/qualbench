"""Cline runner for QualBench — Claude Sonnet via VS Code extension.

This runner simulates Cline (https://github.com/cline/cline) behavior
for solving QualBench issues. Since Cline is a VS Code extension,
this runner uses the underlying Claude API with Cline's prompting style.

Prerequisites:
    pip install anthropic
    export ANTHROPIC_API_KEY=...

Usage:
    python runners/cline_runner.py --dataset dataset/qualbench-v1.json --output results/cline/
"""

import argparse
import json
import os
import time
from pathlib import Path


CLINE_SYSTEM_PROMPT = """You are Cline, a VS Code extension AI assistant specialized in coding tasks.

Your approach:
1. First, explore the codebase to understand the structure
2. Read relevant files related to the task
3. Plan your changes before implementing
4. Make minimal, focused edits
5. Test your changes
6. Iterate if needed

Always:
- Use tools to read files before editing
- Show your reasoning
- Follow existing code style
- Add tests for new functionality
- Verify existing tests still pass"""


def run_cline(
    repo_path: str,
    problem_statement: str,
    timeout: int = 900,
) -> dict:
    """Run Cline-style prompting on a repository.
    
    Simulates Cline's approach using direct Claude API calls.
    """
    start_time = time.time()
    
    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': 'anthropic package not installed: pip install anthropic',
            'time_seconds': 0,
            'changed_files': [],
            'model': 'claude-3-5-sonnet-20241022',
            'cost_usd': 0,
        }
    
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # Phase 1: Explore codebase
    explore_prompt = f"""{CLINE_SYSTEM_PROMPT}

Task: Explore this codebase and understand its structure.

Repository: {repo_path}

Problem to solve:
{problem_statement}

Please:
1. List the directory structure
2. Identify key files related to the problem
3. Read relevant code sections
4. Summarize your findings

Output your exploration in a structured format."""
    
    messages = [{'role': 'user', 'content': explore_prompt}]
    
    try:
        response = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=4096,
            messages=messages,
        )
        exploration = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        
        # Phase 2: Generate solution
        solution_prompt = f"""Based on your exploration:

{exploration}

Now generate the actual code changes to fix the problem:
{problem_statement}

Provide:
1. The exact code changes needed (file path + diff)
2. Any new tests to add
3. Commands to verify the fix

Format as executable commands or clear file edits."""
        
        messages.append({'role': 'assistant', 'content': exploration})
        messages.append({'role': 'user', 'content': solution_prompt})
        
        response2 = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=4096,
            messages=messages,
        )
        solution = response2.content[0].text
        
        total_input = input_tokens + response2.usage.input_tokens
        total_output = output_tokens + response2.usage.output_tokens
        
        # Phase 3: Apply changes (simplified - would parse solution in production)
        # For now, return the solution text for manual review
        elapsed = time.time() - start_time
        
        # Calculate cost (Claude Sonnet pricing)
        # $3/million input, $15/million output
        cost = (total_input / 1_000_000 * 3) + (total_output / 1_000_000 * 15)
        
        return {
            'success': True,
            'returncode': 0,
            'stdout': f"EXPLORATION:\n{exploration}\n\nSOLUTION:\n{solution}",
            'stderr': '',
            'time_seconds': elapsed,
            'changed_files': [],  # Would parse from solution
            'model': 'claude-3-5-sonnet-20241022',
            'cost_usd': round(cost, 3),
            'iterations': 2,
            'tokens': {'input': total_input, 'output': total_output},
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
            'time_seconds': elapsed,
            'changed_files': [],
            'model': 'claude-3-5-sonnet-20241022',
            'cost_usd': 0,
        }


def main():
    parser = argparse.ArgumentParser(description='Run Cline on QualBench dataset')
    parser.add_argument('--dataset', required=True, help='Path to dataset JSON')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--timeout', type=int, default=900, help='Timeout per issue')
    parser.add_argument('--issues', nargs='+', help='Specific issue IDs to run')
    
    args = parser.parse_args()
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set")
        return
    
    # Load dataset
    with open(args.dataset) as f:
        dataset = json.load(f)
    
    issues = dataset['issues']
    if args.issues:
        issues = [i for i in issues if i['id'] in args.issues]
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run Cline on each issue
    results = []
    for issue in issues[:5]:  # Limit to 5 for testing
        print(f"\n🔧 Running Cline on {issue['id']}: {issue['title']}")
        
        repo_path = f"repos/{issue['repo'].split('/')[-1]}"
        
        result = run_cline(
            repo_path=repo_path,
            problem_statement=issue['problem_statement'],
            timeout=args.timeout,
        )
        
        results.append({
            'issue_id': issue['id'],
            'tool': 'cline',
            **result,
        })
        
        status = '✅' if result['success'] else '❌'
        print(f"  {status} {result['time_seconds']:.0f}s ${result['cost_usd']:.2f}")
        
        # Save individual result
        result_file = output_dir / f"{issue['id']}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    # Save summary
    results_file = output_dir / 'cline_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Results saved to {results_file}")
    print(f"  Total: {len(results)} issues")
    print(f"  Success: {sum(1 for r in results if r['success'])}")
    print(f"  Total cost: ${sum(r['cost_usd'] for r in results):.2f}")


if __name__ == '__main__':
    main()
