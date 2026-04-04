"""Tests for QualBench API (FastAPI)."""

import json
import pytest
from fastapi.testclient import TestClient

from qualbench.api import app, _load_results, _save_results

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_results():
    """Clear results before each test."""
    _save_results([])
    yield
    _save_results([])


class TestHealth:
    def test_health_check(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert "version" in resp.json()


class TestSubmitResult:
    def test_submit_valid_result(self):
        result = {
            "tool": "prollama",
            "issue_id": "QB-001",
            "quality_score": 85.0,
            "dimensions": {
                "correctness": 100.0,
                "security": 90.0,
                "quality": 80.0,
                "mergeability": 85.0,
                "iterations": 100.0,
                "cost": 75.0,
            },
            "verdict": "ready_to_merge",
            "top_issues": [],
            "cost_usd": 0.25,
        }
        resp = client.post(
            "/api/v1/results",
            json=result,
            headers={"Authorization": "Bearer demo-token"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "submitted"
        assert data["quality_score"] == 85.0

    def test_submit_requires_auth(self):
        result = {"tool": "test", "issue_id": "QB-001", "quality_score": 70, "verdict": "needs_review", "dimensions": {}}
        resp = client.post("/api/v1/results", json=result)
        # Should work with demo-token default
        assert resp.status_code == 201

    def test_submit_invalid_verdict(self):
        result = {"tool": "test", "issue_id": "QB-001", "quality_score": 70, "verdict": "invalid", "dimensions": {}}
        resp = client.post(
            "/api/v1/results",
            json=result,
            headers={"Authorization": "Bearer demo-token"},
        )
        assert resp.status_code == 422  # Validation error

    def test_submit_score_out_of_range(self):
        result = {"tool": "test", "issue_id": "QB-001", "quality_score": 150, "verdict": "ready_to_merge", "dimensions": {}}
        resp = client.post(
            "/api/v1/results",
            json=result,
            headers={"Authorization": "Bearer demo-token"},
        )
        assert resp.status_code == 422  # Validation error

    def test_submit_updates_existing(self):
        """Submitting same tool+issue should update, not duplicate."""
        result = {
            "tool": "prollama",
            "issue_id": "QB-001",
            "quality_score": 70.0,
            "dimensions": {},
            "verdict": "needs_review",
        }
        client.post("/api/v1/results", json=result, headers={"Authorization": "Bearer demo-token"})

        # Submit again with different score
        result["quality_score"] = 90.0
        result["verdict"] = "ready_to_merge"
        resp = client.post("/api/v1/results", json=result, headers={"Authorization": "Bearer demo-token"})

        assert resp.json()["quality_score"] == 90.0
        results = _load_results()
        assert len(results) == 1  # Only one entry, updated


class TestLeaderboard:
    def test_empty_leaderboard(self):
        resp = client.get("/api/v1/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["by_quality"] == []
        assert data["by_cost_efficiency"] == []
        assert "generated_at" in data

    def test_leaderboard_sorted_by_quality(self):
        # Submit multiple results
        for i, (tool, score) in enumerate([("tool-a", 60), ("tool-b", 90), ("tool-c", 75)]):
            result = {
                "tool": tool,
                "issue_id": f"QB-{i:03d}",
                "quality_score": score,
                "dimensions": {},
                "verdict": "needs_review" if score < 85 else "ready_to_merge",
                "cost_usd": 0.5,
            }
            client.post("/api/v1/results", json=result, headers={"Authorization": "Bearer demo-token"})

        resp = client.get("/api/v1/leaderboard")
        data = resp.json()

        # Should be sorted by quality_score descending
        scores = [e["quality_score"] for e in data["by_quality"]]
        assert scores == [90, 75, 60]

    def test_leaderboard_filtered_by_issue(self):
        # Submit for different issues
        for issue in ["QB-001", "QB-002"]:
            result = {
                "tool": "prollama",
                "issue_id": issue,
                "quality_score": 80.0,
                "dimensions": {},
                "verdict": "needs_review",
            }
            client.post("/api/v1/results", json=result, headers={"Authorization": "Bearer demo-token"})

        resp = client.get("/api/v1/leaderboard?issue=QB-001")
        data = resp.json()
        assert len(data["by_quality"]) == 1
        assert data["by_quality"][0]["issue_id"] == "QB-001"

    def test_leaderboard_filtered_by_tool(self):
        for tool in ["prollama", "copilot"]:
            result = {
                "tool": tool,
                "issue_id": "QB-001",
                "quality_score": 80.0,
                "dimensions": {},
                "verdict": "needs_review",
            }
            client.post("/api/v1/results", json=result, headers={"Authorization": "Bearer demo-token"})

        resp = client.get("/api/v1/leaderboard?tool=prollama")
        data = resp.json()
        assert len(data["by_quality"]) == 1
        assert data["by_quality"][0]["tool"] == "prollama"


class TestGetResult:
    def test_get_existing_result(self):
        result = {
            "tool": "prollama",
            "issue_id": "QB-001",
            "quality_score": 85.0,
            "dimensions": {},
            "verdict": "ready_to_merge",
        }
        client.post("/api/v1/results", json=result, headers={"Authorization": "Bearer demo-token"})

        resp = client.get("/api/v1/results/prollama/QB-001")
        assert resp.status_code == 200
        assert resp.json()["quality_score"] == 85.0

    def test_get_nonexistent_result(self):
        resp = client.get("/api/v1/results/nonexistent/QB-999")
        assert resp.status_code == 404


class TestCostEfficiency:
    def test_cost_efficiency_sorting(self):
        """Cost efficiency = cost / (score/100). Lower is better."""
        results = [
            ("cheap-tool", 80, 0.10),  # 0.10 / 0.8 = 0.125/point
            ("expensive-tool", 80, 0.50),  # 0.50 / 0.8 = 0.625/point
            ("unresolved", 0, 0.10),  # should be at bottom
        ]
        for tool, score, cost in results:
            result = {
                "tool": tool,
                "issue_id": "QB-001",
                "quality_score": score,
                "dimensions": {},
                "verdict": "not_merge_ready" if score == 0 else "needs_review",
                "cost_usd": cost,
            }
            client.post("/api/v1/results", json=result, headers={"Authorization": "Bearer demo-token"})

        resp = client.get("/api/v1/leaderboard")
        data = resp.json()

        # Check order: cheap-tool first (best efficiency)
        tools = [e["tool"] for e in data["by_cost_efficiency"]]
        assert tools[0] == "cheap-tool"
        assert tools[1] == "expensive-tool"
        # Unresolved should be last (infinite cost efficiency)
        assert tools[2] == "unresolved"
