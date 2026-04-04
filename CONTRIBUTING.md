# Contributing to QualBench

## Adding your tool (most common contribution)

1. Copy `runners/template.py` to `runners/your_tool.py`
2. Implement the `Runner` class with a `run()` method that returns the portable schema
3. Test locally: `qualbench run --tool your_tool --issue QB-001`
4. Run the full benchmark: `qualbench run --tool your_tool`
5. Submit a PR with your runner and results

The result must conform to the portable JSON schema (see `docs/schema.md`).

## Adding issues to the dataset

Issues for v1+ must come from public repos with >1000 stars, have a known ground-truth solution (merged PR with tests), be self-contained, have >80% test coverage in affected area, and require real reasoning. Submit with the `dataset-proposal` label.

## Improving evaluation

New automated metrics go in `qualbench/evaluation/`. Scoring weight changes require a GitHub Discussion. The portable schema in `docs/schema.md` is the contract — breaking changes need a version bump.

## Code style

Python 3.10+, formatted with ruff, type hints on public functions, tests for new functionality.

```bash
pip install -e ".[test]"
pytest tests/ -v
ruff check qualbench/ tests/
```
