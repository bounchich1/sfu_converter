# Task 28: Enforce 100% Coverage Gate

## Priority: Medium
## Phase: Phase 6 (100% coverage gate)
## Affected files: `pyproject.toml`, CI config, tests
## References: `docs/technical requirements/06_testing_coverage.md`

## Summary

Raise the coverage gate to 100% statement and branch coverage. Add CI configuration to enforce it.

## Steps

### 1. Update `pyproject.toml`

```toml
[tool.coverage.run]
source = ["sfu_converter"]
branch = true

[tool.coverage.report]
fail_under = 100
show_missing = true
skip_empty = true
exclude_also = [
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
```

### 2. Identify and cover uncovered code

Run coverage and systematically add tests for every uncovered line:
```bash
python -m pytest --cov=sfu_converter --cov-branch --cov-report=html
# Open htmlcov/index.html and inspect red lines
```

Common areas that need coverage:
- Error handling paths (file not found, invalid input)
- Edge cases in parser (empty files, malformed markers)
- CLI argument validation
- All renderer code paths
- All validator branches

### 3. Refactor untestable code

If some code is hard to test (e.g., direct `os.system` calls, `sys.exit`), refactor behind testable ports:
- Replace `sys.exit(0)` with returning exit codes
- Replace `os.system('cls')` with injectable screen-clear function
- Replace direct file I/O with injected adapters

### 4. Add CI configuration

Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: python -m pytest --cov=sfu_converter --cov-branch --cov-report=term-missing --cov-fail-under=100
      - run: python -m pytest --cov=sfu_converter --cov-branch --cov-report=xml
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.os }}
          path: coverage.xml
```

### 5. Quality gate checklist

Before merge, these must all pass:
```bash
python -m pytest --cov=sfu_converter --cov-branch --cov-fail-under=100
sfu-converter lint --input examples/report_10_full.txt --profile research_reports --format json
sfu-converter convert --input examples/report_10_full.txt --output .tmp/test.docx --profile research_reports --validate-output --format json
```

## Tests

- Coverage report shows 100% statement coverage
- Coverage report shows 100% branch coverage
- CI runs on both Windows and Linux
- No `# pragma: no cover` or `# type: ignore` used to skip coverage

## Verification

1. `python -m pytest --cov=sfu_converter --cov-branch --cov-fail-under=100` passes
2. CI pipeline passes on both OS
3. HTML report shows all green
