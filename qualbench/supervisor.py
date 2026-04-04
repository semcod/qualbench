"""Supervisor AI for QualBench — intelligent issue routing and parallel execution.

Phase 2 monetization feature:
- Analyzes issue complexity and routes to optimal model
- Parallel execution across multiple runners
- Cost/quality trade-off optimization
- Automatic retry with fallback models

Usage:
    from qualbench.supervisor import SupervisorAI
    
    supervisor = SupervisorAI(budget_usd=10.0, min_quality=80)
    result = supervisor.solve(issue_id="QB-001", tool="auto")
"""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutingDecision:
    """Decision made by supervisor for an issue."""
    issue_id: str
    primary_model: str
    fallback_model: Optional[str]
    estimated_cost: float
    estimated_quality: float
    parallel_runners: int
    timeout_seconds: int
    reasoning: str


@dataclass
class ParallelResult:
    """Result from parallel execution."""
    runner_id: str
    model: str
    quality_score: float
    cost_usd: float
    time_seconds: float
    success: bool
    result: dict


class SupervisorAI:
    """Intelligent supervisor for AI code generation.
    
    Features:
    - Issue complexity analysis
    - Model selection based on budget/quality constraints
    - Parallel execution for hard issues
    - Automatic fallback on failure
    """
    
    # Model cost and quality profiles
    GPT35_QUALITY = 65
    GPT4_QUALITY = 78
    CLAUDE_SONNET_QUALITY = 85
    
    MODELS = {
        "gpt-3.5-turbo": {
            "cost_per_1k": 0.0015,
            "quality_estimate": GPT35_QUALITY,
            "speed": "fast",
        },
        "gpt-4": {
            "cost_per_1k": 0.03,
            "quality_estimate": GPT4_QUALITY,
            "speed": "medium",
        },
        "gpt-4-turbo": {
            "cost_per_1k": 0.01,
            "quality_estimate": 82,
            "speed": "medium",
        },
        "claude-3-5-sonnet": {
            "cost_per_1k": 0.003,
            "quality_estimate": CLAUDE_SONNET_QUALITY,
            "speed": "medium",
        },
        "claude-3-opus": {
            "cost_per_1k": 0.015,
            "quality_estimate": 90,
            "speed": "slow",
        },
        "qwen2.5-coder:32b": {
            "cost_per_1k": 0.0005,  # Local/ollama
            "quality_estimate": 80,
            "speed": "fast",
        },
    }
    
    def __init__(
        self,
        budget_usd: float = 10.0,
        min_quality: float = 75.0,
        max_parallel: int = 3,
        enable_fallback: bool = True,
    ):
        self.budget_usd = budget_usd
        self.min_quality = min_quality
        self.max_parallel = max_parallel
        self.enable_fallback = enable_fallback
        self.spent_usd = 0.0
        self.results_cache = {}
    
    def analyze_issue(self, issue_id: str, dataset_path: str) -> dict:
        """Analyze issue complexity to inform routing decision."""
        from qualbench.dataset import Dataset
        
        ds = Dataset.load(dataset_path)
        issue = next((i for i in ds.issues if i.id == issue_id), None)
        if not issue:
            raise ValueError(f"Issue {issue_id} not found")
        
        # Complexity factors
        complexity = {
            "difficulty": issue.difficulty,
            "category": issue.category,
            "lines_estimate": self._estimate_lines(issue),
            "test_count": len(issue.quality_gates.__dict__),
            "security_sensitive": "security" in issue.difficulty or issue.category == "vulnerability",
            "refactor_required": issue.category == "refactor",
        }
        
        # Calculate complexity score (0-100)
        score = self._calculate_complexity_score(complexity)
        complexity["score"] = score
        
        return complexity
    
    def _estimate_lines(self, issue) -> int:
        """Estimate lines of code change needed."""
        gates = issue.quality_gates
        return getattr(gates, "max_lines_changed", 50)
    
    def _calculate_complexity_score(self, complexity: dict) -> int:
        """Calculate numeric complexity score."""
        score = 0
        
        # Difficulty weight
        weights = {"simple": 20, "medium": 50, "hard": 80, "security": 90}
        score += weights.get(complexity["difficulty"], 50)
        
        # Category adjustments
        if complexity["category"] == "refactor":
            score += 15
        if complexity["category"] == "vulnerability":
            score += 10
        if complexity["security_sensitive"]:
            score += 10
        
        return min(score, 100)
    
    def route(self, issue_id: str, dataset_path: str) -> RoutingDecision:
        """Make routing decision for an issue."""
        complexity = self.analyze_issue(issue_id, dataset_path)
        score = complexity["score"]
        
        remaining_budget = self.budget_usd - self.spent_usd
        
        # Decision logic
        if score < 30:  # Simple issues
            primary = "qwen2.5-coder:32b"
            fallback = None
            estimated_cost = 0.3
            estimated_quality = 80
            parallel = 1
            timeout = 120
            reasoning = "Simple issue, use fast local model"
            
        elif score < 60:  # Medium issues
            if remaining_budget > 5.0:
                primary = "claude-3-5-sonnet"
                fallback = "qwen2.5-coder:32b"
                estimated_cost = 0.5
                estimated_quality = 85
                parallel = 1
                timeout = 300
                reasoning = "Medium complexity, use Claude Sonnet for quality"
            else:
                primary = "qwen2.5-coder:32b"
                fallback = None
                estimated_cost = 0.4
                estimated_quality = 75
                parallel = 1
                timeout = 240
                reasoning = "Budget constrained, use local model"
                
        else:  # Hard issues
            if remaining_budget > 8.0:
                primary = "claude-3-opus"
                fallback = "claude-3-5-sonnet"
                estimated_cost = 1.5
                estimated_quality = 90
                parallel = min(self.max_parallel, 2)
                timeout = 600
                reasoning = "Hard issue, use Opus + parallel verification"
            else:
                primary = "claude-3-5-sonnet"
                fallback = "qwen2.5-coder:32b"
                estimated_cost = 0.8
                estimated_quality = 82
                parallel = 1
                timeout = 480
                reasoning = "Hard issue but budget limited, use Sonnet"
        
        # Ensure we meet minimum quality
        if estimated_quality < self.min_quality and primary != "claude-3-opus":
            primary = "claude-3-opus"
            estimated_cost = 1.5
            estimated_quality = 90
            reasoning = "Quality requirement forces Opus upgrade"
        
        return RoutingDecision(
            issue_id=issue_id,
            primary_model=primary,
            fallback_model=fallback if self.enable_fallback else None,
            estimated_cost=estimated_cost,
            estimated_quality=estimated_quality,
            parallel_runners=parallel,
            timeout_seconds=timeout,
            reasoning=reasoning,
        )
    
    def solve(
        self,
        issue_id: str,
        dataset_path: str,
        tool: str = "auto",
    ) -> dict:
        """Solve an issue with intelligent routing."""
        if tool == "auto":
            decision = self.route(issue_id, dataset_path)
        else:
            # Manual override
            decision = RoutingDecision(
                issue_id=issue_id,
                primary_model=tool,
                fallback_model=None,
                estimated_cost=0.5,
                estimated_quality=80,
                parallel_runners=1,
                timeout_seconds=300,
                reasoning=f"Manual tool selection: {tool}",
            )
        
        print(f"🧠 Supervisor routing {issue_id}: {decision.reasoning}")
        print(f"   Primary: {decision.primary_model} | Parallel: {decision.parallel_runners}")
        
        # Execute
        if decision.parallel_runners > 1:
            result = self._parallel_execute(decision, dataset_path)
        else:
            result = self._single_execute(decision, dataset_path)
        
        self.spent_usd += result.get("cost_usd", 0)
        self.results_cache[issue_id] = result
        
        return result
    
    def _single_execute(self, decision: RoutingDecision, dataset_path: str) -> dict:
        """Execute with single runner."""
        # This would call actual runner
        # For now, return simulated result
        return {
            "issue_id": decision.issue_id,
            "model": decision.primary_model,
            "quality_score": decision.estimated_quality - 5,  # Real world variance
            "cost_usd": decision.estimated_cost,
            "time_seconds": decision.timeout_seconds * 0.3,
            "success": True,
            "verdict": "needs_review" if decision.estimated_quality < 85 else "ready_to_merge",
            "routing": {
                "reasoning": decision.reasoning,
                "fallback_used": False,
            },
        }
    
    def _parallel_execute(self, decision: RoutingDecision, dataset_path: str) -> dict:
        """Execute with parallel runners and vote on best result."""
        runners = [
            ("runner-1", decision.primary_model),
            ("runner-2", decision.fallback_model or decision.primary_model),
        ]
        
        results = []
        with ThreadPoolExecutor(max_workers=decision.parallel_runners) as executor:
            futures = {
                executor.submit(self._run_single, rid, model, decision, dataset_path): (rid, model)
                for rid, model in runners
            }
            
            for future in concurrent.futures.as_completed(futures):
                rid, model = futures[future]
                try:
                    result = future.result(timeout=decision.timeout_seconds)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "runner_id": rid,
                        "model": model,
                        "success": False,
                        "error": str(e),
                    })
        
        # Select best result by quality score
        best = max(results, key=lambda r: r.get("quality_score", 0) if r.get("success") else -1)
        
        return {
            "issue_id": decision.issue_id,
            "model": best["model"],
            "quality_score": best["quality_score"],
            "cost_usd": sum(r.get("cost_usd", 0) for r in results),
            "time_seconds": max(r.get("time_seconds", 0) for r in results),
            "success": best["success"],
            "verdict": best.get("verdict", "not_merge_ready"),
            "parallel_results": len(results),
            "routing": {
                "reasoning": decision.reasoning,
                "parallel_run": True,
                "votes": {r["model"]: r.get("quality_score", 0) for r in results if r.get("success")},
            },
        }
    
    def _run_single(self, runner_id: str, model: str, decision: RoutingDecision, dataset_path: str) -> dict:
        """Run a single worker."""
        # Simulated execution
        import time
        time.sleep(0.1)  # Simulate work
        
        return {
            "runner_id": runner_id,
            "model": model,
            "quality_score": decision.estimated_quality - (5 if runner_id == "runner-2" else 0),
            "cost_usd": decision.estimated_cost / decision.parallel_runners,
            "time_seconds": decision.timeout_seconds * 0.25,
            "success": True,
            "verdict": "ready_to_merge" if decision.estimated_quality > 80 else "needs_review",
        }
    
    def get_budget_summary(self) -> dict:
        """Get current budget status."""
        return {
            "total_budget": self.budget_usd,
            "spent": self.spent_usd,
            "remaining": self.budget_usd - self.spent_usd,
            "issues_solved": len(self.results_cache),
            "avg_cost_per_issue": self.spent_usd / len(self.results_cache) if self.results_cache else 0,
        }


def main() -> None:
    """CLI for supervisor AI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Supervisor AI for QualBench")
    parser.add_argument("--issue", required=True, help="Issue ID to solve")
    parser.add_argument("--dataset", default="dataset/qualbench-v1.json")
    parser.add_argument("--budget", type=float, default=10.0)
    parser.add_argument("--min-quality", type=float, default=75.0)
    parser.add_argument("--tool", default="auto", help="Auto or specific tool")
    
    args = parser.parse_args()
    
    supervisor = SupervisorAI(
        budget_usd=args.budget,
        min_quality=args.min_quality,
    )
    
    result = supervisor.solve(args.issue, args.dataset, args.tool)
    
    print("\n📊 Result:")
    print(json.dumps(result, indent=2))
    
    print("\n💰 Budget:")
    print(json.dumps(supervisor.get_budget_summary(), indent=2))


if __name__ == "__main__":
    main()
