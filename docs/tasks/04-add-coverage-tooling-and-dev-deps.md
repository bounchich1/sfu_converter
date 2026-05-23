# Task 04: Add Coverage Tooling and Dev Dependencies

## Priority: High
## Phase: Phase 1
## Affected files: `pyproject.toml`, `requirements.txt`

## Summary

Install `pytest-cov` and `coverage` so test coverage can be measured. Currently coverage is unknown because these tools are not installed.

## Detailed Steps

### 1. Add dev dependencies to `pyproject.toml`

In `[project.optional-dependencies]`:
```toml
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "coverage[toml]>=7.0",
]
```

### 2. Configure coverage in `pyproject.toml`

```toml
[tool.coverage.run]
source = ["sfu_converter"]
branch = true

[tool.coverage.report]
show_missing = true
skip_empty = true
# Start with fail_under = 0, raise to 100 in Task 28
fail_under = 0
```

### 3. Create a `Makefile` or document commands

Add to README or create a `Makefile`:
```bash
# Run tests with coverage
python -m pytest --cov=sfu_converter --cov-branch --cov-report=term-missing

# Generate HTML coverage report
python -m pytest --cov=sfu_converter --cov-branch --cov-report=html
```

### 4. Move `pytest` out of `requirements.txt`

`requirements.txt` should contain only production dependencies. `pytest` is a dev dependency.

## Verification

1. `pip install -e ".[dev]"` installs pytest-cov and coverage
2. `python -m pytest --cov=sfu_converter --cov-branch --cov-report=term-missing` runs and shows coverage %
3. Coverage report identifies uncovered lines
