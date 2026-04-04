"""FastAPI leaderboard API for QualBench.

Minimal API per Phase 1 plan:
- POST /api/v1/results — submit result with tool-owner token
- GET /api/v1/leaderboard — get current rankings

Day one: JSON file storage (no database).
"""

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from qualbench.benchmark import QualBenchResult

app = FastAPI(
    title="QualBench Leaderboard API",
    description="Submit and query benchmark results",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
)

# Storage path — configurable via env, defaults to local file
DATA_DIR = Path(os.getenv("QUALBENCH_DATA_DIR", ".data"))
DATA_DIR.mkdir(exist_ok=True)
RESULTS_FILE = DATA_DIR / "results.json"

# Simple token auth for tool owners (day one: single token or demo mode)
API_TOKEN = os.getenv("QUALBENCH_API_TOKEN", "demo-token")


class ResultSubmission(BaseModel):
    """Result in portable schema format."""
    tool: str = Field(..., description="AI tool name")
    issue_id: str = Field(..., description="QualBench issue ID")
    quality_score: float = Field(..., ge=0, le=100)
    dimensions: dict[str, float]
    verdict: str = Field(..., pattern="^(ready_to_merge|needs_review|not_merge_ready)$")
    top_issues: list[str] = []
    patch: str = ""
    resolved: bool = False
    cost_usd: float = 0.0
    time_seconds: float = 0.0
    iterations: int = 1
    model_used: Optional[str] = None


class LeaderboardEntry(BaseModel):
    tool: str
    issue_id: str
    quality_score: float
    verdict: str
    cost_usd: float
    submitted_at: str


class LeaderboardResponse(BaseModel):
    by_quality: list[LeaderboardEntry]
    by_cost_efficiency: list[LeaderboardEntry]
    generated_at: str


def _load_results() -> list[dict]:
    if not RESULTS_FILE.exists():
        return []
    try:
        with open(RESULTS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_results(results: list[dict]):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)


@app.post("/api/v1/results", status_code=201)
def submit_result(
    submission: ResultSubmission,
    authorization: str = Header(None, alias="Authorization"),
) -> dict:
    """Submit a benchmark result. Requires tool-owner token."""
    # Auth check (day one: simple token, can be per-tool later)
    token = authorization.replace("Bearer ", "") if authorization else ""
    if token != API_TOKEN and API_TOKEN != "demo-token":
        raise HTTPException(status_code=401, detail="Invalid token")

    result = {
        **submission.model_dump(),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    results = _load_results()
    # Update if exists (tool + issue_id unique key)
    existing_idx = None
    for i, r in enumerate(results):
        if r.get("tool") == submission.tool and r.get("issue_id") == submission.issue_id:
            existing_idx = i
            break

    if existing_idx is not None:
        results[existing_idx] = result
    else:
        results.append(result)

    _save_results(results)

    return {
        "status": "submitted",
        "tool": submission.tool,
        "issue_id": submission.issue_id,
        "quality_score": submission.quality_score,
    }


@app.get("/api/v1/leaderboard")
def get_leaderboard(
    issue: Optional[str] = None,
    tool: Optional[str] = None,
) -> LeaderboardResponse:
    """Get current leaderboard rankings."""
    results = _load_results()

    # Filter if requested
    if issue:
        results = [r for r in results if r.get("issue_id") == issue]
    if tool:
        results = [r for r in results if r.get("tool") == tool]

    # Convert to leaderboard entries
    entries = [
        LeaderboardEntry(
            tool=r["tool"],
            issue_id=r["issue_id"],
            quality_score=r["quality_score"],
            verdict=r["verdict"],
            cost_usd=r.get("cost_usd", 0),
            submitted_at=r.get("submitted_at", ""),
        )
        for r in results
    ]

    # Sort by quality score (descending)
    by_quality = sorted(entries, key=lambda e: e.quality_score, reverse=True)

    # Sort by cost efficiency (cost per resolved issue, ascending)
    def cost_efficiency(e: LeaderboardEntry) -> float:
        if e.verdict == "not_merge_ready":
            return float("inf")  # Unresolved at bottom
        return e.cost_usd / max(e.quality_score / 100, 0.01)

    by_cost = sorted(entries, key=cost_efficiency)

    return LeaderboardResponse(
        by_quality=by_quality[:50],  # Top 50
        by_cost_efficiency=by_cost[:50],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/v1/results/{tool}/{issue_id}")
def get_result(tool: str, issue_id: str) -> dict:
    """Get specific result by tool and issue."""
    results = _load_results()
    for r in results:
        if r.get("tool") == tool and r.get("issue_id") == issue_id:
            return r
    raise HTTPException(status_code=404, detail="Result not found")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "version": "0.2.0"}
