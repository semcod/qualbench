"""Tests for QualBench v2 — runner, scoring, dataset, schema."""

import json
import pytest

from qualbench.dataset import Dataset, Issue
from qualbench.benchmark import (
    QualBenchResult,
    QualBenchRunner,
    WEIGHTS,
    _score_iterations,
    _score_cost,
    _compute_verdict,
)


class TestQualBenchResult:
    def test_to_dict(self):
        r = QualBenchResult(
            tool="test", issue_id="QB-001", quality_score=74.123,
            dimensions={"correctness": 100, "security": 80, "quality": 65,
                        "mergeability": 75, "iterations": 70, "cost": 90},
            verdict="needs_review", top_issues=["high_complexity"],
        )
        d = r.to_dict()
        assert d["quality_score"] == 74.1
        assert d["dimensions"]["correctness"] == 100.0
        assert d["verdict"] == "needs_review"

    def test_to_json(self):
        r = QualBenchResult(
            tool="test", issue_id="LOCAL", quality_score=50,
            dimensions={"correctness": 0, "security": 50, "quality": 50,
                        "mergeability": 50, "iterations": 50, "cost": 50},
            verdict="not_merge_ready", top_issues=[],
        )
        parsed = json.loads(r.to_json())
        assert "tool" in parsed
        assert "dimensions" in parsed
        assert "verdict" in parsed

    def test_from_dict(self):
        data = {
            "tool": "aider", "issue_id": "QB-005", "quality_score": 82,
            "dimensions": {"correctness": 100, "security": 90, "quality": 70,
                           "mergeability": 85, "iterations": 85, "cost": 75},
            "verdict": "needs_review", "top_issues": [],
        }
        r = QualBenchResult.from_dict(data)
        assert r.tool == "aider"
        assert r.quality_score == 82

    def test_schema_fields_complete(self):
        """Portable schema must have all required fields."""
        r = QualBenchResult(
            tool="t", issue_id="QB-001", quality_score=0,
            dimensions={}, verdict="not_merge_ready", top_issues=[],
        )
        d = r.to_dict()
        required = ["tool", "issue_id", "quality_score", "dimensions",
                     "verdict", "top_issues", "patch", "resolved",
                     "cost_usd", "time_seconds", "iterations", "model_used"]
        for field in required:
            assert field in d, f"Missing field: {field}"


class TestScoring:
    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001

    def test_score_iterations_unresolved(self):
        assert _score_iterations(1, False) == 0

    def test_score_iterations_single_shot(self):
        assert _score_iterations(1, True) == 100

    def test_score_iterations_three(self):
        assert _score_iterations(3, True) == 70

    def test_score_cost_unresolved(self):
        assert _score_cost(0.01, False) == 0

    def test_score_cost_cheap(self):
        assert _score_cost(0.03, True) == 100

    def test_score_cost_expensive(self):
        assert _score_cost(10.0, True) == 5.0

    def test_verdict_ready(self):
        assert _compute_verdict(90) == "ready_to_merge"

    def test_verdict_review(self):
        assert _compute_verdict(70) == "needs_review"

    def test_verdict_not_ready(self):
        assert _compute_verdict(40) == "not_merge_ready"


class TestRunner:
    def test_runner_creates_result(self):
        runner = QualBenchRunner(tool="test-tool", mode="quality", cwd="/tmp")
        result = runner.run("TEST-001")
        assert isinstance(result, QualBenchResult)
        assert result.tool == "test-tool"
        assert result.issue_id == "TEST-001"
        assert 0 <= result.quality_score <= 100
        assert result.verdict in ("ready_to_merge", "needs_review", "not_merge_ready")
        assert isinstance(result.dimensions, dict)
        assert len(result.dimensions) == 6

    def test_runner_json_output_valid(self):
        runner = QualBenchRunner(tool="test", cwd="/tmp")
        result = runner.run()
        parsed = json.loads(result.to_json())
        assert isinstance(parsed["quality_score"], float)
        assert isinstance(parsed["dimensions"], dict)

    def test_runner_modes(self):
        for mode in ("cheap", "quality", "secure"):
            runner = QualBenchRunner(tool="test", mode=mode, cwd="/tmp")
            result = runner.run()
            assert result.cost_usd >= 0


class TestDataset:
    @pytest.fixture
    def sample_dataset(self, tmp_path):
        data = {
            "version": "0.2.0", "name": "test", "description": "Test",
            "issues": [
                {"id": "QB-001", "difficulty": "simple", "category": "bug_fix",
                 "repo": "test/repo", "title": "Bug", "problem_statement": "Fix it"},
                {"id": "QB-002", "difficulty": "hard", "category": "refactor",
                 "repo": "test/repo2", "title": "Refactor", "problem_statement": "Extract"},
            ],
        }
        path = tmp_path / "test.json"
        path.write_text(json.dumps(data))
        return path

    def test_load(self, sample_dataset):
        ds = Dataset.load(sample_dataset)
        assert len(ds) == 2

    def test_filter_by_difficulty(self, sample_dataset):
        ds = Dataset.load(sample_dataset)
        assert len(ds.filter_by_difficulty("simple")) == 1

    def test_summary(self, sample_dataset):
        ds = Dataset.load(sample_dataset)
        s = ds.summary()
        assert s["total_issues"] == 2
        assert len(s["repositories"]) == 2

    def test_load_not_found(self):
        with pytest.raises(FileNotFoundError):
            Dataset.load("/nonexistent.json")
