.PHONY: all setup benchmark evaluate score leaderboard test lint clean

DATASET = dataset/qualbench-v0.json
RESULTS_DIR = results
TIMEOUT = 900

all: test lint benchmark evaluate leaderboard

# --- Development ---

install:
	pip install -e ".[test]"

test:
	pytest tests/ -v --tb=short

lint:
	ruff check qualbench/ tests/

# --- Quick start ---

quickstart:
	qualbench quickstart

run:
	qualbench run --tool prollama

run-json:
	qualbench run --tool prollama --json

# --- Full benchmark ---

setup-repos:
	qualbench setup --dataset $(DATASET)

benchmark: run-copilot run-openhands run-prollama

run-copilot:
	python runners/copilot_runner.py --dataset $(DATASET) --output $(RESULTS_DIR)/copilot/ --timeout $(TIMEOUT)

run-openhands:
	python runners/openhands_runner.py --dataset $(DATASET) --output $(RESULTS_DIR)/openhands/ --timeout $(TIMEOUT)

run-prollama:
	python runners/prollama_runner.py --dataset $(DATASET) --output $(RESULTS_DIR)/prollama/ --timeout $(TIMEOUT)

run-custom:
	@test -n "$(TOOL)" || (echo "Usage: make run-custom TOOL=my_tool" && exit 1)
	python runners/$(TOOL).py --dataset $(DATASET) --output $(RESULTS_DIR)/$(TOOL)/ --timeout $(TIMEOUT)

# --- Evaluate ---

evaluate:
	python scripts/evaluate.py --results-dir $(RESULTS_DIR) --dataset $(DATASET)

leaderboard:
	python scripts/score.py --evaluation $(RESULTS_DIR)/evaluation.json --leaderboard LEADERBOARD.md
	@cat LEADERBOARD.md

# --- Docker ---

docker-build:
	docker build -t softreck/qualbench-action:latest action/

docker-run:
	docker run --rm -v $(PWD):/workspace -w /workspace softreck/qualbench-action:latest

# --- Cleanup ---

clean:
	rm -rf repos/ $(RESULTS_DIR)/ reviews/ dist/ build/ *.egg-info
