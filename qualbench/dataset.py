"""Dataset loading and validation for QualBench."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class QualityGates:
    cc_max: int = 15
    no_new_bandit_issues: bool = True
    max_lines_changed: int = 100
    cc_reduction_required: bool = False
    must_fix_bandit_issue: bool = False


@dataclass
class Issue:
    id: str
    difficulty: str
    category: str
    repo: str
    version: str
    title: str
    problem_statement: str
    expected_fix: str
    quality_gates: QualityGates = field(default_factory=QualityGates)
    base_commit: Optional[str] = None
    test_patch: Optional[str] = None
    baseline_cc: float = 5.0
    baseline_bandit_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "Issue":
        gates_data = data.get("evaluation", {}).get("quality_gates", {})
        gates = QualityGates(
            cc_max=gates_data.get("cc_max", 15),
            no_new_bandit_issues=gates_data.get("no_new_bandit_issues", True),
            max_lines_changed=gates_data.get("max_lines_changed", 100),
            cc_reduction_required=gates_data.get("cc_reduction_required", False),
            must_fix_bandit_issue=gates_data.get("must_fix_bandit_issue", False),
        )
        return cls(
            id=data["id"],
            difficulty=data["difficulty"],
            category=data["category"],
            repo=data["repo"],
            version=data.get("version", ""),
            title=data["title"],
            problem_statement=data["problem_statement"],
            expected_fix=data.get("expected_fix", ""),
            quality_gates=gates,
            base_commit=data.get("base_commit"),
            test_patch=data.get("test_patch"),
            baseline_cc=data.get("baseline_cc", 5.0),
            baseline_bandit_count=data.get("baseline_bandit_count", 0),
        )


@dataclass
class Dataset:
    version: str
    name: str
    description: str
    issues: list[Issue]

    @classmethod
    def load(cls, path: str | Path) -> "Dataset":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        with open(path) as f:
            data = json.load(f)
        return cls(
            version=data.get("version", "0.1.0"),
            name=data.get("name", "QualBench"),
            description=data.get("description", ""),
            issues=[Issue.from_dict(i) for i in data["issues"]],
        )

    def filter_by_difficulty(self, difficulty: str) -> list[Issue]:
        return [i for i in self.issues if i.difficulty == difficulty]

    def filter_by_ids(self, ids: list[str]) -> list[Issue]:
        return [i for i in self.issues if i.id in ids]

    def __len__(self) -> int:
        return len(self.issues)

    def summary(self) -> dict:
        difficulties = {}
        categories = {}
        repos = set()
        for issue in self.issues:
            difficulties[issue.difficulty] = difficulties.get(issue.difficulty, 0) + 1
            categories[issue.category] = categories.get(issue.category, 0) + 1
            repos.add(issue.repo)
        return {
            "total_issues": len(self.issues),
            "difficulties": difficulties,
            "categories": categories,
            "repositories": sorted(repos),
        }
