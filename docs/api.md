# QualBench Leaderboard API

Minimal FastAPI service for submitting and querying benchmark results. Part of Phase 1 core loop.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/results` | Submit result (auth required) |
| GET | `/api/v1/leaderboard` | Get rankings |
| GET | `/api/v1/results/{tool}/{issue_id}` | Get specific result |

## Quick Start

Start the API server and interact with it via CLI or curl.

Start the server, then submit a result and view the leaderboard:

```bash
make serve-api
```

Or use uvicorn directly:

```bash
uvicorn qualbench.api:app --reload --port 8000
```

Submit a result from another terminal:

```bash
qualbench submit --tool prollama --issue QB-001
```

View the leaderboard via CLI or curl:

```bash
qualbench leaderboard
curl http://localhost:8000/api/v1/leaderboard
```

## Authentication

Day one: simple token auth. Set token via env:

```bash
export QUALBENCH_API_TOKEN=your-token
qualbench submit --token $QUALBENCH_API_TOKEN
```

Or use default `demo-token` for local development.

## Submit Result

Submit a benchmark result via the CLI. The CLI handles authentication and result formatting automatically.

```bash
# Run benchmark and submit
qualbench submit --tool prollama --issue QB-001 --api-url http://localhost:8000

# Submit from existing JSON file
qualbench submit --json-file results/prollama/QB-001.json
```

### Request Format

```json
{
  "tool": "prollama",
  "issue_id": "QB-001",
  "quality_score": 85.0,
  "dimensions": {
    "correctness": 100.0,
    "security": 90.0,
    "quality": 80.0,
    "mergeability": 85.0,
    "iterations": 100.0,
    "cost": 75.0
  },
  "verdict": "ready_to_merge",
  "top_issues": [],
  "cost_usd": 0.25,
  "time_seconds": 32.4,
  "iterations": 1,
  "model_used": "qwen2.5-coder:32b"
}
```

### Response

```json
{
  "status": "submitted",
  "tool": "prollama",
  "issue_id": "QB-001",
  "quality_score": 85.0
}
```

## Get Leaderboard

Retrieve current rankings sorted by quality score and cost efficiency.

```bash
curl http://localhost:8000/api/v1/leaderboard
```

### Response

```json
{
  "by_quality": [
    {"tool": "prollama", "quality_score": 91.0, "verdict": "ready_to_merge", ...},
    {"tool": "copilot", "quality_score": 78.0, "verdict": "needs_review", ...}
  ],
  "by_cost_efficiency": [
    {"tool": "taskinity", "cost_usd": 0.05, "quality_score": 80.0, ...},
    {"tool": "prollama", "cost_usd": 0.25, "quality_score": 85.0, ...}
  ],
  "generated_at": "2026-04-04T18:30:00+00:00"
}
```

### Filtering

Filter leaderboard results by issue ID or tool name.

```bash
# Filter by issue
curl "http://localhost:8000/api/v1/leaderboard?issue=QB-001"

# Filter by tool
curl "http://localhost:8000/api/v1/leaderboard?tool=prollama"
```

## Cost Efficiency Ranking

Cost efficiency = cost_usd / (quality_score / 100)

Lower is better. Unresolved issues (verdict: not_merge_ready) are sorted to bottom.

## Storage

Day one: JSON file storage (`.data/results.json`). No database required.

Production: Set `QUALBENCH_DATA_DIR` env var:

```bash
export QUALBENCH_DATA_DIR=/var/lib/qualbench
uvicorn qualbench.api:app
```

## Deployment

Deploy the leaderboard API using Docker or manual configuration.

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[test]"
ENV QUALBENCH_DATA_DIR=/data
EXPOSE 8000
CMD ["uvicorn", "qualbench.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QUALBENCH_DATA_DIR` | `.data` | Results storage path |
| `QUALBENCH_API_TOKEN` | `demo-token` | Auth token |

## Python Client

Use the Python API to run benchmarks and submit results programmatically.

```python
from qualbench.benchmark import QualBenchRunner
import requests

# Run benchmark
runner = QualBenchRunner(tool="prollama")
result = runner.run("QB-001")

# Submit to leaderboard
requests.post(
    "http://localhost:8000/api/v1/results",
    json=result.to_dict(),
    headers={"Authorization": "Bearer demo-token"}
)
```
