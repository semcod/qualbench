"""Tests for QualBench v2 — runner, scoring, dataset, schema."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from qualbench.dataset import Dataset, Issue
from qualbench.benchmark import (
    QualBenchResult,
    QualBenchRunner,
    WEIGHTS,
    _score_iterations,
    _score_cost,
    _compute_verdict,
)
from qualbench.cli import cli


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

    def test_load_v1_dataset(self):
        """Test loading dataset v1 with TypeScript issues."""
        ds = Dataset.load("dataset/qualbench-v1.json")
        assert len(ds) == 50
        summary = ds.summary()
        assert summary["version"] == "1.0.0"
        assert "languages" in summary
        assert summary["languages"]["python"] == 35
        assert summary["languages"]["typescript"] == 15

    def test_filter_by_language(self):
        """Test filtering issues by language (v1 feature)."""
        ds = Dataset.load("dataset/qualbench-v1.json")
        ts_issues = [i for i in ds.issues if i.quality_gates.language == "typescript"]
        py_issues = [i for i in ds.issues if i.quality_gates.language == "python"]
        assert len(ts_issues) == 15
        assert len(py_issues) == 35


class TestCLI:
    """Tests for CLI commands: run, quickstart, compare, info, doctor."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cli_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.3" in result.output or "qualbench" in result.output.lower()

    def test_run_json_output(self, runner):
        """Test that run --json produces valid portable schema."""
        with patch("qualbench.cli.QualBenchRunner") as mock_runner:
            mock_runner.return_value.run.return_value = QualBenchResult(
                tool="test", issue_id="LOCAL", quality_score=75,
                dimensions={"correctness": 100, "security": 80, "quality": 70,
                           "mergeability": 75, "iterations": 80, "cost": 60},
                verdict="needs_review", top_issues=[],
            )
            result = runner.invoke(cli, ["run", "--tool", "test", "--json", "--cwd", "/tmp"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "quality_score" in parsed
        assert "dimensions" in parsed
        assert "verdict" in parsed

    def test_run_fail_on_score_pass(self, runner):
        """Test fail_on_score when score is above threshold."""
        with patch("qualbench.cli.QualBenchRunner") as mock_runner:
            mock_runner.return_value.run.return_value = QualBenchResult(
                tool="test", issue_id="LOCAL", quality_score=75,
                dimensions={"correctness": 100, "security": 80, "quality": 70,
                           "mergeability": 75, "iterations": 80, "cost": 60},
                verdict="needs_review", top_issues=[],
            )
            result = runner.invoke(cli, ["run", "--tool", "test", "--json", "--fail-on-score", "0", "--cwd", "/tmp"])
        # Should pass (exit 0) because any score >= 0
        assert result.exit_code == 0

    def test_run_fail_on_score_fail(self, runner):
        """Test fail_on_score when score would be below threshold."""
        with patch("qualbench.cli.QualBenchRunner") as mock_runner:
            mock_runner.return_value.run.return_value = QualBenchResult(
                tool="test", issue_id="LOCAL", quality_score=75,
                dimensions={"correctness": 100, "security": 80, "quality": 70,
                           "mergeability": 75, "iterations": 80, "cost": 60},
                verdict="needs_review", top_issues=[],
            )
            result = runner.invoke(cli, ["run", "--tool", "test", "--json", "--fail-on-score", "100", "--cwd", "/tmp"])
        # Should fail (exit 1) because score 75 < threshold 100
        assert result.exit_code == 1

    def test_quickstart_command(self, runner):
        """Test quickstart shows report and next steps."""
        with patch("qualbench.cli.QualBenchRunner") as mock_runner:
            mock_runner.return_value.run.return_value = QualBenchResult(
                tool="test", issue_id="QUICKSTART", quality_score=75,
                dimensions={"correctness": 100, "security": 80, "quality": 70,
                           "mergeability": 75, "iterations": 80, "cost": 60},
                verdict="needs_review", top_issues=[],
            )
            result = runner.invoke(cli, ["quickstart", "--tool", "test"])
        assert result.exit_code == 0
        assert "QualBench" in result.output
        assert "Next steps" in result.output or "quickstart" in result.output.lower()

    def test_compare_command(self, runner):
        """Test compare command runs and shows score."""
        with patch("qualbench.cli.QualBenchRunner") as mock_runner:
            mock_runner.return_value.run.return_value = QualBenchResult(
                tool="my-tool", issue_id="QB-001", quality_score=75,
                dimensions={"correctness": 100, "security": 80, "quality": 70,
                           "mergeability": 75, "iterations": 80, "cost": 60},
                verdict="needs_review", top_issues=[],
            )
            result = runner.invoke(cli, ["compare", "my-tool", "--issue", "QB-001"])
        assert result.exit_code == 0
        assert "Comparing" in result.output or "score" in result.output.lower()

    def test_info_command_builtin(self, runner):
        """Test info shows built-in summary when dataset not found."""
        result = runner.invoke(cli, ["info", "--dataset", "/nonexistent/path.json"])
        assert result.exit_code == 0
        assert "QualBench" in result.output

    def test_doctor_command(self, runner):
        """Test doctor checks system tools and Python modules."""
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        # Should report on tools - either OK or MISSING
        assert "python" in result.output.lower() or "git" in result.output.lower()


class TestActionIntegration:
    """Tests for GitHub Action integration points."""

    def test_action_output_schema(self):
        """Verify action can parse runner JSON output."""
        runner = QualBenchRunner(tool="action-test", cwd="/tmp")
        result = runner.run("TEST-ACTION")
        json_str = result.to_json()
        parsed = json.loads(json_str)

        # Action expects these fields in GITHUB_OUTPUT
        assert "quality_score" in parsed
        assert "verdict" in parsed
        assert isinstance(parsed["quality_score"], (int, float))
        assert parsed["verdict"] in ("ready_to_merge", "needs_review", "not_merge_ready")

    def test_verdict_thresholds_match_action(self):
        """Verdict thresholds must match action/fail_on_score logic."""
        assert _compute_verdict(85) == "ready_to_merge"
        assert _compute_verdict(65) == "needs_review"
        assert _compute_verdict(64) == "not_merge_ready"
        # Boundary check
        assert _compute_verdict(84) == "needs_review"
        assert _compute_verdict(86) == "ready_to_merge"
